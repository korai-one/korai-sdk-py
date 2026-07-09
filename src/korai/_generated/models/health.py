from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.health_status import HealthStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.health_checks import HealthChecks


T = TypeVar("T", bound="Health")


@_attrs_define
class Health:
    """
    Attributes:
        status (HealthStatus | Unset):
        version (str | Unset):
        checks (HealthChecks | Unset):
        worker_count (int | Unset):
        connected_count (int | Unset):
    """

    status: HealthStatus | Unset = UNSET
    version: str | Unset = UNSET
    checks: HealthChecks | Unset = UNSET
    worker_count: int | Unset = UNSET
    connected_count: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        version = self.version

        checks: dict[str, Any] | Unset = UNSET
        if not isinstance(self.checks, Unset):
            checks = self.checks.to_dict()

        worker_count = self.worker_count

        connected_count = self.connected_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if status is not UNSET:
            field_dict["status"] = status
        if version is not UNSET:
            field_dict["version"] = version
        if checks is not UNSET:
            field_dict["checks"] = checks
        if worker_count is not UNSET:
            field_dict["worker_count"] = worker_count
        if connected_count is not UNSET:
            field_dict["connected_count"] = connected_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.health_checks import HealthChecks

        d = dict(src_dict)
        _status = d.pop("status", UNSET)
        status: HealthStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = HealthStatus(_status)

        version = d.pop("version", UNSET)

        _checks = d.pop("checks", UNSET)
        checks: HealthChecks | Unset
        if isinstance(_checks, Unset):
            checks = UNSET
        else:
            checks = HealthChecks.from_dict(_checks)

        worker_count = d.pop("worker_count", UNSET)

        connected_count = d.pop("connected_count", UNSET)

        health = cls(
            status=status,
            version=version,
            checks=checks,
            worker_count=worker_count,
            connected_count=connected_count,
        )

        health.additional_properties = d
        return health

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
