from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.anonymous_tier import AnonymousTier


T = TypeVar("T", bound="ListAnonymousTiersResponse200")


@_attrs_define
class ListAnonymousTiersResponse200:
    """
    Attributes:
        tiers (list[AnonymousTier] | Unset):
    """

    tiers: list[AnonymousTier] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        tiers: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.tiers, Unset):
            tiers = []
            for tiers_item_data in self.tiers:
                tiers_item = tiers_item_data.to_dict()
                tiers.append(tiers_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if tiers is not UNSET:
            field_dict["tiers"] = tiers

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.anonymous_tier import AnonymousTier

        d = dict(src_dict)
        _tiers = d.pop("tiers", UNSET)
        tiers: list[AnonymousTier] | Unset = UNSET
        if _tiers is not UNSET:
            tiers = []
            for tiers_item_data in _tiers:
                tiers_item = AnonymousTier.from_dict(tiers_item_data)

                tiers.append(tiers_item)

        list_anonymous_tiers_response_200 = cls(
            tiers=tiers,
        )

        list_anonymous_tiers_response_200.additional_properties = d
        return list_anonymous_tiers_response_200

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
