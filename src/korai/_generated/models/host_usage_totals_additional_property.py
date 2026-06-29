from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="HostUsageTotalsAdditionalProperty")


@_attrs_define
class HostUsageTotalsAdditionalProperty:
    """
    Attributes:
        requests (int | Unset):
        prompt_tokens (int | Unset):
        completion_tokens (int | Unset):
        earned_eur (float | Unset):
    """

    requests: int | Unset = UNSET
    prompt_tokens: int | Unset = UNSET
    completion_tokens: int | Unset = UNSET
    earned_eur: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        requests = self.requests

        prompt_tokens = self.prompt_tokens

        completion_tokens = self.completion_tokens

        earned_eur = self.earned_eur

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if requests is not UNSET:
            field_dict["requests"] = requests
        if prompt_tokens is not UNSET:
            field_dict["prompt_tokens"] = prompt_tokens
        if completion_tokens is not UNSET:
            field_dict["completion_tokens"] = completion_tokens
        if earned_eur is not UNSET:
            field_dict["earned_eur"] = earned_eur

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        requests = d.pop("requests", UNSET)

        prompt_tokens = d.pop("prompt_tokens", UNSET)

        completion_tokens = d.pop("completion_tokens", UNSET)

        earned_eur = d.pop("earned_eur", UNSET)

        host_usage_totals_additional_property = cls(
            requests=requests,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            earned_eur=earned_eur,
        )

        host_usage_totals_additional_property.additional_properties = d
        return host_usage_totals_additional_property

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
