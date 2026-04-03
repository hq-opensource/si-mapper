"""session_lookup.py — Internal service for querying the ADK SQLite session DB
by ``_ag_ui_thread_id``.

Uses SQLite's native ``json_extract()`` to filter state blobs directly inside
the database engine.  The full JSON state is **never deserialized in Python**,
which keeps the lookup fast even with large state objects.

Compatible with both ADK schema v0 and v1 (same table / column names).

Sync usage (scripts, background threads):
    from utils.session_lookup import find_sessions_by_thread_id

    sessions = find_sessions_by_thread_id("thread-abc123")
    latest   = get_latest_session_by_thread_id("thread-abc123")

Async usage (inside coroutines / FastAPI handlers):
    from utils.session_lookup import find_sessions_by_thread_id_async

    sessions = await find_sessions_by_thread_id_async("thread-abc123")
    latest   = await get_latest_session_by_thread_id_async("thread-abc123")
"""

from __future__ import annotations

import logging
import os
import sqlite3
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Mirrors the default in main.py — overridable per call.
_DEFAULT_DB_PATH: str = os.getenv("SESSIONS_DB_PATH", "/app/data/sessions.db")

# How many recent sessions to inspect at most.
_DEFAULT_LIMIT: int = 10

# ---------------------------------------------------------------------------
# Core SQL — filtering, ordering, and capping all happen inside SQLite.
# json_extract() evaluates natively (C) without moving the blob into Python.
# Available since SQLite 3.9.0 (October 2015).
# ---------------------------------------------------------------------------
_SQL = """
    SELECT
        id,
        app_name,
        user_id,
        update_time
    FROM   sessions
    WHERE  json_extract(state, '$._ag_ui_thread_id') = ?
    ORDER  BY update_time DESC
    LIMIT  ?
"""


@dataclass(slots=True, frozen=True)
class SessionMatch:
    """Lightweight projection of a ``sessions`` row that matched the query."""

    id: str
    app_name: str
    user_id: str
    update_time: str  # raw ISO-8601 string as stored by SQLite


# ---------------------------------------------------------------------------
# Sync — uses the stdlib sqlite3 module; zero extra dependencies.
# ---------------------------------------------------------------------------

def find_sessions_by_thread_id(
    thread_id: str,
    *,
    db_path: str | None = None,
    limit: int = _DEFAULT_LIMIT,
) -> list[SessionMatch]:
    """Return the most-recently-updated sessions whose state contains
    ``_ag_ui_thread_id == thread_id``.

    The comparison and ordering are delegated entirely to SQLite via
    ``json_extract()`` — no Python-side JSON parsing occurs.

    Args:
        thread_id: Value to match against ``state._ag_ui_thread_id``.
        db_path:   Path to the SQLite file.  Defaults to the
                   ``SESSIONS_DB_PATH`` env var (``/app/data/sessions.db``).
        limit:     Maximum number of sessions to return (default 10).

    Returns:
        A list of :class:`SessionMatch` objects ordered newest-first.
        Returns an empty list when the database file does not exist or the
        ``sessions`` table is not yet present (e.g. first boot before any
        session has been persisted to disk).
    """
    resolved = db_path or _DEFAULT_DB_PATH

    if not os.path.isfile(resolved):
        logger.debug(
            "[session_lookup] DB not found at %s — returning empty.", resolved
        )
        return []

    try:
        # file URI with mode=ro avoids conflicting with the live
        # DatabaseSessionService that may also have the file open.
        with sqlite3.connect(f"file:{resolved}?mode=ro", uri=True) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(_SQL, (thread_id, limit))
            return [
                SessionMatch(
                    id=row["id"],
                    app_name=row["app_name"],
                    user_id=row["user_id"],
                    update_time=row["update_time"],
                )
                for row in cursor.fetchall()
            ]
    except sqlite3.OperationalError as exc:
        # The `sessions` table may not exist yet on first boot.
        logger.warning("[session_lookup] DB query failed: %s", exc)
        return []


def get_latest_session_by_thread_id(
    thread_id: str,
    *,
    db_path: str | None = None,
) -> SessionMatch | None:
    """Return the single most-recently-updated session matching *thread_id*,
    or ``None`` if no match exists."""
    results = find_sessions_by_thread_id(thread_id, db_path=db_path, limit=1)
    return results[0] if results else None


# ---------------------------------------------------------------------------
# Async shims — offload the sync sqlite3 call to the default thread-pool
# executor so the event loop is never blocked.  No extra dependencies needed.
# ---------------------------------------------------------------------------

async def find_sessions_by_thread_id_async(
    thread_id: str,
    *,
    db_path: str | None = None,
    limit: int = _DEFAULT_LIMIT,
) -> list[SessionMatch]:
    """Non-blocking wrapper around :func:`find_sessions_by_thread_id`.

    Runs the sync sqlite3 query on the default thread-pool executor via
    ``asyncio.to_thread``, keeping the event loop free during the disk read.
    """
    import asyncio
    from functools import partial
    return await asyncio.to_thread(
        partial(find_sessions_by_thread_id, thread_id, db_path=db_path, limit=limit)
    )


async def get_latest_session_by_thread_id_async(
    thread_id: str,
    *,
    db_path: str | None = None,
) -> SessionMatch | None:
    """Async convenience wrapper — returns the single most-recent match or
    ``None``."""
    results = await find_sessions_by_thread_id_async(
        thread_id, db_path=db_path, limit=1
    )
    return results[0] if results else None





