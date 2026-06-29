"""Tools module — registry, definition, invocation of business tools.

Apps define their own tools (calculators, integrations, lookups). The
registry exposes them to the LLM via OpenAI/Anthropic tool-use format,
invokes them on the LLM's request, and returns typed results.

This module is **purely client-side** — there is no HTTP traffic. Tools
live in the host app process and are forwarded to the LLM as JSON
schemas. The LLM emits a tool-call instruction; the app passes it back
to :meth:`ToolsModule.invoke` to execute.

Reference implementations:

* ``cmd/kode/main.go`` — Korai Kode CLI tool registry (Go)
* ``vertical-fiduciaire/backend/app/tools/`` — fiduciaire tools (Python)

Example::

    from pydantic import BaseModel
    from korai.tools import Tool, ToolInput, ToolOutput

    class TaxIn(ToolInput):
        revenue_chf: float

    class TaxOut(ToolOutput):
        tax_chf: float

    class TaxTool(Tool[TaxIn, TaxOut]):
        name = "compute_tax"
        description = "Compute Swiss federal income tax."
        input_model = TaxIn
        output_model = TaxOut

        async def execute(self, input: TaxIn) -> TaxOut:
            return TaxOut(tax_chf=input.revenue_chf * 0.115)

    client.tools.register(TaxTool())
    out = await client.tools.invoke("compute_tax", {"revenue_chf": 100_000})
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel, Field, ValidationError

from korai._errors import KoraiValidationError

if TYPE_CHECKING:
    from korai._client import KoraiClient
    from korai.llm import CompletionResult, Message


# Type vars for input/output schemas.
I = TypeVar("I", bound="ToolInput")  # noqa: E741 — public symbol
O = TypeVar("O", bound="ToolOutput")  # noqa: E741 — public symbol


class ToolInput(BaseModel):
    """Base class for tool inputs.

    Subclass with Pydantic fields. The fields drive both the JSON schema
    sent to the LLM and the validation of inputs received from the LLM.
    """


class ToolOutput(BaseModel):
    """Base class for tool outputs.

    All tool outputs include audit-trail fields for transparent
    reporting: citations consulted, calculation steps, confidence
    level, free-form metadata.
    """

    citations: list[str] = Field(default_factory=list)
    calculation_steps: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class Tool(ABC, Generic[I, O]):
    """Abstract base class for a tool callable by the LLM.

    Subclasses must set :attr:`name`, :attr:`description`,
    :attr:`input_model`, and :attr:`output_model` as **class attributes**
    (not as ``__init__`` parameters), and implement :meth:`execute`.
    """

    name: str
    description: str
    input_model: type[I]
    output_model: type[O]

    @abstractmethod
    async def execute(self, input: I) -> O:  # noqa: A002 — public API
        """Execute the tool. Must be overridden by subclasses."""
        ...

    # ------------------------------------------------------------------
    # Schema conversion
    # ------------------------------------------------------------------

    def _input_schema(self) -> dict[str, Any]:
        """Return the JSON schema of the input model.

        Pydantic injects metadata keys (``title``, ``$defs``) that some
        LLM providers reject; we strip them out where appropriate.
        """
        schema = self.input_model.model_json_schema()
        # Many providers reject ``$defs`` at the root if there are no
        # references — keep it only when present and useful.
        if "$defs" in schema and not _schema_has_refs(schema):
            schema = {k: v for k, v in schema.items() if k != "$defs"}
        return schema

    def to_anthropic_schema(self) -> dict[str, Any]:
        """Convert to Anthropic tool-use schema.

        Anthropic expects ``{"name", "description", "input_schema"}``
        where ``input_schema`` is a JSON Schema with ``type: "object"``.
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self._input_schema(),
        }

    def to_openai_schema(self) -> dict[str, Any]:
        """Convert to OpenAI function-calling schema.

        OpenAI wraps the tool in ``{"type": "function", "function": {...}}``
        with ``parameters`` (their name for ``input_schema``).
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self._input_schema(),
            },
        }


@dataclass
class _RawTool:
    """A tool whose interface is a raw JSON-Schema dict rather than a
    pydantic model.

    Used for tools bridged from external sources (notably MCP servers)
    whose argument schema is plain JSON Schema and whose input is *not*
    locally validated — the upstream source is the authority. Stored
    alongside :class:`Tool` instances in :class:`ToolsModule`; the schema
    and invocation methods recognise it by type.
    """

    name: str
    description: str
    json_schema: dict[str, Any]
    execute: Callable[[dict[str, Any]], Awaitable[Any]]

    def to_anthropic_schema(self) -> dict[str, Any]:
        """Anthropic tool-use schema, emitting ``json_schema`` verbatim."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.json_schema,
        }

    def to_openai_schema(self) -> dict[str, Any]:
        """OpenAI function-calling schema, emitting ``json_schema`` verbatim."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.json_schema,
            },
        }


@runtime_checkable
class McpSession(Protocol):
    """Narrow, duck-typed view of an MCP client session.

    Deliberately structural so a real ``mcp.ClientSession`` (or any
    adapter) satisfies it without the SDK importing the ``mcp`` package.
    A conforming object exposes two awaitables:

    * ``list_tools()`` → an iterable of tool descriptors. Each descriptor
      exposes ``name``, ``description`` and ``inputSchema`` either as
      attributes (the ``mcp`` convention) or as dict keys.
    * ``call_tool(name, arguments)`` → the tool result. A ``dict`` result
      is used as-is; anything else is wrapped as ``{"value": result}``.
    """

    async def list_tools(self) -> list[Any]: ...

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any: ...


def _mcp_field(tool: Any, key: str) -> Any:
    """Read ``key`` from an MCP tool descriptor tolerant of attr/dict form."""
    if isinstance(tool, dict):
        return tool.get(key)
    return getattr(tool, key, None)


def _schema_has_refs(schema: dict[str, Any]) -> bool:
    """True if the schema contains any ``$ref`` reference."""
    stack: list[Any] = [schema]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            if "$ref" in cur:
                return True
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
    return False


@dataclass
class ToolRunResult:
    """Outcome of executing one tool call inside :meth:`ToolsModule.run`."""

    tool_call_id: str
    name: str
    # The tool's output as a JSON-able dict, or ``{"error": "..."}`` if
    # the tool was missing or raised.
    output: dict[str, Any]


@dataclass
class RunToolsResult:
    """Result of the agentic tool-use loop."""

    # Full conversation, including assistant tool-call turns and the
    # role="tool" result messages, as OpenAI-shaped dicts.
    messages: list[dict[str, Any]]
    # The last assistant completion (no further tool calls, unless the
    # loop stopped at max_turns).
    final: CompletionResult
    turns: int
    stopped_at_max_turns: bool = False
    tool_runs: list[ToolRunResult] = field(default_factory=list)


def _normalize_tool_calls(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalise raw tool-call dicts (OpenAI function-call shape or a
    pre-structured ``{id,name,input}`` shape) to ``{id, name, input}``.
    Unparseable ``arguments`` degrade to ``{}``; entries without a name
    are skipped.
    """
    out: list[dict[str, Any]] = []
    for entry in raw or []:
        if not isinstance(entry, dict):
            continue
        fn = entry.get("function") or {}
        name = fn.get("name") or entry.get("name")
        if not name:
            continue
        args = fn.get("arguments", entry.get("input"))
        if isinstance(args, str):
            try:
                parsed = json.loads(args)
                inp = parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                inp = {}
        elif isinstance(args, dict):
            inp = args
        else:
            inp = {}
        out.append({"id": str(entry.get("id", "")), "name": name, "input": inp})
    return out


