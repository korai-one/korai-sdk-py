"""LLM module — chat completions, streaming, tool-use against Korai Cloud.

Korai Cloud exposes an OpenAI-compatible ``POST /v1/chat/completions``
endpoint (streaming SSE or full-response JSON) plus ``GET /v1/models``.
This module wraps both with typed Pydantic models.

Example::

    from korai import KoraiClient
    from korai.llm import Message

    async with KoraiClient(api_key="sk-korai-***") as client:
        result = await client.llm.complete(
            messages=[Message(role="user", content="Bonjour Korai")],
            model="claude-opus-4-7",
        )
        print(result.content)

        async for event in client.llm.stream(
            messages=[Message(role="user", content="Stream me")],
        ):
            if event.type == "content_delta":
                print(event.delta, end="", flush=True)
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field

from korai._client import _RawBody
from korai._errors import KoraiAPIError
from korai._generated.api.inference import count_tokens as count_tokens_api
from korai._generated.api.inference import create_chat_completion
from korai._generated.api.inference import list_models as list_models_api

if TYPE_CHECKING:
    from korai._client import KoraiClient


# ───────────────────────────────────────────────────────────────────────
# Models
# ───────────────────────────────────────────────────────────────────────


class Message(BaseModel):
    """A chat message in a conversation.

    Mirrors the OpenAI chat.completions message schema. Tool-call
    metadata is preserved for round-tripping, even though Korai Cloud's
    OpenAI-compat endpoint only consumes ``role`` + ``content`` today.
    """

    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] | None = None


class Citation(BaseModel):
    """A legal/source citation embedded in an LLM response."""

    display: str
    law_code: str | None = None
    article_number: str | None = None
    paragraph: str | None = None
    letter: str | None = None
    url: str | None = None
    excerpt: str | None = None
    verified: bool | None = None


class CompletionResult(BaseModel):
    """Non-streaming completion response."""

    content: str
    thinking: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    model: str
    stop_reason: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


class TokenCount(BaseModel):
    """Result of ``POST /v1/count_tokens``.

    The exact number of prompt tokens the given messages occupy under the
    hosting model's own tokenizer and chat template (not an estimate). No
    billable generation is performed.
    """

    prompt_tokens: int
    model: str
    resolved_model: str | None = None


class StreamUsage(BaseModel):
    """Token usage carried on the terminal stream chunk."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class StreamEvent(BaseModel):
    """A single streaming chunk event."""

    type: Literal[
        "message_start",
        "thinking_delta",
        "content_delta",
        "tool_use_start",
        "tool_use_input_delta",
        "tool_use_complete",
        "citation",
        "status",
        "usage",
        "message_stop",
        "error",
    ]
    delta: str = ""
    citation: Citation | None = None
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    usage: StreamUsage | None = None
    status: str | None = None
    error: str | None = None


#: The logical model aliases ("modes") the orchestrator resolves at
#: request time against the models connected workers advertise. Pass one
#: as ``model`` to ``complete``/``stream``, or call ``list_modes()``.
Mode = Literal["auto", "fast", "balanced", "deep", "max"]

#: The known modes, in display order (auto first).
MODES: list[str] = ["auto", "fast", "balanced", "deep", "max"]


class ModelInfo(BaseModel):
    """A single model entry from ``GET /v1/models``.

    ``kind`` is ``"alias"`` for the logical tiers
    (auto/fast/balanced/deep/max) or ``"canonical"`` for an actual model
    advertised by a connected
    worker — the latter carry the structured metadata fields.
    """

    id: str
    kind: str | None = None
    description: str | None = None
    family: str | None = None
    variant: str | None = None
    quant: str | None = None
    role: str | None = None
    context_len: int | None = None
    supports_tools: bool | None = None


class SolveRun(BaseModel):
    """A durable ``max``-tier (AB-MCTS) search run.

    Created by :meth:`LLMModule.solve` (``POST /v1/solve``) which returns
    immediately with a ``run_id`` while the search proceeds detached from
    the connection; poll :meth:`LLMModule.get_solve_run`
    (``GET /v1/solve/{run_id}``) until ``status`` reaches a terminal value.

    ``status`` is one of ``running`` | ``done`` | ``error``. ``result``
    holds the final answer once ``done``; ``error`` holds the failure
    message when ``status == "error"``.
    """

    run_id: str
    status: str
    model: str | None = None
    result: str | None = None
    error: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0


