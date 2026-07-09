from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.error_error_type_0 import ErrorErrorType0


T = TypeVar("T", bound="Error")


@_attrs_define
class Error:
    """Canonical error envelope. Most endpoints return `{error:{message,type}}`; a few legacy ones return
    `{error:"<string>"}`. Generators should treat `error` as `object | string`.

        Attributes:
            error (ErrorErrorType0 | str | Unset):
    """

    error: ErrorErrorType0 | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.error_error_type_0 import ErrorErrorType0

        error: dict[str, Any] | str | Unset
        if isinstance(self.error, Unset):
            error = UNSET
        elif isinstance(self.error, ErrorErrorType0):
            error = self.error.to_dict()
        else:
            error = self.error

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if error is not UNSET:
            field_dict["error"] = error

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.error_error_type_0 import ErrorErrorType0

        d = dict(src_dict)

        def _parse_error(data: object) -> ErrorErrorType0 | str | Unset:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                error_type_0 = ErrorErrorType0.from_dict(data)

                return error_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ErrorErrorType0 | str | Unset, data)

        error = _parse_error(d.pop("error", UNSET))

        error = cls(
            error=error,
        )

        error.additional_properties = d
        return error

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
