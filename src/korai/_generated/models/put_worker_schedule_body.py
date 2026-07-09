from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.worker_schedule_type_0 import WorkerScheduleType0


T = TypeVar("T", bound="PutWorkerScheduleBody")


@_attrs_define
class PutWorkerScheduleBody:
    """
    Attributes:
        schedule (None | Unset | WorkerScheduleType0):
    """

    schedule: None | Unset | WorkerScheduleType0 = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.worker_schedule_type_0 import WorkerScheduleType0

        schedule: dict[str, Any] | None | Unset
        if isinstance(self.schedule, Unset):
            schedule = UNSET
        elif isinstance(self.schedule, WorkerScheduleType0):
            schedule = self.schedule.to_dict()
        else:
            schedule = self.schedule

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if schedule is not UNSET:
            field_dict["schedule"] = schedule

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.worker_schedule_type_0 import WorkerScheduleType0

        d = dict(src_dict)

        def _parse_schedule(data: object) -> None | Unset | WorkerScheduleType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_worker_schedule_type_0 = WorkerScheduleType0.from_dict(data)

                return componentsschemas_worker_schedule_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | WorkerScheduleType0, data)

        schedule = _parse_schedule(d.pop("schedule", UNSET))

        put_worker_schedule_body = cls(
            schedule=schedule,
        )

        put_worker_schedule_body.additional_properties = d
        return put_worker_schedule_body

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
