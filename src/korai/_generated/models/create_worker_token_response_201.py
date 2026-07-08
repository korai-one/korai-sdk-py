from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.worker_token import WorkerToken


T = TypeVar("T", bound="CreateWorkerTokenResponse201")


@_attrs_define
class CreateWorkerTokenResponse201:
    """
    Attributes:
        token (str | Unset): Raw worker token — store it now.
        details (WorkerToken | Unset):
        warning (str | Unset):
    """

    token: str | Unset = UNSET
    details: WorkerToken | Unset = UNSET
    warning: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        token = self.token

        details: dict[str, Any] | Unset = UNSET
        if not isinstance(self.details, Unset):
            details = self.details.to_dict()

        warning = self.warning

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if token is not UNSET:
            field_dict["token"] = token
        if details is not UNSET:
            field_dict["details"] = details
        if warning is not UNSET:
            field_dict["warning"] = warning

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.worker_token import WorkerToken

        d = dict(src_dict)
        token = d.pop("token", UNSET)

        _details = d.pop("details", UNSET)
        details: WorkerToken | Unset
        if isinstance(_details, Unset):
            details = UNSET
        else:
            details = WorkerToken.from_dict(_details)

        warning = d.pop("warning", UNSET)

        create_worker_token_response_201 = cls(
            token=token,
            details=details,
            warning=warning,
        )

        create_worker_token_response_201.additional_properties = d
        return create_worker_token_response_201

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
