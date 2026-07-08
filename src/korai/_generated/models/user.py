from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.user_role import UserRole
from ..types import UNSET, Unset

T = TypeVar("T", bound="User")


@_attrs_define
class User:
    """
    Attributes:
        id (UUID | Unset):
        email (str | Unset):
        display_name (str | Unset):
        credits_eur (float | Unset):
        tier (str | Unset):
        role (UserRole | Unset):
        created_at (datetime.datetime | Unset):
    """

    id: UUID | Unset = UNSET
    email: str | Unset = UNSET
    display_name: str | Unset = UNSET
    credits_eur: float | Unset = UNSET
    tier: str | Unset = UNSET
    role: UserRole | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        email = self.email

        display_name = self.display_name

        credits_eur = self.credits_eur

        tier = self.tier

        role: str | Unset = UNSET
        if not isinstance(self.role, Unset):
            role = self.role.value

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if email is not UNSET:
            field_dict["email"] = email
        if display_name is not UNSET:
            field_dict["display_name"] = display_name
        if credits_eur is not UNSET:
            field_dict["credits_eur"] = credits_eur
        if tier is not UNSET:
            field_dict["tier"] = tier
        if role is not UNSET:
            field_dict["role"] = role
        if created_at is not UNSET:
            field_dict["created_at"] = created_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        email = d.pop("email", UNSET)

        display_name = d.pop("display_name", UNSET)

        credits_eur = d.pop("credits_eur", UNSET)

        tier = d.pop("tier", UNSET)

        _role = d.pop("role", UNSET)
        role: UserRole | Unset
        if isinstance(_role, Unset):
            role = UNSET
        else:
            role = UserRole(_role)

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = datetime.datetime.fromisoformat(_created_at)

        user = cls(
            id=id,
            email=email,
            display_name=display_name,
            credits_eur=credits_eur,
            tier=tier,
            role=role,
            created_at=created_at,
        )

        user.additional_properties = d
        return user

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
