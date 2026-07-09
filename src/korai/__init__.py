"""Korai Platform SDK for Python.

Provides typed, async-native clients for building apps on Korai:

* ``korai.auth``    — login, JWT, multi-tenant context
* ``korai.tenant``  — organization (cabinet) management
* ``korai.llm``     — chat completions wrapper (Korai Cloud)
* ``korai.rag``     — vector retrieval + reranker primitives
* ``korai.audit``   — append-only signed audit log
* ``korai.tools``   — tool registry and invocation
* ``korai.billing`` — quotas and usage tracking

Quick start::

    from korai import KoraiClient
    from korai.llm import Message

    async def main() -> None:
        async with KoraiClient(api_key="sk-korai-***") as client:
            result = await client.llm.complete(
                messages=[Message(role="user", content="Hello")],
                model="claude-opus-4-7",
            )
            print(result.content)

For app authors, see the dedicated module docs.
"""

from korai._client import KoraiClient
from korai._sync import SyncKoraiClient
from korai._errors import (
    KoraiAPIError,
    KoraiAuthError,
    KoraiBadRequestError,
    KoraiConfigError,
    KoraiConnectionError,
    KoraiError,
    KoraiNotFoundError,
    KoraiPermissionError,
    KoraiRateLimitError,
    KoraiServerError,
    KoraiUnprocessableError,
    KoraiValidationError,
)
from korai._version import __version__
from korai.session import (
    Block,
    ImageBlock,
    Session,
    SessionMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    flat_to_session_message,
    flat_to_session_messages,
    session_from_dict,
    session_from_json,
    session_message_to_flat,
    session_messages_to_flat,
    session_to_dict,
    session_to_json,
)

__all__ = [
    "Block",
    "ImageBlock",
    "Session",
    "SessionMessage",
    "TextBlock",
    "ToolResultBlock",
    "ToolUseBlock",
    "KoraiAPIError",
    "KoraiAuthError",
    "KoraiBadRequestError",
    "KoraiClient",
    "KoraiConfigError",
    "KoraiConnectionError",
    "KoraiError",
    "KoraiNotFoundError",
    "KoraiPermissionError",
    "KoraiRateLimitError",
    "KoraiServerError",
    "KoraiUnprocessableError",
    "KoraiValidationError",
    "SyncKoraiClient",
    "__version__",
    "flat_to_session_message",
    "flat_to_session_messages",
    "session_from_dict",
    "session_from_json",
    "session_message_to_flat",
    "session_messages_to_flat",
    "session_to_dict",
    "session_to_json",
]
