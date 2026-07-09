from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetVeilRootResponse200")


@_attrs_define
class GetVeilRootResponse200:
    """
    Attributes:
        tree_size (int | Unset):
        root (str | Unset): base64 (standard) SHA-256 Merkle root.
        signature (str | Unset): base64 (standard) Ed25519 signature over the root.
    """

    tree_size: int | Unset = UNSET
    root: str | Unset = UNSET
    signature: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        tree_size = self.tree_size

        root = self.root

        signature = self.signature

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if tree_size is not UNSET:
            field_dict["tree_size"] = tree_size
        if root is not UNSET:
            field_dict["root"] = root
        if signature is not UNSET:
            field_dict["signature"] = signature

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        tree_size = d.pop("tree_size", UNSET)

        root = d.pop("root", UNSET)

        signature = d.pop("signature", UNSET)

        get_veil_root_response_200 = cls(
            tree_size=tree_size,
            root=root,
            signature=signature,
        )

        get_veil_root_response_200.additional_properties = d
        return get_veil_root_response_200

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
