from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.api_key import APIKey


T = TypeVar("T", bound="CreateApiKeyResponse201")


@_attrs_define
class CreateApiKeyResponse201:
    """
    Attributes:
        key (str | Unset): Raw API key — store it now.
        details (APIKey | Unset):
        warning (str | Unset):
    """

    key: str | Unset = UNSET
    details: APIKey | Unset = UNSET
    warning: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        key = self.key

        details: dict[str, Any] | Unset = UNSET
        if not isinstance(self.details, Unset):
            details = self.details.to_dict()

        warning = self.warning

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if key is not UNSET:
            field_dict["key"] = key
        if details is not UNSET:
            field_dict["details"] = details
        if warning is not UNSET:
            field_dict["warning"] = warning

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.api_key import APIKey

        d = dict(src_dict)
        key = d.pop("key", UNSET)

        _details = d.pop("details", UNSET)
        details: APIKey | Unset
        if isinstance(_details, Unset):
            details = UNSET
        else:
            details = APIKey.from_dict(_details)

        warning = d.pop("warning", UNSET)

        create_api_key_response_201 = cls(
            key=key,
            details=details,
            warning=warning,
        )

        create_api_key_response_201.additional_properties = d
        return create_api_key_response_201

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
