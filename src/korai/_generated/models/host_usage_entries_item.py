from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="HostUsageEntriesItem")


@_attrs_define
class HostUsageEntriesItem:
    """
    Attributes:
        id (int | Unset):
        worker_id (str | Unset):
        owner_id (str | Unset):
        model (str | Unset):
        tier (str | Unset):
        prompt_tokens (int | Unset):
        completion_tokens (int | Unset):
        rate_per_ktok_eur (float | Unset):
        earned_eur (float | Unset):
        created_at (datetime.datetime | Unset):
    """

    id: int | Unset = UNSET
    worker_id: str | Unset = UNSET
    owner_id: str | Unset = UNSET
    model: str | Unset = UNSET
    tier: str | Unset = UNSET
    prompt_tokens: int | Unset = UNSET
    completion_tokens: int | Unset = UNSET
    rate_per_ktok_eur: float | Unset = UNSET
    earned_eur: float | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        worker_id = self.worker_id

        owner_id = self.owner_id

        model = self.model

        tier = self.tier

        prompt_tokens = self.prompt_tokens

        completion_tokens = self.completion_tokens

        rate_per_ktok_eur = self.rate_per_ktok_eur

        earned_eur = self.earned_eur

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if worker_id is not UNSET:
            field_dict["worker_id"] = worker_id
        if owner_id is not UNSET:
            field_dict["owner_id"] = owner_id
        if model is not UNSET:
            field_dict["model"] = model
        if tier is not UNSET:
            field_dict["tier"] = tier
        if prompt_tokens is not UNSET:
            field_dict["prompt_tokens"] = prompt_tokens
        if completion_tokens is not UNSET:
            field_dict["completion_tokens"] = completion_tokens
        if rate_per_ktok_eur is not UNSET:
            field_dict["rate_per_ktok_eur"] = rate_per_ktok_eur
        if earned_eur is not UNSET:
            field_dict["earned_eur"] = earned_eur
        if created_at is not UNSET:
            field_dict["created_at"] = created_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        worker_id = d.pop("worker_id", UNSET)

        owner_id = d.pop("owner_id", UNSET)

        model = d.pop("model", UNSET)

        tier = d.pop("tier", UNSET)

        prompt_tokens = d.pop("prompt_tokens", UNSET)

        completion_tokens = d.pop("completion_tokens", UNSET)

        rate_per_ktok_eur = d.pop("rate_per_ktok_eur", UNSET)

        earned_eur = d.pop("earned_eur", UNSET)

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = datetime.datetime.fromisoformat(_created_at)

        host_usage_entries_item = cls(
            id=id,
            worker_id=worker_id,
            owner_id=owner_id,
            model=model,
            tier=tier,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            rate_per_ktok_eur=rate_per_ktok_eur,
            earned_eur=earned_eur,
            created_at=created_at,
        )

        host_usage_entries_item.additional_properties = d
        return host_usage_entries_item

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
