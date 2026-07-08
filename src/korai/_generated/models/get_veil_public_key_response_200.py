from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetVeilPublicKeyResponse200")


@_attrs_define
class GetVeilPublicKeyResponse200:
    """
    Attributes:
        alg (Literal['ed25519'] | Unset):
        public_key (str | Unset): base64 (standard) Ed25519 public key.
        size (int | Unset): Current Merkle tree size.
    """

    alg: Literal["ed25519"] | Unset = UNSET
    public_key: str | Unset = UNSET
    size: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        alg = self.alg

        public_key = self.public_key

        size = self.size

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if alg is not UNSET:
            field_dict["alg"] = alg
        if public_key is not UNSET:
            field_dict["public_key"] = public_key
        if size is not UNSET:
            field_dict["size"] = size

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        alg = cast(Literal["ed25519"] | Unset, d.pop("alg", UNSET))
        if alg != "ed25519" and not isinstance(alg, Unset):
            raise ValueError(f"alg must match const 'ed25519', got '{alg}'")

        public_key = d.pop("public_key", UNSET)

        size = d.pop("size", UNSET)

        get_veil_public_key_response_200 = cls(
            alg=alg,
            public_key=public_key,
            size=size,
        )

        get_veil_public_key_response_200.additional_properties = d
        return get_veil_public_key_response_200

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
