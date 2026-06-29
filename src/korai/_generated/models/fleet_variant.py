from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.fleet_variant_backend import FleetVariantBackend
from ..types import UNSET, Unset

T = TypeVar("T", bound="FleetVariant")


@_attrs_define
class FleetVariant:
    """
    Attributes:
        hf_repo (str | Unset):
        hf_filename (str | Unset):
        size_gb (int | Unset):
        min_vram_gb (int | Unset):
        backend (FleetVariantBackend | Unset):
    """

    hf_repo: str | Unset = UNSET
    hf_filename: str | Unset = UNSET
    size_gb: int | Unset = UNSET
    min_vram_gb: int | Unset = UNSET
    backend: FleetVariantBackend | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        hf_repo = self.hf_repo

        hf_filename = self.hf_filename

        size_gb = self.size_gb

        min_vram_gb = self.min_vram_gb

        backend: str | Unset = UNSET
        if not isinstance(self.backend, Unset):
            backend = self.backend.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if hf_repo is not UNSET:
            field_dict["hf_repo"] = hf_repo
        if hf_filename is not UNSET:
            field_dict["hf_filename"] = hf_filename
        if size_gb is not UNSET:
            field_dict["size_gb"] = size_gb
        if min_vram_gb is not UNSET:
            field_dict["min_vram_gb"] = min_vram_gb
        if backend is not UNSET:
            field_dict["backend"] = backend

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        hf_repo = d.pop("hf_repo", UNSET)

        hf_filename = d.pop("hf_filename", UNSET)

        size_gb = d.pop("size_gb", UNSET)

        min_vram_gb = d.pop("min_vram_gb", UNSET)

        _backend = d.pop("backend", UNSET)
        backend: FleetVariantBackend | Unset
        if isinstance(_backend, Unset):
            backend = UNSET
        else:
            backend = FleetVariantBackend(_backend)

        fleet_variant = cls(
            hf_repo=hf_repo,
            hf_filename=hf_filename,
            size_gb=size_gb,
            min_vram_gb=min_vram_gb,
            backend=backend,
        )

        fleet_variant.additional_properties = d
        return fleet_variant

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
