from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreditPackage")


@_attrs_define
class CreditPackage:
    """
    Attributes:
        id (str | Unset):
        label (str | Unset):
        credits_eur (float | Unset):
        price_cents (int | Unset):
    """

    id: str | Unset = UNSET
    label: str | Unset = UNSET
    credits_eur: float | Unset = UNSET
    price_cents: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        label = self.label

        credits_eur = self.credits_eur

        price_cents = self.price_cents

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if label is not UNSET:
            field_dict["label"] = label
        if credits_eur is not UNSET:
            field_dict["credits_eur"] = credits_eur
        if price_cents is not UNSET:
            field_dict["price_cents"] = price_cents

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        label = d.pop("label", UNSET)

        credits_eur = d.pop("credits_eur", UNSET)

        price_cents = d.pop("price_cents", UNSET)

        credit_package = cls(
            id=id,
            label=label,
            credits_eur=credits_eur,
            price_cents=price_cents,
        )

        credit_package.additional_properties = d
        return credit_package

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
