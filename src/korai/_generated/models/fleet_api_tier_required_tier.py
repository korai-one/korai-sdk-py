from enum import Enum


class FleetApiTierRequiredTier(str, Enum):
    MAX = "max"
    PRO = "pro"

    def __str__(self) -> str:
        return str(self.value)
