"""RAG module — vector retrieval, reranking, citation extraction.

Provides primitives for building RAG over a custom corpus stored in
SQLAlchemy/Postgres+pgvector. Designed so an app can plug in its own
table schema (corpus name → table name) and avoid a hard dependency on
any specific embedding provider.

Optional features that need extras:

* Embedding (``bge-m3``) and reranking (``bge-reranker-v2-m3``) require
  ``korai[embeddings]`` (which pulls in ``sentence-transformers``). If
  the extras are not installed, :meth:`embed` and :meth:`rerank` raise
  :class:`KoraiConfigError`.
* :meth:`retrieve` and :meth:`index_documents` need ``korai[sqlalchemy]``.

The module is designed to **degrade gracefully** when extras are
missing — instantiating the module is always cheap; expensive imports
happen lazily on the first call.

Example::

    from korai import KoraiClient

    client = KoraiClient(db_url="postgresql+asyncpg://user:pwd@host/db")
    chunks = await client.rag.retrieve("Comment fonctionne la TVA suisse ?")
    top = await client.rag.rerank(query, chunks, top_n=5)
"""

from __future__ import annotations

import asyncio
import re
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field

from korai._errors import KoraiConfigError, KoraiValidationError

# Strict regex for table / column / schema identifiers. We disallow
# anything that isn't ASCII alphanumeric or underscore so we can safely
# interpolate these names into SQL strings later (pgvector lookups need
# raw column names — not all dialects support quoted parameters here).
# This guards against SQL injection if an app populates the corpus
# config from environment variables or untrusted config files.
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")


def _validate_identifier(value: str | None, field: str) -> str | None:
    """Reject SQL identifiers that don't match :data:`_IDENT_RE`.

    Pass-through ``None`` (used for optional column names). Raises
    :class:`KoraiValidationError` with a clear message for any other
    invalid value, including the rejected ``field`` name so the caller
    can fix their :meth:`RAGModule.configure_corpus` call.
    """
    if value is None:
        return None
    if not isinstance(value, str) or not _IDENT_RE.match(value):
        raise KoraiValidationError(
            f"RAG corpus '{field}' must match {_IDENT_RE.pattern} "
            f"(got {value!r}). Identifiers are interpolated into SQL "
            f"so this validation is a defense-in-depth against SQL "
            f"injection if config is sourced from env or user input."
        )
    return value

if TYPE_CHECKING:
    from korai._client import KoraiClient


# ───────────────────────────────────────────────────────────────────────
# Models
# ───────────────────────────────────────────────────────────────────────


class RetrievedChunk(BaseModel):
    """A chunk returned by retrieval."""

    chunk_id: str
    text: str
    score: float
    source_id: str
    citation: str | None = None
    language: str | None = None
    jurisdiction: str | None = None
    url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IndexableDocument(BaseModel):
    """A document to be indexed."""

    chunk_id: str
    text: str
    source_id: str
    citation: str | None = None
    language: str | None = None
    jurisdiction: str | None = None
    url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# ───────────────────────────────────────────────────────────────────────
# Module
# ───────────────────────────────────────────────────────────────────────


