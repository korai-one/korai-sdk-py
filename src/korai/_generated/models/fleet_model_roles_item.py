from enum import Enum


class FleetModelRolesItem(str, Enum):
    CODE = "code"
    DEEP = "deep"
    FAST = "fast"
    LONG = "long"
    ULTRADEEP = "ultradeep"
    VISION = "vision"

    def __str__(self) -> str:
        return str(self.value)
