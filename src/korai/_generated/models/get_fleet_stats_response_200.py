from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetFleetStatsResponse200")


@_attrs_define
class GetFleetStatsResponse200:
    """
    Attributes:
        schema_version (int | Unset):
        version (int | Unset):
        published_at (datetime.datetime | Unset):
        models (int | Unset):
        tiers (int | Unset):
        api_tiers (int | Unset):
        deprecated (int | Unset):
    """

    schema_version: int | Unset = UNSET
    version: int | Unset = UNSET
    published_at: datetime.datetime | Unset = UNSET
    models: int | Unset = UNSET
    tiers: int | Unset = UNSET
    api_tiers: int | Unset = UNSET
    deprecated: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        schema_version = self.schema_version

        version = self.version

        published_at: str | Unset = UNSET
        if not isinstance(self.published_at, Unset):
            published_at = self.published_at.isoformat()

        models = self.models

        tiers = self.tiers

        api_tiers = self.api_tiers

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
        d = dict(src_dict)
        schema_version = d.pop("schema_version", UNSET)

        version = d.pop("version", UNSET)

        _published_at = d.pop("published_at", UNSET)
        published_at: datetime.datetime | Unset
        if isinstance(_published_at, Unset):
            published_at = UNSET
        else:
            published_at = datetime.datetime.fromisoformat(_published_at)

        models = d.pop("models", UNSET)

        tiers = d.pop("tiers", UNSET)

        api_tiers = d.pop("api_tiers", UNSET)

        deprecated = d.pop("deprecated", UNSET)

        get_fleet_stats_response_200 = cls(
            schema_version=schema_version,
            version=version,
            published_at=published_at,
            models=models,
            tiers=tiers,
            api_tiers=api_tiers,
            deprecated=deprecated,
        )

        get_fleet_stats_response_200.additional_properties = d
        return get_fleet_stats_response_200

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
