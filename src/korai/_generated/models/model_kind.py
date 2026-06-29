from enum import Enum


class ModelKind(str, Enum):
    ALIAS = "alias"
    CANONICAL = "canonical"

    def __str__(self) -> str:
        return str(self.value)
