from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.worker_token import WorkerToken


T = TypeVar("T", bound="ListWorkerTokensResponse200")


@_attrs_define
class ListWorkerTokensResponse200:
    """
    Attributes:
        tokens (list[WorkerToken] | Unset):
    """

    tokens: list[WorkerToken] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        tokens: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.tokens, Unset):
            tokens = []
            for tokens_item_data in self.tokens:
                tokens_item = tokens_item_data.to_dict()
                tokens.append(tokens_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if tokens is not UNSET:
            field_dict["tokens"] = tokens

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.worker_token import WorkerToken

        d = dict(src_dict)
        _tokens = d.pop("tokens", UNSET)
        tokens: list[WorkerToken] | Unset = UNSET
        if _tokens is not UNSET:
            tokens = []
            for tokens_item_data in _tokens:
                tokens_item = WorkerToken.from_dict(tokens_item_data)

                tokens.append(tokens_item)

        list_worker_tokens_response_200 = cls(
            tokens=tokens,
        )

        list_worker_tokens_response_200.additional_properties = d
        return list_worker_tokens_response_200

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
