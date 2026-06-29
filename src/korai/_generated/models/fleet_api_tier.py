from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.fleet_api_tier_provider import FleetApiTierProvider
from ..models.fleet_api_tier_required_tier import FleetApiTierRequiredTier
from ..types import UNSET, Unset

T = TypeVar("T", bound="FleetApiTier")


@_attrs_define
class FleetApiTier:
    """
    Attributes:
        provider (FleetApiTierProvider | Unset):
        provider_model (str | Unset):
        base_url (str | Unset):
        roles (list[str] | Unset):
        required_tier (FleetApiTierRequiredTier | Unset):
    """

    provider: FleetApiTierProvider | Unset = UNSET
    provider_model: str | Unset = UNSET
    base_url: str | Unset = UNSET
    roles: list[str] | Unset = UNSET
    required_tier: FleetApiTierRequiredTier | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        provider: str | Unset = UNSET
        if not isinstance(self.provider, Unset):
            provider = self.provider.value

        provider_model = self.provider_model

        base_url = self.base_url

        roles: list[str] | Unset = UNSET
        if not isinstance(self.roles, Unset):
            roles = self.roles

        required_tier: str | Unset = UNSET
        if not isinstance(self.required_tier, Unset):
            required_tier = self.required_tier.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if provider is not UNSET:
            field_dict["provider"] = provider
        if provider_model is not UNSET:
            field_dict["provider_model"] = provider_model
        if base_url is not UNSET:
            field_dict["base_url"] = base_url
        if roles is not UNSET:
            field_dict["roles"] = roles
        if required_tier is not UNSET:
            field_dict["required_tier"] = required_tier

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _provider = d.pop("provider", UNSET)
        provider: FleetApiTierProvider | Unset
        if isinstance(_provider, Unset):
            provider = UNSET
        else:
            provider = FleetApiTierProvider(_provider)

        provider_model = d.pop("provider_model", UNSET)

        base_url = d.pop("base_url", UNSET)

        roles = cast(list[str], d.pop("roles", UNSET))

        _required_tier = d.pop("required_tier", UNSET)
        required_tier: FleetApiTierRequiredTier | Unset
        if isinstance(_required_tier, Unset):
            required_tier = UNSET
        else:
            required_tier = FleetApiTierRequiredTier(_required_tier)

        fleet_api_tier = cls(
            provider=provider,
            provider_model=provider_model,
            base_url=base_url,
            roles=roles,
            required_tier=required_tier,
        )

        fleet_api_tier.additional_properties = d
        return fleet_api_tier

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
