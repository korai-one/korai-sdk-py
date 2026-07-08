"""Shared pytest fixtures for the Korai SDK test suite.

We intentionally bind every test to a deterministic ``base_url``
(``https://test.korai.local``) so respx mocks are easy to read.
"""

from __future__ import annotations

import base64
import hmac
import json
from collections.abc import AsyncIterator
from typing import Any

import pytest
import pytest_asyncio
import respx

from korai import KoraiClient

TEST_BASE_URL = "https://test.korai.local"


def _make_jwt(claims: dict[str, Any]) -> str:
    """Build an HS256 JWT with a known secret (for unverified-decode tests)."""
    header = {"alg": "HS256", "typ": "JWT"}

    def _b64(d: bytes) -> str:
        return base64.urlsafe_b64encode(d).rstrip(b"=").decode("ascii")

    header_b64 = _b64(json.dumps(header, separators=(",", ":")).encode())
    claims_b64 = _b64(json.dumps(claims, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{claims_b64}".encode()
    sig = hmac.new(b"test-secret", signing_input, "sha256").digest()
    sig_b64 = _b64(sig)
    return f"{header_b64}.{claims_b64}.{sig_b64}"


@pytest.fixture
def fake_jwt() -> str:
    """A JWT with predictable claims used across tenant/auth tests."""
    return _make_jwt(
        {
            "sub": "user-123",
            "email": "alice@example.com",
            "role": "admin",
            "cab": "org-42",
            "iat": 1_700_000_000,
            "exp": 9_999_999_999,
        }
    )


@pytest_asyncio.fixture
async def client() -> AsyncIterator[KoraiClient]:
    """A fresh KoraiClient pointed at the test base_url.

    Retries are disabled here so unit tests assert pure error-mapping /
    transport behavior; retry/backoff has its own test module.
    """
    c = KoraiClient(api_key="sk-korai-test", base_url=TEST_BASE_URL, max_retries=0)
    try:
        yield c
    finally:
        await c.aclose()


@pytest_asyncio.fixture
async def signed_client() -> AsyncIterator[KoraiClient]:
    """A KoraiClient configured with an audit_secret + in-memory storage."""
    c = KoraiClient(
        api_key="sk-korai-test",
        base_url=TEST_BASE_URL,
        audit_secret=b"shared-hmac-secret",
        organization_id="org-42",
    )
    try:
        yield c
    finally:
        await c.aclose()


@pytest.fixture
def respx_mock() -> respx.Router:
    """Yield a respx router scoped to a test."""
    with respx.mock(base_url=TEST_BASE_URL, assert_all_called=False) as router:
        yield router


__all__ = ["TEST_BASE_URL", "client", "fake_jwt", "respx_mock", "signed_client"]