# ───────────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────────


def _serialize_messages(
    messages: list[Message] | list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Convert a heterogeneous message list to plain dicts."""
    out: list[dict[str, Any]] = []
    for m in messages:
        if isinstance(m, Message):
            out.append(m.model_dump(exclude_none=True))
        elif isinstance(m, dict):
            out.append(m)
        else:  # pragma: no cover - defensive
            raise TypeError(f"unsupported message type: {type(m).__name__}")
    return out


def _build_request_body(
    messages: list[Message] | list[dict[str, Any]],
    model: str,
    max_tokens: int,
    temperature: float,
    system: str | None,
    tools: list[dict[str, Any]] | None,
    stream: bool,
) -> dict[str, Any]:
    msgs = _serialize_messages(messages)
    if system:
        msgs = [{"role": "system", "content": system}, *msgs]
    body: dict[str, Any] = {
        "model": model,
        "messages": msgs,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": stream,
    }
    if tools is not None:
        # The orchestrator ignores unknown fields today (tools come via
        # the Phase 7 in-server loop) but we forward them for forward-compat.
        body["tools"] = tools
    return body


def _solve_post_kwargs(*, body: _RawBody) -> dict[str, Any]:
    """Build the httpx kwargs for ``POST /v1/solve`` (mirrors a generated
    ``_get_kwargs`` so it routes through ``_call_gen``)."""
    return {
        "method": "post",
        "url": "/v1/solve",
        "json": body.to_dict(),
        "headers": {"Content-Type": "application/json"},
    }


def _solve_get_kwargs(*, run_id: str) -> dict[str, Any]:
    """Build the httpx kwargs for ``GET /v1/solve/{run_id}``."""
    return {"method": "get", "url": f"/v1/solve/{run_id}"}


def _parse_solve_run(data: Any) -> SolveRun:
    """Parse a ``/v1/solve`` (POST or GET) JSON body into a SolveRun."""
    if not isinstance(data, dict):  # pragma: no cover - defensive
        data = {}
    usage = data.get("usage")
    if not isinstance(usage, dict):
        usage = {}
    return SolveRun(
        run_id=str(data.get("run_id", "")),
        status=str(data.get("status", "")),
        model=data.get("model"),
        result=data.get("result"),
        error=data.get("error"),
        prompt_tokens=int(usage.get("prompt_tokens", 0) or 0),
        completion_tokens=int(usage.get("completion_tokens", 0) or 0),
    )


# ───────────────────────────────────────────────────────────────────────
# Module
# ───────────────────────────────────────────────────────────────────────


class LLMModule:
    """LLM operations against Korai Cloud.

    Wraps ``POST /v1/chat/completions`` and ``GET /v1/models``. Routing,
    fallback and the Phase-7 web tool loop are handled server-side by
    the orchestrator — this module is purely a typed transport.
    """

    def __init__(self, client: KoraiClient) -> None:
        self._client = client

    async def complete(
        self,
        messages: list[Message] | list[dict[str, Any]],
        model: str = "claude-opus-4-7",
        max_tokens: int = 4096,
        temperature: float = 1.0,
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        thinking: bool = True,
    ) -> CompletionResult:
        """Non-streaming chat completion.

        Args:
            messages: Conversation history. Either Pydantic
                :class:`Message` instances or raw dicts in OpenAI
                schema.
            model: Korai model alias (``auto``, ``fast``, ``balanced``,
                ``deep``, ``max``) or canonical worker model id.
            max_tokens: Hard ceiling on assistant output (server caps at
                16k).
            temperature: Standard sampling temperature.
            system: Optional system prompt prepended to ``messages``.
            tools: OpenAI-style tool schemas. Forwarded for forward
                compatibility — current orchestrator ignores them and
                runs its own internal web tool loop.
            thinking: Reserved. Today the server decides per model.

        Returns:
            :class:`CompletionResult` with content, citations, usage,
            and measured latency.

        Example::

            result = await client.llm.complete(
                messages=[Message(role="user", content="Hello")],
            )
            print(result.content, result.input_tokens, result.output_tokens)
        """
        body = _build_request_body(
            messages, model, max_tokens, temperature, system, tools, stream=False
        )
        t0 = time.perf_counter()
        data = await self._client._call_gen(
            create_chat_completion._get_kwargs,
            path="/v1/chat/completions",
            body=_RawBody(body),
        )
        latency_ms = int((time.perf_counter() - t0) * 1000)
        return self._parse_completion(data, latency_ms)

    async def count_tokens(
        self,
        *,
        messages: list[Message] | list[dict[str, Any]],
        model: str = "auto",
    ) -> TokenCount:
        """Count the prompt tokens the given messages occupy — exactly.

        Calls ``POST /v1/count_tokens``: the orchestrator resolves the
        ``model`` alias the same way :meth:`complete` does and counts
        against that model's own tokenizer + chat template. This performs
        no billable generation.

        Only ``role`` + ``content`` of each message affect the count, so
        sampling/tool fields are dropped before sending.

        Args:
            messages: Conversation to measure. Either Pydantic
                :class:`Message` instances or raw dicts in OpenAI schema.
            model: Korai model alias (``auto``, ``fast``, ``balanced``,
                ``deep``, ``max``) or canonical worker model id.

        Returns:
            :class:`TokenCount` with ``prompt_tokens``, the requested
            ``model``, and the ``resolved_model`` the count was computed
            against (``None`` if the server omits it).

        Example::

            tc = await client.llm.count_tokens(
                messages=[Message(role="user", content="Hello")],
            )
            print(tc.prompt_tokens, tc.resolved_model)
        """
        msgs = [
            {"role": m["role"], "content": m["content"]}
            for m in _serialize_messages(messages)
        ]
        body: dict[str, Any] = {"model": model, "messages": msgs}
        data = await self._client._call_gen(
            count_tokens_api._get_kwargs,
            path="/v1/count_tokens",
            body=_RawBody(body),
        )
        if not isinstance(data, dict):  # pragma: no cover - defensive
            data = {}
        return TokenCount(
            prompt_tokens=int(data.get("prompt_tokens", 0) or 0),
            model=str(data.get("model", model)),
            resolved_model=data.get("resolved_model"),
        )

    async def stream(
        self,
        messages: list[Message] | list[dict[str, Any]],
        model: str = "claude-opus-4-7",
        max_tokens: int = 4096,
        temperature: float = 1.0,
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        thinking: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        """Streaming chat completion.

        Yields :class:`StreamEvent` instances. The first one is always
        ``message_start``; the last is ``message_stop`` (or ``error``).
        ``content_delta`` events carry the incremental text.

        Example::

            async for ev in client.llm.stream(messages=[...]):
                if ev.type == "content_delta":
                    print(ev.delta, end="")
                elif ev.type == "citation":
                    citations.append(ev.citation)
        """
        body = _build_request_body(
            messages, model, max_tokens, temperature, system, tools, stream=True
        )
        return self._stream_iter(body)

    async def collect_stream(
        self, events: AsyncIterator[StreamEvent]
    ) -> CompletionResult:
        """Fold a stream of :class:`StreamEvent` into a CompletionResult.

        Mirrors the Anthropic SDK's ``stream.get_final_message()``:
        concatenate ``content_delta`` and ``thinking_delta`` deltas,
        collect ``citation`` events, and surface a terminal
        ``error`` event by raising.

        Args:
            events: The async iterator returned by :meth:`stream`.

        Returns:
            A :class:`CompletionResult`. ``input_tokens`` / ``output_tokens``
            come from the terminal ``usage`` event (``0`` only if the
            worker's backend didn't report usage); ``latency_ms`` is ``0``
            and ``stop_reason`` is ``"stop"``.

        Raises:
            KoraiAPIError: If an ``error`` event is received.
        """
        content_parts: list[str] = []
        thinking_parts: list[str] = []
        citations: list[Citation] = []
        tool_calls: list[dict[str, Any]] = []
        input_tokens = 0
        output_tokens = 0

        async for ev in events:
            if ev.type == "content_delta":
                content_parts.append(ev.delta)
            elif ev.type == "thinking_delta":
                thinking_parts.append(ev.delta)
            elif ev.type == "citation":
                if ev.citation is not None:
                    citations.append(ev.citation)
            elif ev.type == "tool_use_complete":
                tool_calls.append(
                    {"name": ev.tool_name, "input": ev.tool_input or {}}
                )
            elif ev.type == "status":
                # Progress markers are not folded into the assembled
                # message (mirrors the JS SDK); ignore.
                continue
            elif ev.type == "usage":
                if ev.usage is not None:
                    input_tokens = ev.usage.prompt_tokens
                    output_tokens = ev.usage.completion_tokens
            elif ev.type == "error":
                raise KoraiAPIError(
                    status_code=0,
                    message=ev.error or "stream error",
                    body=None,
                )

        thinking = "".join(thinking_parts) or None
        return CompletionResult(
            content="".join(content_parts),
            thinking=thinking,
            citations=citations,
            tool_calls=tool_calls,
            model="unknown",
            stop_reason="stop",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=0,
        )

    async def stream_to_completion(self, **kwargs: Any) -> CompletionResult:
        """Stream a completion and return the folded final result.

        Convenience wrapper combining :meth:`stream` and
        :meth:`collect_stream`. Accepts the same keyword arguments as
        :meth:`stream`.

        Example::

            result = await client.llm.stream_to_completion(
                messages=[Message(role="user", content="Hello")],
            )
            print(result.content)
        """
        events = await self.stream(**kwargs)
        return await self.collect_stream(events)

    async def list_models(self) -> list[str]:
        """List models advertised by Korai Cloud.

        Returns the ``id`` field of every entry in ``GET /v1/models``.
        Includes the user-facing aliases (``auto``/``fast``/...) plus
        any canonical IDs that connected workers have advertised.
        """
        data = await self._client._call_gen(
            list_models_api._get_kwargs, path="/v1/models"
        )
        items = data.get("data", []) if isinstance(data, dict) else []
        ids: list[str] = []
        for entry in items:
            if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                ids.append(entry["id"])
        return ids

    async def list_models_detailed(self) -> list[ModelInfo]:
        """List models with full metadata (family, variant, quant, role,
        context length, tool support).

        Same endpoint as :meth:`list_models`, but returns structured
        :class:`ModelInfo` entries instead of bare ids — use this to see
        the *actual* models a connected worker advertises, not just the
        logical aliases.
        """
        data = await self._client._call_gen(
            list_models_api._get_kwargs, path="/v1/models"
        )
        items = data.get("data", []) if isinstance(data, dict) else []
        return [
            ModelInfo.model_validate(entry)
            for entry in items
            if isinstance(entry, dict) and isinstance(entry.get("id"), str)
        ]

    async def list_modes(self) -> list[ModelInfo]:
        """List the logical modes (aliases) the orchestrator exposes,
        with their server-provided descriptions — the ``kind == "alias"``
        subset of ``/v1/models``. Useful for rendering a mode picker.
        """
        models = await self.list_models_detailed()
        return [m for m in models if m.kind == "alias"]

    # ------------------------------------------------------------------
    # Durable solve (max tier — AB-MCTS deep search)
    # ------------------------------------------------------------------

    async def solve(
        self,
        messages: list[Message] | list[dict[str, Any]],
        *,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        system: str | None = None,
    ) -> SolveRun:
        """Start a durable ``max``-tier (AB-MCTS) search run.

        Calls ``POST /v1/solve`` with ``model="max"``. The server detaches
        the search from the connection and returns ``202`` immediately with
        a ``run_id`` and ``status == "running"`` — poll
        :meth:`get_solve_run` (or use :meth:`solve_and_wait`) to retrieve
        the result later. The ``stream`` field is ignored server-side.

        Args:
            messages: Conversation history. Either Pydantic
                :class:`Message` instances or raw dicts in OpenAI schema.
            max_tokens: Hard ceiling on the final answer's tokens.
            temperature: Standard sampling temperature.
            system: Optional system prompt prepended to ``messages``.

        Returns:
            A :class:`SolveRun` carrying the ``run_id`` and initial
            ``status`` (``"running"``).

        Raises:
            KoraiAPIError: On a non-2xx response — including
                ``503 storage_unavailable`` when the server has no Postgres.

        Example::

            run = await client.llm.solve(
                messages=[Message(role="user", content="Prove ...")],
            )
            print(run.run_id)
        """
        body = _build_request_body(
            messages, "max", max_tokens, temperature, system, None, stream=False
        )
        data = await self._client._call_gen(
            _solve_post_kwargs, path="/v1/solve", body=_RawBody(body)
        )
        return _parse_solve_run(data)

    async def get_solve_run(self, run_id: str) -> SolveRun:
        """Fetch the current state of a durable solve run.

        Calls ``GET /v1/solve/{run_id}``. ``status`` is one of
        ``running`` | ``done`` | ``error``; once ``done`` the ``result``
        field holds the final answer.

        Args:
            run_id: The id returned by :meth:`solve`.

        Returns:
            A :class:`SolveRun` snapshot.

        Raises:
            KoraiAPIError: On a non-2xx response — an unknown ``run_id``
                surfaces as a ``404`` (``KoraiNotFoundError``).
        """
        data = await self._client._call_gen(
            _solve_get_kwargs, path=f"/v1/solve/{run_id}", run_id=run_id
        )
        return _parse_solve_run(data)

    async def solve_and_wait(
        self,
        messages: list[Message] | list[dict[str, Any]],
        *,
        poll_interval: float = 2.0,
        timeout: float = 600.0,
        **kw: Any,
    ) -> SolveRun:
        """Start a solve run and poll until it terminates.

        Convenience wrapper: calls :meth:`solve`, then polls
        :meth:`get_solve_run` every ``poll_interval`` seconds until the run
        reaches a terminal status (``done`` / ``error``) or ``timeout``
        elapses. Extra keyword arguments (``max_tokens``, ``temperature``,
        ``system``) are forwarded to :meth:`solve`.

        Args:
            messages: Conversation history (see :meth:`solve`).
            poll_interval: Seconds between ``get_solve_run`` polls.
            timeout: Maximum total seconds to wait before giving up.

        Returns:
            The terminal :class:`SolveRun` with ``status == "done"``.

        Raises:
            KoraiAPIError: If the run ends with ``status == "error"``.
            TimeoutError: If ``timeout`` elapses before the run terminates.
        """
        run = await self.solve(messages, **kw)
        deadline = time.monotonic() + timeout
        while True:
            if run.status == "done":
                return run
            if run.status == "error":
                raise KoraiAPIError(
                    status_code=0,
                    message=run.error or "solve run failed",
                    body=None,
                )
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"solve run {run.run_id} did not finish within {timeout}s"
                )
            await asyncio.sleep(poll_interval)
            run = await self.get_solve_run(run.run_id)

    # ------------------------------------------------------------------
    # Internal: parsing
    # ------------------------------------------------------------------

    def _parse_completion(self, data: dict[str, Any], latency_ms: int) -> CompletionResult:
        """Parse an OpenAI-compat full response into a CompletionResult."""
        choices = data.get("choices") or []
        first = choices[0] if choices else {}
        message = first.get("message") or {}
        content = message.get("content") or ""
        finish_reason = first.get("finish_reason") or "stop"

        usage = data.get("usage") or {}
        input_tokens = int(usage.get("prompt_tokens", 0) or 0)
        output_tokens = int(usage.get("completion_tokens", 0) or 0)

        # The orchestrator may attach an ``attribution`` block with
        # citations from the Phase-7 tool loop. Normalize it here.
        citations: list[Citation] = []
        attribution = data.get("attribution")
        if isinstance(attribution, dict):
            for cit in attribution.get("citations") or []:
                citations.append(_coerce_citation(cit))
        # Tool calls round-trip if the orchestrator surfaces them.
        raw_tool_calls = message.get("tool_calls") or []
        tool_calls = list(raw_tool_calls) if isinstance(raw_tool_calls, list) else []

        thinking = message.get("thinking") or message.get("reasoning_content")

        return CompletionResult(
            content=content,
            thinking=thinking if isinstance(thinking, str) else None,
            citations=citations,
            tool_calls=tool_calls,
            model=str(data.get("model", "unknown")),
            stop_reason=str(finish_reason),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
        )

    async def _stream_iter(self, body: dict[str, Any]) -> AsyncIterator[StreamEvent]:
        """Open the SSE stream and yield parsed StreamEvent instances."""
        merged_headers = self._client._default_headers()
        merged_headers["Accept"] = "text/event-stream"
        try:
            async with self._client._http.stream(
                "POST",
                "/v1/chat/completions",
                json=body,
                headers=merged_headers,
                timeout=None,
            ) as response:
                if response.status_code >= 400:
                    # Read body so the typed error has context.
                    raw = await response.aread()
                    try:
                        parsed: Any = json.loads(raw.decode("utf-8") or "null")
                    except json.JSONDecodeError:
                        parsed = raw.decode("utf-8", errors="replace")
                    raise KoraiAPIError(status_code=response.status_code, body=parsed)

                yield StreamEvent(type="message_start")
                started_content = False
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    payload = line[5:].lstrip()
                    if payload == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    for ev in _events_from_chunk(chunk, started_content):
                        if ev.type == "content_delta":
                            started_content = True
                        yield ev
                yield StreamEvent(type="message_stop")
        except KoraiAPIError:
            raise
        except Exception as exc:
            yield StreamEvent(type="error", error=str(exc))


def _events_from_chunk(
    chunk: dict[str, Any], _started_content: bool
) -> list[StreamEvent]:
    """Translate one OpenAI-compat SSE envelope into StreamEvents."""
    events: list[StreamEvent] = []

    # Server-side error envelope.
    err = chunk.get("error")
    if isinstance(err, dict) and err.get("message"):
        events.append(StreamEvent(type="error", error=str(err["message"])))
        return events

    # Progress markers (orchestrator emits e.g. ``consulting`` /
    # ``synthesizing`` for deep-mode multi-model synthesis, ``exploring``
    # for the ``max``-tier AB-MCTS search, plus tool-loop statuses).
    # Surface them so progress UIs can render them.
    status = chunk.get("status")
    if isinstance(status, str) and status:
        events.append(StreamEvent(type="status", status=status))

    # Attribution / citations (orchestrator emits this once near the end).
    attribution = chunk.get("attribution")
    if isinstance(attribution, dict):
        for cit in attribution.get("citations") or []:
            events.append(StreamEvent(type="citation", citation=_coerce_citation(cit)))

    choices = chunk.get("choices") or []
    for choice in choices:
        delta = choice.get("delta") or {}
        if isinstance(delta, dict):
            # Thinking content (mlx_lm thinking models surface this in
            # a separate field; fall back gracefully if absent).
            thinking_delta = delta.get("thinking") or delta.get("reasoning_content")
            if isinstance(thinking_delta, str) and thinking_delta:
                events.append(StreamEvent(type="thinking_delta", delta=thinking_delta))

            text = delta.get("content")
            if isinstance(text, str) and text:
                events.append(StreamEvent(type="content_delta", delta=text))

            tool_calls = delta.get("tool_calls")
            if isinstance(tool_calls, list):
                for tc in tool_calls:
                    if not isinstance(tc, dict):
                        continue
                    func = tc.get("function") or {}
                    if isinstance(func, dict):
                        name = func.get("name")
                        args_str = func.get("arguments")
                        try:
                            tinput = json.loads(args_str) if args_str else None
                        except json.JSONDecodeError:
                            tinput = None
                        events.append(
                            StreamEvent(
                                type="tool_use_complete",
                                tool_name=name if isinstance(name, str) else None,
                                tool_input=tinput
                                if isinstance(tinput, dict)
                                else None,
                            )
                        )

    # Usage rides the terminal chunk (orchestrator sets it alongside
    # finish_reason). Surface it so streamed turns can account cost.
    usage = chunk.get("usage")
    if isinstance(usage, dict):
        events.append(
            StreamEvent(
                type="usage",
                usage=StreamUsage(
                    prompt_tokens=int(usage.get("prompt_tokens", 0) or 0),
                    completion_tokens=int(usage.get("completion_tokens", 0) or 0),
                    total_tokens=int(usage.get("total_tokens", 0) or 0),
                ),
            )
        )
    return events


def _coerce_citation(raw: Any) -> Citation:
    """Turn whatever the server sent into a Citation, lossily if needed."""
    if isinstance(raw, dict):
        # Common shapes: {"title": "...", "url": "..."} or full Citation.
        return Citation(
            display=str(raw.get("display") or raw.get("title") or raw.get("url") or ""),
            law_code=raw.get("law_code"),
            article_number=raw.get("article_number"),
            paragraph=raw.get("paragraph"),
            letter=raw.get("letter"),
            url=raw.get("url"),
            excerpt=raw.get("excerpt") or raw.get("snippet"),
            verified=raw.get("verified"),
        )
    return Citation(display=str(raw))


__all__ = [
    "Citation",
    "CompletionResult",
    "LLMModule",
    "Message",
    "SolveRun",
    "StreamEvent",
    "StreamUsage",
    "TokenCount",
]
