from enum import Enum


class FleetApiTierProvider(str, Enum):
    DEEPINFRA = "deepinfra"
    TOGETHER = "together"

    def __str__(self) -> str:
        return str(self.value)
