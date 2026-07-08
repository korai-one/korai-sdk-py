"""Canonical, block-based session type for STORAGE and cross-tool TELEPORT.

This is **not** the inference wire. The inference wire stays the flat
OpenAI-shaped :class:`korai.llm.Message`; OpenAI-compatibility is a product
feature and is unchanged by anything here. Storage != inference.

This module is the Python mirror of the Go SDK's canonical session type
(``korai-platform/packages/sdk-go/session.go``). The JSON wire form is
byte-compatible across Go / JS / Python: identical field names, identical block
``kind`` tags, identical key ordering — a session written by any one SDK
deserializes losslessly in the others. Cross-check against ``session.go`` before
changing a field name or tag. The canonical JSON uses **compact separators**
(``,`` / ``:``) so the bytes match Go's ``json.Marshal`` and JS's
``JSON.stringify``; use :func:`session_to_json` rather than a bare
``json.dumps``.

The canonical type is the SUPERSET of every producer's model: it carries
ordered, tagged content blocks (text / tool-use / tool-result / image) so the
richest producer (korai-code-cli's structured content blocks) persists without
losing fidelity, while flat producers (kode, the dashboard) map UP into it
trivially. See ``docs/HISTORY_SYNC.md`` §14 in the korai repo.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Union

from korai.llm import Message

# ───────────────────────────────────────────────────────────────────────
# Block variants
# ───────────────────────────────────────────────────────────────────────


@dataclass
class TextBlock:
    """A plain-text content segment."""

    text: str = ""


@dataclass
class ToolUseBlock:
    """A tool invocation produced by the model.

    ``input`` is the argument object exactly as the model emitted it (a parsed
    JSON object; it serialises back to a compact JSON object so it round-trips
    byte-for-byte with Go's ``json.RawMessage``). ``None`` means "no input".
    """

    id: str = ""
    name: str = ""
    input: dict[str, Any] | None = None


@dataclass
class ToolResultBlock:
    """The result of an executed tool call, fed back to the model.

    ``name`` is the producing tool's name; optional, preserved so a flat
    ``role="tool"`` message (which carries a ``name``) survives a round trip.
    """

    tool_call_id: str = ""
    name: str = ""
    content: str = ""
    is_error: bool = False


@dataclass
class ImageBlock:
    """An image for a vision-capable model.

    ``source`` is a data URI (``data:image/png;base64,<...>``) or an https URL.
    """

    source: str = ""


#: The sealed union over content variants in a :class:`SessionMessage`. The set
#: (text / tool_use / tool_result / image) covers korai-code-cli's full block
#: set so teleport is lossless.
Block = Union[TextBlock, ToolUseBlock, ToolResultBlock, ImageBlock]


# ───────────────────────────────────────────────────────────────────────
# Session + message
# ───────────────────────────────────────────────────────────────────────


@dataclass
class SessionMessage:
    """One turn in a stored conversation.

    Unlike the flat wire :class:`~korai.llm.Message`, its content is an ordered
    list of typed :data:`Block`\\ s, so a single turn can interleave text, tool
    calls, tool results and images without loss. ``role`` is one of
    ``system`` / ``user`` / ``assistant`` / ``tool``.
    """

    role: str
    blocks: list[Block] = field(default_factory=list)


@dataclass
class Session:
    """One stored conversation: metadata plus its ordered messages.

    ``tool`` records which surface produced it (e.g. ``korai-code-cli``,
    ``kode``, ``dashboard``); advisory metadata, not used for routing.
    ``created`` / ``updated`` are opaque RFC 3339 timestamp strings as the
    producer emits them — ``updated`` is derived from storage, not content, so
    it never perturbs a content hash.
    """

    id: str = ""
    created: str = ""
    updated: str = ""
    cwd: str = ""
    model: str = ""
    tool: str = ""
    messages: list[SessionMessage] = field(default_factory=list)


# ───────────────────────────────────────────────────────────────────────
# JSON (de)serialization — canonical key order + Go omitempty parity.
#
# Field insertion order matches Go's struct tags exactly (dicts preserve
# insertion order; json.dumps preserves that). Empty fields are omitted per
# Go's `omitempty`. Unknown block kinds are skipped on decode so a newer
# producer's blocks don't break an older reader.
# ───────────────────────────────────────────────────────────────────────


def _block_to_dict(b: Block) -> dict[str, Any]:
    # Canonical blockDTO order: kind, text, id, name, input, tool_call_id,
    # content, is_error, source.
    if isinstance(b, TextBlock):
        d: dict[str, Any] = {"kind": "text"}
        if b.text:
            d["text"] = b.text
        return d
    if isinstance(b, ToolUseBlock):
        d = {"kind": "tool_use"}
        if b.id:
            d["id"] = b.id
        if b.name:
            d["name"] = b.name
        if b.input is not None:
            d["input"] = b.input
        return d
    if isinstance(b, ToolResultBlock):
        d = {"kind": "tool_result"}
        if b.name:
            d["name"] = b.name
        if b.tool_call_id:
            d["tool_call_id"] = b.tool_call_id
        if b.content:
            d["content"] = b.content
        if b.is_error:
            d["is_error"] = True
        return d
    if isinstance(b, ImageBlock):
        d = {"kind": "image"}
        if b.source:
            d["source"] = b.source
        return d
    raise TypeError(f"unsupported block type: {type(b).__name__}")  # pragma: no cover


def _block_from_dict(d: dict[str, Any]) -> Block | None:
    kind = d.get("kind")
    if kind == "text":
        return TextBlock(text=str(d.get("text", "") or ""))
    if kind == "tool_use":
        raw_input = d.get("input")
        return ToolUseBlock(
            id=str(d.get("id", "") or ""),
            name=str(d.get("name", "") or ""),
            input=raw_input if isinstance(raw_input, dict) else None,
        )
    if kind == "tool_result":
        return ToolResultBlock(
            tool_call_id=str(d.get("tool_call_id", "") or ""),
            name=str(d.get("name", "") or ""),
            content=str(d.get("content", "") or ""),
            is_error=bool(d.get("is_error", False)),
        )
    if kind == "image":
        return ImageBlock(source=str(d.get("source", "") or ""))
    # Unknown kind — skip (forward-compatibility with newer producers).
    return None


def _message_to_dict(m: SessionMessage) -> dict[str, Any]:
    return {"role": m.role, "blocks": [_block_to_dict(b) for b in m.blocks]}


def _message_from_dict(d: dict[str, Any]) -> SessionMessage:
    raw_blocks = d.get("blocks")
    blocks: list[Block] = []
    if isinstance(raw_blocks, list):
        for rb in raw_blocks:
            if isinstance(rb, dict):
                b = _block_from_dict(rb)
                if b is not None:
                    blocks.append(b)
    return SessionMessage(role=str(d.get("role", "user") or "user"), blocks=blocks)


def session_to_dict(s: Session) -> dict[str, Any]:
    """Render a :class:`Session` to a JSON-ready dict with canonical Go key
    order (id, created, updated, cwd, model, tool?, messages) and omitempty."""
    d: dict[str, Any] = {
        "id": s.id,
        "created": s.created,
        "updated": s.updated,
        "cwd": s.cwd,
        "model": s.model,
    }
    if s.tool:  # omitempty — inserted before `messages`
        d["tool"] = s.tool
    d["messages"] = [_message_to_dict(m) for m in s.messages]
    return d


def session_from_dict(d: dict[str, Any]) -> Session:
    """Reconstruct a :class:`Session` from a parsed wire dict."""
    raw_messages = d.get("messages")
    messages: list[SessionMessage] = []
    if isinstance(raw_messages, list):
        for rm in raw_messages:
            if isinstance(rm, dict):
                messages.append(_message_from_dict(rm))
    return Session(
        id=str(d.get("id", "") or ""),
        created=str(d.get("created", "") or ""),
        updated=str(d.get("updated", "") or ""),
        cwd=str(d.get("cwd", "") or ""),
        model=str(d.get("model", "") or ""),
        tool=str(d.get("tool", "") or ""),
        messages=messages,
    )


def session_to_json(s: Session) -> str:
    """Serialise a :class:`Session` to its canonical, compact JSON string.

    Uses ``separators=(",", ":")`` so the bytes match Go's ``json.Marshal`` and
    JS's ``JSON.stringify`` output.
    """
    return json.dumps(session_to_dict(s), separators=(",", ":"), ensure_ascii=False)


def session_from_json(text: str) -> Session:
    """Parse a canonical session JSON string back into a :class:`Session`."""
    return session_from_dict(json.loads(text))


# ───────────────────────────────────────────────────────────────────────
# Rich <-> flat projection.
#
# The flat Message (korai.llm) is the OpenAI-shaped inference wire type. These
# helpers map between it and the canonical SessionMessage. flat -> rich -> flat
# is LOSSLESS for flat inputs. rich -> flat is lossy in the documented ways:
#   - interleaved-block ORDERING across block *types* within one message is not
#     representable flat (all text collapses into `content`, all tool-uses into
#     `tool_calls`);
#   - `is_error` on a ToolResultBlock and any tool-result past the first are
#     dropped (the flat shape carries neither);
#   - ImageBlocks are dropped: the Python flat Message has no multimodal `parts`
#     field, so images cannot be projected down.
# ───────────────────────────────────────────────────────────────────────


def flat_to_session_message(m: Message) -> SessionMessage:
    """Map a flat wire :class:`~korai.llm.Message` UP into a
    :class:`SessionMessage`.

    A ``role="tool"`` message becomes a single :class:`ToolResultBlock`;
    otherwise the ``content`` string becomes a :class:`TextBlock` (when
    non-empty), followed by one :class:`ToolUseBlock` per tool call. Each tool
    call is read in the structured ``{id, name, input}`` shape.
    """
    if m.role == "tool":
        return SessionMessage(
            role=m.role,
            blocks=[
                ToolResultBlock(
                    tool_call_id=m.tool_call_id or "",
                    name=m.name or "",
                    content=m.content or "",
                )
            ],
        )
    blocks: list[Block] = []
    if m.content:
        blocks.append(TextBlock(text=m.content))
    for tc in m.tool_calls or []:
        if not isinstance(tc, dict):
            continue
        raw_input = tc.get("input")
        blocks.append(
            ToolUseBlock(
                id=str(tc.get("id", "") or ""),
                name=str(tc.get("name", "") or ""),
                input=raw_input if isinstance(raw_input, dict) else None,
            )
        )
    return SessionMessage(role=m.role, blocks=blocks)


def session_message_to_flat(m: SessionMessage) -> Message:
    """Project a :class:`SessionMessage` DOWN into a flat wire
    :class:`~korai.llm.Message` for inference.

    See the module block comment for what this direction drops. Tool calls are
    emitted in the structured ``{id, name, input}`` shape (``input`` omitted
    when the block carried none).
    """
    # A message bearing a tool result maps to a flat role="tool" message.
    for b in m.blocks:
        if isinstance(b, ToolResultBlock):
            return Message(
                role="tool",
                content=b.content,
                name=b.name or None,
                tool_call_id=b.tool_call_id or None,
            )

    texts: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    for b in m.blocks:
        if isinstance(b, TextBlock):
            texts.append(b.text)
        elif isinstance(b, ToolUseBlock):
            tc: dict[str, Any] = {"id": b.id, "name": b.name}
            if b.input is not None:
                tc["input"] = b.input
            tool_calls.append(tc)
        elif isinstance(b, ImageBlock):
            # Python flat Message has no `parts` — image blocks are dropped.
            continue
    return Message(
        role=m.role,  # type: ignore[arg-type]
        content="".join(texts),
        tool_calls=tool_calls or None,
    )


def flat_to_session_messages(msgs: list[Message]) -> list[SessionMessage]:
    """Slice form of :func:`flat_to_session_message`."""
    return [flat_to_session_message(m) for m in msgs]


def session_messages_to_flat(msgs: list[SessionMessage]) -> list[Message]:
    """Slice form of :func:`session_message_to_flat`."""
    return [session_message_to_flat(m) for m in msgs]


__all__ = [
    "Block",
    "ImageBlock",
    "Session",
    "SessionMessage",
    "TextBlock",
    "ToolResultBlock",
    "ToolUseBlock",
    "flat_to_session_message",
    "flat_to_session_messages",
    "session_from_dict",
    "session_from_json",
    "session_message_to_flat",
    "session_messages_to_flat",
    "session_to_dict",
    "session_to_json",
]
