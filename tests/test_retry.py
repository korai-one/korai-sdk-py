"""Tests for automatic retries + backoff."""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
import pytest_asyncio
import respx

from korai import KoraiAPIError, KoraiClient

TEST_BASE_URL = "https://test.korai.local"


@pytest_asyncio.fixture
async def retry_client() -> AsyncIterator[KoraiClient]:
    c = KoraiClient(api_key="sk-korai-test", base_url=TEST_BASE_URL, max_retries=2)
    try:
        yield c
    finally:
        await c.aclose()


def _transient() -> httpx.Response:
    # Retry-After: 0 keeps the backoff instant.
    return httpx.Response(
        503,
        headers={"Retry-After": "0"},
        json={"error": {"message": "transient", "type": "transient"}},
    )


async def test_retries_then_succeeds(
    retry_client: KoraiClient, respx_mock: respx.Router
) -> None:
    route = respx_mock.get("/billing/balance").mock(
        side_effect=[_transient(), httpx.Response(200, json={"balance_eur": 1.5})]
    )
    balance = await retry_client.billing.get_balance()
    assert balance.balance_eur == 1.5
    assert route.call_count == 2  # one failure + one success


async def test_retries_exhausted(
    retry_client: KoraiClient, respx_mock: respx.Router
) -> None:
    route = respx_mock.get("/billing/balance").mock(side_effect=lambda request: _transient())
    with pytest.raises(KoraiAPIError) as excinfo:
        await retry_client.billing.get_balance()
    assert excinfo.value.status_code == 503
    assert route.call_count == 3  # initial + 2 retries


async def test_no_retry_on_non_retryable(
    retry_client: KoraiClient, respx_mock: respx.Router
) -> None:
    route = respx_mock.get("/billing/balance").mock(
        return_value=httpx.Response(400, json={"error": {"message": "bad"}})
    )
    with pytest.raises(KoraiAPIError):
        await retry_client.billing.get_balance()
    assert route.call_count == 1  # no retry on 400


async def test_max_retries_zero_disables(respx_mock: respx.Router) -> None:
    client = KoraiClient(api_key="sk-korai-test", base_url=TEST_BASE_URL, max_retries=0)
    route = respx_mock.get("/billing/balance").mock(side_effect=lambda request: _transient())
    with pytest.raises(KoraiAPIError):
        await client.billing.get_balance()
    assert route.call_count == 1
    await client.aclose()
