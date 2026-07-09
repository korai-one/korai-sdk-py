from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.worker_schedule_type_0 import WorkerScheduleType0


T = TypeVar("T", bound="HostWorkerStat")


@_attrs_define
class HostWorkerStat:
    """
    Attributes:
        worker_id (str | Unset):
        connected_at (datetime.datetime | Unset):
        accelerator (str | Unset):
        model (str | Unset):
        memory_gb (int | Unset):
        country (str | Unset):
        models (list[str] | Unset):
        uptime_seconds (int | Unset):
        schedule (None | Unset | WorkerScheduleType0):
        on_schedule (bool | Unset):
    """

    worker_id: str | Unset = UNSET
    connected_at: datetime.datetime | Unset = UNSET
    accelerator: str | Unset = UNSET
    model: str | Unset = UNSET
    memory_gb: int | Unset = UNSET
    country: str | Unset = UNSET
    models: list[str] | Unset = UNSET
    uptime_seconds: int | Unset = UNSET
    schedule: None | Unset | WorkerScheduleType0 = UNSET
    on_schedule: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.worker_schedule_type_0 import WorkerScheduleType0

        worker_id = self.worker_id

        connected_at: str | Unset = UNSET
        if not isinstance(self.connected_at, Unset):
            connected_at = self.connected_at.isoformat()

        accelerator = self.accelerator

        model = self.model

        memory_gb = self.memory_gb

        country = self.country

        models: list[str] | Unset = UNSET
        if not isinstance(self.models, Unset):
            models = self.models

        uptime_seconds = self.uptime_seconds

        schedule: dict[str, Any] | None | Unset
        if isinstance(self.schedule, Unset):
            schedule = UNSET
        elif isinstance(self.schedule, WorkerScheduleType0):
            schedule = self.schedule.to_dict()
        else:
            schedule = self.schedule

        on_schedule = self.on_schedule

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if worker_id is not UNSET:
            field_dict["worker_id"] = worker_id
        if connected_at is not UNSET:
            field_dict["connected_at"] = connected_at
        if accelerator is not UNSET:
            field_dict["accelerator"] = accelerator
        if model is not UNSET:
            field_dict["model"] = model
        if memory_gb is not UNSET:
            field_dict["memory_gb"] = memory_gb
        if country is not UNSET:
            field_dict["country"] = country
        if models is not UNSET:
            field_dict["models"] = models
        if uptime_seconds is not UNSET:
            field_dict["uptime_seconds"] = uptime_seconds
        if schedule is not UNSET:
            field_dict["schedule"] = schedule
        if on_schedule is not UNSET:
            field_dict["on_schedule"] = on_schedule

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.worker_schedule_type_0 import WorkerScheduleType0

        d = dict(src_dict)
        worker_id = d.pop("worker_id", UNSET)

        _connected_at = d.pop("connected_at", UNSET)
        connected_at: datetime.datetime | Unset
        if isinstance(_connected_at, Unset):
            connected_at = UNSET
        else:
            connected_at = datetime.datetime.fromisoformat(_connected_at)

        accelerator = d.pop("accelerator", UNSET)

        model = d.pop("model", UNSET)

        memory_gb = d.pop("memory_gb", UNSET)

        country = d.pop("country", UNSET)

        models = cast(list[str], d.pop("models", UNSET))

        uptime_seconds = d.pop("uptime_seconds", UNSET)

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

        on_schedule = d.pop("on_schedule", UNSET)

        host_worker_stat = cls(
            worker_id=worker_id,
            connected_at=connected_at,
            accelerator=accelerator,
            model=model,
            memory_gb=memory_gb,
            country=country,
            models=models,
            uptime_seconds=uptime_seconds,
            schedule=schedule,
            on_schedule=on_schedule,
        )

        host_worker_stat.additional_properties = d
        return host_worker_stat

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