class RAGModule:
    """RAG retrieval primitives.

    Configurable via :meth:`configure_corpus` (table name, embedding
    column, dimensions). Defaults match the schema used by
    ``vertical-fiduciaire``.
    """

    # Default embedding model + dimensions (bge-m3).
    DEFAULT_EMBEDDING_MODEL = "BAAI/bge-m3"
    DEFAULT_RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
    DEFAULT_EMBEDDING_DIM = 1024

    def __init__(self, client: KoraiClient) -> None:
        self._client = client
        self._embedder: Any = None
        self._reranker: Any = None
        self._corpora: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Corpus configuration
    # ------------------------------------------------------------------

    def configure_corpus(
        self,
        name: str = "default",
        *,
        table: str = "rag_chunks",
        text_column: str = "text",
        embedding_column: str = "embedding",
        id_column: str = "chunk_id",
        source_column: str = "source_id",
        citation_column: str | None = "citation",
        language_column: str | None = "language",
        jurisdiction_column: str | None = "jurisdiction",
        url_column: str | None = "url",
        metadata_column: str | None = "metadata",
        embedding_dim: int = DEFAULT_EMBEDDING_DIM,
    ) -> None:
        """Register a corpus mapping name → table schema.

        Defaults match the layout of ``vertical-fiduciaire`` but every
        column is overridable. All identifiers (table + columns) are
        validated against a strict regex (``^[A-Za-z_][A-Za-z0-9_]{0,62}$``)
        before being stored — they get interpolated into SQL strings, so
        the regex is a defense-in-depth against SQL injection when the
        corpus config comes from env vars or user input.
        """
        self._corpora[name] = {
            "table": _validate_identifier(table, "table"),
            "text_column": _validate_identifier(text_column, "text_column"),
            "embedding_column": _validate_identifier(
                embedding_column, "embedding_column"
            ),
            "id_column": _validate_identifier(id_column, "id_column"),
            "source_column": _validate_identifier(source_column, "source_column"),
            "citation_column": _validate_identifier(
                citation_column, "citation_column"
            ),
            "language_column": _validate_identifier(
                language_column, "language_column"
            ),
            "jurisdiction_column": _validate_identifier(
                jurisdiction_column, "jurisdiction_column"
            ),
            "url_column": _validate_identifier(url_column, "url_column"),
            "metadata_column": _validate_identifier(
                metadata_column, "metadata_column"
            ),
            "embedding_dim": embedding_dim,
        }

    def _corpus_config(self, name: str) -> dict[str, Any]:
        if name not in self._corpora:
            self.configure_corpus(name)
        return self._corpora[name]

    # ------------------------------------------------------------------
    # Embedding (lazy bge-m3)
    # ------------------------------------------------------------------

    def _ensure_embedder(self) -> Any:
        if self._embedder is not None:
            return self._embedder
        try:
            from sentence_transformers import SentenceTransformer  # noqa: PLC0415
        except ImportError as exc:  # pragma: no cover
            raise KoraiConfigError(
                "Embeddings require the 'embeddings' extra. "
                "Install with `pip install korai[embeddings]`."
            ) from exc
        self._embedder = SentenceTransformer(self.DEFAULT_EMBEDDING_MODEL)
        return self._embedder

    async def embed(
        self,
        texts: list[str],
        *,
        normalize: bool = True,
    ) -> list[list[float]]:
        """Embed a batch of texts. Uses ``bge-m3`` by default.

        Runs the encoder in a thread pool so it doesn't block the event
        loop. Returns L2-normalized vectors when ``normalize=True`` (so
        cosine similarity == dot product).

        Raises :class:`KoraiConfigError` if the ``embeddings`` extra is
        not installed.
        """
        if not texts:
            return []
        embedder = self._ensure_embedder()

        def _encode() -> list[list[float]]:
            vecs = embedder.encode(
                texts,
                normalize_embeddings=normalize,
                convert_to_numpy=True,
            )
            return [list(map(float, v)) for v in vecs]

        return await asyncio.to_thread(_encode)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    async def retrieve(
        self,
        query: str,
        *,
        corpus: str = "default",
        languages: list[Literal["fr", "de", "it", "en"]] | None = None,
        jurisdictions: list[str] | None = None,
        top_k: int = 30,
        min_score: float = 0.3,
    ) -> list[RetrievedChunk]:
        """Vector retrieval over the configured corpus.

        Implements pure vector search via pgvector's ``<=>`` (cosine
        distance). For hybrid (vector + BM25) you can layer BM25 on top
        of the returned chunks in your app — the SDK keeps the primitive
        surface minimal.

        Returns chunks with score ``= 1 - cosine_distance``. Filters out
        anything below ``min_score``.
        """
        if not self._client.db_url:
            raise KoraiConfigError(
                "RAG.retrieve requires a `db_url` on KoraiClient."
            )
        cfg = self._corpus_config(corpus)
        engine = await self._get_engine()
        embeddings = await self.embed([query])
        query_vec = embeddings[0]
        rows = await self._vector_search(
            engine,
            cfg,
            query_vec,
            top_k=top_k,
            languages=languages,
            jurisdictions=jurisdictions,
        )
        chunks: list[RetrievedChunk] = []
        for row in rows:
            score = float(row.get("_score", 0.0))
            if score < min_score:
                continue
            chunks.append(
                RetrievedChunk(
                    chunk_id=str(row.get(cfg["id_column"], "")),
                    text=str(row.get(cfg["text_column"], "")),
                    score=score,
                    source_id=str(row.get(cfg["source_column"], "")),
                    citation=row.get(cfg["citation_column"])
                    if cfg["citation_column"]
                    else None,
                    language=row.get(cfg["language_column"])
                    if cfg["language_column"]
                    else None,
                    jurisdiction=row.get(cfg["jurisdiction_column"])
                    if cfg["jurisdiction_column"]
                    else None,
                    url=row.get(cfg["url_column"]) if cfg["url_column"] else None,
                    metadata=row.get(cfg["metadata_column"]) or {}
                    if cfg["metadata_column"]
                    else {},
                )
            )
        return chunks

    async def _vector_search(
        self,
        engine: Any,
        cfg: dict[str, Any],
        query_vec: list[float],
        top_k: int,
        languages: list[str] | None,
        jurisdictions: list[str] | None,
    ) -> list[dict[str, Any]]:
        """Execute the SQL vector search. Isolated so tests can patch."""
        from sqlalchemy import text  # noqa: PLC0415

        cols = [
            cfg["id_column"],
            cfg["text_column"],
            cfg["source_column"],
        ]
        for opt in (
            cfg["citation_column"],
            cfg["language_column"],
            cfg["jurisdiction_column"],
            cfg["url_column"],
            cfg["metadata_column"],
        ):
            if opt:
                cols.append(opt)
        select_clause = ", ".join(cols)
        # Convert vector to pgvector literal.
        vec_literal = "[" + ",".join(f"{x:.8f}" for x in query_vec) + "]"
        # 1 - cosine_distance == cosine similarity score.
        score_expr = (
            f"1 - ({cfg['embedding_column']} <=> '{vec_literal}'::vector)"
        )
        where_clauses: list[str] = []
        params: dict[str, Any] = {"limit": top_k}
        if languages and cfg["language_column"]:
            where_clauses.append(f"{cfg['language_column']} = ANY(:languages)")
            params["languages"] = languages
        if jurisdictions and cfg["jurisdiction_column"]:
            where_clauses.append(
                f"{cfg['jurisdiction_column']} = ANY(:jurisdictions)"
            )
            params["jurisdictions"] = jurisdictions
        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        sql = (
            f"SELECT {select_clause}, {score_expr} AS _score "
            f"FROM {cfg['table']} {where_sql} "
            f"ORDER BY _score DESC LIMIT :limit"
        )
        async with engine.begin() as conn:
            res = await conn.execute(text(sql), params)
            rows = res.mappings().all()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Rerank
    # ------------------------------------------------------------------

    def _ensure_reranker(self) -> Any:
        if self._reranker is not None:
            return self._reranker
        try:
            from sentence_transformers import CrossEncoder  # noqa: PLC0415
        except ImportError as exc:  # pragma: no cover
            raise KoraiConfigError(
                "Reranking requires the 'embeddings' extra. "
                "Install with `pip install korai[embeddings]`."
            ) from exc
        self._reranker = CrossEncoder(self.DEFAULT_RERANKER_MODEL)
        return self._reranker

    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_n: int = 10,
    ) -> list[RetrievedChunk]:
        """Cross-encoder rerank.

        Uses ``bge-reranker-v2-m3`` by default. Replaces ``score`` on
        each chunk with the reranker score and returns the top ``top_n``
        sorted descending.
        """
        if not chunks:
            return []
        reranker = self._ensure_reranker()
        pairs = [[query, c.text] for c in chunks]

        def _score() -> list[float]:
            scores = reranker.predict(pairs)
            return [float(s) for s in scores]

        scores = await asyncio.to_thread(_score)
        ranked = []
        for chunk, score in zip(chunks, scores, strict=False):
            new_chunk = chunk.model_copy(update={"score": score})
            ranked.append(new_chunk)
        ranked.sort(key=lambda c: c.score, reverse=True)
        return ranked[:top_n]

    async def retrieve_and_rerank(
        self,
        query: str,
        *,
        corpus: str = "default",
        languages: list[Literal["fr", "de", "it", "en"]] | None = None,
        jurisdictions: list[str] | None = None,
        top_k: int = 30,
        top_n: int = 10,
        min_score: float = 0.3,
    ) -> list[RetrievedChunk]:
        """Convenience: :meth:`retrieve` + :meth:`rerank` in one call."""
        chunks = await self.retrieve(
            query,
            corpus=corpus,
            languages=languages,
            jurisdictions=jurisdictions,
            top_k=top_k,
            min_score=min_score,
        )
        return await self.rerank(query, chunks, top_n=top_n)

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    async def index_documents(
        self,
        documents: list[dict[str, Any]] | list[IndexableDocument],
        *,
        corpus: str = "default",
    ) -> int:
        """Index a batch of documents into the configured corpus.

        Embeds each ``text`` field and inserts (or upserts) into the
        configured table. Returns the number of indexed documents.

        ``documents`` may be either dicts (must contain ``chunk_id``,
        ``text``, ``source_id``) or :class:`IndexableDocument` instances.
        """
        if not documents:
            return 0
        if not self._client.db_url:
            raise KoraiConfigError(
                "RAG.index_documents requires a `db_url` on KoraiClient."
            )
        normalized: list[IndexableDocument] = []
        for d in documents:
            if isinstance(d, IndexableDocument):
                normalized.append(d)
            else:
                normalized.append(IndexableDocument(**d))
        cfg = self._corpus_config(corpus)
        engine = await self._get_engine()
        embeddings = await self.embed([d.text for d in normalized])
        await self._upsert_documents(engine, cfg, normalized, embeddings)
        return len(normalized)

    async def _upsert_documents(
        self,
        engine: Any,
        cfg: dict[str, Any],
        documents: list[IndexableDocument],
        embeddings: list[list[float]],
    ) -> None:
        """Upsert rows into the configured corpus table."""
        from sqlalchemy import text  # noqa: PLC0415

        cols = [
            cfg["id_column"],
            cfg["text_column"],
            cfg["source_column"],
            cfg["embedding_column"],
        ]
        param_names = [":id", ":text", ":source_id", ":embedding"]
        for opt, name in (
            (cfg["citation_column"], "citation"),
            (cfg["language_column"], "language"),
            (cfg["jurisdiction_column"], "jurisdiction"),
            (cfg["url_column"], "url"),
            (cfg["metadata_column"], "metadata"),
        ):
            if opt:
                cols.append(opt)
                param_names.append(":" + name)
        sql = (
            f"INSERT INTO {cfg['table']} ({', '.join(cols)}) "
            f"VALUES ({', '.join(param_names)}) "
            f"ON CONFLICT ({cfg['id_column']}) DO UPDATE SET "
            f"{cfg['text_column']} = EXCLUDED.{cfg['text_column']}, "
            f"{cfg['embedding_column']} = EXCLUDED.{cfg['embedding_column']}"
        )
        async with engine.begin() as conn:
            for doc, vec in zip(documents, embeddings, strict=False):
                vec_literal = "[" + ",".join(f"{x:.8f}" for x in vec) + "]"
                params: dict[str, Any] = {
                    "id": doc.chunk_id,
                    "text": doc.text,
                    "source_id": doc.source_id,
                    "embedding": vec_literal,
                }
                if cfg["citation_column"]:
                    params["citation"] = doc.citation
                if cfg["language_column"]:
                    params["language"] = doc.language
                if cfg["jurisdiction_column"]:
                    params["jurisdiction"] = doc.jurisdiction
                if cfg["url_column"]:
                    params["url"] = doc.url
                if cfg["metadata_column"]:
                    params["metadata"] = doc.metadata
                await conn.execute(text(sql), params)

    # ------------------------------------------------------------------
    # Engine cache
    # ------------------------------------------------------------------

    _engine_cache: Any = None

    async def _get_engine(self) -> Any:
        if self._engine_cache is not None:
            return self._engine_cache
        try:
            from sqlalchemy.ext.asyncio import create_async_engine  # noqa: PLC0415
        except ImportError as exc:  # pragma: no cover
            raise KoraiConfigError(
                "RAG requires SQLAlchemy. Install with `pip install korai[sqlalchemy]`."
            ) from exc
        self._engine_cache = create_async_engine(self._client.db_url, future=True)  # type: ignore[arg-type]
        return self._engine_cache


__all__ = ["IndexableDocument", "RAGModule", "RetrievedChunk"]
