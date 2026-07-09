from enum import Enum


class ChatCompletionChunkChoicesItemFinishReasonType3Type1(str, Enum):
    LENGTH = "length"
    STOP = "stop"

    def __str__(self) -> str:
        return str(self.value)
