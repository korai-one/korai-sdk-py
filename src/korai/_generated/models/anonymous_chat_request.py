from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.chat_message import ChatMessage


T = TypeVar("T", bound="AnonymousChatRequest")


@_attrs_define
class AnonymousChatRequest:
    """
    Attributes:
        token (str): Single-shot wallet token (the credential).
        session_id (UUID): Persistent browser session id (rate-limit only; not identity).
        messages (list[ChatMessage]):
        model (str | Unset):
        stream (bool | Unset):  Default: False.
    """

    token: str
    session_id: UUID
    messages: list[ChatMessage]
    model: str | Unset = UNSET
    stream: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        token = self.token

        session_id = str(self.session_id)

        messages = []
        for messages_item_data in self.messages:
            messages_item = messages_item_data.to_dict()
            messages.append(messages_item)

        model = self.model

        stream = self.stream

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "token": token,
                "session_id": session_id,
                "messages": messages,
            }
        )
        if model is not UNSET:
            field_dict["model"] = model
        if stream is not UNSET:
            field_dict["stream"] = stream

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.chat_message import ChatMessage

        d = dict(src_dict)
        token = d.pop("token")

        session_id = UUID(d.pop("session_id"))

        messages = []
        _messages = d.pop("messages")
        for messages_item_data in _messages:
            messages_item = ChatMessage.from_dict(messages_item_data)

            messages.append(messages_item)

        model = d.pop("model", UNSET)

        stream = d.pop("stream", UNSET)

        anonymous_chat_request = cls(
            token=token,
            session_id=session_id,
            messages=messages,
            model=model,
            stream=stream,
        )

        anonymous_chat_request.additional_properties = d
        return anonymous_chat_request

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
