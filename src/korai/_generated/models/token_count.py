from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TokenCount")


@_attrs_define
class TokenCount:
    """
    Attributes:
        object_ (Literal['token_count']):
        model (str): The alias or id the caller requested.
        prompt_tokens (int): Exact prompt-token count from the model's tokenizer.
        resolved_model (str | Unset): The canonical model the count was computed against.
    """

    object_: Literal["token_count"]
    model: str
    prompt_tokens: int
    resolved_model: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        object_ = self.object_

        model = self.model

        prompt_tokens = self.prompt_tokens

        resolved_model = self.resolved_model

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "object": object_,
                "model": model,
                "prompt_tokens": prompt_tokens,
            }
        )
        if resolved_model is not UNSET:
            field_dict["resolved_model"] = resolved_model

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        object_ = cast(Literal["token_count"], d.pop("object"))
        if object_ != "token_count":
            raise ValueError(f"object must match const 'token_count', got '{object_}'")

        model = d.pop("model")

        prompt_tokens = d.pop("prompt_tokens")

        resolved_model = d.pop("resolved_model", UNSET)

        token_count = cls(
            object_=object_,
            model=model,
            prompt_tokens=prompt_tokens,
            resolved_model=resolved_model,
        )

        token_count.additional_properties = d
        return token_count

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
