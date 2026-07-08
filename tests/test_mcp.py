"""Tests for the MCP client bridge + raw-schema tool support in ToolsModule."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx
import respx

from korai import KoraiClient


@dataclass
class _FakeMcpTool:
    """Mimics an mcp.types.Tool descriptor (attribute access)."""

    name: str
    description: str
    inputSchema: dict[str, Any]  # noqa: N815 — matches the mcp wire field


class FakeMcpSession:
    """Canned MCP session: attribute-style tools + recorded calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def list_tools(self) -> list[Any]:
        return [
            _FakeMcpTool(
                name="echo",
                description="Echo the message back",
                inputSchema={
                    "type": "object",
                    "properties": {"message": {"type": "string"}},
                    "required": ["message"],
                },
            ),
            # dict-style descriptor + missing schema → defaults to object.
            {"name": "ping", "description": "Ping the server"},
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        self.calls.append((name, arguments))
        if name == "echo":
            return {"echoed": arguments.get("message")}
        return "pong"  # non-dict → wrapped as {"value": ...}


async def test_register_mcp_server_registers_tools(client: KoraiClient) -> None:
    session = FakeMcpSession()
    names = await client.tools.register_mcp_server(session)

    assert names == ["echo", "ping"]
    assert client.tools.names() == ["echo", "ping"]


async def test_to_openai_schemas_emits_mcp_schema_verbatim(
    client: KoraiClient,
) -> None:
    session = FakeMcpSession()
    await client.tools.register_mcp_server(session)

    schemas = {s["function"]["name"]: s for s in client.tools.to_openai_schemas()}
    echo = schemas["echo"]
    assert echo["type"] == "function"
    assert echo["function"]["parameters"] == {
        "type": "object",
        "properties": {"message": {"type": "string"}},
        "required": ["message"],
    }
    # Missing inputSchema → default object schema.
    assert schemas["ping"]["function"]["parameters"] == {"type": "object"}


async def test_to_anthropic_schemas_emits_mcp_schema_verbatim(
    client: KoraiClient,
) -> None:
    session = FakeMcpSession()
    await client.tools.register_mcp_server(session)
    schemas = {s["name"]: s for s in client.tools.to_anthropic_schemas()}
    assert schemas["echo"]["input_schema"]["properties"]["message"]["type"] == "string"


async def test_invoke_routes_to_session(client: KoraiClient) -> None:
    session = FakeMcpSession()
    await client.tools.register_mcp_server(session)

    out = await client.tools.invoke("echo", {"message": "hi"})
    assert out == {"echoed": "hi"}

    # Non-dict result is wrapped.
    pong = await client.tools.invoke("ping", {})
    assert pong == {"value": "pong"}

    assert session.calls == [("echo", {"message": "hi"}), ("ping", {})]


async def test_namespace_prefixes_names(client: KoraiClient) -> None:
    session = FakeMcpSession()
    names = await client.tools.register_mcp_server(session, namespace="srv")

    assert names == ["srv__echo", "srv__ping"]
    out = await client.tools.invoke("srv__echo", {"message": "ns"})
    assert out == {"echoed": "ns"}
    # The original (unprefixed) name is what reaches the MCP session.
    assert session.calls[-1] == ("echo", {"message": "ns"})


async def test_register_raw_basic(client: KoraiClient) -> None:
    async def _execute(args: dict[str, Any]) -> dict[str, Any]:
        return {"doubled": args["n"] * 2}

    client.tools.register_raw(
        name="double",
        description="Double a number",
        json_schema={"type": "object", "properties": {"n": {"type": "integer"}}},
        execute=_execute,
    )

    assert "double" in client.tools.names()
    out = await client.tools.invoke("double", {"n": 21})
    assert out == {"doubled": 42}


def _mcp_tool_call_response() -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "1",
            "object": "chat.completion",
            "created": 0,
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
                                "function": {
                                    "name": "echo",
                                    "arguments": '{"message": "yo"}',
                                },
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ],
        },
    )


def _final_response(content: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "2",
            "object": "chat.completion",
            "created": 0,
            "model": "auto",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
        },
    )


async def test_run_uses_mcp_tool_end_to_end(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    route = respx_mock.post("/v1/chat/completions").mock(
        side_effect=[_mcp_tool_call_response(), _final_response("done: yo")]
    )
    session = FakeMcpSession()
    await client.tools.register_mcp_server(session)

    res = await client.tools.run(messages=[{"role": "user", "content": "echo yo"}])

    assert res.final.content == "done: yo"
    assert res.tool_runs[0].name == "echo"
    assert res.tool_runs[0].output == {"echoed": "yo"}
    assert session.calls == [("echo", {"message": "yo"})]
    # Tool result was fed back to the model.
    second = json.loads(route.calls[1].request.read())
    tool_msgs = [m for m in second["messages"] if m["role"] == "tool"]
    assert json.loads(tool_msgs[0]["content"]) == {"echoed": "yo"}
