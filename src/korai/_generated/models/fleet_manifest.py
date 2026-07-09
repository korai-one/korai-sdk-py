from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.fleet_manifest_api_tiers import FleetManifestApiTiers
    from ..models.fleet_manifest_models import FleetManifestModels
    from ..models.fleet_manifest_tiers import FleetManifestTiers


T = TypeVar("T", bound="FleetManifest")


@_attrs_define
class FleetManifest:
    """
    Attributes:
        schema_version (int | Unset):
        version (int | Unset):
        published_at (datetime.datetime | Unset):
        models (FleetManifestModels | Unset):
        tiers (FleetManifestTiers | Unset):
        api_tiers (FleetManifestApiTiers | Unset):
        deprecated (list[str] | Unset):
    """

    schema_version: int | Unset = UNSET
    version: int | Unset = UNSET
    published_at: datetime.datetime | Unset = UNSET
    models: FleetManifestModels | Unset = UNSET
    tiers: FleetManifestTiers | Unset = UNSET
    api_tiers: FleetManifestApiTiers | Unset = UNSET
    deprecated: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        schema_version = self.schema_version

        version = self.version

        published_at: str | Unset = UNSET
        if not isinstance(self.published_at, Unset):
            published_at = self.published_at.isoformat()

        models: dict[str, Any] | Unset = UNSET
        if not isinstance(self.models, Unset):
            models = self.models.to_dict()

        tiers: dict[str, Any] | Unset = UNSET
        if not isinstance(self.tiers, Unset):
            tiers = self.tiers.to_dict()

        api_tiers: dict[str, Any] | Unset = UNSET
        if not isinstance(self.api_tiers, Unset):
            api_tiers = self.api_tiers.to_dict()

        deprecated: list[str] | Unset = UNSET
        if not isinstance(self.deprecated, Unset):
            deprecated = self.deprecated

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if schema_version is not UNSET:
            field_dict["schema_version"] = schema_version
        if version is not UNSET:
            field_dict["version"] = version
        if published_at is not UNSET:
            field_dict["published_at"] = published_at
        if models is not UNSET:
            field_dict["models"] = models
        if tiers is not UNSET:
            field_dict["tiers"] = tiers
        if api_tiers is not UNSET:
            field_dict["api_tiers"] = api_tiers
        if deprecated is not UNSET:
            field_dict["deprecated"] = deprecated

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.fleet_manifest_api_tiers import FleetManifestApiTiers
        from ..models.fleet_manifest_models import FleetManifestModels
        from ..models.fleet_manifest_tiers import FleetManifestTiers

        d = dict(src_dict)
        schema_version = d.pop("schema_version", UNSET)

        version = d.pop("version", UNSET)

        _published_at = d.pop("published_at", UNSET)
        published_at: datetime.datetime | Unset
        if isinstance(_published_at, Unset):
            published_at = UNSET
        else:
            published_at = datetime.datetime.fromisoformat(_published_at)

        _models = d.pop("models", UNSET)
        models: FleetManifestModels | Unset
        if isinstance(_models, Unset):
            models = UNSET
        else:
            models = FleetManifestModels.from_dict(_models)

        _tiers = d.pop("tiers", UNSET)
        tiers: FleetManifestTiers | Unset
        if isinstance(_tiers, Unset):
            tiers = UNSET
        else:
            tiers = FleetManifestTiers.from_dict(_tiers)

        _api_tiers = d.pop("api_tiers", UNSET)
        api_tiers: FleetManifestApiTiers | Unset
        if isinstance(_api_tiers, Unset):
            api_tiers = UNSET
        else:
            api_tiers = FleetManifestApiTiers.from_dict(_api_tiers)

        deprecated = cast(list[str], d.pop("deprecated", UNSET))

        fleet_manifest = cls(
            schema_version=schema_version,
            version=version,
            published_at=published_at,
            models=models,
            tiers=tiers,
            api_tiers=api_tiers,
            deprecated=deprecated,
        )

        fleet_manifest.additional_properties = d
        return fleet_manifest

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
