"""Fleet module — the model catalog Korai Cloud can serve.

Where :meth:`korai.llm.LLMModule.list_models` reports the models a
*connected worker* currently advertises (live availability), the fleet
manifest is the **catalog**: every model the network is configured to
run, with its variants, VRAM tiers, and backends — independent of who is
connected right now.

Backed by the public ``GET /v1/fleet/manifest`` and ``GET
/v1/fleet/stats`` endpoints (no auth required).

Example::

    manifest = await client.fleet.get_manifest()
    for model_id, model in manifest.models.items():
        print(model_id, model.family, list(model.variants))
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from korai._generated.api.fleet import get_fleet_manifest, get_fleet_stats

if TYPE_CHECKING:
    from korai._client import KoraiClient


class FleetVariant(BaseModel):
    """One downloadable variant of a model (quant/backend combo)."""

    hf_repo: str | None = None
    hf_filename: str | None = None
    size_gb: int | None = None
    min_vram_gb: int | None = None
    backend: str | None = None


class FleetModel(BaseModel):
    """A model in the catalog, with its variants and roles."""

    creator: str | None = None
    license: str | None = None
    family: str | None = None
    total_params: str | None = None
    active_params: str | None = None
    context_len: int | None = None
    multimodal: bool | None = None
    roles: list[str] = Field(default_factory=list)
    variants: dict[str, FleetVariant] = Field(default_factory=dict)


class FleetManifest(BaseModel):
    """The full fleet manifest."""

    schema_version: int = 0
    version: int = 0
    published_at: str | None = None
    models: dict[str, FleetModel] = Field(default_factory=dict)
    tiers: dict[str, Any] = Field(default_factory=dict)
    api_tiers: dict[str, Any] = Field(default_factory=dict)
    deprecated: list[str] = Field(default_factory=list)


class FleetStats(BaseModel):
    """Summary counts derived from the manifest."""

    schema_version: int = 0
    version: int = 0
    published_at: str | None = None
    models: int = 0
    tiers: int = 0
    api_tiers: int = 0
    deprecated: int = 0


class FleetModule:
    """Read the model catalog (manifest + summary stats)."""

    def __init__(self, client: KoraiClient) -> None:
        self._client = client

    async def get_manifest(self) -> FleetManifest:
        """Return the full fleet manifest — the catalog of models the
        network can serve, with variants, VRAM tiers, and backends."""
        data = await self._client._call_gen(
            get_fleet_manifest._get_kwargs, path="/v1/fleet/manifest"
        )
        if not isinstance(data, dict):
            return FleetManifest()
        return FleetManifest.model_validate(data)

    async def get_stats(self) -> FleetStats:
        """Return summary counts (number of models, tiers, etc.)."""
        data = await self._client._call_gen(
            get_fleet_stats._get_kwargs, path="/v1/fleet/stats"
        )
        if not isinstance(data, dict):
            return FleetStats()
        return FleetStats.model_validate(data)


__all__ = [
    "FleetManifest",
    "FleetModel",
    "FleetModule",
    "FleetStats",
    "FleetVariant",
]
