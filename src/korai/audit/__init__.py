"""Audit module — append-only signed audit log.

Generic re-implementation of the chain pattern used in
``vertical-fiduciaire/backend/services/audit.py``: each entry stores
``prev_hash`` / ``row_hash`` (SHA-256 chained) and an optional HMAC
``signature`` keyed off ``KoraiClient.audit_secret``.

Two storage backends are supported:

* **InMemoryAuditStore** — default. Zero deps. Useful for tests, quick
  prototypes, and apps that re-export to a database themselves.
* **SQLAlchemyAuditStore** — opt-in, lazily imported from the
  ``korai[sqlalchemy]`` extra. Persists to any SQLAlchemy-supported
  database (Postgres, SQLite). The table is auto-created on first use.

Use cases
---------

Audit logging for compliance (OAR / EXPERTsuisse / FINMA in Switzerland,
ISO 27001, etc). Apps log every privileged operation; a regulator can
later run :meth:`AuditModule.verify_chain` to detect tampering and
:meth:`AuditModule.export` to extract the full trail in CSV or JSON.

Example::

    await client.audit.log(
        "dossier.created",
        user_id="u_123",
        resource_type="dossier",
        resource_id="d_456",
        payload={"name": "Acme SA"},
    )
    result = await client.audit.verify_chain()
    assert result.is_valid
"""

from __future__ import annotations

import asyncio
import csv
import hashlib
import hmac
import io
import json
import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from korai._errors import KoraiConfigError

if TYPE_CHECKING:
    from korai._client import KoraiClient


# ───────────────────────────────────────────────────────────────────────
# Models
# ───────────────────────────────────────────────────────────────────────


