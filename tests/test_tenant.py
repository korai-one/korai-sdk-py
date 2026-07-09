"""Tests for korai.tenant.TenantModule."""

from __future__ import annotations

import httpx
import pytest
import respx

from korai import KoraiAuthError, KoraiClient
from korai.tenant import Membership, Organization

from .conftest import TEST_BASE_URL


async def test_get_current_returns_org_from_endpoint(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/tenant").mock(
        return_value=httpx.Response(
            200,
            json={
                "organization": {
                    "id": "org-1",
                    "name": "Acme SA",
                    "country": "CH",
                    "industry": "fiduciaire",
                    "created_at": "2026-01-01",
                    "member_count": 5,
                }
            },
        )
    )
    org = await client.tenant.get_current()
    assert isinstance(org, Organization)
    assert org.id == "org-1"
    assert org.industry == "fiduciaire"


async def test_get_current_falls_back_to_jwt(
    client: KoraiClient, respx_mock: respx.Router, fake_jwt: str
) -> None:
    client.set_tokens(fake_jwt)
    respx_mock.get("/tenant").mock(return_value=httpx.Response(404))
    org = await client.tenant.get_current()
    assert org.id == "org-42"


async def test_list_my_organizations_falls_back_to_single_org(
    client: KoraiClient, respx_mock: respx.Router, fake_jwt: str
) -> None:
    client.set_tokens(fake_jwt)
    respx_mock.get("/tenant/organizations").mock(
        return_value=httpx.Response(404)
    )
    respx_mock.get("/tenant").mock(return_value=httpx.Response(404))
    orgs = await client.tenant.list_my_organizations()
    assert len(orgs) == 1
    assert orgs[0].id == "org-42"


async def test_list_my_organizations_endpoint(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/tenant/organizations").mock(
        return_value=httpx.Response(
            200,
            json={
                "organizations": [
                    {
                        "id": "o1",
                        "name": "Org 1",
                        "country": "CH",
                        "created_at": "2026-01-01",
                        "member_count": 1,
                    },
                    {
                        "id": "o2",
                        "name": "Org 2",
                        "country": "FR",
                        "created_at": "2026-01-01",
                        "member_count": 2,
                    },
                ]
            },
        )
    )
    orgs = await client.tenant.list_my_organizations()
    assert len(orgs) == 2
    assert orgs[1].country == "FR"


async def test_switch_to_falls_back_to_header_only(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.post("/tenant/switch").mock(return_value=httpx.Response(404))
    await client.tenant.switch_to("org-new")
    assert client.organization_id == "org-new"


async def test_switch_to_stores_new_token(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.post("/tenant/switch").mock(
        return_value=httpx.Response(
            200,
            json={"access_token": "new-jwt", "refresh_token": "new-refresh"},
        )
    )
    await client.tenant.switch_to("org-new")
    assert client.access_token == "new-jwt"


async def test_list_members_raises_not_implemented_when_endpoint_missing(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/tenant/members").mock(return_value=httpx.Response(501))
    with pytest.raises(NotImplementedError):
        await client.tenant.list_members()


async def test_list_members_works_when_endpoint_exists(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.get("/tenant/members").mock(
        return_value=httpx.Response(
            200,
            json={
                "members": [
                    {
                        "organization_id": "o1",
                        "organization_name": "Acme",
                        "role": "admin",
                        "is_active": True,
                    }
                ]
            },
        )
    )
    members = await client.tenant.list_members()
    assert len(members) == 1
    assert isinstance(members[0], Membership)
    assert members[0].role == "admin"


async def test_invite_member_raises_not_implemented(
    client: KoraiClient, respx_mock: respx.Router
) -> None:
    respx_mock.post("/tenant/invite").mock(return_value=httpx.Response(404))
    with pytest.raises(NotImplementedError):
        await client.tenant.invite_member("alice@example.com", "collaborator")


async def test_claims_requires_token() -> None:
    c = KoraiClient(base_url=TEST_BASE_URL)
    try:
        with pytest.raises(KoraiAuthError):
            c.tenant._claims()
    finally:
        await c.aclose()
