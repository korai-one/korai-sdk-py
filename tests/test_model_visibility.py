"""Tests for live model listing (detailed) + the fleet catalog."""

from __future__ import annotations

import httpx
import respx

from korai import KoraiClient
from korai.fleet import FleetManifest, FleetStats
from korai.llm import MODES, ModelInfo

MODELS_RESPONSE = {
    "object": "list",
    "data": [
        {"id": "auto", "object": "model", "kind": "alias", "description": "Auto"},
        {
            "id": "gemma-4-31b-thinking-4bit",
            "object": "model",
            "kind": "canonical",
            "family": "gemma",
            "variant": "thinking",
            "quant": "4bit",
            "role": "deep",
            "context_len": 32768,
            "supports_tools": True,
        },
    ],
}

MANIFEST_RESPONSE = {
    "schema_version": 1,
    "version": 7,
    "published_at": "2026-06-19T00:00:00Z",
    "models": {
        "gemma-4-31b-thinking": {
            "creator": "Google",
            "family": "gemma",
            "context_len": 32768,
            "roles": ["deep"],
            "variants": {
                "4bit": {"hf_repo": "org/repo", "size_gb": 18, "min_vram_gb": 24, "backend": "mlx"}
            },
        }
    },
    "tiers": {"apple-32": {"description": "M-series 32GB"}},
    "api_tiers": {},
    "deprecated": ["old-model"],
}


async def test_list_models_detailed(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/v1/models").mock(return_value=httpx.Response(200, json=MODELS_RESPONSE))
    models = await client.llm.list_models_detailed()
    assert all(isinstance(m, ModelInfo) for m in models)
    canonical = [m for m in models if m.kind == "canonical"]
    assert len(canonical) == 1
    m = canonical[0]
    assert m.id == "gemma-4-31b-thinking-4bit"
    assert m.family == "gemma"
    assert m.context_len == 32768
    assert m.supports_tools is True


async def test_list_modes(client: KoraiClient, respx_mock: respx.Router) -> None:
    respx_mock.get("/v1/models").mock(return_value=httpx.Response(200, json=MODELS_RESPONSE))
    modes = await client.llm.list_modes()
    assert [m.id for m in modes] == ["auto"]  # only the kind=="alias" entry
    assert modes[0].description == "Auto"
    assert MODES == ["auto", "fast", "balanced", "deep"]


async def test_fleet_get_manifest(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/v1/fleet/manifest").mock(
        return_value=httpx.Response(200, json=MANIFEST_RESPONSE)
    )
    manifest = await client.fleet.get_manifest()
    assert isinstance(manifest, FleetManifest)
    assert manifest.version == 7
    assert "gemma-4-31b-thinking" in manifest.models
    model = manifest.models["gemma-4-31b-thinking"]
    assert model.creator == "Google"
    assert "4bit" in model.variants
    assert model.variants["4bit"].backend == "mlx"
    assert manifest.deprecated == ["old-model"]


async def test_fleet_get_stats(client: KoraiClient, respx_mock: respx.Router) -> None:
    respx_mock.get("/v1/fleet/stats").mock(
        return_value=httpx.Response(
            200,
            json={"schema_version": 1, "version": 7, "models": 3, "tiers": 4, "api_tiers": 2, "deprecated": 1},
        )
    )
    stats = await client.fleet.get_stats()
    assert isinstance(stats, FleetStats)
    assert stats.models == 3
    assert stats.tiers == 4