class AuditEntry(BaseModel):
    """An audit log entry. The chain fields (``prev_hash``, ``row_hash``,
    ``signature``) are computed by the store on insertion."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    sequence_no: int
    organization_id: str | None = None
    event_type: str
    user_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    ip_address: str | None = None
    severity: str = "info"
    prev_hash: str | None = None
    row_hash: str | None = None
    signature: str | None = None
    created_at: datetime


class ChainVerificationResult(BaseModel):
    """Result of :meth:`AuditModule.verify_chain`."""

    is_valid: bool
    checked_count: int
    first_invalid_sequence: int | None = None
    detail: str | None = None


# ───────────────────────────────────────────────────────────────────────
# Hashing
# ───────────────────────────────────────────────────────────────────────


def _canonical_payload(payload: dict[str, Any]) -> str:
    """Serialize ``payload`` deterministically so hashes are reproducible."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _row_hash(entry: AuditEntry) -> str:
    """Compute the SHA-256 hash of an entry given its predecessor's hash.

    The hash domain mirrors the reference implementation in
    ``vertical-fiduciaire``: it includes every field that should be
    tamper-evident, plus the predecessor ``prev_hash``. The hash is
    deterministic for a given entry so that
    :meth:`AuditModule.verify_chain` can recompute it without state.
    """
    parts: list[str] = [
        entry.prev_hash or "",
        str(entry.sequence_no),
        entry.id,
        entry.organization_id or "",
        entry.event_type,
        entry.user_id or "",
        entry.resource_type or "",
        entry.resource_id or "",
        entry.ip_address or "",
        entry.severity,
        _canonical_payload(entry.payload),
        entry.created_at.replace(microsecond=0).isoformat(),
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _sign(row_hash: str, secret: bytes | None) -> str | None:
    if not secret:
        return None
    return hmac.new(secret, row_hash.encode("utf-8"), hashlib.sha256).hexdigest()


# ───────────────────────────────────────────────────────────────────────
# Storage backends
# ───────────────────────────────────────────────────────────────────────


class AuditStore(ABC):
    """Abstract storage backend for audit entries."""

    @abstractmethod
    async def append(self, entry: AuditEntry) -> AuditEntry: ...

    @abstractmethod
    async def list(
        self,
        organization_id: str | None,
        event_type: str | None,
        resource_id: str | None,
        from_date: datetime | None,
        to_date: datetime | None,
        limit: int,
    ) -> list[AuditEntry]: ...

    @abstractmethod
    async def last_for_org(self, organization_id: str | None) -> AuditEntry | None: ...

    @abstractmethod
    async def all_for_org(self, organization_id: str | None) -> list[AuditEntry]: ...


class InMemoryAuditStore(AuditStore):
    """Simple list-backed store. Coroutine-safe via :class:`asyncio.Lock`.

    The lock serializes all mutations and reads against the underlying list
    so that concurrent ``audit.log()`` calls cannot interleave and produce
    duplicate ``sequence_no`` values, which would invalidate the chain
    hash. Reads also acquire the lock so iterators don't see torn writes.
    """

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []
        self._lock = asyncio.Lock()

    async def append(self, entry: AuditEntry) -> AuditEntry:
        async with self._lock:
            self._entries.append(entry)
            return entry

    async def list(
        self,
        organization_id: str | None,
        event_type: str | None,
        resource_id: str | None,
        from_date: datetime | None,
        to_date: datetime | None,
        limit: int,
    ) -> list[AuditEntry]:
        async with self._lock:
            # Snapshot under the lock so the returned list is stable even
            # if more entries land afterwards.
            entries_snapshot = list(self._entries)
        out: list[AuditEntry] = []
        for e in entries_snapshot:
            if organization_id and e.organization_id != organization_id:
                continue
            if event_type and e.event_type != event_type:
                continue
            if resource_id and e.resource_id != resource_id:
                continue
            if from_date and e.created_at < from_date:
                continue
            if to_date and e.created_at > to_date:
                continue
            out.append(e)
            if len(out) >= limit:
                break
        return out

    async def last_for_org(self, organization_id: str | None) -> AuditEntry | None:
        async with self._lock:
            for entry in reversed(self._entries):
                if entry.organization_id == organization_id:
                    return entry
            return None

    async def all_for_org(self, organization_id: str | None) -> list[AuditEntry]:
        async with self._lock:
            return [e for e in self._entries if e.organization_id == organization_id]


class SQLAlchemyAuditStore(AuditStore):
    """Persistent store using a SQLAlchemy async engine.

    Lazily imports SQLAlchemy + a dialect driver. Enable with::

        client = KoraiClient(db_url="sqlite+aiosqlite:///./korai_audit.db")

    The table is created on first :meth:`append`. Schema mirrors the
    fields of :class:`AuditEntry`.
    """

    def __init__(self, db_url: str) -> None:
        try:
            from sqlalchemy import (  # noqa: PLC0415
                JSON,
                Column,
                DateTime,
                Integer,
                MetaData,
                String,
                Table,
                Text,
                and_,
                select,
            )
            from sqlalchemy.ext.asyncio import (  # noqa: PLC0415
                AsyncEngine,
                create_async_engine,
            )
        except ImportError as exc:  # pragma: no cover - import-time only
            raise KoraiConfigError(
                "SQLAlchemy is not installed. Install with `pip install korai[sqlalchemy]`."
            ) from exc

        self._select = select
        self._and = and_
        self._engine: AsyncEngine = create_async_engine(db_url, future=True)
        self._metadata = MetaData()
        self._table = Table(
            "korai_audit_entries",
            self._metadata,
            Column("id", String(64), primary_key=True),
            Column("sequence_no", Integer, nullable=False, index=True),
            Column("organization_id", String(64), nullable=True, index=True),
            Column("event_type", String(128), nullable=False, index=True),
            Column("user_id", String(64), nullable=True),
            Column("resource_type", String(64), nullable=True),
            Column("resource_id", String(64), nullable=True, index=True),
            Column("payload", JSON, nullable=False),
            Column("ip_address", String(45), nullable=True),
            Column("severity", String(16), nullable=False, default="info"),
            Column("prev_hash", String(64), nullable=True),
            Column("row_hash", String(64), nullable=True),
            Column("signature", Text, nullable=True),
            Column("created_at", DateTime(timezone=True), nullable=False),
        )
        self._initialized = False

    async def _ensure_schema(self) -> None:
        if self._initialized:
            return
        async with self._engine.begin() as conn:
            await conn.run_sync(self._metadata.create_all)
        self._initialized = True

    async def append(self, entry: AuditEntry) -> AuditEntry:
        await self._ensure_schema()
        async with self._engine.begin() as conn:
            await conn.execute(
                self._table.insert().values(**_entry_to_row(entry))
            )
        return entry

    async def list(
        self,
        organization_id: str | None,
        event_type: str | None,
        resource_id: str | None,
        from_date: datetime | None,
        to_date: datetime | None,
        limit: int,
    ) -> list[AuditEntry]:
        await self._ensure_schema()
        stmt = self._select(self._table).order_by(self._table.c.sequence_no.asc())
        clauses = []
        if organization_id is not None:
            clauses.append(self._table.c.organization_id == organization_id)
        if event_type is not None:
            clauses.append(self._table.c.event_type == event_type)
        if resource_id is not None:
            clauses.append(self._table.c.resource_id == resource_id)
        if from_date is not None:
            clauses.append(self._table.c.created_at >= from_date)
        if to_date is not None:
            clauses.append(self._table.c.created_at <= to_date)
        if clauses:
            stmt = stmt.where(self._and(*clauses))
        stmt = stmt.limit(limit)
        async with self._engine.begin() as conn:
            res = await conn.execute(stmt)
            rows = res.mappings().all()
        return [_row_to_entry(dict(r)) for r in rows]

    async def last_for_org(self, organization_id: str | None) -> AuditEntry | None:
        await self._ensure_schema()
        stmt = (
            self._select(self._table)
            .order_by(self._table.c.sequence_no.desc())
            .limit(1)
        )
        if organization_id is not None:
            stmt = stmt.where(self._table.c.organization_id == organization_id)
        async with self._engine.begin() as conn:
            res = await conn.execute(stmt)
            row = res.mappings().first()
        return _row_to_entry(dict(row)) if row else None

    async def all_for_org(self, organization_id: str | None) -> list[AuditEntry]:
        await self._ensure_schema()
        stmt = self._select(self._table).order_by(
            self._table.c.sequence_no.asc()
        )
        if organization_id is not None:
            stmt = stmt.where(self._table.c.organization_id == organization_id)
        async with self._engine.begin() as conn:
            res = await conn.execute(stmt)
            rows = res.mappings().all()
        return [_row_to_entry(dict(r)) for r in rows]


def _entry_to_row(entry: AuditEntry) -> dict[str, Any]:
    return {
        "id": entry.id,
        "sequence_no": entry.sequence_no,
        "organization_id": entry.organization_id,
        "event_type": entry.event_type,
        "user_id": entry.user_id,
        "resource_type": entry.resource_type,
        "resource_id": entry.resource_id,
        "payload": entry.payload,
        "ip_address": entry.ip_address,
        "severity": entry.severity,
        "prev_hash": entry.prev_hash,
        "row_hash": entry.row_hash,
        "signature": entry.signature,
        "created_at": entry.created_at,
    }


def _row_to_entry(row: dict[str, Any]) -> AuditEntry:
    raw_created = row.get("created_at")
    if isinstance(raw_created, str):
        raw_created = datetime.fromisoformat(raw_created)
    if isinstance(raw_created, datetime) and raw_created.tzinfo is None:
        # SQLite stores naive datetimes — re-attach UTC so the
        # round-tripped hash matches the originally-computed hash.
        raw_created = raw_created.replace(tzinfo=UTC)
    return AuditEntry(
        id=row["id"],
        sequence_no=row["sequence_no"],
        organization_id=row.get("organization_id"),
        event_type=row["event_type"],
        user_id=row.get("user_id"),
        resource_type=row.get("resource_type"),
        resource_id=row.get("resource_id"),
        payload=row.get("payload") or {},
        ip_address=row.get("ip_address"),
        severity=row.get("severity") or "info",
        prev_hash=row.get("prev_hash"),
        row_hash=row.get("row_hash"),
        signature=row.get("signature"),
        created_at=raw_created or datetime.now(UTC),
    )


# ───────────────────────────────────────────────────────────────────────
# Module
# ───────────────────────────────────────────────────────────────────────


class AuditModule:
    """Append-only audit log operations.

    Apps log events here; verification + export are exposed for
    compliance. The module's storage backend is selected by the parent
    :class:`KoraiClient`'s ``db_url`` argument.

    Storage selection:

    * ``client.db_url is None`` → :class:`InMemoryAuditStore`
    * ``client.db_url`` set → :class:`SQLAlchemyAuditStore`

    Apps that want to inject their own SQLAlchemy session can pass a
    custom store via :meth:`set_store`.
    """

    def __init__(self, client: KoraiClient) -> None:
        self._client = client
        self._store: AuditStore | None = None

    def set_store(self, store: AuditStore) -> None:
        """Override the default backend (e.g. when the host app already
        owns a SQLAlchemy session)."""
        self._store = store

    @property
    def store(self) -> AuditStore:
        if self._store is None:
            if self._client.db_url:
                self._store = SQLAlchemyAuditStore(self._client.db_url)
            else:
                self._store = InMemoryAuditStore()
        return self._store

    async def log(
        self,
        event_type: str,
        *,
        user_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        payload: dict[str, Any] | None = None,
        severity: str = "info",
        ip_address: str | None = None,
        organization_id: str | None = None,
    ) -> AuditEntry:
        """Append an entry to the audit log.

        Computes the chained hash and HMAC signature automatically.

        Args:
            event_type: Machine-readable event id, e.g. ``"dossier.created"``.
            user_id: Optional actor.
            resource_type: e.g. ``"dossier"``.
            resource_id: e.g. ``"d_123"``.
            payload: Free-form, JSON-serializable data.
            severity: One of ``info`` | ``warning`` | ``critical``.
            ip_address: Optional caller IP.
            organization_id: Override the client-level
                ``organization_id`` (defaults to it if unset).

        Example::

            await client.audit.log(
                "dossier.created",
                user_id="u_42",
                payload={"name": "Acme SA"},
            )
        """
        org_id = organization_id or self._client.organization_id
        last = await self.store.last_for_org(org_id)
        sequence_no = (last.sequence_no + 1) if last else 1
        prev_hash = last.row_hash if last else None
        entry = AuditEntry(
            id=str(uuid.uuid4()),
            sequence_no=sequence_no,
            organization_id=org_id,
            event_type=event_type,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            payload=payload or {},
            ip_address=ip_address,
            severity=severity,
            prev_hash=prev_hash,
            row_hash=None,
            signature=None,
            # Microseconds dropped so the value is stable across stores
            # (SQLite/Postgres round-trips can lose sub-second precision).
            created_at=datetime.now(UTC).replace(microsecond=0),
        )
        entry.row_hash = _row_hash(entry)
        entry.signature = _sign(entry.row_hash, self._client.audit_secret)
        return await self.store.append(entry)

    async def verify_chain(
        self,
        organization_id: str | None = None,
    ) -> ChainVerificationResult:
        """Re-compute hashes for the entire chain. Detect tampering.

        Walks the chain in ``sequence_no`` order. For each entry, the
        previous ``row_hash`` must match the current ``prev_hash``, and
        re-computing :func:`_row_hash` on the entry must equal the
        stored ``row_hash``. Optional HMAC signatures are verified when
        the client has an ``audit_secret``.
        """
        org_id = organization_id or self._client.organization_id
        entries = await self.store.all_for_org(org_id)
        previous: AuditEntry | None = None
        for entry in entries:
            if previous is None:
                if entry.prev_hash:
                    return ChainVerificationResult(
                        is_valid=False,
                        checked_count=0,
                        first_invalid_sequence=entry.sequence_no,
                        detail="first entry has non-empty prev_hash",
                    )
            else:
                if entry.prev_hash != previous.row_hash:
                    return ChainVerificationResult(
                        is_valid=False,
                        checked_count=entry.sequence_no - 1,
                        first_invalid_sequence=entry.sequence_no,
                        detail="prev_hash does not match previous row_hash",
                    )
                if entry.sequence_no != previous.sequence_no + 1:
                    return ChainVerificationResult(
                        is_valid=False,
                        checked_count=entry.sequence_no - 1,
                        first_invalid_sequence=entry.sequence_no,
                        detail="sequence_no skipped",
                    )
            expected_hash = _row_hash(entry)
            if entry.row_hash != expected_hash:
                return ChainVerificationResult(
                    is_valid=False,
                    checked_count=entry.sequence_no - 1,
                    first_invalid_sequence=entry.sequence_no,
                    detail="row_hash mismatch (data tampered)",
                )
            if self._client.audit_secret is not None:
                expected_sig = _sign(entry.row_hash or "", self._client.audit_secret)
                if entry.signature != expected_sig:
                    return ChainVerificationResult(
                        is_valid=False,
                        checked_count=entry.sequence_no - 1,
                        first_invalid_sequence=entry.sequence_no,
                        detail="HMAC signature mismatch",
                    )
            previous = entry
        return ChainVerificationResult(
            is_valid=True,
            checked_count=len(entries),
        )

    async def list_entries(
        self,
        *,
        event_type: str | None = None,
        resource_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        limit: int = 100,
        organization_id: str | None = None,
    ) -> list[AuditEntry]:
        """Query the audit log."""
        org_id = organization_id or self._client.organization_id
        return await self.store.list(
            organization_id=org_id,
            event_type=event_type,
            resource_id=resource_id,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
        )

    async def export(
        self,
        *,
        format: str = "csv",  # noqa: A002 — public API
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        organization_id: str | None = None,
    ) -> bytes:
        """Export the audit log as CSV or JSON bytes.

        Args:
            format: ``"csv"`` (one row per entry, payload JSON-encoded)
                or ``"json"`` (a JSON array).
            from_date / to_date: Optional time bounds.

        Example::

            data = await client.audit.export(format="csv")
            Path("audit.csv").write_bytes(data)
        """
        if format not in ("csv", "json"):
            raise ValueError("format must be 'csv' or 'json'")
        entries = await self.list_entries(
            from_date=from_date,
            to_date=to_date,
            limit=10**9,
            organization_id=organization_id,
        )
        if format == "json":
            return json.dumps(
                [e.model_dump(mode="json") for e in entries],
                indent=2,
                ensure_ascii=False,
            ).encode("utf-8")
        # CSV
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(
            [
                "sequence_no",
                "id",
                "organization_id",
                "event_type",
                "user_id",
                "resource_type",
                "resource_id",
                "severity",
                "ip_address",
                "payload",
                "prev_hash",
                "row_hash",
                "signature",
                "created_at",
            ]
        )
        for e in entries:
            writer.writerow(
                [
                    e.sequence_no,
                    e.id,
                    e.organization_id or "",
                    e.event_type,
                    e.user_id or "",
                    e.resource_type or "",
                    e.resource_id or "",
                    e.severity,
                    e.ip_address or "",
                    json.dumps(e.payload, ensure_ascii=False),
                    e.prev_hash or "",
                    e.row_hash or "",
                    e.signature or "",
                    e.created_at.isoformat(),
                ]
            )
        return buf.getvalue().encode("utf-8")


__all__ = [
    "AuditEntry",
    "AuditModule",
    "AuditStore",
    "ChainVerificationResult",
    "InMemoryAuditStore",
    "SQLAlchemyAuditStore",
]
