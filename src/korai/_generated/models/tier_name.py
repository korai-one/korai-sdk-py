from enum import Enum


class TierName(str, Enum):
    FREE = "free"
    LIGHT = "light"
    PLUS = "plus"
    PRO = "pro"
    STANDARD = "standard"

    def __str__(self) -> str:
        return str(self.value)
