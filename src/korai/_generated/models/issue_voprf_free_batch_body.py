from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="IssueVoprfFreeBatchBody")


@_attrs_define
class IssueVoprfFreeBatchBody:
    """
    Attributes:
        session_token (str):
        blinded (list[str]):
    """

    session_token: str
    blinded: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        session_token = self.session_token

        blinded = self.blinded

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "session_token": session_token,
                "blinded": blinded,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        session_token = d.pop("session_token")

        blinded = cast(list[str], d.pop("blinded"))

        issue_voprf_free_batch_body = cls(
            session_token=session_token,
            blinded=blinded,
        )

        issue_voprf_free_batch_body.additional_properties = d
        return issue_voprf_free_batch_body

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
