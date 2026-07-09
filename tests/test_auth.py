"""Tests for korai.auth.AuthModule."""

from __future__ import annotations

import httpx
import pytest
import respx

from korai import KoraiAuthError, KoraiClient
from korai.auth import APIKey, CurrentUser, TokenPair, decode_jwt_unverified

from .conftest import TEST_BASE_URL


async def test_login_stores_token(
    client: KoraiClient, respx_mock: respx.Router, fake_jwt: str
) -> None:
    respx_mock.post("/auth/login").mock(
        return_value=httpx.Response(
            200,
            json={
                "user": {"id": "user-1", "email": "alice@example.com"},
                "token": fake_jwt,
            },
        )
    )
    pair = await client.auth.login("alice@example.com", "secret")
    assert isinstance(pair, TokenPair)
    assert pair.access_token == fake_jwt
    assert client.access_token == fake_jwt


async def test_login_bad_credentials(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.post("/auth/login").mock(
        return_value=httpx.Response(
            401,
            json={"error": {"message": "invalid email or password", "type": "auth"}},
        )
    )
    with pytest.raises(KoraiAuthError):
        await client.auth.login("alice@example.com", "wrong")


async def test_register_calls_signup(
    client: KoraiClient, respx_mock: respx.Router, fake_jwt: str
) -> None:
    route = respx_mock.post("/auth/signup").mock(
        return_value=httpx.Response(
            201,
            json={
                "user": {"id": "u-2", "email": "bob@example.com"},
                "token": fake_jwt,
            },
        )
    )
    pair = await client.auth.register(
        email="bob@example.com",
        password="hunter2hunter2",
        full_name="Bob",
        organization_name="Acme SA",
    )
    assert pair.access_token == fake_jwt
    body = route.calls[0].request.read().decode()
    assert "bob@example.com" in body
    assert "display_name" in body


async def test_register_passes_organization_country(
    client: KoraiClient, respx_mock: respx.Router, fake_jwt: str
) -> None:
    route = respx_mock.post("/auth/signup").mock(
        return_value=httpx.Response(
            201,
            json={"user": {"id": "u-3", "email": "carol@x"}, "token": fake_jwt},
        )
    )
    await client.auth.register(
        email="carol@x", password="abcdefgh", full_name="Carol"
    )
    assert route.called


async def test_me_reads_user_from_orchestrator(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/auth/me").mock(
        return_value=httpx.Response(
            200,
            json={
                "user": {
                    "id": "u-1",
                    "email": "alice@example.com",
                    "display_name": "Alice",
                    "role": "admin",
                }
            },
        )
    )
    me = await client.auth.me()
    assert isinstance(me, CurrentUser)
    assert me.id == "u-1"
    assert me.full_name == "Alice"
    assert me.role == "admin"


async def test_me_falls_back_to_jwt_when_endpoint_missing(
    client: KoraiClient, respx_mock: respx.Router, fake_jwt: str
) -> None:
    client.set_tokens(fake_jwt)
    respx_mock.get("/auth/me").mock(return_value=httpx.Response(404))
    me = await client.auth.me()
    assert me.id == "user-123"
    assert me.email == "alice@example.com"
    assert me.organization_id == "org-42"


async def test_me_raises_when_no_token() -> None:
    c = KoraiClient(base_url=TEST_BASE_URL)
    try:
        with pytest.raises(KoraiAuthError):
            c.auth._me_from_token()
    finally:
        await c.aclose()


async def test_logout_clears_local_tokens_even_on_404(
    client: KoraiClient, respx_mock: respx.Router, fake_jwt: str
) -> None:
    client.set_tokens(fake_jwt, "refresh")
    respx_mock.post("/auth/logout").mock(return_value=httpx.Response(404))
    await client.auth.logout()
    assert client.access_token is None
    assert client.refresh_token is None


async def test_logout_succeeds_when_endpoint_returns_200(
    client: KoraiClient, respx_mock: respx.Router, fake_jwt: str
) -> None:
    client.set_tokens(fake_jwt)
    respx_mock.post("/auth/logout").mock(return_value=httpx.Response(200, json={}))
    await client.auth.logout()
    assert client.access_token is None


async def test_refresh_returns_existing_when_endpoint_missing(
    client: KoraiClient, respx_mock: respx.Router, fake_jwt: str
) -> None:
    client.set_tokens(fake_jwt)
    respx_mock.post("/auth/refresh").mock(return_value=httpx.Response(404))
    pair = await client.auth.refresh("some-refresh")
    # Refresh endpoint missing → original token preserved.
    assert pair.access_token == fake_jwt


async def test_refresh_when_endpoint_exists(
    client: KoraiClient, respx_mock: respx.Router, fake_jwt: str
) -> None:
    respx_mock.post("/auth/refresh").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "new-access",
                "refresh_token": "new-refresh",
                "expires_in": 3600,
            },
        )
    )
    pair = await client.auth.refresh("old-refresh")
    assert pair.access_token == "new-access"
    assert pair.refresh_token == "new-refresh"
    assert pair.expires_in == 3600


async def test_create_api_key(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.post("/auth/keys").mock(
        return_value=httpx.Response(
            201,
            json={
                "key": "sk-korai-newrawvalue",
                "details": {
                    "id": "key-1",
                    "label": "ci",
                    "prefix": "sk-korai-newr",
                    "created_at": "2026-01-01T00:00:00Z",
                },
                "warning": "Save this key — it will not be shown again.",
            },
        )
    )
    key = await client.auth.create_api_key(label="ci")
    assert isinstance(key, APIKey)
    assert key.id == "key-1"
    assert key.key == "sk-korai-newrawvalue"
    assert key.prefix == "sk-korai-newr"


async def test_list_api_keys(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/auth/keys").mock(
        return_value=httpx.Response(
            200,
            json={
                "keys": [
                    {"id": "k1", "label": "prod", "prefix": "sk-korai-aaaa"},
                    {"id": "k2", "label": "dev", "prefix": "sk-korai-bbbb"},
                ]
            },
        )
    )
    keys = await client.auth.list_api_keys()
    assert len(keys) == 2
    assert keys[0].id == "k1"
    assert keys[1].label == "dev"
    # Raw key is never returned on list.
    assert keys[0].key is None


async def test_delete_api_key(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    route = respx_mock.delete("/auth/keys/k1").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    await client.auth.delete_api_key("k1")
    assert route.called


async def test_decode_jwt_unverified(fake_jwt: str) -> None:
    claims = decode_jwt_unverified(fake_jwt)
    assert claims["sub"] == "user-123"
    assert claims["cab"] == "org-42"


async def test_decode_jwt_unverified_rejects_garbage() -> None:
    with pytest.raises(ValueError):
        decode_jwt_unverified("not-a-jwt")
