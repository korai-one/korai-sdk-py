from enum import Enum


class AnonymousSubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"

    def __str__(self) -> str:
        return str(self.value)
