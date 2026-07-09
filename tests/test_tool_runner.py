"""Tests for the agentic tool-use loop (ToolsModule.run)."""

from __future__ import annotations

import json

import httpx
import respx

from korai import KoraiClient
from korai.tools import Tool, ToolInput, ToolOutput


class AddInput(ToolInput):
    a: int
    b: int


class AddOutput(ToolOutput):
    sum: int


class AddTool(Tool[AddInput, AddOutput]):
    name = "add"
    description = "Add two integers"
    input_model = AddInput
    output_model = AddOutput

    async def execute(self, input: AddInput) -> AddOutput:  # noqa: A002
        return AddOutput(sum=input.a + input.b)


def _tool_call_response() -> httpx.Response:
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
                                    "name": "add",
                                    "arguments": '{"a": 2, "b": 3}',
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


async def test_run_executes_then_completes(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    route = respx_mock.post("/v1/chat/completions").mock(
        side_effect=[_tool_call_response(), _final_response("The answer is 5.")]
    )
    client.tools.register(AddTool())

    res = await client.tools.run(messages=[{"role": "user", "content": "what is 2+3?"}])

    assert res.turns == 2
    assert res.stopped_at_max_turns is False
    assert res.final.content == "The answer is 5."
    assert len(res.tool_runs) == 1
    assert res.tool_runs[0].name == "add"
    assert res.tool_runs[0].output["sum"] == 5
    # The second request must carry the tool result back to the model.
    second = json.loads(route.calls[1].request.read())
    tool_msgs = [m for m in second["messages"] if m["role"] == "tool"]
    assert tool_msgs and tool_msgs[0]["tool_call_id"] == "call_1"
    assert json.loads(tool_msgs[0]["content"])["sum"] == 5


async def test_run_feeds_tool_error_back(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    # No tool registered → invoke raises → error fed back, loop continues.
    respx_mock.post("/v1/chat/completions").mock(
        side_effect=[_tool_call_response(), _final_response("sorry")]
    )
    res = await client.tools.run(messages=[{"role": "user", "content": "add"}])
    assert res.final.content == "sorry"
    assert "error" in res.tool_runs[0].output


async def test_run_stops_at_max_turns(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.post("/v1/chat/completions").mock(
        side_effect=lambda request: _tool_call_response()  # always asks for a tool
    )
    client.tools.register(AddTool())
    res = await client.tools.run(
        messages=[{"role": "user", "content": "loop"}], max_turns=3
    )
    assert res.turns == 3
    assert res.stopped_at_max_turns is True
