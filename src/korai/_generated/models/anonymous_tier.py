from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.tier_name import TierName
from ..types import UNSET, Unset

T = TypeVar("T", bound="AnonymousTier")


@_attrs_define
class AnonymousTier:
    """
    Attributes:
        name (TierName | Unset):
        monthly_price_eur (float | Unset):
        tokens_per_tranche (int | Unset):
        tranche_hours (int | Unset):
        requests_per_minute (int | Unset):
    """

    name: TierName | Unset = UNSET
    monthly_price_eur: float | Unset = UNSET
    tokens_per_tranche: int | Unset = UNSET
    tranche_hours: int | Unset = UNSET
    requests_per_minute: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name: str | Unset = UNSET
        if not isinstance(self.name, Unset):
            name = self.name.value

        monthly_price_eur = self.monthly_price_eur

        tokens_per_tranche = self.tokens_per_tranche

        tranche_hours = self.tranche_hours

        requests_per_minute = self.requests_per_minute

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if monthly_price_eur is not UNSET:
            field_dict["monthly_price_eur"] = monthly_price_eur
        if tokens_per_tranche is not UNSET:
            field_dict["tokens_per_tranche"] = tokens_per_tranche
        if tranche_hours is not UNSET:
            field_dict["tranche_hours"] = tranche_hours
        if requests_per_minute is not UNSET:
            field_dict["requests_per_minute"] = requests_per_minute

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _name = d.pop("name", UNSET)
        name: TierName | Unset
        if isinstance(_name, Unset):
            name = UNSET
        else:
            name = TierName(_name)

        monthly_price_eur = d.pop("monthly_price_eur", UNSET)

        tokens_per_tranche = d.pop("tokens_per_tranche", UNSET)

        tranche_hours = d.pop("tranche_hours", UNSET)

        requests_per_minute = d.pop("requests_per_minute", UNSET)

        anonymous_tier = cls(
            name=name,
            monthly_price_eur=monthly_price_eur,
            tokens_per_tranche=tokens_per_tranche,
            tranche_hours=tranche_hours,
            requests_per_minute=requests_per_minute,
        )

        anonymous_tier.additional_properties = d
        return anonymous_tier

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
