from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.anonymous_subscription_status import AnonymousSubscriptionStatus
from ..models.tier_name import TierName
from ..types import UNSET, Unset

T = TypeVar("T", bound="AnonymousSubscription")


@_attrs_define
class AnonymousSubscription:
    """
    Attributes:
        stripe_subscription_id (str | Unset):
        tier (TierName | Unset):
        status (AnonymousSubscriptionStatus | Unset):
        current_period_end (datetime.datetime | Unset):
    """

    stripe_subscription_id: str | Unset = UNSET
    tier: TierName | Unset = UNSET
    status: AnonymousSubscriptionStatus | Unset = UNSET
    current_period_end: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        stripe_subscription_id = self.stripe_subscription_id

        tier: str | Unset = UNSET
        if not isinstance(self.tier, Unset):
            tier = self.tier.value

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        current_period_end: str | Unset = UNSET
        if not isinstance(self.current_period_end, Unset):
            current_period_end = self.current_period_end.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if stripe_subscription_id is not UNSET:
            field_dict["stripe_subscription_id"] = stripe_subscription_id
        if tier is not UNSET:
            field_dict["tier"] = tier
        if status is not UNSET:
            field_dict["status"] = status
        if current_period_end is not UNSET:
            field_dict["current_period_end"] = current_period_end

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        stripe_subscription_id = d.pop("stripe_subscription_id", UNSET)

        _tier = d.pop("tier", UNSET)
        tier: TierName | Unset
        if isinstance(_tier, Unset):
            tier = UNSET
        else:
            tier = TierName(_tier)

        _status = d.pop("status", UNSET)
        status: AnonymousSubscriptionStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = AnonymousSubscriptionStatus(_status)

        _current_period_end = d.pop("current_period_end", UNSET)
        current_period_end: datetime.datetime | Unset
        if isinstance(_current_period_end, Unset):
            current_period_end = UNSET
        else:
            current_period_end = datetime.datetime.fromisoformat(_current_period_end)

        anonymous_subscription = cls(
            stripe_subscription_id=stripe_subscription_id,
            tier=tier,
            status=status,
            current_period_end=current_period_end,
        )

        anonymous_subscription.additional_properties = d
        return anonymous_subscription

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
