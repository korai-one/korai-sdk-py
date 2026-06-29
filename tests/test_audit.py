"""Tests for korai.audit.AuditModule."""

from __future__ import annotations

import csv
import io
import json

import pytest

from korai import KoraiClient
from korai.audit import (
    AuditEntry,
    ChainVerificationResult,
    InMemoryAuditStore,
)


async def test_log_creates_entry(signed_client: KoraiClient) -> None:
    entry = await signed_client.audit.log(
        "dossier.created",
        user_id="u-1",
        resource_type="dossier",
        resource_id="d-1",
        payload={"name": "Acme SA"},
    )
    assert isinstance(entry, AuditEntry)
    assert entry.sequence_no == 1
    assert entry.event_type == "dossier.created"
    assert entry.row_hash is not None
    assert entry.signature is not None  # secret was set


async def test_chain_grows(signed_client: KoraiClient) -> None:
    e1 = await signed_client.audit.log("a", payload={"i": 1})
    e2 = await signed_client.audit.log("b", payload={"i": 2})
    e3 = await signed_client.audit.log("c", payload={"i": 3})
    assert e2.prev_hash == e1.row_hash
    assert e3.prev_hash == e2.row_hash
    assert e3.sequence_no == 3


async def test_verify_chain_ok(signed_client: KoraiClient) -> None:
    for i in range(5):
        await signed_client.audit.log("event", payload={"i": i})
    result = await signed_client.audit.verify_chain()
    assert isinstance(result, ChainVerificationResult)
    assert result.is_valid
    assert result.checked_count == 5


async def test_verify_chain_detects_tampering(signed_client: KoraiClient) -> None:
    e1 = await signed_client.audit.log("a", payload={"i": 1})
    e2 = await signed_client.audit.log("b", payload={"i": 2})
    # Tamper with the payload of entry e1 in the in-memory store.
    store = signed_client.audit.store
    assert isinstance(store, InMemoryAuditStore)
    store._entries[0].payload = {"i": 999}
    result = await signed_client.audit.verify_chain()
    assert not result.is_valid
    assert result.first_invalid_sequence == e1.sequence_no
    assert "row_hash mismatch" in (result.detail or "")
    # e2 stayed untouched in the in-memory store but the chain breaks at e1.
    assert e2.prev_hash == e1.row_hash


async def test_verify_chain_detects_signature_break() -> None:
    c = KoraiClient(audit_secret=b"secret-A")
    try:
        await c.audit.log("x")
        await c.audit.log("y")
        # Substitute a different secret retrospectively.
        c.audit_secret = b"secret-B"
        result = await c.audit.verify_chain()
        assert not result.is_valid
        assert "HMAC" in (result.detail or "")
    finally:
        await c.aclose()


async def test_list_entries_filter() -> None:
    c = KoraiClient()
    try:
        await c.audit.log("alpha")
        await c.audit.log("beta")
        await c.audit.log("alpha")
        all_entries = await c.audit.list_entries()
        assert len(all_entries) == 3
        only_alpha = await c.audit.list_entries(event_type="alpha")
        assert len(only_alpha) == 2
        for e in only_alpha:
            assert e.event_type == "alpha"
    finally:
        await c.aclose()


async def test_export_csv() -> None:
    c = KoraiClient()
    try:
        await c.audit.log("e", payload={"k": "v1"})
        await c.audit.log("e", payload={"k": "v2"})
        data = await c.audit.export(format="csv")
        text = data.decode("utf-8")
        rows = list(csv.reader(io.StringIO(text)))
        assert rows[0][0] == "sequence_no"
        assert len(rows) == 3
    finally:
        await c.aclose()


async def test_export_json() -> None:
    c = KoraiClient()
    try:
        await c.audit.log("e", payload={"k": "v"})
        data = await c.audit.export(format="json")
        decoded = json.loads(data.decode("utf-8"))
        assert isinstance(decoded, list)
        assert len(decoded) == 1
        assert decoded[0]["event_type"] == "e"
    finally:
        await c.aclose()


async def test_export_unknown_format_raises() -> None:
    c = KoraiClient()
    try:
        with pytest.raises(ValueError):
            await c.audit.export(format="xml")
    finally:
        await c.aclose()


async def test_inmemory_store_directly() -> None:
    s = InMemoryAuditStore()
    assert await s.last_for_org(None) is None
    assert await s.all_for_org(None) == []


async def test_audit_log_uses_organization_id_from_client() -> None:
    c = KoraiClient(organization_id="org-xyz")
    try:
        e = await c.audit.log("evt")
        assert e.organization_id == "org-xyz"
    finally:
        await c.aclose()


async def test_sqlalchemy_store_roundtrip() -> None:
    pytest.importorskip("sqlalchemy")
    pytest.importorskip("aiosqlite")
    c = KoraiClient(
        db_url="sqlite+aiosqlite:///:memory:",
        organization_id="org-sql",
        audit_secret=b"k",
    )
    try:
        for i in range(3):
            await c.audit.log("event", payload={"i": i})
        result = await c.audit.verify_chain()
        assert result.is_valid
        assert result.checked_count == 3
        listed = await c.audit.list_entries()
        assert len(listed) == 3
    finally:
        await c.aclose()
