from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="IssueAnonymousFreeBatchBody")


@_attrs_define
class IssueAnonymousFreeBatchBody:
    """
    Attributes:
        session_token (str): Random ≥32-char (hex) browser session id.
        count (int | Unset): Requested token count; capped at tier quota. Default: 10.
    """

    session_token: str
    count: int | Unset = 10
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        session_token = self.session_token

        count = self.count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "session_token": session_token,
            }
        )
        if count is not UNSET:
            field_dict["count"] = count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        session_token = d.pop("session_token")

        count = d.pop("count", UNSET)

        issue_anonymous_free_batch_body = cls(
            session_token=session_token,
            count=count,
        )

        issue_anonymous_free_batch_body.additional_properties = d
        return issue_anonymous_free_batch_body

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
