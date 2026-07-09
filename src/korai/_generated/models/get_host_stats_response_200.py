from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.host_worker_stat import HostWorkerStat


T = TypeVar("T", bound="GetHostStatsResponse200")


@_attrs_define
class GetHostStatsResponse200:
    """
    Attributes:
        workers (list[HostWorkerStat] | Unset):
        worker_count (int | Unset):
    """

    workers: list[HostWorkerStat] | Unset = UNSET
    worker_count: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        workers: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.workers, Unset):
            workers = []
            for workers_item_data in self.workers:
                workers_item = workers_item_data.to_dict()
                workers.append(workers_item)

        worker_count = self.worker_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if workers is not UNSET:
            field_dict["workers"] = workers
        if worker_count is not UNSET:
            field_dict["worker_count"] = worker_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.host_worker_stat import HostWorkerStat

        d = dict(src_dict)
        _workers = d.pop("workers", UNSET)
        workers: list[HostWorkerStat] | Unset = UNSET
        if _workers is not UNSET:
            workers = []
            for workers_item_data in _workers:
                workers_item = HostWorkerStat.from_dict(workers_item_data)

                workers.append(workers_item)

        worker_count = d.pop("worker_count", UNSET)

        get_host_stats_response_200 = cls(
            workers=workers,
            worker_count=worker_count,
        )

        get_host_stats_response_200.additional_properties = d
        return get_host_stats_response_200

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
