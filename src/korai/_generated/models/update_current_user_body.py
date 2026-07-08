from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateCurrentUserBody")


@_attrs_define
class UpdateCurrentUserBody:
    """All fields optional. current_password and new_password must be supplied together. display_name is trimmed and
    clamped to 80 chars.

        Attributes:
            display_name (None | str | Unset):
            current_password (None | str | Unset):
            new_password (None | str | Unset):
    """

    display_name: None | str | Unset = UNSET
    current_password: None | str | Unset = UNSET
    new_password: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        display_name: None | str | Unset
        if isinstance(self.display_name, Unset):
            display_name = UNSET
        else:
            display_name = self.display_name

        current_password: None | str | Unset
        if isinstance(self.current_password, Unset):
            current_password = UNSET
        else:
            current_password = self.current_password

        new_password: None | str | Unset
        if isinstance(self.new_password, Unset):
            new_password = UNSET
        else:
            new_password = self.new_password

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if display_name is not UNSET:
            field_dict["display_name"] = display_name
        if current_password is not UNSET:
            field_dict["current_password"] = current_password
        if new_password is not UNSET:
            field_dict["new_password"] = new_password

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_display_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        display_name = _parse_display_name(d.pop("display_name", UNSET))

        def _parse_current_password(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        current_password = _parse_current_password(d.pop("current_password", UNSET))

        def _parse_new_password(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        new_password = _parse_new_password(d.pop("new_password", UNSET))

        update_current_user_body = cls(
            display_name=display_name,
            current_password=current_password,
            new_password=new_password,
        )

        update_current_user_body.additional_properties = d
        return update_current_user_body

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
