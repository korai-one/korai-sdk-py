from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.tier_name import TierName
from ..types import UNSET, Unset

T = TypeVar("T", bound="TokenBatch")


@_attrs_define
class TokenBatch:
    """A wallet of single-shot bearer tokens. Each token is base64url(batch_id[16] || nonce[16] || HMAC-SHA256[32]).

    Attributes:
        batch_id (UUID | Unset):
        tier (TierName | Unset):
        issued_at (datetime.datetime | Unset):
        expires_at (datetime.datetime | Unset):
        max_tokens (int | Unset):
        tokens (list[str] | Unset):
    """

    batch_id: UUID | Unset = UNSET
    tier: TierName | Unset = UNSET
    issued_at: datetime.datetime | Unset = UNSET
    expires_at: datetime.datetime | Unset = UNSET
    max_tokens: int | Unset = UNSET
    tokens: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        batch_id: str | Unset = UNSET
        if not isinstance(self.batch_id, Unset):
            batch_id = str(self.batch_id)

        tier: str | Unset = UNSET
        if not isinstance(self.tier, Unset):
            tier = self.tier.value

        issued_at: str | Unset = UNSET
        if not isinstance(self.issued_at, Unset):
            issued_at = self.issued_at.isoformat()

        expires_at: str | Unset = UNSET
        if not isinstance(self.expires_at, Unset):
            expires_at = self.expires_at.isoformat()

        max_tokens = self.max_tokens

        tokens: list[str] | Unset = UNSET
        if not isinstance(self.tokens, Unset):
            tokens = self.tokens

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if batch_id is not UNSET:
            field_dict["batch_id"] = batch_id
        if tier is not UNSET:
            field_dict["tier"] = tier
        if issued_at is not UNSET:
            field_dict["issued_at"] = issued_at
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at
        if max_tokens is not UNSET:
            field_dict["max_tokens"] = max_tokens
        if tokens is not UNSET:
            field_dict["tokens"] = tokens

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

        _tier = d.pop("tier", UNSET)
        tier: TierName | Unset
        if isinstance(_tier, Unset):
            tier = UNSET
        else:
            tier = TierName(_tier)

        _issued_at = d.pop("issued_at", UNSET)
        issued_at: datetime.datetime | Unset
        if isinstance(_issued_at, Unset):
            issued_at = UNSET
        else:
            issued_at = datetime.datetime.fromisoformat(_issued_at)

        _expires_at = d.pop("expires_at", UNSET)
        expires_at: datetime.datetime | Unset
        if isinstance(_expires_at, Unset):
            expires_at = UNSET
        else:
            expires_at = datetime.datetime.fromisoformat(_expires_at)

        max_tokens = d.pop("max_tokens", UNSET)

        tokens = cast(list[str], d.pop("tokens", UNSET))

        token_batch = cls(
            batch_id=batch_id,
            tier=tier,
            issued_at=issued_at,
            expires_at=expires_at,
            max_tokens=max_tokens,
            tokens=tokens,
        )

        token_batch.additional_properties = d
        return token_batch

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
