# korai (Korai Platform SDK for Python)

Async-native Python SDK for the Korai Platform. Build verticales
(Korai Fiduciaire, Korai Avocat, …) on top of Korai Cloud's
OpenAI-compatible inference, multi-tenant auth, and the local
compliance primitives (audit log, RAG, tool registry).

## Installation

Installed directly from the mirror repo (no PyPI yet):

```bash
pip install "git+https://github.com/korai-one/korai-sdk-py@v0.1.0"

# Optional extras
pip install "korai[fastapi] @ git+https://github.com/korai-one/korai-sdk-py@v0.1.0"   # FastAPI helpers
pip install "korai[sqlalchemy] @ git+https://github.com/korai-one/korai-sdk-py@v0.1.0" # ORM extensions (audit + RAG)
pip install "korai[embeddings] @ git+https://github.com/korai-one/korai-sdk-py@v0.1.0" # bge-m3 embedder + reranker
pip install "korai[all] @ git+https://github.com/korai-one/korai-sdk-py@v0.1.0"
```

## Quick start

```python
import asyncio
from korai import KoraiClient
from korai.llm import Message

async def main() -> None:
    async with KoraiClient(api_key="sk-korai-***") as client:
        result = await client.llm.complete(
            messages=[Message(role="user", content="Bonjour Korai")],
            model="claude-opus-4-7",
        )
        print(result.content)

asyncio.run(main())
```

A more complete example combining LLM + audit + tools is in
[`examples/quickstart.py`](examples/quickstart.py).

## Modules

| Module | Status | Description |
|---|---|---|
| `korai.auth` | beta | Login, signup, JWT, current user, API keys |
| `korai.tenant` | partial | Multi-tenant orgs (JWT introspection today) |
| `korai.llm` | beta | Chat completions + SSE streaming + tool round-trip |
| `korai.rag` | beta | pgvector retrieval + bge-m3 / bge-reranker |
| `korai.audit` | beta | Append-only signed audit log (SHA-256 chain + HMAC) |
| `korai.tools` | beta | Pure client-side tool registry + Anthropic/OpenAI schemas |
| `korai.billing` | beta | Credit balance, transactions, Stripe checkout |

**Status legend** : `scaffolded` = interfaces only. `partial` = some
methods working, others stubbed pending Cloud endpoints. `beta` =
working, API may shift before 1.0. `stable` = production-ready.

## Configuration cheat-sheet

```python
client = KoraiClient(
    api_key="sk-korai-...",                   # OR set tokens via auth.login()
    base_url="https://cloud.korai.one",       # default
    timeout=60.0,
    organization_id="org-uuid",               # X-Korai-Organization header
    db_url="postgresql+asyncpg://...",        # for audit + rag
    audit_secret=b"hmac-secret",              # HMAC for audit signatures
)
```

## Error handling

All HTTP errors are typed:

```python
from korai import KoraiAPIError, KoraiAuthError, KoraiRateLimitError

try:
    await client.llm.complete(...)
except KoraiAuthError:
    await client.auth.login(...)
except KoraiRateLimitError as exc:
    await asyncio.sleep(exc.retry_after or 1.0)
except KoraiAPIError as exc:
    print(exc.status_code, exc.message)
```

## Development

```bash
cd korai-platform/packages/sdk-py
uv sync --all-extras
uv run pytest -v
uv run ruff check src tests
uv run mypy src/
```

## Versioning

SemVer 2.0.0. Pre-1.0.0, breaking changes possible between minor versions.

## License

Apache-2.0.
