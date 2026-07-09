"""Tests for korai.billing.BillingModule."""

from __future__ import annotations

import httpx
import pytest
import respx

from korai import KoraiAPIError, KoraiClient
from korai.billing import Balance, CreditPackage, Transaction


async def test_get_balance(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/billing/balance").mock(
        return_value=httpx.Response(200, json={"balance_eur": 12.34})
    )
    bal = await client.billing.get_balance()
    assert isinstance(bal, Balance)
    assert bal.balance_eur == 12.34


async def test_list_transactions(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/billing/transactions").mock(
        return_value=httpx.Response(
            200,
            json={
                "transactions": [
                    {
                        "id": "t1",
                        "user_id": "u1",
                        "amount_eur": 5.0,
                        "kind": "purchase",
                        "description": "starter pack",
                        "created_at": "2026-01-01T00:00:00Z",
                    },
                    {
                        "id": "t2",
                        "user_id": "u1",
                        "amount_eur": -0.05,
                        "kind": "consumption",
                        "metadata": {
                            "model": "claude-opus-4-7",
                            "input_tokens": 12,
                            "output_tokens": 4,
                        },
                        "created_at": "2026-01-02T10:00:00Z",
                    },
                ]
            },
        )
    )
    txns = await client.billing.list_transactions(limit=20)
    assert len(txns) == 2
    assert isinstance(txns[0], Transaction)
    assert txns[0].kind == "purchase"
    assert txns[1].metadata["model"] == "claude-opus-4-7"


async def test_list_packages(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/billing/packages").mock(
        return_value=httpx.Response(
            200,
            json={
                "packages": [
                    {
                        "id": "starter",
                        "label": "Starter",
                        "credits_eur": 10.0,
                        "price_cents": 1000,
                    }
                ]
            },
        )
    )
    pkgs = await client.billing.list_packages()
    assert len(pkgs) == 1
    assert isinstance(pkgs[0], CreditPackage)
    assert pkgs[0].id == "starter"


async def test_create_checkout_returns_url(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.post("/billing/checkout").mock(
        return_value=httpx.Response(
            200, json={"checkout_url": "https://stripe.example/x"}
        )
    )
    url = await client.billing.create_checkout(package_id="starter")
    assert url == "https://stripe.example/x"


async def test_create_checkout_missing_url(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.post("/billing/checkout").mock(
        return_value=httpx.Response(200, json={"unexpected": "shape"})
    )
    with pytest.raises(KoraiAPIError):
        await client.billing.create_checkout(package_id="starter")


async def test_get_quotas_falls_back_to_empty(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/billing/quotas").mock(return_value=httpx.Response(404))
    quotas = await client.billing.get_quotas()
    assert quotas == []


async def test_get_subscription_returns_none_when_missing(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/billing/subscription").mock(
        return_value=httpx.Response(404)
    )
    sub = await client.billing.get_subscription()
    assert sub is None


async def test_get_usage_falls_back_to_transactions(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/billing/usage").mock(return_value=httpx.Response(404))
    respx_mock.get("/billing/transactions").mock(
        return_value=httpx.Response(
            200,
            json={
                "transactions": [
                    {
                        "id": "t1",
                        "amount_eur": -0.10,
                        "kind": "consumption",
                        "created_at": "2026-04-01T08:00:00Z",
                        "metadata": {
                            "model": "auto",
                            "input_tokens": 50,
                            "output_tokens": 100,
                        },
                    },
                    {
                        "id": "t2",
                        "amount_eur": -0.05,
                        "kind": "consumption",
                        "created_at": "2026-04-01T09:00:00Z",
                        "metadata": {
                            "model": "auto",
                            "input_tokens": 25,
                            "output_tokens": 50,
                        },
                    },
                ]
            },
        )
    )
    usage = await client.billing.get_usage()
    assert len(usage) == 1
    assert usage[0].date == "2026-04-01"
    assert usage[0].input_tokens == 75
    assert usage[0].output_tokens == 150
