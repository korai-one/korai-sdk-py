"""Tests for environment-variable configuration of :class:`KoraiClient`.

Covers GAP 4: ``KORAI_API_KEY`` / ``KORAI_BASE_URL`` fallbacks, with an
explicit constructor argument always taking precedence.
"""

from __future__ import annotations

import pytest

from korai import KoraiClient


async def test_api_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KORAI_API_KEY", "sk-korai-from-env")
    c = KoraiClient()
    try:
        assert c.api_key == "sk-korai-from-env"
    finally:
        await c.aclose()


async def test_explicit_api_key_overrides_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KORAI_API_KEY", "sk-korai-from-env")
    c = KoraiClient(api_key="sk-korai-explicit")
    try:
        assert c.api_key == "sk-korai-explicit"
    finally:
        await c.aclose()


async def test_api_key_none_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KORAI_API_KEY", raising=False)
    c = KoraiClient()
    try:
        assert c.api_key is None
    finally:
        await c.aclose()


async def test_base_url_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KORAI_BASE_URL", "https://env.korai.local")
    c = KoraiClient()
    try:
        assert c.base_url == "https://env.korai.local"
    finally:
        await c.aclose()


async def test_explicit_base_url_overrides_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KORAI_BASE_URL", "https://env.korai.local")
    c = KoraiClient(base_url="https://explicit.korai.local")
    try:
        assert c.base_url == "https://explicit.korai.local"
    finally:
        await c.aclose()


async def test_base_url_defaults_to_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("KORAI_BASE_URL", raising=False)
    c = KoraiClient()
    try:
        assert c.base_url == "https://cloud.korai.one"
    finally:
        await c.aclose()
