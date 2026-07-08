"""Authentication module — login, signup, JWT, current user, API keys.

Korai Cloud exposes:

* ``POST /auth/signup`` → returns ``{user, token}``
* ``POST /auth/login`` → returns ``{user, token}``
* ``GET  /auth/me`` (authed) → returns ``{user}``
* ``POST /auth/keys`` (authed) → ``{key, details}``
* ``GET  /auth/keys`` (authed)
* ``DELETE /auth/keys/:id`` (authed)

Today there is **no refresh-token endpoint** server-side: the orchestrator
issues a single 7-day HS256 JWT. :meth:`AuthModule.refresh` therefore
keeps a TODO marker and returns the existing pair untouched if the
endpoint is missing. :meth:`AuthModule.logout` is best-effort and clears
local tokens.

Example::

    async with KoraiClient(base_url="https://cloud.korai.one") as client:
        pair = await client.auth.login("user@example.com", "secret123")
        me = await client.auth.me()
        print(me.email, me.role)
"""

from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field

from korai._client import _RawBody
from korai._errors import KoraiAPIError, KoraiAuthError
from korai._generated.api.auth import (
    create_api_key as create_api_key_api,
)
from korai._generated.api.auth import (
    delete_api_key as delete_api_key_api,
)
from korai._generated.api.auth import (
    get_current_user as get_current_user_api,
)
from korai._generated.api.auth import (
    list_api_keys as list_api_keys_api,
)
from korai._generated.api.auth import (
    login as login_api,
)
from korai._generated.api.auth import (
    signup as signup_api,
)

if TYPE_CHECKING:
    from korai._client import KoraiClient


# Hard-coded mirror of internal/auth/jwt.go::TokenDuration (7 days).
_DEFAULT_TOKEN_TTL_SECONDS = 7 * 24 * 3600


class TokenPair(BaseModel):
    """Pair of access + refresh JWT tokens.

    Korai Cloud only issues a single token today — :attr:`refresh_token`
    will mirror :attr:`access_token` for forward compatibility until a
    real refresh endpoint exists.
    """

    access_token: str
    refresh_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int = Field(
        default=_DEFAULT_TOKEN_TTL_SECONDS,
        description="Seconds until access_token expiry",
    )


class CurrentUser(BaseModel):
    """The authenticated user as exposed by ``GET /auth/me``."""

    id: str
    email: str
    full_name: str = ""
    preferred_language: Literal["fr", "de", "it", "en"] = "fr"
    organization_id: str | None = None
    role: str | None = None


class APIKey(BaseModel):
    """An API key registered with Korai Cloud. The full ``key`` value is
    only present when returned from :meth:`create_api_key` — listings
    redact it down to a non-secret prefix."""

    id: str
    label: str = ""
    prefix: str = ""
    key: str | None = None  # only on creation
    last_used_at: str | None = None
    created_at: str | None = None


