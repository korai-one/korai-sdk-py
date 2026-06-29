from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="FleetTier")


@_attrs_define
class FleetTier:
    """
    Attributes:
        description (str | Unset):
        min_vram_gb (int | Unset):
        max_vram_gb (int | Unset):
        models (list[str] | Unset): canonical_id#variant refs.
        load_simultaneous (int | Unset):
    """

    description: str | Unset = UNSET
    min_vram_gb: int | Unset = UNSET
    max_vram_gb: int | Unset = UNSET
    models: list[str] | Unset = UNSET
    load_simultaneous: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        description = self.description

        min_vram_gb = self.min_vram_gb

        max_vram_gb = self.max_vram_gb

        models: list[str] | Unset = UNSET
        if not isinstance(self.models, Unset):
            models = self.models

        load_simultaneous = self.load_simultaneous

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if description is not UNSET:
            field_dict["description"] = description
        if min_vram_gb is not UNSET:
            field_dict["min_vram_gb"] = min_vram_gb
        if max_vram_gb is not UNSET:
            field_dict["max_vram_gb"] = max_vram_gb
        if models is not UNSET:
            field_dict["models"] = models
        if load_simultaneous is not UNSET:
            field_dict["load_simultaneous"] = load_simultaneous

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        description = d.pop("description", UNSET)

        min_vram_gb = d.pop("min_vram_gb", UNSET)

        max_vram_gb = d.pop("max_vram_gb", UNSET)

        models = cast(list[str], d.pop("models", UNSET))

        load_simultaneous = d.pop("load_simultaneous", UNSET)

        fleet_tier = cls(
            description=description,
            min_vram_gb=min_vram_gb,
            max_vram_gb=max_vram_gb,
            models=models,
            load_simultaneous=load_simultaneous,
        )

        fleet_tier.additional_properties = d
        return fleet_tier

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
