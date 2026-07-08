from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="WorkerScheduleType0")


@_attrs_define
class WorkerScheduleType0:
    """
    Attributes:
        enabled (bool | Unset):
        days (list[int] | Unset):
        start_hour (int | Unset):
        end_hour (int | Unset):
        timezone (str | Unset):
        max_session_minutes (int | Unset):
    """

    enabled: bool | Unset = UNSET
    days: list[int] | Unset = UNSET
    start_hour: int | Unset = UNSET
    end_hour: int | Unset = UNSET
    timezone: str | Unset = UNSET
    max_session_minutes: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        enabled = self.enabled

        days: list[int] | Unset = UNSET
        if not isinstance(self.days, Unset):
            days = self.days

        start_hour = self.start_hour

        end_hour = self.end_hour

        timezone = self.timezone

        max_session_minutes = self.max_session_minutes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if days is not UNSET:
            field_dict["days"] = days
        if start_hour is not UNSET:
            field_dict["start_hour"] = start_hour
        if end_hour is not UNSET:
            field_dict["end_hour"] = end_hour
        if timezone is not UNSET:
            field_dict["timezone"] = timezone
        if max_session_minutes is not UNSET:
            field_dict["max_session_minutes"] = max_session_minutes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        enabled = d.pop("enabled", UNSET)

        days = cast(list[int], d.pop("days", UNSET))

        start_hour = d.pop("start_hour", UNSET)

        end_hour = d.pop("end_hour", UNSET)

        timezone = d.pop("timezone", UNSET)

        max_session_minutes = d.pop("max_session_minutes", UNSET)

        worker_schedule_type_0 = cls(
            enabled=enabled,
            days=days,
            start_hour=start_hour,
            end_hour=end_hour,
            timezone=timezone,
            max_session_minutes=max_session_minutes,
        )

        worker_schedule_type_0.additional_properties = d
        return worker_schedule_type_0

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
