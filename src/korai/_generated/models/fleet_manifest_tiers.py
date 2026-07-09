from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.fleet_tier import FleetTier


T = TypeVar("T", bound="FleetManifestTiers")


@_attrs_define
class FleetManifestTiers:
    """ """

    additional_properties: dict[str, FleetTier] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            field_dict[prop_name] = prop.to_dict()

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.fleet_tier import FleetTier

        d = dict(src_dict)
        fleet_manifest_tiers = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():
            additional_property = FleetTier.from_dict(prop_dict)

            additional_properties[prop_name] = additional_property

        fleet_manifest_tiers.additional_properties = additional_properties
        return fleet_manifest_tiers

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> FleetTier:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: FleetTier) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
