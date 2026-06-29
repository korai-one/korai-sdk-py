"""Tenant module — organization (cabinet) context, members, switching.

A user can belong to multiple organizations (cabinets, hospitals,
studios). Each session is scoped to one organization. The SDK exposes
helpers to inspect the current tenant and switch contexts.

State of the world
------------------

The orchestrator does **not** yet expose organization endpoints — the
single ``cab`` JWT claim is the only multi-tenant signal currently
available. Most methods on this module therefore return data extracted
from the JWT (when possible) or raise :class:`NotImplementedError` with
a clear ``TODO(cloud)`` message.

When the cloud endpoints land (``GET /tenant``, ``POST /tenant/switch``,
``GET /tenant/members``, ``POST /tenant/invite``) this module's
signatures are forward-compatible and can be wired up without breaking
callers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel

from korai._errors import KoraiAPIError, KoraiAuthError
from korai.auth import decode_jwt_unverified

if TYPE_CHECKING:
    from korai._client import KoraiClient


class Organization(BaseModel):
    """A tenant organization (cabinet, hospital, studio, etc.)."""

    id: str
    name: str = ""
    country: str = "CH"
    industry: str | None = None
    created_at: str = ""
    member_count: int = 0


class Membership(BaseModel):
    """User's membership in an organization."""

    organization_id: str
    organization_name: str = ""
    role: Literal["admin", "partner", "collaborator", "accountant", "reader"] = (
        "collaborator"
    )
    is_active: bool = True


class TenantModule:
    """Multi-tenant operations.

    Status: partial. ``get_current()`` and ``list_my_organizations()``
    work today by introspecting the current JWT. Member listing and
    invitations require server-side endpoints not yet exposed.
    """

    def __init__(self, client: KoraiClient) -> None:
        self._client = client

    # ------------------------------------------------------------------
    # JWT-backed helpers
    # ------------------------------------------------------------------

    def _claims(self) -> dict[str, Any]:
        """Return JWT claims, raising :class:`KoraiAuthError` if no token."""
        token = self._client.access_token or self._client.api_key
        if not token:
            raise KoraiAuthError(
                status_code=401, message="no token available to introspect"
            )
        try:
            return decode_jwt_unverified(token)
        except ValueError as exc:
            raise KoraiAuthError(
                status_code=401, message=f"cannot decode token: {exc}"
            ) from exc

    async def get_current(self) -> Organization:
        """Return the organization of the current session.

        Tries ``GET /tenant`` first; on 404/501 (endpoint not yet
        deployed) it falls back to extracting the ``cab`` claim from the
        JWT, returning an :class:`Organization` with id only.
        """
        try:
            data = await self._client._request("GET", "/tenant")
        except KoraiAPIError as exc:
            if exc.status_code in (404, 405, 501):
                # TODO(cloud): /tenant endpoint not yet exposed.
                claims = self._claims()
                org_id = (
                    self._client.organization_id
                    or claims.get("cab")
                    or claims.get("organization_id")
                )
                if not org_id:
                    raise KoraiAuthError(
                        status_code=401,
                        message="no organization in JWT — set client.organization_id",
                    ) from exc
                return Organization(id=str(org_id))
            raise
        if isinstance(data, dict) and "organization" in data:
            data = data["organization"]
        return Organization(**(data if isinstance(data, dict) else {"id": ""}))

    async def list_my_organizations(self) -> list[Organization]:
        """List organizations the current user is member of.

        Tries ``GET /tenant/organizations`` first; on 404/501 falls back
        to a single-element list with the JWT's ``cab`` claim.
        """
        try:
            data = await self._client._request("GET", "/tenant/organizations")
        except KoraiAPIError as exc:
            if exc.status_code in (404, 405, 501):
                # TODO(cloud): /tenant/organizations endpoint missing.
                org = await self.get_current()
                return [org]
            raise
        items = data.get("organizations", []) if isinstance(data, dict) else []
        return [Organization(**i) for i in items if isinstance(i, dict)]

    async def switch_to(self, organization_id: str) -> None:
        """Switch session to a different organization.

        Today this only mutates the client-side ``organization_id``
        header — the orchestrator does not re-issue a JWT scoped to the
        new tenant. When ``POST /tenant/switch`` ships, this method
        will additionally store the freshly-issued tokens.
        """
        self._client.organization_id = organization_id
        try:
            data = await self._client._request(
                "POST",
                "/tenant/switch",
                json_body={"organization_id": organization_id},
            )
        except KoraiAPIError as exc:
            if exc.status_code in (404, 405, 501):
                # TODO(cloud): /tenant/switch endpoint missing — header-only.
                return
            raise
        if isinstance(data, dict):
            access = data.get("access_token") or data.get("token")
            if isinstance(access, str):
                self._client.set_tokens(access, data.get("refresh_token") or access)

    # ------------------------------------------------------------------
    # Members + invites — pending Cloud endpoints
    # ------------------------------------------------------------------

    async def list_members(self) -> list[Membership]:
        """List members of the current organization (admin only).

        TODO(cloud): endpoint ``GET /tenant/members`` is not yet
        exposed. Will be implemented when the Cloud API ships.
        """
        try:
            data = await self._client._request("GET", "/tenant/members")
        except KoraiAPIError as exc:
            if exc.status_code in (404, 405, 501):
                raise NotImplementedError(
                    "Pending Cloud API endpoint: GET /tenant/members"
                ) from exc
            raise
        items = data.get("members", []) if isinstance(data, dict) else []
        return [Membership(**i) for i in items if isinstance(i, dict)]

    async def invite_member(
        self,
        email: str,
        role: Literal["admin", "partner", "collaborator", "accountant", "reader"],
    ) -> None:
        """Invite someone to the current organization.

        TODO(cloud): endpoint ``POST /tenant/invite`` is not yet
        exposed.
        """
        try:
            await self._client._request(
                "POST",
                "/tenant/invite",
                json_body={"email": email, "role": role},
            )
        except KoraiAPIError as exc:
            if exc.status_code in (404, 405, 501):
                raise NotImplementedError(
                    "Pending Cloud API endpoint: POST /tenant/invite"
                ) from exc
            raise


__all__ = ["Membership", "Organization", "TenantModule"]
