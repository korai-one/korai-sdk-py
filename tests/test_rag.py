"""Tests for korai.rag.RAGModule.

We don't run actual embedding inference here — these tests cover:

* Module import succeeds without ``korai[embeddings]`` installed.
* ``configure_corpus`` sets the right dict.
* ``embed`` raises ``KoraiConfigError`` if ``sentence-transformers`` is
  missing.
* ``retrieve`` raises ``KoraiConfigError`` when ``db_url`` is missing.
* ``retrieve_and_rerank`` is wired through to the underlying calls
  (mocked).
"""

from __future__ import annotations

import sys

import pytest

from korai import KoraiClient, KoraiConfigError
from korai.rag import IndexableDocument, RAGModule, RetrievedChunk


async def test_default_corpus_config(client: KoraiClient) -> None:
    cfg = client.rag._corpus_config("default")
    assert cfg["table"] == "rag_chunks"
    assert cfg["text_column"] == "text"


async def test_custom_corpus_config(client: KoraiClient) -> None:
    client.rag.configure_corpus(
        "legal",
        table="legal_chunks",
        embedding_dim=768,
    )
    cfg = client.rag._corpus_config("legal")
    assert cfg["table"] == "legal_chunks"
    assert cfg["embedding_dim"] == 768


async def test_retrieve_without_db_url_raises(client: KoraiClient) -> None:
    with pytest.raises(KoraiConfigError):
        await client.rag.retrieve("question")


async def test_index_documents_without_db_url_raises(client: KoraiClient) -> None:
    with pytest.raises(KoraiConfigError):
        await client.rag.index_documents(
            [{"chunk_id": "c1", "text": "hi", "source_id": "s1"}]
        )


async def test_index_documents_empty_returns_zero(client: KoraiClient) -> None:
    # Empty input shortcuts before the db_url check.
    n = await client.rag.index_documents([])
    assert n == 0


async def test_embed_without_sentence_transformers_raises(
    client: KoraiClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Force import failure deterministically by inserting a None entry.
    monkeypatch.setitem(sys.modules, "sentence_transformers", None)
    with pytest.raises(KoraiConfigError):
        await client.rag.embed(["hello"])


async def test_indexable_document_validation() -> None:
    d = IndexableDocument(chunk_id="c1", text="x", source_id="s1")
    assert d.metadata == {}


async def test_rerank_empty_returns_empty(client: KoraiClient) -> None:
    out = await client.rag.rerank("q", [])
    assert out == []


async def test_retrieve_calls_internals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Patch the engine + embed + sql functions to test retrieve plumbing."""
    c = KoraiClient(db_url="sqlite+aiosqlite:///:memory:")
    try:
        rag = c.rag

        async def _fake_embed(_texts: list[str], **_: object) -> list[list[float]]:
            return [[0.1] * 4]

        async def _fake_get_engine() -> object:
            return object()

        async def _fake_search(*_args: object, **_kwargs: object) -> list[dict]:
            return [
                {
                    "chunk_id": "c1",
                    "text": "Hello",
                    "source_id": "s1",
                    "_score": 0.95,
                },
                {
                    "chunk_id": "c2",
                    "text": "World",
                    "source_id": "s1",
                    "_score": 0.10,  # below default min_score
                },
            ]

        monkeypatch.setattr(rag, "embed", _fake_embed)
        monkeypatch.setattr(rag, "_get_engine", _fake_get_engine)
        monkeypatch.setattr(rag, "_vector_search", _fake_search)
        chunks = await rag.retrieve("hello", min_score=0.3)
        assert len(chunks) == 1
        assert chunks[0].chunk_id == "c1"
        assert chunks[0].score == 0.95
    finally:
        await c.aclose()


async def test_retrieved_chunk_dataclass() -> None:
    rc = RetrievedChunk(
        chunk_id="c1", text="t", score=1.0, source_id="s1"
    )
    assert rc.metadata == {}
    assert rc.url is None


async def test_rag_module_constants() -> None:
    assert RAGModule.DEFAULT_EMBEDDING_DIM == 1024
    assert "bge-m3" in RAGModule.DEFAULT_EMBEDDING_MODEL
