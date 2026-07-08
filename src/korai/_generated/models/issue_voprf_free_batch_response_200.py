from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="IssueVoprfFreeBatchResponse200")


@_attrs_define
class IssueVoprfFreeBatchResponse200:
    """
    Attributes:
        batch_id (UUID | Unset):
        elements (list[str] | Unset):
        proof (str | Unset): base64url DLEQ proof.
    """

    batch_id: UUID | Unset = UNSET
    elements: list[str] | Unset = UNSET
    proof: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        batch_id: str | Unset = UNSET
        if not isinstance(self.batch_id, Unset):
            batch_id = str(self.batch_id)

        elements: list[str] | Unset = UNSET
        if not isinstance(self.elements, Unset):
            elements = self.elements

        proof = self.proof

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if batch_id is not UNSET:
            field_dict["batch_id"] = batch_id
        if elements is not UNSET:
            field_dict["elements"] = elements
        if proof is not UNSET:
            field_dict["proof"] = proof

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _batch_id = d.pop("batch_id", UNSET)
        batch_id: UUID | Unset
        if isinstance(_batch_id, Unset):
            batch_id = UNSET
        else:
            batch_id = UUID(_batch_id)

        elements = cast(list[str], d.pop("elements", UNSET))

        proof = d.pop("proof", UNSET)

        issue_voprf_free_batch_response_200 = cls(
            batch_id=batch_id,
            elements=elements,
            proof=proof,
        )

        issue_voprf_free_batch_response_200.additional_properties = d
        return issue_voprf_free_batch_response_200

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
