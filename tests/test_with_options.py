"""Tests for KoraiClient.with_options (Anthropic-parity per-request overrides)."""

from __future__ import annotations

import httpx
import pytest
import respx

from korai import KoraiAPIError, KoraiClient

TEST_BASE_URL = "https://test.korai.local"


def _transient() -> httpx.Response:
    # Retry-After: 0 keeps the backoff instant.
    return httpx.Response(
        503,
        headers={"Retry-After": "0"},
        json={"error": {"message": "transient", "type": "transient"}},
    )


async def test_with_options_distinct_instance_preserves_base_url() -> None:
    base = KoraiClient(api_key="sk-korai-test", base_url=TEST_BASE_URL, max_retries=2)
    clone = base.with_options(max_retries=0)
    try:
        assert clone is not base
        assert clone.base_url == base.base_url
        assert clone.api_key == base.api_key
        assert clone._max_retries == 0
        assert base._max_retries == 2  # original untouched
    finally:
        await base.aclose()
        await clone.aclose()


async def test_with_options_max_retries_zero_disables_retry(
    respx_mock: respx.Router,
) -> None:
    base = KoraiClient(api_key="sk-korai-test", base_url=TEST_BASE_URL, max_retries=2)
    clone = base.with_options(max_retries=0)
    route = respx_mock.get("/billing/balance").mock(
        side_effect=lambda request: _transient()
    )
    try:
        with pytest.raises(KoraiAPIError):
            await clone.billing.get_balance()
        assert route.call_count == 1  # no retry on the clone
    finally:
        await base.aclose()
        await clone.aclose()


async def test_with_options_timeout_override_inherits_retries() -> None:
    base = KoraiClient(
        api_key="sk-korai-test",
        base_url=TEST_BASE_URL,
        timeout=60.0,
        max_retries=2,
    )
    clone = base.with_options(timeout=1.5)
    try:
        assert clone._timeout == 1.5
        assert clone._max_retries == 2  # inherited
    finally:
        await base.aclose()
        await clone.aclose()


async def test_with_options_copies_tokens() -> None:
    base = KoraiClient(api_key="sk-korai-test", base_url=TEST_BASE_URL)
    base.set_tokens("access-abc", "refresh-xyz")
    clone = base.with_options(timeout=5.0)
    try:
        assert clone.access_token == "access-abc"
        assert clone.refresh_token == "refresh-xyz"
    finally:
        await base.aclose()
        await clone.aclose()