def decode_jwt_unverified(token: str) -> dict[str, Any]:
    """Decode a JWT *without* verifying its signature.

    Use sparingly — it's only safe when the token was just issued by a
    trusted source (e.g. extracting the user id from your own freshly
    received access token). Intended for offline introspection in
    :meth:`AuthModule.me`'s fallback path.
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("malformed JWT (expected 3 segments)")
    payload_b64 = parts[1]
    # base64url with no padding
    pad = "=" * (-len(payload_b64) % 4)
    raw = base64.urlsafe_b64decode(payload_b64 + pad)
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JWT payload: {exc}") from exc
    if not isinstance(decoded, dict):
        raise ValueError("JWT payload is not a JSON object")
    return decoded


def _coerce_user(raw: dict[str, Any] | None) -> CurrentUser:
    """Turn the orchestrator user JSON into a CurrentUser, filling gaps."""
    if not isinstance(raw, dict):
        raise ValueError("expected user object in response")
    return CurrentUser(
        id=str(raw.get("id", "")),
        email=str(raw.get("email", "")),
        full_name=str(raw.get("display_name") or raw.get("full_name") or ""),
        preferred_language=raw.get("preferred_language") or "fr",  # type: ignore[arg-type]
        organization_id=raw.get("organization_id") or raw.get("cab"),
        role=raw.get("role"),
    )


class AuthModule:
    """Authentication operations.

    All mutating calls automatically store the returned tokens on the
    parent :class:`KoraiClient`, so subsequent calls are authenticated
    without manual plumbing.
    """

    def __init__(self, client: KoraiClient) -> None:
        self._client = client

    # ------------------------------------------------------------------
    # Login / signup / logout
    # ------------------------------------------------------------------

    async def login(self, email: str, password: str) -> TokenPair:
        """Login with email + password.

        Stores the returned token on the client and returns a
        :class:`TokenPair`. Raises :class:`KoraiAuthError` on
        wrong credentials.

        Example::

            pair = await client.auth.login("alice@example.com", "secret")
        """
        data = await self._client._call_gen(
            login_api._get_kwargs,
            path="/auth/login",
            body=_RawBody({"email": email, "password": password}),
        )
        return self._consume_auth_response(data)

    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        organization_name: str | None = None,
        organization_country: str = "CH",  # noqa: ARG002 — reserved
    ) -> TokenPair:
        """Register a new user. Behaves like login afterwards.

        ``organization_name`` and ``organization_country`` are accepted
        for API compatibility with the future ``/auth/signup`` schema —
        they are forwarded but the orchestrator ignores them today
        (organizations are not yet exposed via the Cloud API).

        Example::

            pair = await client.auth.register(
                email="me@example.com",
                password="hunter2hunter2",
                full_name="Jane Doe",
            )
        """
        body: dict[str, Any] = {
            "email": email,
            "password": password,
            "display_name": full_name,
        }
        if organization_name:
            body["organization_name"] = organization_name
        data = await self._client._call_gen(
            signup_api._get_kwargs, path="/auth/signup", body=_RawBody(body)
        )
        return self._consume_auth_response(data)

    async def refresh(self, refresh_token: str) -> TokenPair:
        """Exchange a refresh token for a new TokenPair.

        TODO(cloud): the orchestrator does not expose ``/auth/refresh``
        today (single 7-day JWT, no refresh flow). When that endpoint
        ships, this method already calls it. Until then we return the
        token untouched — the caller can detect this by comparing
        ``access_token``.
        """
        try:
            data = await self._client._request(
                "POST",
                "/auth/refresh",
                json_body={"refresh_token": refresh_token},
            )
        except KoraiAPIError as exc:
            if exc.status_code in (404, 405, 501):
                # Endpoint not implemented — return the token as-is.
                return TokenPair(
                    access_token=self._client.access_token or refresh_token,
                    refresh_token=refresh_token,
                )
            raise
        return self._consume_auth_response(data)

    async def me(self) -> CurrentUser:
        """Return the current authenticated user.

        Calls ``GET /auth/me`` if a JWT is set; on 404/501 it falls back
        to decoding the access token claims (sub/email/role) without
        verifying its signature — useful for offline tools that only
        need to know who they are.
        """
        try:
            data = await self._client._call_gen(
                get_current_user_api._get_kwargs, path="/auth/me"
            )
        except KoraiAPIError as exc:
            if exc.status_code in (404, 405, 501):
                return self._me_from_token()
            raise
        user_raw = data.get("user") if isinstance(data, dict) else None
        if user_raw is None and isinstance(data, dict):
            user_raw = data
        return _coerce_user(user_raw)

    async def logout(self) -> None:
        """Best-effort logout.

        JWT is stateless server-side, so the orchestrator may not
        implement ``/auth/logout``. We attempt the call (so server-side
        audit can record it if it is implemented), then always clear
        the in-memory tokens so subsequent SDK calls are unauthenticated.
        """
        try:
            await self._client._request("POST", "/auth/logout")
        except KoraiAPIError as exc:
            # 404/405/501 → server doesn't implement logout, that's OK.
            if exc.status_code not in (404, 405, 501):
                # 401 also fine — already logged out server-side.
                if exc.status_code != 401:
                    raise
        finally:
            self._client.clear_tokens()

    # ------------------------------------------------------------------
    # API keys
    # ------------------------------------------------------------------

    async def create_api_key(self, label: str = "default") -> APIKey:
        """Create a new API key (sk-korai-…). The raw key is only
        returned once — store it immediately.

        Example::

            key = await client.auth.create_api_key("ci-pipeline")
            print(key.key)  # only printable here
        """
        data = await self._client._call_gen(
            create_api_key_api._get_kwargs,
            path="/auth/keys",
            body=_RawBody({"label": label}),
        )
        details = data.get("details", {}) if isinstance(data, dict) else {}
        return APIKey(
            id=str(details.get("id", "")),
            label=str(details.get("label", label)),
            prefix=str(details.get("prefix", "")),
            key=data.get("key") if isinstance(data, dict) else None,
            last_used_at=details.get("last_used_at"),
            created_at=details.get("created_at"),
        )

    async def list_api_keys(self) -> list[APIKey]:
        """List API keys for the current user (raw key not included)."""
        data = await self._client._call_gen(
            list_api_keys_api._get_kwargs, path="/auth/keys"
        )
        keys = data.get("keys", []) if isinstance(data, dict) else []
        out: list[APIKey] = []
        for raw in keys:
            if not isinstance(raw, dict):
                continue
            out.append(
                APIKey(
                    id=str(raw.get("id", "")),
                    label=str(raw.get("label", "")),
                    prefix=str(raw.get("prefix", "")),
                    last_used_at=raw.get("last_used_at"),
                    created_at=raw.get("created_at"),
                )
            )
        return out

    async def delete_api_key(self, key_id: str) -> None:
        """Revoke an API key by id."""
        await self._client._call_gen(
            delete_api_key_api._get_kwargs, path=f"/auth/keys/{key_id}", id=key_id
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _consume_auth_response(self, data: dict[str, Any]) -> TokenPair:
        """Extract ``token`` (or ``access_token``/``refresh_token``)
        from the orchestrator response and store on the client."""
        if not isinstance(data, dict):
            raise KoraiAuthError(status_code=0, message="malformed auth response")
        access = data.get("access_token") or data.get("token")
        refresh = data.get("refresh_token") or access
        if not isinstance(access, str) or not access:
            raise KoraiAuthError(status_code=0, message="auth response missing token")
        expires_in_raw = data.get("expires_in")
        try:
            expires_in = int(expires_in_raw) if expires_in_raw is not None else _DEFAULT_TOKEN_TTL_SECONDS
        except (TypeError, ValueError):
            expires_in = _DEFAULT_TOKEN_TTL_SECONDS
        pair = TokenPair(
            access_token=access,
            refresh_token=refresh if isinstance(refresh, str) else access,
            expires_in=expires_in,
        )
        self._client.set_tokens(pair.access_token, pair.refresh_token)
        return pair

    def _me_from_token(self) -> CurrentUser:
        """Fallback for /auth/me — decode JWT claims without verification.

        Maps the Korai claims (``sub``/``email``/``role``/optional
        ``cab`` for organization id) into :class:`CurrentUser`.
        """
        token = self._client.access_token or self._client.api_key
        if not token:
            raise KoraiAuthError(
                status_code=401, message="no access token to introspect"
            )
        try:
            claims = decode_jwt_unverified(token)
        except ValueError as exc:
            # Static API keys are not JWTs — return a minimal user.
            if token.startswith("sk-korai-"):
                return CurrentUser(id="api-key", email="api-key@korai.one")
            raise KoraiAuthError(
                status_code=401, message=f"cannot decode token: {exc}"
            ) from exc
        return CurrentUser(
            id=str(claims.get("sub", "")),
            email=str(claims.get("email", "")),
            full_name=str(claims.get("name", "")),
            preferred_language=claims.get("lang") or "fr",  # type: ignore[arg-type]
            organization_id=claims.get("cab") or claims.get("organization_id"),
            role=claims.get("role"),
        )


__all__ = [
    "APIKey",
    "AuthModule",
    "CurrentUser",
    "TokenPair",
    "decode_jwt_unverified",
]
