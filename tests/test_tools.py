"""Tests for korai.tools.ToolsModule."""

from __future__ import annotations

import pytest
from pydantic import Field

from korai import KoraiClient, KoraiValidationError
from korai.tools import Tool, ToolInput, ToolOutput


class AddInput(ToolInput):
    a: int = Field(description="First addend")
    b: int = Field(description="Second addend")


class AddOutput(ToolOutput):
    sum: int


class AddTool(Tool[AddInput, AddOutput]):
    name = "add"
    description = "Add two integers"
    input_model = AddInput
    output_model = AddOutput

    async def execute(self, input: AddInput) -> AddOutput:  # noqa: A002
        return AddOutput(
            sum=input.a + input.b,
            calculation_steps=[f"{input.a} + {input.b} = {input.a + input.b}"],
        )


async def test_register_and_list(client: KoraiClient) -> None:
    client.tools.register(AddTool())
    assert client.tools.names() == ["add"]
    assert isinstance(client.tools.get("add"), AddTool)
    assert len(client.tools.list()) == 1


async def test_invoke_valid(client: KoraiClient) -> None:
    client.tools.register(AddTool())
    out = await client.tools.invoke("add", {"a": 2, "b": 3})
    assert isinstance(out, AddOutput)
    assert out.sum == 5
    assert out.calculation_steps == ["2 + 3 = 5"]


async def test_invoke_invalid_input_raises_validation(
    client: KoraiClient,
) -> None:
    client.tools.register(AddTool())
    with pytest.raises(KoraiValidationError):
        await client.tools.invoke("add", {"a": "nope"})


async def test_invoke_unknown_tool_raises_keyerror(client: KoraiClient) -> None:
    with pytest.raises(KeyError):
        await client.tools.invoke("missing", {})


async def test_unregister(client: KoraiClient) -> None:
    client.tools.register(AddTool())
    assert client.tools.unregister("add") is True
    assert client.tools.unregister("add") is False  # second time → False
    assert client.tools.get("add") is None


async def test_anthropic_schema_shape(client: KoraiClient) -> None:
    client.tools.register(AddTool())
    schemas = client.tools.to_anthropic_schemas()
    assert len(schemas) == 1
    s = schemas[0]
    assert s["name"] == "add"
    assert s["description"] == "Add two integers"
    assert s["input_schema"]["type"] == "object"
    assert "a" in s["input_schema"]["properties"]
    assert "b" in s["input_schema"]["properties"]


async def test_openai_schema_shape(client: KoraiClient) -> None:
    client.tools.register(AddTool())
    schemas = client.tools.to_openai_schemas()
    s = schemas[0]
    assert s["type"] == "function"
    assert s["function"]["name"] == "add"
    assert "parameters" in s["function"]


async def test_register_rejects_nameless_tool(client: KoraiClient) -> None:
    class BadTool(AddTool):
        name = ""

    with pytest.raises(KoraiValidationError):
        client.tools.register(BadTool())


async def test_re_register_replaces(client: KoraiClient) -> None:
    client.tools.register(AddTool())
    first = client.tools.get("add")

    class AddTool2(AddTool):
        description = "Different description"

    client.tools.register(AddTool2())
    second = client.tools.get("add")
    assert first is not second
    assert second is not None
    assert second.description == "Different description"


async def test_tool_output_audit_fields_default() -> None:
    out = AddOutput(sum=5)
    assert out.confidence == 1.0
    assert out.citations == []
    assert out.calculation_steps == []
    assert out.metadata == {}


class NestedInput(ToolInput):
    """Input with a nested object — exercises the $defs handling."""

    name: str
    coords: dict[str, float] = Field(default_factory=dict)


class NestedOutput(ToolOutput):
    ok: bool


class NestedTool(Tool[NestedInput, NestedOutput]):
    name = "nested"
    description = "uses a nested input"
    input_model = NestedInput
    output_model = NestedOutput

    async def execute(self, input: NestedInput) -> NestedOutput:  # noqa: A002
        return NestedOutput(ok=bool(input.name))


async def test_nested_schema_renders(client: KoraiClient) -> None:
    client.tools.register(NestedTool())
    schemas = client.tools.to_anthropic_schemas()
    assert schemas[0]["input_schema"]["properties"]["name"]["type"] == "string"
