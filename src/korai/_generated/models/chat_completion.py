from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.chat_completion_choices_item import ChatCompletionChoicesItem
    from ..models.usage import Usage


T = TypeVar("T", bound="ChatCompletion")


@_attrs_define
class ChatCompletion:
    """
    Attributes:
        id (str | Unset):
        object_ (Literal['chat.completion'] | Unset):
        created (int | Unset): Unix seconds.
        model (str | Unset):
        choices (list[ChatCompletionChoicesItem] | Unset):
        usage (Usage | Unset):
    """

    id: str | Unset = UNSET
    object_: Literal["chat.completion"] | Unset = UNSET
    created: int | Unset = UNSET
    model: str | Unset = UNSET
    choices: list[ChatCompletionChoicesItem] | Unset = UNSET
    usage: Usage | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        object_ = self.object_

        created = self.created

        model = self.model

        choices: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.choices, Unset):
            choices = []
            for choices_item_data in self.choices:
                choices_item = choices_item_data.to_dict()
                choices.append(choices_item)

        usage: dict[str, Any] | Unset = UNSET
        if not isinstance(self.usage, Unset):
            usage = self.usage.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if object_ is not UNSET:
            field_dict["object"] = object_
        if created is not UNSET:
            field_dict["created"] = created
        if model is not UNSET:
            field_dict["model"] = model
        if choices is not UNSET:
            field_dict["choices"] = choices
        if usage is not UNSET:
            field_dict["usage"] = usage

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.chat_completion_choices_item import ChatCompletionChoicesItem
        from ..models.usage import Usage

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        object_ = cast(Literal["chat.completion"] | Unset, d.pop("object", UNSET))
        if object_ != "chat.completion" and not isinstance(object_, Unset):
            raise ValueError(f"object must match const 'chat.completion', got '{object_}'")

        created = d.pop("created", UNSET)

        model = d.pop("model", UNSET)

        _choices = d.pop("choices", UNSET)
        choices: list[ChatCompletionChoicesItem] | Unset = UNSET
        if _choices is not UNSET:
            choices = []
            for choices_item_data in _choices:
                choices_item = ChatCompletionChoicesItem.from_dict(choices_item_data)

                choices.append(choices_item)

        _usage = d.pop("usage", UNSET)
        usage: Usage | Unset
        if isinstance(_usage, Unset):
            usage = UNSET
        else:
            usage = Usage.from_dict(_usage)

        chat_completion = cls(
            id=id,
            object_=object_,
            created=created,
            model=model,
            choices=choices,
            usage=usage,
        )

        chat_completion.additional_properties = d
        return chat_completion

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
