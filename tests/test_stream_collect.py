"""Tests for LLMModule.collect_stream / stream_to_completion."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx
import pytest
import respx

from korai import KoraiAPIError, KoraiClient
from korai.llm import CompletionResult, Message, StreamEvent


def _sse_chunks(events: list[dict]) -> bytes:
    """Encode a list of dicts as concatenated SSE chunks ending with [DONE]."""
    out = bytearray()
    for ev in events:
        out.extend(b"data: ")
        out.extend(json.dumps(ev).encode("utf-8"))
        out.extend(b"\n\n")
    out.extend(b"data: [DONE]\n\n")
    return bytes(out)


async def test_stream_to_completion_concatenates_content(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    chunks = [
        {
            "id": "c1",
            "choices": [{"index": 0, "delta": {"content": "Bonjour"}, "finish_reason": None}],
        },
        {
            "id": "c1",
            "choices": [{"index": 0, "delta": {"content": " Korai"}, "finish_reason": None}],
        },
        {
            "id": "c1",
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
    result = await client.llm.stream_to_completion(
        messages=[Message(role="user", content="hi")]
    )
    assert isinstance(result, CompletionResult)
    assert result.content == "Bonjour Korai"
    assert result.stop_reason == "stop"


async def test_collect_stream_gathers_thinking_and_citations(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    chunks = [
        {
            "id": "c1",
            "choices": [
                {"index": 0, "delta": {"thinking": "hmm"}, "finish_reason": None}
            ],
        },
        {
            "id": "c1",
            "attribution": {
                "citations": [{"title": "RFC 9110", "url": "https://example.com/x"}]
            },
            "choices": [
                {"index": 0, "delta": {"content": "answer"}, "finish_reason": "stop"}
            ],
        },
    ]
    respx_mock.post("/v1/chat/completions").mock(
        return_value=httpx.Response(200, content=_sse_chunks(chunks))
    )
    stream = await client.llm.stream(messages=[Message(role="user", content="hi")])
    result = await client.llm.collect_stream(stream)
    assert result.content == "answer"
    assert result.thinking == "hmm"
    assert len(result.citations) == 1
    assert result.citations[0].url == "https://example.com/x"


async def test_collect_stream_raises_on_error_event(client: KoraiClient) -> None:
    async def _events() -> AsyncIterator[StreamEvent]:
        yield StreamEvent(type="message_start")
        yield StreamEvent(type="content_delta", delta="partial")
        yield StreamEvent(type="error", error="boom")

    with pytest.raises(KoraiAPIError) as excinfo:
        await client.llm.collect_stream(_events())
    assert "boom" in str(excinfo.value)
