from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.model_kind import ModelKind
from ..types import UNSET, Unset

T = TypeVar("T", bound="Model")


@_attrs_define
class Model:
    """
    Attributes:
        id (str | Unset):
        object_ (Literal['model'] | Unset):
        created (int | Unset):
        owned_by (Literal['korai'] | Unset):
        kind (ModelKind | Unset):
        description (str | Unset):
        family (str | Unset):
        variant (str | Unset):
        quant (str | Unset):
        role (str | Unset):
        context_len (int | Unset):
        supports_tools (bool | Unset):
    """

    id: str | Unset = UNSET
    object_: Literal["model"] | Unset = UNSET
    created: int | Unset = UNSET
    owned_by: Literal["korai"] | Unset = UNSET
    kind: ModelKind | Unset = UNSET
    description: str | Unset = UNSET
    family: str | Unset = UNSET
    variant: str | Unset = UNSET
    quant: str | Unset = UNSET
    role: str | Unset = UNSET
    context_len: int | Unset = UNSET
    supports_tools: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        object_ = self.object_

        created = self.created

        owned_by = self.owned_by

        kind: str | Unset = UNSET
        if not isinstance(self.kind, Unset):
            kind = self.kind.value

        description = self.description

        family = self.family

        variant = self.variant

        quant = self.quant

        role = self.role

        context_len = self.context_len

        supports_tools = self.supports_tools

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if object_ is not UNSET:
            field_dict["object"] = object_
        if created is not UNSET:
            field_dict["created"] = created
        if owned_by is not UNSET:
            field_dict["owned_by"] = owned_by
        if kind is not UNSET:
            field_dict["kind"] = kind
        if description is not UNSET:
            field_dict["description"] = description
        if family is not UNSET:
            field_dict["family"] = family
        if variant is not UNSET:
            field_dict["variant"] = variant
        if quant is not UNSET:
            field_dict["quant"] = quant
        if role is not UNSET:
            field_dict["role"] = role
        if context_len is not UNSET:
            field_dict["context_len"] = context_len
        if supports_tools is not UNSET:
            field_dict["supports_tools"] = supports_tools

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        object_ = cast(Literal["model"] | Unset, d.pop("object", UNSET))
        if object_ != "model" and not isinstance(object_, Unset):
            raise ValueError(f"object must match const 'model', got '{object_}'")

        created = d.pop("created", UNSET)

        owned_by = cast(Literal["korai"] | Unset, d.pop("owned_by", UNSET))
        if owned_by != "korai" and not isinstance(owned_by, Unset):
            raise ValueError(f"owned_by must match const 'korai', got '{owned_by}'")

        _kind = d.pop("kind", UNSET)
        kind: ModelKind | Unset
        if isinstance(_kind, Unset):
            kind = UNSET
        else:
            kind = ModelKind(_kind)

        description = d.pop("description", UNSET)

        family = d.pop("family", UNSET)

        variant = d.pop("variant", UNSET)

        quant = d.pop("quant", UNSET)

        role = d.pop("role", UNSET)

        context_len = d.pop("context_len", UNSET)

        supports_tools = d.pop("supports_tools", UNSET)

        model = cls(
            id=id,
            object_=object_,
            created=created,
            owned_by=owned_by,
            kind=kind,
            description=description,
            family=family,
            variant=variant,
            quant=quant,
            role=role,
            context_len=context_len,
            supports_tools=supports_tools,
        )

        model.additional_properties = d
        return model

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
