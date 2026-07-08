from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.transaction_kind import TransactionKind
from ..types import UNSET, Unset

T = TypeVar("T", bound="Transaction")


@_attrs_define
class Transaction:
    """
    Attributes:
        id (int | Unset):
        user_id (UUID | Unset):
        kind (TransactionKind | Unset):
        amount_eur (float | Unset):
        balance_after (float | Unset):
        description (str | Unset):
        stripe_id (None | str | Unset):
        created_at (datetime.datetime | Unset):
    """

    id: int | Unset = UNSET
    user_id: UUID | Unset = UNSET
    kind: TransactionKind | Unset = UNSET
    amount_eur: float | Unset = UNSET
    balance_after: float | Unset = UNSET
    description: str | Unset = UNSET
    stripe_id: None | str | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        user_id: str | Unset = UNSET
        if not isinstance(self.user_id, Unset):
            user_id = str(self.user_id)

        kind: str | Unset = UNSET
        if not isinstance(self.kind, Unset):
            kind = self.kind.value

        amount_eur = self.amount_eur

        balance_after = self.balance_after

        description = self.description

        stripe_id: None | str | Unset
        if isinstance(self.stripe_id, Unset):
            stripe_id = UNSET
        else:
            stripe_id = self.stripe_id

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if kind is not UNSET:
            field_dict["kind"] = kind
        if amount_eur is not UNSET:
            field_dict["amount_eur"] = amount_eur
        if balance_after is not UNSET:
            field_dict["balance_after"] = balance_after
        if description is not UNSET:
            field_dict["description"] = description
        if stripe_id is not UNSET:
            field_dict["stripe_id"] = stripe_id
        if created_at is not UNSET:
            field_dict["created_at"] = created_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        _user_id = d.pop("user_id", UNSET)
        user_id: UUID | Unset
        if isinstance(_user_id, Unset):
            user_id = UNSET
        else:
            user_id = UUID(_user_id)

        _kind = d.pop("kind", UNSET)
        kind: TransactionKind | Unset
        if isinstance(_kind, Unset):
            kind = UNSET
        else:
            kind = TransactionKind(_kind)

        amount_eur = d.pop("amount_eur", UNSET)

        balance_after = d.pop("balance_after", UNSET)

        description = d.pop("description", UNSET)

        def _parse_stripe_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        stripe_id = _parse_stripe_id(d.pop("stripe_id", UNSET))

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = datetime.datetime.fromisoformat(_created_at)

        transaction = cls(
            id=id,
            user_id=user_id,
            kind=kind,
            amount_eur=amount_eur,
            balance_after=balance_after,
            description=description,
            stripe_id=stripe_id,
            created_at=created_at,
        )

        transaction.additional_properties = d
        return transaction

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
