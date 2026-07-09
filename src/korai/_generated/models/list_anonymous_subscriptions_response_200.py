from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.anonymous_subscription import AnonymousSubscription


T = TypeVar("T", bound="ListAnonymousSubscriptionsResponse200")


@_attrs_define
class ListAnonymousSubscriptionsResponse200:
    """
    Attributes:
        subscriptions (list[AnonymousSubscription] | Unset):
    """

    subscriptions: list[AnonymousSubscription] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        subscriptions: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.subscriptions, Unset):
            subscriptions = []
            for subscriptions_item_data in self.subscriptions:
                subscriptions_item = subscriptions_item_data.to_dict()
                subscriptions.append(subscriptions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if subscriptions is not UNSET:
            field_dict["subscriptions"] = subscriptions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.anonymous_subscription import AnonymousSubscription

        d = dict(src_dict)
        _subscriptions = d.pop("subscriptions", UNSET)
        subscriptions: list[AnonymousSubscription] | Unset = UNSET
        if _subscriptions is not UNSET:
            subscriptions = []
            for subscriptions_item_data in _subscriptions:
                subscriptions_item = AnonymousSubscription.from_dict(subscriptions_item_data)

                subscriptions.append(subscriptions_item)

        list_anonymous_subscriptions_response_200 = cls(
            subscriptions=subscriptions,
        )

        list_anonymous_subscriptions_response_200.additional_properties = d
        return list_anonymous_subscriptions_response_200

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
