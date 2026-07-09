from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PeekAnonymousTrancheResponse200")


@_attrs_define
class PeekAnonymousTrancheResponse200:
    """
    Attributes:
        issued (bool | Unset):
        next_reset_at (datetime.datetime | Unset):
    """

    issued: bool | Unset = UNSET
    next_reset_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        issued = self.issued

        next_reset_at: str | Unset = UNSET
        if not isinstance(self.next_reset_at, Unset):
            next_reset_at = self.next_reset_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if issued is not UNSET:
            field_dict["issued"] = issued
        if next_reset_at is not UNSET:
            field_dict["next_reset_at"] = next_reset_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        issued = d.pop("issued", UNSET)

        _next_reset_at = d.pop("next_reset_at", UNSET)
        next_reset_at: datetime.datetime | Unset
        if isinstance(_next_reset_at, Unset):
            next_reset_at = UNSET
        else:
            next_reset_at = datetime.datetime.fromisoformat(_next_reset_at)

        peek_anonymous_tranche_response_200 = cls(
            issued=issued,
            next_reset_at=next_reset_at,
        )

        peek_anonymous_tranche_response_200.additional_properties = d
        return peek_anonymous_tranche_response_200

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