def _message_to_dict(m: Message | dict[str, Any]) -> dict[str, Any]:
    """Coerce a Message model or dict to a plain OpenAI-shaped dict."""
    if isinstance(m, dict):
        return m
    return m.model_dump(exclude_none=True)


class ToolsModule:
    """Registry + invocation of locally-defined tools.

    Tools registered here are pure Python — they don't talk to Korai
    Cloud. The LLM is informed of them via :meth:`to_anthropic_schemas`
    or :meth:`to_openai_schemas`; when the LLM emits a tool call, the
    app routes it back through :meth:`invoke`.
    """

    def __init__(self, client: KoraiClient) -> None:
        self._client = client
        # Holds both pydantic-backed ``Tool`` instances and ``_RawTool``
        # wrappers (raw JSON-schema tools, e.g. bridged from MCP). Both
        # expose ``name`` and ``to_{openai,anthropic}_schema()``.
        self._tools: dict[str, Tool[Any, Any] | _RawTool] = {}

    def register(self, tool: Tool[Any, Any]) -> None:
        """Register a tool. Names must be unique; re-registering a name
        replaces the previous tool (useful for hot-reload)."""
        if not getattr(tool, "name", None):
            raise KoraiValidationError("tool.name must be set")
        self._tools[tool.name] = tool

    def register_raw(
        self,
        *,
        name: str,
        description: str,
        json_schema: dict[str, Any],
        execute: Callable[[dict[str, Any]], Awaitable[Any]],
    ) -> None:
        """Register a tool defined by a raw JSON-Schema dict.

        Unlike :meth:`register`, the input is **not** validated locally
        against a pydantic model — ``execute`` receives the LLM's argument
        dict as-is and is responsible (or its upstream, e.g. an MCP
        server) for validating it. ``json_schema`` is emitted verbatim by
        :meth:`to_openai_schemas` / :meth:`to_anthropic_schemas`.

        Re-registering an existing name replaces it, exactly like
        :meth:`register`.

        Args:
            name: Unique tool name.
            description: Human/LLM-facing description.
            json_schema: JSON Schema (typically ``{"type": "object", ...}``)
                describing the tool arguments.
            execute: Async callable taking the argument dict and returning
                the tool result (a dict, or any JSON-able value).
        """
        if not name:
            raise KoraiValidationError("tool name must be set")
        self._tools[name] = _RawTool(
            name=name,
            description=description,
            json_schema=json_schema,
            execute=execute,
        )

    def unregister(self, name: str) -> bool:
        """Remove a tool by name. Returns True if it existed."""
        return self._tools.pop(name, None) is not None

    def get(self, name: str) -> Tool[Any, Any] | _RawTool | None:
        """Return the tool with the given name, or ``None``.

        May return a :class:`Tool` instance or a :class:`_RawTool` wrapper
        (for tools registered via :meth:`register_raw` / MCP)."""
        return self._tools.get(name)

    def list(self) -> list[Tool[Any, Any] | _RawTool]:
        """Return all registered tools in insertion order.

        Entries are :class:`Tool` instances or :class:`_RawTool` wrappers."""
        return list(self._tools.values())

    def names(self) -> list[str]:
        """Return the names of all registered tools (pydantic and raw)."""
        return list(self._tools.keys())

    def to_anthropic_schemas(self) -> list[dict[str, Any]]:
        """Tool schemas formatted for Anthropic Messages API."""
        return [t.to_anthropic_schema() for t in self._tools.values()]

    def to_openai_schemas(self) -> list[dict[str, Any]]:
        """Tool schemas formatted for OpenAI Chat Completions API."""
        return [t.to_openai_schema() for t in self._tools.values()]

    async def register_mcp_server(
        self,
        session: McpSession,
        *,
        namespace: str | None = None,
    ) -> list[str]:
        """Register every tool exposed by a connected MCP server.

        Bridges an MCP client session into this registry so the existing
        :meth:`run` tool-runner can call MCP tools. The ``session`` is
        duck-typed against :class:`McpSession` — a real ``mcp.ClientSession``
        satisfies it, but the SDK never imports the ``mcp`` package.

        Each MCP tool is registered via :meth:`register_raw`: its
        ``inputSchema`` is used verbatim as the JSON schema (defaulting to
        ``{"type": "object"}`` when absent), and invocation routes back to
        ``session.call_tool``. A non-dict tool result is wrapped as
        ``{"value": result}``.

        Args:
            session: An object exposing async ``list_tools()`` and
                ``call_tool(name, arguments)`` (attributes or dict keys for
                ``name`` / ``description`` / ``inputSchema``).
            namespace: When set, tool names are prefixed with
                ``f"{namespace}__{name}"`` to avoid collisions when bridging
                multiple servers.

        Returns:
            The list of (possibly namespaced) names that were registered.
        """
        registered: list[str] = []
        for tool in await session.list_tools():
            original = _mcp_field(tool, "name")
            if not original:
                continue
            description = _mcp_field(tool, "description") or ""
            schema = _mcp_field(tool, "inputSchema")
            if not isinstance(schema, dict):
                schema = {"type": "object"}
            registered_name = f"{namespace}__{original}" if namespace else original

            # Bind ``original`` per-iteration to avoid lambda late-binding.
            def _make_executor(
                tool_name: str,
            ) -> Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]:
                async def _execute(input_dict: dict[str, Any]) -> dict[str, Any]:
                    result = await session.call_tool(tool_name, input_dict)
                    return result if isinstance(result, dict) else {"value": result}

                return _execute

            self.register_raw(
                name=registered_name,
                description=description,
                json_schema=schema,
                execute=_make_executor(original),
            )
            registered.append(registered_name)
        return registered

    async def invoke(
        self,
        name: str,
        input_dict: dict[str, Any],
    ) -> ToolOutput | dict[str, Any]:
        """Invoke a tool by name.

        For pydantic-backed tools, ``input_dict`` is validated against the
        tool's ``input_model`` (validation errors raise
        :class:`KoraiValidationError`) and a :class:`ToolOutput` is
        returned. For raw tools (see :meth:`register_raw` /
        :meth:`register_mcp_server`), ``input_dict`` is passed through
        unvalidated to the tool's ``execute`` and its result dict is
        returned directly.

        Example::

            out = await client.tools.invoke(
                "compute_tax", {"revenue_chf": 100000}
            )
        """
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"tool '{name}' not registered")
        if isinstance(tool, _RawTool):
            return await tool.execute(input_dict)
        try:
            validated_input = tool.input_model(**input_dict)
        except ValidationError as exc:
            raise KoraiValidationError(
                f"invalid input for tool '{name}': {exc.errors()}"
            ) from exc
        return await tool.execute(validated_input)

    async def run(
        self,
        messages: list[Message] | list[dict[str, Any]],
        *,
        model: str = "auto",
        system: str | None = None,
        temperature: float = 1.0,
        max_turns: int = 5,
    ) -> RunToolsResult:
        """Agentic tool-use loop: send the conversation plus the
        registered tool schemas to the model, execute any tool calls it
        returns locally via :meth:`invoke`, feed the results back as
        ``role="tool"`` messages, and repeat until the model answers
        without requesting tools (or ``max_turns`` is reached).

        This is the hand-written ergonomic layer on top of the generated
        chat-completion core — the Python analogue of OpenAI's
        ``runTools``. A tool error (missing tool or failed validation /
        execution) is fed back to the model as ``{"error": ...}`` rather
        than aborting the loop.

        Example::

            client.tools.register(AddTool())
            res = await client.tools.run(
                messages=[{"role": "user", "content": "what is 2+3?"}],
            )
            print(res.final.content)
        """
        schemas = self.to_openai_schemas()
        msgs: list[dict[str, Any]] = [_message_to_dict(m) for m in messages]
        final: CompletionResult | None = None
        tool_runs: list[ToolRunResult] = []

        for turn in range(max_turns):
            result = await self._client.llm.complete(
                messages=msgs,
                model=model,
                tools=schemas,
                system=system if turn == 0 else None,
                temperature=temperature,
            )
            final = result

            assistant: dict[str, Any] = {"role": "assistant", "content": result.content}
            if result.tool_calls:
                assistant["tool_calls"] = result.tool_calls
            msgs.append(assistant)

            calls = _normalize_tool_calls(result.tool_calls)
            if not calls:
                return RunToolsResult(
                    messages=msgs, final=result, turns=turn + 1, tool_runs=tool_runs
                )

            for call in calls:
                try:
                    output = await self.invoke(call["name"], call["input"])
                    # Pydantic ToolOutput → dict; raw tools already return a dict.
                    payload: dict[str, Any] = (
                        output.model_dump(mode="json")
                        if isinstance(output, ToolOutput)
                        else output
                    )
                except Exception as exc:  # intentional: tool errors feed back
                    payload = {"error": str(exc)}
                tool_runs.append(
                    ToolRunResult(
                        tool_call_id=call["id"], name=call["name"], output=payload
                    )
                )
                msgs.append(
                    {
                        "role": "tool",
                        "name": call["name"],
                        "tool_call_id": call["id"],
                        "content": json.dumps(payload),
                    }
                )

        return RunToolsResult(
            messages=msgs,
            final=final,  # type: ignore[arg-type]  # max_turns>=1 so always set
            turns=max_turns,
            stopped_at_max_turns=True,
            tool_runs=tool_runs,
        )


__all__ = [
    "McpSession",
    "RunToolsResult",
    "Tool",
    "ToolInput",
    "ToolOutput",
    "ToolRunResult",
    "ToolsModule",
]
