"""Tests for korai.session — canonical session type + projection.

Covers the JSON round-trip (byte-compatible with the Go/JS SDKs), the Go
omitempty / key-order parity, and the rich<->flat projection (flat -> rich ->
flat lossless).
"""

from __future__ import annotations

from korai.llm import Message
from korai.session import (
    ImageBlock,
    Session,
    SessionMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    flat_to_session_message,
    flat_to_session_messages,
    session_from_json,
    session_message_to_flat,
    session_messages_to_flat,
    session_to_json,
)

RICH_SESSION = Session(
    id="sess_1",
    created="2026-07-08T10:00:00Z",
    updated="2026-07-08T10:05:00Z",
    cwd="/home/user/project",
    model="auto",
    tool="korai-code-cli",
    messages=[
        SessionMessage(role="user", blocks=[TextBlock(text="Read main.go")]),
        SessionMessage(
            role="assistant",
            blocks=[
                TextBlock(text="Let me read it."),
                ToolUseBlock(id="call_1", name="read_file", input={"path": "main.go"}),
            ],
        ),
        SessionMessage(
            role="tool",
            blocks=[
                ToolResultBlock(
                    tool_call_id="call_1",
                    name="read_file",
                    content="package main",
                )
            ],
        ),
        SessionMessage(
            role="user",
            blocks=[ImageBlock(source="data:image/png;base64,AAAA")],
        ),
    ],
)


def test_session_json_round_trip() -> None:
    back = session_from_json(session_to_json(RICH_SESSION))
    assert back == RICH_SESSION


def test_canonical_field_names_tags_and_order() -> None:
    js = session_to_json(RICH_SESSION)
    # Session key order: id, created, updated, cwd, model, tool, messages.
    assert js.startswith(
        '{"id":"sess_1","created":"2026-07-08T10:00:00Z",'
        '"updated":"2026-07-08T10:05:00Z","cwd":"/home/user/project",'
        '"model":"auto","tool":"korai-code-cli","messages":'
    )
    # tool_use block key order: kind, id, name, input.
    assert '{"kind":"tool_use","id":"call_1","name":"read_file","input":{"path":"main.go"}}' in js
    # tool_result key order: kind, name, tool_call_id, content (is_error omitted).
    assert '{"kind":"tool_result","name":"read_file","tool_call_id":"call_1","content":"package main"}' in js
    assert '{"kind":"image","source":"data:image/png;base64,AAAA"}' in js
    # omitempty: is_error=False omitted.
    assert '"is_error"' not in js


def test_tool_omitted_when_absent() -> None:
    s = Session(id="x", model="auto", tool="", messages=[])
    js = session_to_json(s)
    assert '"tool"' not in js
    assert '"model":"auto","messages":[]' in js


def test_unknown_block_kind_skipped() -> None:
    wire = (
        '{"id":"x","created":"","updated":"","cwd":"","model":"",'
        '"messages":[{"role":"assistant","blocks":['
        '{"kind":"text","text":"hi"},{"kind":"future_kind","foo":1}]}]}'
    )
    s = session_from_json(wire)
    assert s.messages[0].blocks == [TextBlock(text="hi")]


def test_flat_to_rich_to_flat_text_lossless() -> None:
    m = Message(role="user", content="hello")
    assert session_message_to_flat(flat_to_session_message(m)) == m


def test_flat_to_rich_to_flat_tool_calls_lossless() -> None:
    m = Message(
        role="assistant",
        content="using a tool",
        tool_calls=[{"id": "c1", "name": "search", "input": {"q": "korai"}}],
    )
    assert session_message_to_flat(flat_to_session_message(m)) == m


def test_flat_to_rich_to_flat_tool_result_lossless() -> None:
    m = Message(role="tool", content="result", name="search", tool_call_id="c1")
    assert session_message_to_flat(flat_to_session_message(m)) == m


def test_empty_assistant_projects_to_no_blocks() -> None:
    m = Message(role="assistant", content="")
    rich = flat_to_session_message(m)
    assert rich.blocks == []
    assert session_message_to_flat(rich) == m


def test_slice_forms_round_trip() -> None:
    msgs = [
        Message(role="user", content="hi"),
        Message(role="assistant", content="yo"),
    ]
    assert session_messages_to_flat(flat_to_session_messages(msgs)) == msgs


def test_image_block_dropped_on_down_projection() -> None:
    flat = session_message_to_flat(
        SessionMessage(
            role="user",
            blocks=[TextBlock(text="look"), ImageBlock(source="data:foo")],
        )
    )
    assert flat == Message(role="user", content="look")
