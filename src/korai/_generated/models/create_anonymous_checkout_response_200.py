from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateAnonymousCheckoutResponse200")


@_attrs_define
class CreateAnonymousCheckoutResponse200:
    """
    Attributes:
        checkout_url (str | Unset):
        dev_stub (bool | Unset):
    """

    checkout_url: str | Unset = UNSET
    dev_stub: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        checkout_url = self.checkout_url

        dev_stub = self.dev_stub

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if checkout_url is not UNSET:
            field_dict["checkout_url"] = checkout_url
        if dev_stub is not UNSET:
            field_dict["dev_stub"] = dev_stub

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        checkout_url = d.pop("checkout_url", UNSET)

        dev_stub = d.pop("dev_stub", UNSET)

        create_anonymous_checkout_response_200 = cls(
            checkout_url=checkout_url,
            dev_stub=dev_stub,
        )

        create_anonymous_checkout_response_200.additional_properties = d
        return create_anonymous_checkout_response_200

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
