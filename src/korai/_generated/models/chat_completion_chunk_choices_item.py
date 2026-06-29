from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.chat_completion_chunk_choices_item_finish_reason_type_1 import (
    ChatCompletionChunkChoicesItemFinishReasonType1,
)
from ..models.chat_completion_chunk_choices_item_finish_reason_type_2_type_1 import (
    ChatCompletionChunkChoicesItemFinishReasonType2Type1,
)
from ..models.chat_completion_chunk_choices_item_finish_reason_type_3_type_1 import (
    ChatCompletionChunkChoicesItemFinishReasonType3Type1,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.chat_completion_chunk_choices_item_delta import (
        ChatCompletionChunkChoicesItemDelta,
    )


T = TypeVar("T", bound="ChatCompletionChunkChoicesItem")


@_attrs_define
class ChatCompletionChunkChoicesItem:
    """
    Attributes:
        index (int | Unset):
        delta (ChatCompletionChunkChoicesItemDelta | Unset):
        finish_reason (ChatCompletionChunkChoicesItemFinishReasonType1 |
            ChatCompletionChunkChoicesItemFinishReasonType2Type1 | ChatCompletionChunkChoicesItemFinishReasonType3Type1 |
            None | Unset):
    """

    index: int | Unset = UNSET
    delta: ChatCompletionChunkChoicesItemDelta | Unset = UNSET
    finish_reason: (
        ChatCompletionChunkChoicesItemFinishReasonType1
        | ChatCompletionChunkChoicesItemFinishReasonType2Type1
        | ChatCompletionChunkChoicesItemFinishReasonType3Type1
        | None
        | Unset
    ) = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        index = self.index

        delta: dict[str, Any] | Unset = UNSET
        if not isinstance(self.delta, Unset):
            delta = self.delta.to_dict()

        finish_reason: None | str | Unset
        if isinstance(self.finish_reason, Unset):
            finish_reason = UNSET
        elif (
            isinstance(self.finish_reason, ChatCompletionChunkChoicesItemFinishReasonType1)
            or isinstance(self.finish_reason, ChatCompletionChunkChoicesItemFinishReasonType2Type1)
            or isinstance(self.finish_reason, ChatCompletionChunkChoicesItemFinishReasonType3Type1)
        ):
            finish_reason = self.finish_reason.value
        else:
            finish_reason = self.finish_reason

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if index is not UNSET:
            field_dict["index"] = index
        if delta is not UNSET:
            field_dict["delta"] = delta
        if finish_reason is not UNSET:
            field_dict["finish_reason"] = finish_reason

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.chat_completion_chunk_choices_item_delta import (
            ChatCompletionChunkChoicesItemDelta,
        )

        d = dict(src_dict)
        index = d.pop("index", UNSET)

        _delta = d.pop("delta", UNSET)
        delta: ChatCompletionChunkChoicesItemDelta | Unset
        if isinstance(_delta, Unset):
            delta = UNSET
        else:
            delta = ChatCompletionChunkChoicesItemDelta.from_dict(_delta)

        def _parse_finish_reason(
            data: object,
        ) -> (
            ChatCompletionChunkChoicesItemFinishReasonType1
            | ChatCompletionChunkChoicesItemFinishReasonType2Type1
            | ChatCompletionChunkChoicesItemFinishReasonType3Type1
            | None
            | Unset
        ):
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                finish_reason_type_1 = ChatCompletionChunkChoicesItemFinishReasonType1(data)

                return finish_reason_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, str):
                    raise TypeError()
                finish_reason_type_2_type_1 = ChatCompletionChunkChoicesItemFinishReasonType2Type1(
                    data
                )

                return finish_reason_type_2_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, str):
                    raise TypeError()
                finish_reason_type_3_type_1 = ChatCompletionChunkChoicesItemFinishReasonType3Type1(
                    data
                )

                return finish_reason_type_3_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                ChatCompletionChunkChoicesItemFinishReasonType1
                | ChatCompletionChunkChoicesItemFinishReasonType2Type1
                | ChatCompletionChunkChoicesItemFinishReasonType3Type1
                | None
                | Unset,
                data,
            )

        finish_reason = _parse_finish_reason(d.pop("finish_reason", UNSET))

        chat_completion_chunk_choices_item = cls(
            index=index,
            delta=delta,
            finish_reason=finish_reason,
        )

        chat_completion_chunk_choices_item.additional_properties = d
        return chat_completion_chunk_choices_item

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
