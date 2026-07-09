"""Top-level KoraiClient — entry point for all SDK modules.

The :class:`KoraiClient` is the single object an application instantiates.
It owns the :class:`httpx.AsyncClient` used to talk to Korai Cloud,
the optional access/refresh JWT tokens, and lazily-instantiated module
namespaces (``client.llm``, ``client.audit`` …).

The client is async-native — every network call is awaitable. Use it as
an ``async with`` context manager to ensure the underlying HTTP pool is
closed properly::

    async with KoraiClient(api_key="kfid_***") as client:
        result = await client.llm.complete(messages=[...])

Refresh-token flow
------------------

When the orchestrator returns 401 on a request that wasn't itself an
``/auth/*`` call, the client transparently calls
:meth:`korai.auth.AuthModule.refresh` and retries once. If the refresh
itself fails (or no refresh token is set), the original 401 is raised
to the caller.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

import httpx

from korai._errors import (
    KoraiAPIError,
    KoraiAuthError,
    KoraiBadRequestError,
    KoraiConnectionError,
    KoraiNotFoundError,
    KoraiPermissionError,
    KoraiRateLimitError,
    KoraiServerError,
    KoraiUnprocessableError,
)
from korai._generated.client import Client as _GenClient
from korai._version import __version__

if TYPE_CHECKING:
    from korai.audit import AuditModule
    from korai.auth import AuthModule
    from korai.billing import BillingModule
    from korai.fleet import FleetModule
    from korai.llm import LLMModule
    from korai.rag import RAGModule
    from korai.tenant import TenantModule
    from korai.tools import ToolsModule

logger = logging.getLogger("korai")


# Endpoints that are themselves part of the auth dance — we never try
# to refresh a token while logging in or refreshing.
_AUTH_PATHS = ("/auth/login", "/auth/signup", "/auth/refresh", "/auth/logout")


def _is_retryable_status(status: int) -> bool:
    """Transient statuses worth retrying (matches the Anthropic SDK set)."""
    return status in (408, 409, 429) or status >= 500


# Headers a Korai/proxy stack may use to expose the request correlation id,
# checked in order. Lookup is case-insensitive via httpx.Headers.
_REQUEST_ID_HEADERS = ("x-request-id", "request-id", "x-korai-request-id")


def _extract_request_id(headers: httpx.Headers) -> str | None:
    """Best-effort extraction of the server-issued request id from response
    headers. Returns the first matching header value, or ``None``."""
    for name in _REQUEST_ID_HEADERS:
        value = headers.get(name)
        if value:
            return value
    return None


class _RawBody:
    """Duck-typed body wrapper for the generated api functions.

    openapi-python-client serialises a request via ``body.to_dict()``.
    Passing this shim lets module methods send the SDK's own richer dict
    payload verbatim — including fields the generated request model does
    not model (``tools``, ``system``, per-message ``name``) — without
    constructing attrs request models field-by-field.
    """

    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def to_dict(self) -> dict[str, Any]:
        return self._payload


class KoraiClient:
    """Top-level Korai SDK client.

    Holds shared configuration (API key or JWT, base URL, http client) and
    exposes the seven module namespaces. Each module is lazily
    instantiated on first access.

    Args:
        api_key: A long-lived API key (``sk-korai-...``). Sent in every
            request as ``Authorization: Bearer <api_key>``. Mutually
            exclusive with passing a JWT via :meth:`set_tokens`. When
            ``None``, falls back to the ``KORAI_API_KEY`` environment
            variable.
        base_url: Base URL of the Korai Cloud orchestrator. When not
            given, the ``KORAI_BASE_URL`` environment variable is used if
            set, otherwise it defaults to production. For local
            development, pass ``http://localhost:8080``. An explicit
            argument always wins over the environment.
        timeout: HTTP request timeout in seconds. Streaming responses
            apply this only to the connect phase.
        organization_id: Optional tenant scoping for multi-tenant users.
            Sent as ``X-Korai-Organization`` header.
        db_url: Optional SQLAlchemy database URL used by the audit module
            for the local signed log and by the RAG module for vector
            retrieval. Falls back to ``sqlite+aiosqlite:///./korai_local.db``
            if not set and the audit module is used.
        audit_secret: HMAC key (bytes/str) used to sign audit entries. If
            not set, audit signatures are disabled but the chain hashes
            still protect against tampering.

    Example::

        client = KoraiClient(api_key="sk-korai-***")
        await client.llm.complete(...)
        await client.audit.log("event.foo")
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
        organization_id: str | None = None,
        *,
        max_retries: int = 2,
        db_url: str | None = None,
        audit_secret: bytes | str | None = None,
    ) -> None:
        # Resolve credentials/base URL from the environment when the caller
        # did not pass them explicitly. An explicit argument always wins.
        self.api_key = api_key or os.environ.get("KORAI_API_KEY")
        resolved_base_url = (
            base_url or os.environ.get("KORAI_BASE_URL") or "https://cloud.korai.one"
        )
        self.base_url = resolved_base_url.rstrip("/")
        self.organization_id = organization_id
        self._max_retries = max_retries
        self._timeout = timeout
        self.db_url = db_url
        if isinstance(audit_secret, str):
            audit_secret = audit_secret.encode("utf-8")
        self.audit_secret: bytes | None = audit_secret

        # JWT state — populated on auth.login() / auth.refresh().
        self._access_token: str | None = None
        self._refresh_token: str | None = None

        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            event_hooks={"request": [self._inject_auth]},
        )
        # Generated transport core (openapi-python-client) built from
        # specs/openapi.yaml. It shares the SDK's httpx client, so respx,
        # the connection pool, and the _inject_auth event hook all apply.
        # Module methods route through it via _call_gen; see docs/CODEGEN.md.
        self._gen = _GenClient(base_url=self.base_url)
        self._gen.set_async_httpx_client(self._http)
        self._refresh_lock = asyncio.Lock()

        # Lazy module references — populated on first access.
        self._auth: AuthModule | None = None
        self._tenant: TenantModule | None = None
        self._llm: LLMModule | None = None
        self._rag: RAGModule | None = None
        self._audit: AuditModule | None = None
        self._tools: ToolsModule | None = None
        self._billing: BillingModule | None = None
        self._fleet: FleetModule | None = None

    # ------------------------------------------------------------------
    # Authorization plumbing
    # ------------------------------------------------------------------

    def _default_headers(self) -> dict[str, str]:
        h: dict[str, str] = {
            "User-Agent": f"korai-sdk-py/{__version__}",
            "Accept": "application/json",
        }
        bearer = self._access_token or self.api_key
        if bearer:
            h["Authorization"] = f"Bearer {bearer}"
        if self.organization_id:
            h["X-Korai-Organization"] = self.organization_id
        return h

    async def _inject_auth(self, request: httpx.Request) -> None:
        """httpx request event hook: inject the dynamic header set onto
        every outgoing request. The SDK's own ``_request`` already sets
        these explicitly; generated-client calls (which build their own
        requests) rely on this hook. ``setdefault`` never overrides an
        explicitly-set header, so the two paths don't collide.
        """
        for key, value in self._default_headers().items():
            request.headers.setdefault(key, value)

    def set_tokens(self, access_token: str, refresh_token: str | None = None) -> None:
        """Store JWT tokens issued by the orchestrator after login.

        Subsequent requests will use the access token as Bearer credential
        instead of the static ``api_key``. If a refresh token is provided
        and the orchestrator returns 401, the client will attempt one
        automatic refresh before re-raising.
        """
        self._access_token = access_token
        self._refresh_token = refresh_token

    def clear_tokens(self) -> None:
        """Erase the in-memory access/refresh tokens (best-effort logout)."""
        self._access_token = None
        self._refresh_token = None

    @property
    def access_token(self) -> str | None:
        """Currently stored JWT access token, if any."""
        return self._access_token

    @property
    def refresh_token(self) -> str | None:
        """Currently stored JWT refresh token, if any."""
        return self._refresh_token

    # ------------------------------------------------------------------
    # Core HTTP
    # ------------------------------------------------------------------

    async def _send_with_retry(
        self, send: Callable[[], Awaitable[httpx.Response]]
    ) -> httpx.Response:
        """Issue a request via ``send`` (a fresh-request factory), retrying
        transient failures (408/409/429/5xx + connection errors) with
        exponential backoff + jitter, honoring Retry-After. ``send`` must
        build a fresh request on each call so the body can be re-sent.
        """
        for attempt in range(self._max_retries + 1):
            try:
                response = await send()
            except httpx.HTTPError:
                if attempt >= self._max_retries:
                    raise
                await asyncio.sleep(self._retry_delay(attempt, None))
                continue
            if (
                response.status_code < 400
                or attempt >= self._max_retries
                or not _is_retryable_status(response.status_code)
            ):
                return response
            await response.aread()  # free the connection before retrying
            await asyncio.sleep(
                self._retry_delay(attempt, response.headers.get("Retry-After"))
            )
        raise RuntimeError("unreachable")  # the loop always returns or raises

    @staticmethod
    def _retry_delay(attempt: int, retry_after: str | None) -> float:
        """Backoff for retry ``attempt`` (0-based). Honors Retry-After
        (seconds) when present; otherwise exponential (0.5s base, 8s cap)
        with 50–100% jitter."""
        if retry_after:
            try:
                secs = float(retry_after)
                if secs >= 0:
                    return min(secs, 60.0)
            except ValueError:
                pass
        exp = min(8.0, 0.5 * (2**attempt))
        return exp * (0.5 + random.random() * 0.5)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        _retry_after_refresh: bool = True,
    ) -> Any:
        """Send a JSON request, parse the JSON response, return the body.

        Centralizes:

        * Default headers (User-Agent, Authorization, X-Korai-Organization)
        * 4xx/5xx → typed :class:`KoraiAPIError` subclasses
        * Automatic JWT refresh on 401 (single retry)
        * Optional caller-provided headers and timeout overrides

        Returns the decoded JSON body. Empty bodies become ``{}``. Raw
        bytes responses (e.g. exports) should use :meth:`_request_raw`.
        """
        merged_headers = self._default_headers()
        if headers:
            merged_headers.update(headers)

        try:
            response = await self._send_with_retry(
                lambda: self._http.request(
                    method,
                    path,
                    json=json_body,
                    params=params,
                    headers=merged_headers,
                    timeout=timeout,
                )
            )
        except httpx.HTTPError as exc:
            raise KoraiConnectionError(
                status_code=0,
                message=f"network error: {exc}",
                body=None,
            ) from exc

        # 401 → try refresh once, then retry the original call.
        if (
            response.status_code == 401
            and _retry_after_refresh
            and self._refresh_token
            and not any(path.startswith(p) for p in _AUTH_PATHS)
        ):
            refreshed = await self._try_refresh()
            if refreshed:
                return await self._request(
                    method,
                    path,
                    json_body=json_body,
                    params=params,
                    headers=headers,
                    timeout=timeout,
                    _retry_after_refresh=False,
                )

        if response.status_code >= 400:
            self._raise_for_status(response)

        if not response.content:
            return {}
        try:
            return response.json()
        except json.JSONDecodeError:
            return {"_raw": response.text}

    async def _request_raw(
        self,
        method: str,
        path: str,
        *,
        json_body: Any | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """Same as :meth:`_request` but returns the raw httpx response.

        Use this for binary downloads, SSE streaming, or any endpoint
        where you need to read headers / status manually.
        """
        merged_headers = self._default_headers()
        if headers:
            merged_headers.update(headers)
        try:
            response = await self._send_with_retry(
                lambda: self._http.request(
                    method,
                    path,
                    json=json_body,
                    params=params,
                    headers=merged_headers,
                    timeout=timeout,
                )
            )
        except httpx.HTTPError as exc:
            raise KoraiConnectionError(
                status_code=0,
                message=f"network error: {exc}",
                body=None,
            ) from exc
        if response.status_code >= 400:
            self._raise_for_status(response)
        return response

    async def request_raw(
        self,
        method: str,
        path: str,
        *,
        json_body: Any | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """Public raw-response escape hatch.

        Send an arbitrary request through the SDK's transport — auth
        headers merged, transient failures retried via
        :meth:`_send_with_retry` — and return the raw
        :class:`httpx.Response` **without raising on non-2xx**. The caller
        inspects ``response.status_code`` / ``response.headers`` /
        ``response.json()`` directly.

        Use this when an endpoint isn't yet modelled by a typed module,
        when you need the response headers or status verbatim, or when a
        4xx/5xx body carries information you want to handle yourself rather
        than as a :class:`~korai._errors.KoraiAPIError`.

        Unlike :meth:`_request` / :meth:`_request_raw`, this does **not**
        attempt the automatic JWT refresh on 401 — a 401 Response is
        returned to the caller like any other status.

        Example::

            resp = await client.request_raw("GET", "/v1/whoami")
            if resp.status_code == 200:
                print(resp.json())

        Returns:
            The raw :class:`httpx.Response`, regardless of status code.
        """
        merged_headers = self._default_headers()
        if headers:
            merged_headers.update(headers)
        try:
            return await self._send_with_retry(
                lambda: self._http.request(
                    method,
                    path,
                    json=json_body,
                    params=params,
                    headers=merged_headers,
                    timeout=timeout,
                )
            )
        except httpx.HTTPError as exc:
            raise KoraiConnectionError(
                status_code=0,
                message=f"network error: {exc}",
                body=None,
            ) from exc

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Convert a 4xx/5xx response into a typed exception and raise."""
        body: Any
        try:
            body = response.json()
        except json.JSONDecodeError:
            body = response.text

        retry_after_raw = response.headers.get("Retry-After")
        retry_after: float | None = None
        if retry_after_raw:
            try:
                retry_after = float(retry_after_raw)
            except ValueError:
                retry_after = None

        kwargs: dict[str, Any] = {
            "status_code": response.status_code,
            "body": body,
            "retry_after": retry_after,
            "request_id": _extract_request_id(response.headers),
        }
        status = response.status_code
        cls: type[KoraiAPIError]
        if status == 400:
            cls = KoraiBadRequestError
        elif status == 401:
            cls = KoraiAuthError
        elif status == 403:
            cls = KoraiPermissionError
        elif status == 404:
            cls = KoraiNotFoundError
        elif status == 422:
            cls = KoraiUnprocessableError
        elif status == 429:
            cls = KoraiRateLimitError
        elif status >= 500:
            cls = KoraiServerError
        else:
            cls = KoraiAPIError
        raise cls(**kwargs)

    async def _call_gen(
        self,
        get_kwargs: Any,
        *,
        path: str,
        _retry_after_refresh: bool = True,
        **kwargs: Any,
    ) -> Any:
        """Send a request via the generated transport core and return the
        decoded JSON body, preserving the SDK's 401-refresh + typed-error
        behaviour.

        ``get_kwargs`` is a generated ``_get_kwargs`` builder from a
        ``korai._generated.api.*`` module: it turns endpoint arguments
        (``body=...``, ``id=...``, query params) into the httpx request
        kwargs (method + URL from the spec). We issue the request on the
        shared httpx client — so respx, the pool, and the _inject_auth
        hook all apply — and decode the response ourselves rather than
        through the generated attrs models (their strict ``format: uuid``
        parsing rejects non-UUID test/staging ids).
        """
        request_kwargs = get_kwargs(**kwargs)
        try:
            resp = await self._send_with_retry(
                lambda: self._gen.get_async_httpx_client().request(**request_kwargs)
            )
        except httpx.HTTPError as exc:
            raise KoraiConnectionError(
                status_code=0, message=f"network error: {exc}", body=None
            ) from exc

        if (
            resp.status_code == 401
            and _retry_after_refresh
            and self._refresh_token
            and not any(path.startswith(p) for p in _AUTH_PATHS)
            and await self._try_refresh()
        ):
            return await self._call_gen(
                get_kwargs, path=path, _retry_after_refresh=False, **kwargs
            )

        if resp.status_code >= 400:
            self._raise_for_status(resp)

        if not resp.content:
            return {}
        try:
            return resp.json()
        except json.JSONDecodeError:
            return {"_raw": resp.text}

    async def _try_refresh(self) -> bool:
        """Best-effort JWT refresh. Returns True if a new token is in place."""
        async with self._refresh_lock:
            if not self._refresh_token:
                return False
            try:
                # Lazy-import to avoid a cyclic import on module load.
                from korai.auth import AuthModule

                auth_mod = AuthModule(self)
                pair = await auth_mod.refresh(self._refresh_token)
                self.set_tokens(pair.access_token, pair.refresh_token)
                return True
            except Exception as exc:
                logger.warning("Korai SDK: token refresh failed: %s", exc)
                return False

    def with_options(
        self,
        *,
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> KoraiClient:
        """Return a new client with per-request configuration overrides.

        Mirrors the Anthropic SDK's ``client.with_options(...)``. The
        returned :class:`KoraiClient` shares the same authentication
        (``api_key`` plus any access/refresh JWT currently set), base URL
        and organization scoping, but overrides ``timeout`` and/or
        ``max_retries``. Any option left as ``None`` inherits this
        client's current value.

        The clone owns its *own* ``httpx.AsyncClient`` (and connection
        pool), so it must be closed independently — use it as an
        ``async with`` block or call :meth:`aclose`. The original client
        is unaffected.

        Example::

            fast = client.with_options(timeout=5.0, max_retries=0)
            async with fast:
                await fast.llm.complete(messages=[...])
        """
        clone = KoraiClient(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self._timeout if timeout is None else timeout,
            organization_id=self.organization_id,
            max_retries=self._max_retries if max_retries is None else max_retries,
            db_url=self.db_url,
            audit_secret=self.audit_secret,
        )
        if self._access_token is not None:
            clone.set_tokens(self._access_token, self._refresh_token)
        return clone

    # ------------------------------------------------------------------
    # Module accessors (lazy)
    # ------------------------------------------------------------------

    @property
    def auth(self) -> AuthModule:
        if self._auth is None:
            from korai.auth import AuthModule

            self._auth = AuthModule(self)
        return self._auth

    @property
    def tenant(self) -> TenantModule:
        if self._tenant is None:
            from korai.tenant import TenantModule

            self._tenant = TenantModule(self)
        return self._tenant

    @property
    def llm(self) -> LLMModule:
        if self._llm is None:
            from korai.llm import LLMModule

            self._llm = LLMModule(self)
        return self._llm

    @property
    def rag(self) -> RAGModule:
        if self._rag is None:
            from korai.rag import RAGModule

            self._rag = RAGModule(self)
        return self._rag

    @property
    def audit(self) -> AuditModule:
        if self._audit is None:
            from korai.audit import AuditModule

            self._audit = AuditModule(self)
        return self._audit

    @property
    def tools(self) -> ToolsModule:
        if self._tools is None:
            from korai.tools import ToolsModule

            self._tools = ToolsModule(self)
        return self._tools

    @property
    def billing(self) -> BillingModule:
        if self._billing is None:
            from korai.billing import BillingModule

            self._billing = BillingModule(self)
        return self._billing

    @property
    def fleet(self) -> FleetModule:
        if self._fleet is None:
            from korai.fleet import FleetModule

            self._fleet = FleetModule(self)
        return self._fleet

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def aclose(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._http.aclose()

    async def __aenter__(self) -> KoraiClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()


__all__ = ["KoraiClient"]
