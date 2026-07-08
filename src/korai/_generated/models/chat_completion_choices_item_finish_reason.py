from enum import Enum


class ChatCompletionChoicesItemFinishReason(str, Enum):
    LENGTH = "length"
    STOP = "stop"

    def __str__(self) -> str:
        return str(self.value)
