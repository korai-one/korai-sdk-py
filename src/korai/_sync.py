"""Synchronous Korai client.

:class:`SyncKoraiClient` is a thin **facade** over the async
:class:`korai.KoraiClient`: it drives the async client from a dedicated
event loop running on a daemon thread, so every method can be called from
ordinary synchronous code — including from inside frameworks that already
run their own event loop, where ``asyncio.run`` would fail.

Every async method of the async client and its modules is mirrored
synchronously (coroutines block and return their result; async generators
become plain generators). The **async** :class:`KoraiClient` remains the
typed source of truth for method signatures — the sync surface mirrors it
1:1, so see those modules for parameter docs.

Example::

    from korai import SyncKoraiClient

    with SyncKoraiClient(api_key="sk-korai-***") as client:
        result = client.llm.complete(messages=[{"role": "user", "content": "Hi"}])
        for event in client.llm.stream(messages=[...]):
            print(event.delta, end="")
"""

from __future__ import annotations

import asyncio
import contextlib
import functools
import inspect
import threading
from collections.abc import Iterator
from typing import Any

from korai._client import KoraiClient


class _Portal:
    """A daemon thread running a dedicated asyncio event loop.

    All coroutines from the async client are submitted here and awaited to
    completion, bridging async → sync without an ``asyncio.run`` per call
    (which would forbid use from inside an existing loop and rebuild the
    httpx connection pool every time).
    """

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever,
            name="korai-sync-portal",
            daemon=True,
        )
        self._thread.start()

    def run(self, coro: Any) -> Any:
        """Run a coroutine on the portal loop and block for its result."""
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result()

    def iterate(self, agen: Any) -> Iterator[Any]:
        """Drive an async generator on the portal loop as a sync generator."""
        try:
            while True:
                try:
                    yield asyncio.run_coroutine_threadsafe(
                        agen.__anext__(), self._loop
                    ).result()
                except StopAsyncIteration:
                    return
        finally:
            # Best-effort close of the async generator if the consumer stops early.
            with_aclose = getattr(agen, "aclose", None)
            if with_aclose is not None:
                # Cleanup must not raise; the generator may already be done.
                with contextlib.suppress(Exception):
                    asyncio.run_coroutine_threadsafe(agen.aclose(), self._loop).result()

    def close(self) -> None:
        if self._loop.is_closed():
            return
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)
        self._loop.close()


class _SyncModule:
    """Wraps an async module so its coroutine methods run synchronously and
    its async-generator methods become sync generators. Plain sync methods
    and attributes (e.g. ``tools.register``) pass through unchanged.
    """

    def __init__(self, target: Any, portal: _Portal) -> None:
        object.__setattr__(self, "_target", target)
        object.__setattr__(self, "_portal", portal)

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._target, name)
        if inspect.iscoroutinefunction(attr):

            @functools.wraps(attr)
            def call(*args: Any, **kwargs: Any) -> Any:
                result = self._portal.run(attr(*args, **kwargs))
                # Some methods are `async def` that *return* an async
                # iterator (e.g. llm.stream) rather than being async-gen
                # functions; drive that iterator synchronously too.
                if hasattr(result, "__anext__"):
                    return self._portal.iterate(result)
                return result

            return call
        if inspect.isasyncgenfunction(attr):

            @functools.wraps(attr)
            def gen(*args: Any, **kwargs: Any) -> Iterator[Any]:
                return self._portal.iterate(attr(*args, **kwargs))

            return gen
        return attr


class SyncKoraiClient:
    """Synchronous facade over :class:`korai.KoraiClient`.

    Takes the same constructor arguments as the async client. Use as a
    context manager (or call :meth:`close`) so the underlying connection
    pool and the portal thread are released.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._portal = _Portal()
        self._async = KoraiClient(*args, **kwargs)

    @classmethod
    def _wrap(cls, async_client: KoraiClient) -> SyncKoraiClient:
        """Wrap an existing async client (used by with_options) on a fresh
        portal so each sync client owns its own loop and closes cleanly."""
        self = cls.__new__(cls)
        self._portal = _Portal()
        self._async = async_client
        return self

    # --- module accessors (mirror KoraiClient's lazy module properties) ---

    @property
    def auth(self) -> Any:
        return _SyncModule(self._async.auth, self._portal)

    @property
    def tenant(self) -> Any:
        return _SyncModule(self._async.tenant, self._portal)

    @property
    def llm(self) -> Any:
        return _SyncModule(self._async.llm, self._portal)

    @property
    def rag(self) -> Any:
        return _SyncModule(self._async.rag, self._portal)

    @property
    def audit(self) -> Any:
        return _SyncModule(self._async.audit, self._portal)

    @property
    def tools(self) -> Any:
        return _SyncModule(self._async.tools, self._portal)

    @property
    def billing(self) -> Any:
        return _SyncModule(self._async.billing, self._portal)

    @property
    def fleet(self) -> Any:
        return _SyncModule(self._async.fleet, self._portal)

    # --- client-level config passthrough ---

    @property
    def api_key(self) -> str | None:
        return self._async.api_key

    @property
    def base_url(self) -> str:
        return self._async.base_url

    @property
    def organization_id(self) -> str | None:
        return self._async.organization_id

    def set_tokens(self, access_token: str, refresh_token: str | None = None) -> None:
        self._async.set_tokens(access_token, refresh_token)

    def clear_tokens(self) -> None:
        self._async.clear_tokens()

    def request_raw(self, *args: Any, **kwargs: Any) -> Any:
        """Synchronous :meth:`KoraiClient.request_raw` — the raw-response
        escape hatch (no raise on non-2xx)."""
        return self._portal.run(self._async.request_raw(*args, **kwargs))

    def with_options(self, **kwargs: Any) -> SyncKoraiClient:
        """Return a new SyncKoraiClient with per-call overrides (timeout /
        max_retries), mirroring :meth:`KoraiClient.with_options`."""
        return SyncKoraiClient._wrap(self._async.with_options(**kwargs))

    # --- lifecycle ---

    def close(self) -> None:
        try:
            self._portal.run(self._async.aclose())
        finally:
            self._portal.close()

    def __enter__(self) -> SyncKoraiClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


__all__ = ["SyncKoraiClient"]
