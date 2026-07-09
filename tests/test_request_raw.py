"""Tests for the public raw-response escape hatch (KoraiClient.request_raw)."""

from __future__ import annotations

import httpx
import respx

from korai import KoraiClient


async def test_request_raw_returns_response_with_headers(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/v1/whoami").mock(
        return_value=httpx.Response(
            200,
            json={"ok": True},
            headers={"X-Custom-Header": "korai-value"},
        )
    )

    resp = await client.request_raw("GET", "/v1/whoami")

    assert resp.status_code == 200
    assert resp.headers["X-Custom-Header"] == "korai-value"
    assert resp.json() == {"ok": True}


async def test_request_raw_does_not_raise_on_5xx(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.post("/v1/flaky").mock(
        return_value=httpx.Response(503, json={"error": "unavailable"})
    )

    # Must return the Response rather than raising KoraiServerError.
    resp = await client.request_raw("POST", "/v1/flaky", json_body={"x": 1})

    assert resp.status_code == 503
    assert resp.json() == {"error": "unavailable"}
