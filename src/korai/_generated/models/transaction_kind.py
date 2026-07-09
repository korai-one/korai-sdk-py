from enum import Enum


class TransactionKind(str, Enum):
    PAYOUT = "payout"
    TOPUP = "topup"
    USAGE = "usage"

    def __str__(self) -> str:
        return str(self.value)
