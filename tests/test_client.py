"""Tests for korai._client.KoraiClient HTTP plumbing."""

from __future__ import annotations

import httpx
import pytest
import respx

from korai import (
    KoraiAPIError,
    KoraiAuthError,
    KoraiClient,
    KoraiNotFoundError,
    KoraiRateLimitError,
)
from korai._version import __version__

from .conftest import TEST_BASE_URL


async def test_default_headers_with_api_key(client: KoraiClient) -> None:
    h = client._default_headers()
    assert h["Authorization"] == "Bearer sk-korai-test"
    assert h["User-Agent"] == f"korai-sdk-py/{__version__}"
    assert h["Accept"] == "application/json"


async def test_default_headers_no_credentials() -> None:
    c = KoraiClient(base_url=TEST_BASE_URL)
    try:
        h = c._default_headers()
        assert "Authorization" not in h
        assert h["User-Agent"].startswith("korai-sdk-py/")
    finally:
        await c.aclose()


async def test_set_and_clear_tokens(client: KoraiClient) -> None:
    client.set_tokens("access-1", "refresh-1")
    assert client.access_token == "access-1"
    assert client.refresh_token == "refresh-1"
    h = client._default_headers()
    assert h["Authorization"] == "Bearer access-1"  # token wins over api_key

    client.clear_tokens()
    assert client.access_token is None
    assert client.refresh_token is None


async def test_organization_header(client: KoraiClient) -> None:
    client.organization_id = "org-foo"
    assert client._default_headers()["X-Korai-Organization"] == "org-foo"


async def test_request_returns_json_body(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/foo").mock(return_value=httpx.Response(200, json={"ok": True}))
    data = await client._request("GET", "/foo")
    assert data == {"ok": True}


async def test_request_raises_400(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/bar").mock(
        return_value=httpx.Response(
            400, json={"error": {"message": "bad", "type": "invalid_request"}}
        )
    )
    with pytest.raises(KoraiAPIError) as exc:
        await client._request("GET", "/bar")
    assert exc.value.status_code == 400
    assert exc.value.message == "bad"
    assert exc.value.error_type == "invalid_request"


async def test_request_raises_401_as_auth(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/secret").mock(
        return_value=httpx.Response(401, json={"error": "denied"})
    )
    with pytest.raises(KoraiAuthError):
        await client._request("GET", "/secret")


async def test_request_raises_404(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/missing").mock(return_value=httpx.Response(404))
    with pytest.raises(KoraiNotFoundError):
        await client._request("GET", "/missing")


async def test_rate_limit_retry_after(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/slow").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "12"})
    )
    with pytest.raises(KoraiRateLimitError) as exc:
        await client._request("GET", "/slow")
    assert exc.value.retry_after == 12.0


async def test_request_empty_body(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.delete("/foo/1").mock(return_value=httpx.Response(204))
    out = await client._request("DELETE", "/foo/1")
    assert out == {}


async def test_request_network_error_wrapped(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/oops").mock(side_effect=httpx.ConnectError("boom"))
    with pytest.raises(KoraiAPIError) as exc:
        await client._request("GET", "/oops")
    assert exc.value.status_code == 0


async def test_async_context_manager() -> None:
    async with KoraiClient(api_key="sk-korai-test", base_url=TEST_BASE_URL) as c:
        assert isinstance(c, KoraiClient)


async def test_modules_lazy_loading(client: KoraiClient) -> None:
    # Each accessor should return a real module instance and cache it.
    a1 = client.auth
    a2 = client.auth
    assert a1 is a2
    assert client.llm.__class__.__name__ == "LLMModule"
    assert client.audit.__class__.__name__ == "AuditModule"
    assert client.tools.__class__.__name__ == "ToolsModule"
    assert client.tenant.__class__.__name__ == "TenantModule"
    assert client.billing.__class__.__name__ == "BillingModule"
    assert client.rag.__class__.__name__ == "RAGModule"
