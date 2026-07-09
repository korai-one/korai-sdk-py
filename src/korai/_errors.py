"""Exception hierarchy for the Korai Platform SDK.

All SDK errors inherit from :class:`KoraiError`, and HTTP-related errors
inherit from :class:`KoraiAPIError`. This lets app authors catch broad
categories or specific failure modes.

Example::

    from korai import KoraiClient, KoraiAPIError

    try:
        await client.llm.complete(messages=...)
    except KoraiAPIError as exc:
        if exc.status_code == 401:
            await client.auth.refresh(...)
        elif exc.status_code == 429:
            await asyncio.sleep(exc.retry_after or 1.0)
"""

from __future__ import annotations

from typing import Any


class KoraiError(Exception):
    """Base class for every error raised by the SDK."""


class KoraiAPIError(KoraiError):
    """Raised when Korai Cloud returns a 4xx/5xx HTTP response.

    Attributes:
        status_code: HTTP status code returned by the orchestrator.
        body: Parsed JSON body (if any), otherwise the raw bytes/str.
        message: A human-readable error message extracted from the body
            when possible.
        error_type: The orchestrator-specific error_type field
            (``invalid_request``, ``authentication_error``, ``server_error``,
            ``not_found``, ``conflict`` …).
        retry_after: When the server returned a ``Retry-After`` header
            (e.g. on 429), the parsed value in seconds.
        request_id: The server-issued request correlation id, extracted
            best-effort from the ``x-request-id`` / ``request-id`` /
            ``x-korai-request-id`` response headers when present.
    """

    def __init__(
        self,
        status_code: int,
        body: Any | None = None,
        message: str | None = None,
        error_type: str | None = None,
        retry_after: float | None = None,
        request_id: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.body = body
        self.retry_after = retry_after
        self.request_id = request_id
        # Extract message + error_type from a structured body when the
        # caller didn't pass them explicitly.
        if isinstance(body, dict):
            err = body.get("error")
            if isinstance(err, dict):
                if message is None:
                    message = err.get("message")
                if error_type is None:
                    error_type = err.get("type")
            elif isinstance(err, str) and message is None:
                message = err
        self.error_type = error_type
        self.message = message or f"HTTP {status_code}"
        super().__init__(f"[{status_code}] {self.message}")


class KoraiBadRequestError(KoraiAPIError):
    """Raised on 400 — the request was malformed or semantically invalid."""


class KoraiAuthError(KoraiAPIError):
    """Raised on 401 — authentication failure (missing/invalid credentials)."""


class KoraiPermissionError(KoraiAPIError):
    """Raised on 403 — authenticated but not authorized for the resource."""


class KoraiNotFoundError(KoraiAPIError):
    """Raised on 404."""


class KoraiUnprocessableError(KoraiAPIError):
    """Raised on 422 — request was well-formed but failed validation."""


class KoraiRateLimitError(KoraiAPIError):
    """Raised on 429 — caller should respect ``retry_after``."""


class KoraiServerError(KoraiAPIError):
    """Raised on any 5xx — an error on the Korai Cloud side."""


class KoraiConnectionError(KoraiAPIError):
    """Raised when the request never reached the server (network/transport
    failure, DNS, connect/read timeout). ``status_code`` is ``0``."""


class KoraiValidationError(KoraiError):
    """Raised when SDK-side validation rejects an input.

    Used for tool invocations with invalid inputs, schema mismatches, etc.
    """


class KoraiConfigError(KoraiError):
    """Raised when an SDK feature is used without the required
    configuration (e.g. RAG queries when no ``db_url`` was passed)."""


__all__ = [
    "KoraiAPIError",
    "KoraiAuthError",
    "KoraiBadRequestError",
    "KoraiConfigError",
    "KoraiConnectionError",
    "KoraiError",
    "KoraiNotFoundError",
    "KoraiPermissionError",
    "KoraiRateLimitError",
    "KoraiServerError",
    "KoraiUnprocessableError",
    "KoraiValidationError",
]
