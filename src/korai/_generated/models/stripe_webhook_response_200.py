from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="StripeWebhookResponse200")


@_attrs_define
class StripeWebhookResponse200:
    """
    Attributes:
        received (bool | Unset):
        new_balance_eur (float | Unset):
    """

    received: bool | Unset = UNSET
    new_balance_eur: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        received = self.received

        new_balance_eur = self.new_balance_eur

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if received is not UNSET:
            field_dict["received"] = received
        if new_balance_eur is not UNSET:
            field_dict["new_balance_eur"] = new_balance_eur

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        received = d.pop("received", UNSET)

        new_balance_eur = d.pop("new_balance_eur", UNSET)

        stripe_webhook_response_200 = cls(
            received=received,
            new_balance_eur=new_balance_eur,
        )

        stripe_webhook_response_200.additional_properties = d
        return stripe_webhook_response_200

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
