"""Billing module — credit balance, transactions, usage, checkout.

Wraps the ``/billing/*`` endpoints currently exposed by Korai Cloud:

* ``GET  /billing/balance``      → credit balance (EUR)
* ``GET  /billing/transactions`` → recent transactions
* ``GET  /billing/packages``     → list of credit packages
* ``POST /billing/checkout``     → Stripe Checkout Session URL

Quotas and subscription tiers are not yet exposed by the orchestrator
(today's billing is purely credit-based) — the corresponding methods
return placeholder objects and document the missing endpoint.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field

from korai._client import _RawBody
from korai._errors import KoraiAPIError
from korai._generated.api.billing import (
    create_checkout as create_checkout_api,
)
from korai._generated.api.billing import (
    get_balance as get_balance_api,
)
from korai._generated.api.billing import (
    list_packages as list_packages_api,
)
from korai._generated.api.billing import (
    list_transactions as list_transactions_api,
)

if TYPE_CHECKING:
    from korai._client import KoraiClient


class Quota(BaseModel):
    """A usage quota."""

    name: str
    used: int
    limit: int | None  # None = unlimited
    period: Literal["day", "month", "year", "lifetime"]
    resets_at: str | None  # ISO datetime


class Subscription(BaseModel):
    """An active subscription."""

    id: str
    tier: str
    status: Literal["active", "past_due", "canceled", "trial"]
    current_period_start: str
    current_period_end: str
    seats: int


class UsageRecord(BaseModel):
    """Usage line for a single time bucket.

    The cost field is in **euros** to match the ledger currency exposed by
    ``GET /billing/transactions`` (the orchestrator settles credits in EUR).
    A previous version misnamed this ``cost_chf`` while filling it with EUR
    values — see CHANGELOG.
    """

    date: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_eur: float


class Balance(BaseModel):
    """Current credit balance."""

    balance_eur: float


class Transaction(BaseModel):
    """A single credit ledger entry."""

    id: str
    user_id: str | None = None
    amount_eur: float
    kind: str  # "purchase" | "consumption" | "refund" | …
    description: str | None = None
    created_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CreditPackage(BaseModel):
    """A Stripe-backed credit package available for checkout."""

    id: str
    label: str = ""
    credits_eur: float = 0.0
    price_cents: int = 0


class BillingModule:
    """Billing operations against Korai Cloud."""

    def __init__(self, client: KoraiClient) -> None:
        self._client = client

    # ------------------------------------------------------------------
    # Live endpoints
    # ------------------------------------------------------------------

    async def get_balance(self) -> Balance:
        """Return the current credit balance for the authenticated user.

        Example::

            bal = await client.billing.get_balance()
            print(f"{bal.balance_eur:.2f} EUR")
        """
        data = await self._client._call_gen(
            get_balance_api._get_kwargs, path="/billing/balance"
        )
        if not isinstance(data, dict):
            return Balance(balance_eur=0.0)
        return Balance(balance_eur=float(data.get("balance_eur", 0.0)))

    async def list_transactions(self, limit: int = 50) -> list[Transaction]:
        """List recent ledger entries."""
        data = await self._client._call_gen(
            list_transactions_api._get_kwargs,
            path="/billing/transactions",
            limit=limit,
        )
        items = data.get("transactions", []) if isinstance(data, dict) else []
        out: list[Transaction] = []
        for raw in items:
            if not isinstance(raw, dict):
                continue
            out.append(
                Transaction(
                    id=str(raw.get("id", "")),
                    user_id=raw.get("user_id"),
                    amount_eur=float(raw.get("amount_eur", 0.0)),
                    kind=str(raw.get("kind", "")),
                    description=raw.get("description"),
                    created_at=raw.get("created_at"),
                    metadata=raw.get("metadata") or {},
                )
            )
        return out

    async def list_packages(self) -> list[CreditPackage]:
        """List credit packages available for purchase."""
        data = await self._client._call_gen(
            list_packages_api._get_kwargs, path="/billing/packages"
        )
        items = data.get("packages", []) if isinstance(data, dict) else []
        return [
            CreditPackage(
                id=str(i.get("id", "")),
                label=str(i.get("label", "")),
                credits_eur=float(i.get("credits_eur", 0.0)),
                price_cents=int(i.get("price_cents", 0)),
            )
            for i in items
            if isinstance(i, dict)
        ]

    async def create_checkout(
        self,
        *,
        package_id: str | None = None,
        tier: str | None = None,
        seats: int = 1,  # noqa: ARG002
        success_url: str | None = None,  # noqa: ARG002
        cancel_url: str | None = None,  # noqa: ARG002
    ) -> str:
        """Create a Stripe Checkout Session and return its URL.

        The orchestrator's billing today is purely credit-based: it
        accepts a ``package_id`` (e.g. "starter", "pro") and ignores
        ``tier``/``seats``/``success_url``/``cancel_url`` (the latter
        are configured server-side). The signature accepts both shapes
        for forward compatibility.

        Example::

            url = await client.billing.create_checkout(package_id="starter")
            webbrowser.open(url)
        """
        body = {"package_id": package_id or tier or "default"}
        data = await self._client._call_gen(
            create_checkout_api._get_kwargs,
            path="/billing/checkout",
            body=_RawBody(body),
        )
        if isinstance(data, dict) and isinstance(data.get("checkout_url"), str):
            return data["checkout_url"]
        raise KoraiAPIError(
            status_code=500,
            message="checkout endpoint did not return a URL",
            body=data,
        )

    # ------------------------------------------------------------------
    # Pending Cloud endpoints
    # ------------------------------------------------------------------

    async def get_quotas(self) -> list[Quota]:
        """Return active quotas.

        TODO(cloud): not yet exposed by the orchestrator (billing is
        credit-based today, no quota limits). Returns ``[]``.
        """
        try:
            data = await self._client._request("GET", "/billing/quotas")
        except KoraiAPIError as exc:
            if exc.status_code in (404, 405, 501):
                return []
            raise
        items = data.get("quotas", []) if isinstance(data, dict) else []
        return [Quota(**i) for i in items if isinstance(i, dict)]

    async def get_subscription(self) -> Subscription | None:
        """Return the active subscription, if any.

        TODO(cloud): not yet exposed (orchestrator only has one-off
        credit packages today). Returns ``None``.
        """
        try:
            data = await self._client._request("GET", "/billing/subscription")
        except KoraiAPIError as exc:
            if exc.status_code in (404, 405, 501):
                return None
            raise
        if not isinstance(data, dict) or not data.get("id"):
            return None
        return Subscription(**data)

    async def get_usage(
        self,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> list[UsageRecord]:
        """Return per-day usage records.

        Tries ``GET /billing/usage`` first; falls back to deriving usage
        from the transaction ledger when the dedicated endpoint is not
        yet exposed.
        """
        params: dict[str, Any] = {}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        try:
            data = await self._client._request(
                "GET", "/billing/usage", params=params or None
            )
            items = data.get("usage", []) if isinstance(data, dict) else []
            return [UsageRecord(**i) for i in items if isinstance(i, dict)]
        except KoraiAPIError as exc:
            if exc.status_code not in (404, 405, 501):
                raise
        # Fallback: aggregate transactions client-side.
        txns = await self.list_transactions(limit=1000)
        # TODO(cloud): expose /billing/usage with proper per-model
        # token attribution so we don't have to fall back here.
        records: dict[tuple[str, str], UsageRecord] = {}
        for t in txns:
            if t.kind != "consumption":
                continue
            day = (t.created_at or "")[:10] or "unknown"
            model = str(t.metadata.get("model", "unknown"))
            key = (day, model)
            existing = records.get(key)
            if existing is None:
                records[key] = UsageRecord(
                    date=day,
                    model=model,
                    input_tokens=int(t.metadata.get("input_tokens", 0)),
                    output_tokens=int(t.metadata.get("output_tokens", 0)),
                    cost_eur=abs(t.amount_eur),
                )
            else:
                existing.input_tokens += int(t.metadata.get("input_tokens", 0))
                existing.output_tokens += int(t.metadata.get("output_tokens", 0))
                existing.cost_eur += abs(t.amount_eur)
        return list(records.values())


__all__ = [
    "Balance",
    "BillingModule",
    "CreditPackage",
    "Quota",
    "Subscription",
    "Transaction",
    "UsageRecord",
]
