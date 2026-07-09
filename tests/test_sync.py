"""Tests for the synchronous facade (SyncKoraiClient).

These are plain (non-async) test functions — the whole point is that the
client is usable from synchronous code. respx patches httpx globally, so it
intercepts the requests the sync client issues on its background loop.
"""

from __future__ import annotations

import json

import httpx
import respx

from korai import SyncKoraiClient
from korai.tools import Tool, ToolInput, ToolOutput

TEST_BASE_URL = "https://test.korai.local"


def _sse_chunks(events: list[dict]) -> bytes:
    out = bytearray()
    for ev in events:
        out.extend(b"data: ")
        out.extend(json.dumps(ev).encode("utf-8"))
        out.extend(b"\n\n")
    out.extend(b"data: [DONE]\n\n")
    return bytes(out)


def test_sync_buffered_call(respx_mock: respx.Router) -> None:
    respx_mock.get("/billing/balance").mock(
        return_value=httpx.Response(200, json={"balance_eur": 1.5})
    )
    with SyncKoraiClient(api_key="sk-korai-test", base_url=TEST_BASE_URL) as client:
        balance = client.billing.get_balance()
        assert balance.balance_eur == 1.5


def test_sync_list_models(respx_mock: respx.Router) -> None:
    respx_mock.get("/v1/models").mock(
        return_value=httpx.Response(
            200,
            json={"object": "list", "data": [{"id": "auto", "kind": "alias"}]},
        )
    )
    with SyncKoraiClient(base_url=TEST_BASE_URL) as client:
        assert client.llm.list_models() == ["auto"]


def test_sync_count_tokens(respx_mock: respx.Router) -> None:
    respx_mock.post("/v1/count_tokens").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "token_count",
                "model": "auto",
                "resolved_model": "claude-opus-4-7",
                "prompt_tokens": 42,
            },
        )
    )
    with SyncKoraiClient(base_url=TEST_BASE_URL) as client:
        tc = client.llm.count_tokens(messages=[{"role": "user", "content": "hi"}])
        assert tc.prompt_tokens == 42
        assert tc.resolved_model == "claude-opus-4-7"


def test_sync_streaming(respx_mock: respx.Router) -> None:
    chunks = [
        {"choices": [{"index": 0, "delta": {"content": "Bon"}, "finish_reason": None}]},
        {"choices": [{"index": 0, "delta": {"content": "jour"}, "finish_reason": None}]},
        {"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]},
    ]
    respx_mock.post("/v1/chat/completions").mock(
        return_value=httpx.Response(
            200, content=_sse_chunks(chunks), headers={"content-type": "text/event-stream"}
        )
    )
    with SyncKoraiClient(base_url=TEST_BASE_URL) as client:
        deltas = [
            ev.delta
            for ev in client.llm.stream(messages=[{"role": "user", "content": "hi"}])
            if ev.type == "content_delta"
        ]
    assert "".join(deltas) == "Bonjour"


class _AddIn(ToolInput):
    a: int
    b: int


class _AddOut(ToolOutput):
    sum: int


class _AddTool(Tool[_AddIn, _AddOut]):
    name = "add"
    description = "Add two integers"
    input_model = _AddIn
    output_model = _AddOut

    async def execute(self, value: _AddIn) -> _AddOut:
        return _AddOut(sum=value.a + value.b)


def test_sync_tool_runner(respx_mock: respx.Router) -> None:
    tool_call = {
        "id": "1",
        "object": "chat.completion",
        "model": "auto",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "add", "arguments": '{"a": 2, "b": 3}'},
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
    }
    final = {
        "id": "2",
        "object": "chat.completion",
        "model": "auto",
        "choices": [
            {"index": 0, "message": {"role": "assistant", "content": "5"}, "finish_reason": "stop"}
        ],
    }
    respx_mock.post("/v1/chat/completions").mock(
        side_effect=[httpx.Response(200, json=tool_call), httpx.Response(200, json=final)]
    )
    with SyncKoraiClient(base_url=TEST_BASE_URL) as client:
        client.tools.register(_AddTool())  # sync method passes through
        res = client.tools.run(messages=[{"role": "user", "content": "2+3?"}])
        assert res.final.content == "5"
        assert res.tool_runs[0].output["sum"] == 5


def test_sync_request_raw_no_raise(respx_mock: respx.Router) -> None:
    respx_mock.get("/health").mock(
        return_value=httpx.Response(503, headers={"x-request-id": "req_1"}, json={"error": {}})
    )
    with SyncKoraiClient(base_url=TEST_BASE_URL, max_retries=0) as client:
        resp = client.request_raw("GET", "/health")
        assert resp.status_code == 503  # did not raise
        assert resp.headers["x-request-id"] == "req_1"


def test_sync_with_options(respx_mock: respx.Router) -> None:
    respx_mock.get("/billing/balance").mock(
        return_value=httpx.Response(200, json={"balance_eur": 9.0})
    )
    with SyncKoraiClient(base_url=TEST_BASE_URL, max_retries=2) as client:
        clone = client.with_options(max_retries=0)
        try:
            assert clone.base_url == TEST_BASE_URL
            assert clone.billing.get_balance().balance_eur == 9.0
        finally:
            clone.close()
