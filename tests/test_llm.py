"""Tests for korai.llm.LLMModule."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from korai import KoraiAPIError, KoraiClient
from korai.llm import MODES, CompletionResult, Message, SolveRun, StreamEvent, TokenCount

OPENAI_RESPONSE = {
    "id": "chatcmpl-1",
    "object": "chat.completion",
    "created": 1_700_000_000,
    "model": "claude-opus-4-7",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Bonjour Korai!",
            },
            "finish_reason": "stop",
        }
    ],
    "usage": {
        "prompt_tokens": 12,
        "completion_tokens": 4,
        "total_tokens": 16,
    },
}


async def test_complete_simple(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    route = respx_mock.post("/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=OPENAI_RESPONSE)
    )
    result = await client.llm.complete(
        messages=[Message(role="user", content="Hello")]
    )
    assert isinstance(result, CompletionResult)
    assert result.content == "Bonjour Korai!"
    assert result.input_tokens == 12
    assert result.output_tokens == 4
    assert result.model == "claude-opus-4-7"
    assert result.stop_reason == "stop"
    assert result.latency_ms >= 0
    body = json.loads(route.calls[0].request.read())
    assert body["stream"] is False
    assert body["messages"][-1]["role"] == "user"


async def test_complete_with_system_prompt(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    route = respx_mock.post("/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=OPENAI_RESPONSE)
    )
    await client.llm.complete(
        messages=[Message(role="user", content="Hi")],
        system="You are precise.",
    )
    body = json.loads(route.calls[0].request.read())
    assert body["messages"][0]["role"] == "system"
    assert body["messages"][0]["content"] == "You are precise."


async def test_complete_with_dict_messages(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.post("/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=OPENAI_RESPONSE)
    )
    out = await client.llm.complete(
        messages=[{"role": "user", "content": "ping"}]
    )
    assert out.content == "Bonjour Korai!"


async def test_complete_with_tools_forwards_field(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    route = respx_mock.post("/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=OPENAI_RESPONSE)
    )
    await client.llm.complete(
        messages=[Message(role="user", content="Hi")],
        tools=[{"type": "function", "function": {"name": "ping"}}],
    )
    body = json.loads(route.calls[0].request.read())
    assert body["tools"][0]["function"]["name"] == "ping"


async def test_complete_extracts_attribution(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    payload = {
        **OPENAI_RESPONSE,
        "attribution": {
            "citations": [
                {
                    "title": "RFC 9110",
                    "url": "https://example.com/rfc9110",
                    "snippet": "HTTP semantics",
                }
            ]
        },
    }
    respx_mock.post("/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=payload)
    )
    result = await client.llm.complete(
        messages=[Message(role="user", content="info")]
    )
    assert len(result.citations) == 1
    assert result.citations[0].url == "https://example.com/rfc9110"
    assert result.citations[0].excerpt == "HTTP semantics"


async def test_list_models(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/v1/models").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "list",
                "data": [
                    {"id": "auto", "object": "model"},
                    {"id": "claude-opus-4-7", "object": "model"},
                ],
            },
        )
    )
    models = await client.llm.list_models()
    assert "auto" in models
    assert "claude-opus-4-7" in models


async def test_list_models_returns_empty_on_unexpected_shape(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/v1/models").mock(
        return_value=httpx.Response(200, json={"unexpected": "shape"})
    )
    models = await client.llm.list_models()
    assert models == []


async def test_count_tokens(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    route = respx_mock.post("/v1/count_tokens").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "token_count",
                "model": "auto",
                "resolved_model": "claude-opus-4-7",
                "prompt_tokens": 27,
            },
        )
    )
    result = await client.llm.count_tokens(
        messages=[Message(role="user", content="Combien de tokens ?")],
    )
    assert isinstance(result, TokenCount)
    assert result.prompt_tokens == 27
    assert result.model == "auto"
    assert result.resolved_model == "claude-opus-4-7"
    body = json.loads(route.calls[0].request.read())
    assert body["model"] == "auto"
    assert body["messages"] == [
        {"role": "user", "content": "Combien de tokens ?"}
    ]
    # Sampling/stream fields must not leak into the count request.
    assert "max_tokens" not in body
    assert "stream" not in body


async def test_count_tokens_drops_extra_message_fields(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    route = respx_mock.post("/v1/count_tokens").mock(
        return_value=httpx.Response(
            200,
            json={"object": "token_count", "model": "fast", "prompt_tokens": 3},
        )
    )
    result = await client.llm.count_tokens(
        messages=[
            {"role": "assistant", "content": "hi", "name": "bot", "tool_calls": []}
        ],
        model="fast",
    )
    assert result.prompt_tokens == 3
    assert result.resolved_model is None
    body = json.loads(route.calls[0].request.read())
    # Only role + content survive serialization.
    assert body["messages"] == [{"role": "assistant", "content": "hi"}]


def _sse_chunks(events: list[dict]) -> bytes:
    """Encode a list of dicts as concatenated SSE chunks ending with [DONE]."""
    out = bytearray()
    for ev in events:
        out.extend(b"data: ")
        out.extend(json.dumps(ev).encode("utf-8"))
        out.extend(b"\n\n")
    out.extend(b"data: [DONE]\n\n")
    return bytes(out)


async def test_stream_basic(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    chunks = [
        {
            "id": "c1",
            "object": "chat.completion.chunk",
            "model": "claude-opus-4-7",
            "choices": [{"index": 0, "delta": {"content": "Hello"}, "finish_reason": None}],
        },
        {
            "id": "c1",
            "object": "chat.completion.chunk",
            "model": "claude-opus-4-7",
            "choices": [{"index": 0, "delta": {"content": " World"}, "finish_reason": None}],
        },
        {
            "id": "c1",
            "object": "chat.completion.chunk",
            "model": "claude-opus-4-7",
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        },
    ]
    respx_mock.post("/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            content=_sse_chunks(chunks),
            headers={"content-type": "text/event-stream"},
        )
    )
    types: list[str] = []
    deltas: list[str] = []
    stream = await client.llm.stream(
        messages=[Message(role="user", content="hi")]
    )
    async for ev in stream:
        types.append(ev.type)
        if ev.type == "content_delta":
            deltas.append(ev.delta)
    assert types[0] == "message_start"
    assert types[-1] == "message_stop"
    assert "".join(deltas) == "Hello World"


async def test_stream_with_tool_use(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    chunks = [
        {
            "id": "c1",
            "object": "chat.completion.chunk",
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "lookup",
                                    "arguments": '{"q":"x"}',
                                }
                            }
                        ]
                    },
                    "finish_reason": None,
                }
            ],
        },
    ]
    respx_mock.post("/v1/chat/completions").mock(
        return_value=httpx.Response(200, content=_sse_chunks(chunks))
    )
    events: list[StreamEvent] = []
    stream = await client.llm.stream(messages=[Message(role="user", content="hi")])
    async for ev in stream:
        events.append(ev)
    tool_events = [e for e in events if e.type == "tool_use_complete"]
    assert len(tool_events) == 1
    assert tool_events[0].tool_name == "lookup"
    assert tool_events[0].tool_input == {"q": "x"}


async def test_stream_emits_error_on_4xx(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.post("/v1/chat/completions").mock(
        return_value=httpx.Response(400, json={"error": {"message": "bad"}})
    )
    with pytest.raises(KoraiAPIError):
        stream = await client.llm.stream(messages=[Message(role="user", content="hi")])
        async for _ in stream:
            pass


async def test_stream_yields_thinking_delta(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    chunks = [
        {
            "id": "c1",
            "choices": [
                {
                    "index": 0,
                    "delta": {"thinking": "let me consider..."},
                    "finish_reason": None,
                }
            ],
        },
        {
            "id": "c1",
            "choices": [
                {"index": 0, "delta": {"content": "answer"}, "finish_reason": "stop"}
            ],
        },
    ]
    respx_mock.post("/v1/chat/completions").mock(
        return_value=httpx.Response(200, content=_sse_chunks(chunks))
    )
    types: list[str] = []
    stream = await client.llm.stream(messages=[Message(role="user", content="hi")])
    async for ev in stream:
        types.append(ev.type)
    assert "thinking_delta" in types
    assert "content_delta" in types


def test_events_from_chunk_emits_usage() -> None:
    from korai.llm import _events_from_chunk

    evs = _events_from_chunk(
        {
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
        },
        True,
    )
    usage_evs = [e for e in evs if e.type == "usage"]
    assert len(usage_evs) == 1
    assert usage_evs[0].usage is not None
    assert usage_evs[0].usage.prompt_tokens == 11
    assert usage_evs[0].usage.completion_tokens == 7
    assert usage_evs[0].usage.total_tokens == 18


def test_events_from_chunk_emits_status() -> None:
    from korai.llm import _events_from_chunk

    evs = _events_from_chunk({"status": "consulting"}, False)
    assert len(evs) == 1
    assert evs[0].type == "status"
    assert evs[0].status == "consulting"


async def test_collect_stream_folds_usage(client: KoraiClient) -> None:
    from korai.llm import StreamUsage

    async def gen():
        yield StreamEvent(type="content_delta", delta="hi")
        yield StreamEvent(
            type="usage",
            usage=StreamUsage(prompt_tokens=11, completion_tokens=7, total_tokens=18),
        )

    result = await client.llm.collect_stream(gen())
    assert result.content == "hi"
    assert result.input_tokens == 11
    assert result.output_tokens == 7


# ───────────────────────────────────────────────────────────────────────
# max mode + durable solve
# ───────────────────────────────────────────────────────────────────────


def test_max_mode_in_modes() -> None:
    assert "max" in MODES
    # Ladder order preserved, max last.
    assert MODES == ["auto", "fast", "balanced", "deep", "max"]


async def test_solve_posts_and_parses_run_id(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    route = respx_mock.post("/v1/solve").mock(
        return_value=httpx.Response(202, json={"run_id": "run-abc", "status": "running"})
    )
    run = await client.llm.solve(
        messages=[Message(role="user", content="Prove it")],
    )
    assert isinstance(run, SolveRun)
    assert run.run_id == "run-abc"
    assert run.status == "running"
    body = json.loads(route.calls[0].request.read())
    assert body["model"] == "max"
    assert body["messages"][-1]["content"] == "Prove it"


async def test_get_solve_run_parses_done(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/v1/solve/run-abc").mock(
        return_value=httpx.Response(
            200,
            json={
                "run_id": "run-abc",
                "status": "done",
                "model": "max",
                "result": "42",
                "error": None,
                "usage": {"prompt_tokens": 100, "completion_tokens": 250},
            },
        )
    )
    run = await client.llm.get_solve_run("run-abc")
    assert run.status == "done"
    assert run.result == "42"
    assert run.model == "max"
    assert run.prompt_tokens == 100
    assert run.completion_tokens == 250


async def test_get_solve_run_404_raises(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/v1/solve/missing").mock(
        return_value=httpx.Response(404, json={"error": {"message": "not found"}})
    )
    with pytest.raises(KoraiAPIError):
        await client.llm.get_solve_run("missing")


async def test_solve_and_wait_polls_until_done(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.post("/v1/solve").mock(
        return_value=httpx.Response(202, json={"run_id": "run-1", "status": "running"})
    )
    states = iter(
        [
            {"run_id": "run-1", "status": "running"},
            {
                "run_id": "run-1",
                "status": "done",
                "result": "final",
                "usage": {"prompt_tokens": 5, "completion_tokens": 9},
            },
        ]
    )
    respx_mock.get("/v1/solve/run-1").mock(
        side_effect=lambda request: httpx.Response(200, json=next(states))
    )
    run = await client.llm.solve_and_wait(
        messages=[Message(role="user", content="go")],
        poll_interval=0.0,
        timeout=5.0,
    )
    assert run.status == "done"
    assert run.result == "final"
    assert run.completion_tokens == 9


async def test_solve_and_wait_raises_on_error(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.post("/v1/solve").mock(
        return_value=httpx.Response(202, json={"run_id": "run-e", "status": "running"})
    )
    respx_mock.get("/v1/solve/run-e").mock(
        return_value=httpx.Response(
            200, json={"run_id": "run-e", "status": "error", "error": "boom"}
        )
    )
    with pytest.raises(KoraiAPIError):
        await client.llm.solve_and_wait(
            messages=[Message(role="user", content="go")],
            poll_interval=0.0,
            timeout=5.0,
        )
