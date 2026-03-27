# 13-11 — Session Persistence (Auto-Save & Restore)

**Phase:** 13 — Multi-Project Support
**Status:** Not started
**Updated:** 2026-03-26
**Depends on:** `13-07` (system context in CopilotKit state), `13-09` (agent system context awareness)
**Affects:** `agent/` and `mapper/`

---

## Overview

Every time the agent process restarts today, all conversation history and work state is lost. Sessions are held entirely in `InMemorySessionService` (ADK) and `GLOBAL_SESSION_STORE` (the real-time UI mirror in `callback_utils.py`). Neither survives a restart.

This step introduces **transparent, incremental auto-save** of agent sessions and a **session selector UI** in the mapper navbar. Users can name sessions, associate them with a system, restore a previous session, and delete old ones — without any manual save action.

---

## Background — What Constitutes a Session

An ADK session has two distinct data layers:

| Layer | Type | Owner | Content |
|---|---|---|---|
| `Session.state` | `dict[str, Any]` | ADK `SessionService` | Tasks, equipment dict, agent status, `active_project`, `active_system`, `ai_model_name`, snapshots |
| `Session.events` | `list[Event]` | ADK `SessionService` | Full conversation history — every LLM turn, tool call, tool response |
| `GLOBAL_SESSION_STORE[session_id]` | `dict` | `callback_utils.py` | Real-time UI mirror: thoughts, tool_calls, events (last 200), current_step |

The `GLOBAL_SESSION_STORE` is a denormalised read-model derived from `Session.state` — it is rebuilt from ADK events on restore and **does not need separate persistence**.

---

## Why `SqliteSessionService` Is the Right Choice

Google ADK ships three persistence backends out of the box (discovered from the installed package):

| Class | Backend | Use case |
|---|---|---|
| `InMemorySessionService` | RAM | Current — dev/test only, lost on restart |
| `SqliteSessionService` | SQLite via `aiosqlite` | **Recommended** — zero extra deps, file-based, incremental |
| `DatabaseSessionService` | SQLAlchemy async (PostgreSQL, MySQL, etc.) | Production scale-out |
| `VertexAiSessionService` | Google Vertex AI managed | Google Cloud deployments |

**`SqliteSessionService` is the right choice for this step because:**
- It is already a dependency of `google-adk` — no new packages to install.
- It stores each event as an individual row, appended via `append_event()` after every LLM turn. This **is** incremental auto-save — no polling or debouncing needed.
- It supports `list_sessions()`, `get_session()`, `delete_session()` natively.
- It is file-based and consistent with the rest of the project's file-first storage pattern (`project.json`, `system.json`).
- It can be upgraded to `DatabaseSessionService` (PostgreSQL) later with a one-line URL change.

Swapping from in-memory to SQLite is a **single change** in `main.py`:

```python
# Before
adk_agent = ADKAgent(..., use_in_memory_services=True)

# After — inject the session service explicitly
from google.adk.sessions import SqliteSessionService

session_service = SqliteSessionService(db_path=SESSIONS_DB_PATH)
adk_agent = ADKAgent(..., session_service=session_service, use_in_memory_services=True)
```

`use_in_memory_services=True` is kept so that artifact, memory, and credential services continue to use in-memory defaults. Only `session_service` is overridden.

---

## Incremental Auto-Save — How It Works

`SqliteSessionService` implements `BaseSessionService.append_event()`, which the ADK runtime calls **after every event** in the conversation (LLM response, tool call, tool response). Each event is written as a JSON row in the `events` table. Session state is upserted after every state-mutating event.

The auto-save timeline during a single LLM turn:

```
User sends message
  → ADK creates/updates session
  → LLM responds (function call)  → append_event() → SQLite row written ✓
  → Tool executes                 → append_event() → SQLite row written ✓
  → Tool response                 → append_event() → SQLite row written ✓
  → LLM final response            → append_event() → SQLite row written ✓
  → callback_utils updates state  → session state upserted ✓
```

**No explicit "save" action is needed.** If the process crashes mid-turn, completed events up to that point are already persisted.

---

## Compression Strategy – DO NOT IMPLEMENT IN FIRST IMPLEMENTATION

Measured on a realistic session state (50 events, 30 thoughts, 40 tool calls, 10 tasks):

| Format | Size |
|---|---|
| Raw JSON | 34,685 bytes |
| `zlib` level 9 + base64 | 1,176 bytes (**3.4% of original**) |

LLM-generated text is highly repetitive and compresses extremely well.

**Recommendation: do not compress the event rows** — SQLite already handles page-level storage efficiently, and compressing individual rows would prevent SQLite from searching them. Instead, **compress only `Session.state`** when writing a state snapshot, using a thin wrapper:

```python
# agent/utils/session_utils.py

import zlib, json, base64

def compress_state(state: dict) -> dict:
    """Return a copy of state with large list fields compressed."""
    COMPRESS_KEYS = {"events", "thoughts", "tool_calls", "python_code_snapshots", "ttl_code_snapshots"}
    result = {}
    for k, v in state.items():
        if k in COMPRESS_KEYS and isinstance(v, list) and len(json.dumps(v)) > 4096:
            raw = json.dumps(v).encode()
            result[f"_gz_{k}"] = base64.b64encode(zlib.compress(raw, level=9)).decode()
        else:
            result[k] = v
    return result

def decompress_state(state: dict) -> dict:
    """Restore compressed fields."""
    result = {}
    for k, v in state.items():
        if k.startswith("_gz_") and isinstance(v, str):
            original_key = k[4:]
            result[original_key] = json.loads(zlib.decompress(base64.b64decode(v)))
        else:
            result[k] = v
    return result
```

This is optional in the first implementation — start without compression and add it if storage size becomes a concern.

> **See `13-11-session-persistence_appendix-session-size-estimates.md`** for a full breakdown of predicted session sizes by scenario, deployment scale estimates, thinking-model impact, and recommended monitoring thresholds.

---

## Session Metadata — Name and System Association

ADK's `Session` model has no `name` field. The cleanest approach is to store metadata directly in `Session.state` using reserved keys, so they survive save/restore automatically:

```python
# Keys stored in Session.state by the agent at session creation
"session_name"  → str    # User-facing name, e.g. "Chilled Water Plant — Run 3"
"system_id"     → str    # active_system.id — used to filter sessions in the UI
"project_id"    → str    # active_project.id — for completeness
"created_at"    → str    # ISO 8601 — set once at creation
```

`session_name` defaults to `"Session {YYYY-MM-DD HH:MM}"` at creation and can be renamed by the user.

These keys are written by a new agent-side API endpoint (`POST /sessions`) and updated in state by the callback when `active_system` changes.

---

## System Data Model Extension — The Missing Link

The current document stores `system_id` inside each session's state and queries back with `GET /sessions?system_id=...`. This is a **session → system** reference only. It does not make the system aware of its sessions.

The `System` interface and its `system.json` file must be extended to hold a lightweight index of its sessions. This is the canonical link from **system → sessions**.

### `SessionRef` — new type

```typescript
// mapper/src/lib/projects.ts  (and mirrored in mapper/src/types/index.ts)

export interface SessionRef {
  /** ADK session ID — matches Session.id in SqliteSessionService. */
  session_id: string;
  /** User-facing name, e.g. "Chilled Water Plant — Run 3". */
  session_name: string;
  /** ISO 8601. Set once at creation, never updated. */
  created_at: string;
}
```

### `System` interface — add `sessions` field

```typescript
export interface System {
  id: string;
  name: string;
  folder_path: string;
  graphivac_grid_id: string;
  ai_model_name: string;
  created_at: string;
  updated_at: string;
  /** Ordered list of agent sessions associated with this system. Latest first. */
  sessions: SessionRef[];   // ← new, defaults to [] on creation
}
```

`system.json` on disk then looks like:

```json
{
  "id": "sys-xyz789",
  "name": "Chilled Water Plant",
  "folder_path": "sys-xyz789",
  "graphivac_grid_id": "G-LAiRS3mgp6",
  "ai_model_name": "gemini-3.1-pro",
  "created_at": "2026-03-20T10:00:00Z",
  "updated_at": "2026-03-26T14:32:00Z",
  "sessions": [
    { "session_id": "session-abc123", "session_name": "Initial mapping", "created_at": "2026-03-20T10:05:00Z" },
    { "session_id": "session-def456", "session_name": "BACnet pass", "created_at": "2026-03-26T09:00:00Z" }
  ]
}
```

### Why the mapper owns the session index (not the agent)

| Concern | Answer |
|---|---|
| **Single source of truth for the list** | `system.json` — readable by the mapper without calling the agent |
| **Source of truth for session data** | SQLite via `SqliteSessionService` — the agent owns this |
| **Who coordinates both?** | The mapper's API routes — they write `system.json` and call the agent in one transaction |
| **Cascade delete** | Deleting a system calls the agent to delete each `session_id` in `system.sessions`, then `rm -rf` the folder |
| **Cascade on agent restart** | Agent reads `system_id` from session state; mapper reads `system.json` — both are consistent |

### Mapper-side API routes for session management

Rather than the frontend calling the agent directly for session CRUD, all session management goes through **mapper API routes** that coordinate the two sides atomically:

```
POST   /api/projects/{proj_id}/systems/{sys_id}/sessions
  1. Calls agent POST /sessions  → gets session_id
  2. Prepends SessionRef to system.json sessions array
  3. Returns { session_id, session_name }

DELETE /api/projects/{proj_id}/systems/{sys_id}/sessions/{session_id}
  1. Calls agent DELETE /sessions/{session_id}
  2. Removes SessionRef from system.json sessions array
  3. Returns 204

PATCH  /api/projects/{proj_id}/systems/{sys_id}/sessions/{session_id}
  { "session_name": "New name" }
  1. Calls agent PATCH /sessions/{session_id}
  2. Updates session_name in system.json sessions array
  3. Returns updated SessionRef

POST   /api/projects/{proj_id}/systems/{sys_id}/sessions/{session_id}/restore
  1. Calls agent POST /sessions/{session_id}/restore
  2. Returns { session_id, session_name }  (no system.json write needed)
```

The `GET` direction is **free** — the session list is already in `activeSystem.sessions` loaded by `WorkspaceContext`. No separate fetch to the agent is needed to display the list.

### Cascade delete when a system is deleted

`deleteSystemFromDisk` in `projects.ts` must be extended:

```typescript
// Before rm -rf, delete each session from the agent's SQLite
for (const ref of system.sessions) {
  await fetch(`${AGENT_URL}/sessions/${ref.session_id}`, { method: 'DELETE' });
}
await fs.rm(dir, { recursive: true, force: true });
```

This ensures no orphaned rows remain in SQLite after a system is deleted.

### `WorkspaceContext` — no separate sessions state needed

Because sessions live in `activeSystem.sessions`, the context already exposes them. The `SessionSelector` reads `activeSystem?.sessions ?? []` directly — no new `sessions` / `refreshSessions` fields are needed on the context. Mutations (create, rename, delete) call the mapper API routes and then call `refreshSystems()` to reload the updated `system.json`.

---

## Database File Location

The SQLite file is configured via a new env var `SESSIONS_DB_PATH`, defaulting to `./data/sessions.db` relative to the agent working directory:

```python
SESSIONS_DB_PATH = os.getenv("SESSIONS_DB_PATH", "./data/sessions.db")
```

In Docker, this path should be a **named volume mount** so it survives container restarts:

```yaml
# docker-compose.yml
volumes:
  - ./agent/data:/app/data
```

A single file stores sessions for all projects and systems (the system is identified by the `system_id` key in `Session.state`). This is simpler than per-system files and consistent with how a relational DB would be used.

---

## Changes Required

### Agent side (`agent/`)

#### 1. `agent/main.py` — inject `SqliteSessionService`

```python
from google.adk.sessions import SqliteSessionService
import pathlib

SESSIONS_DB_PATH = os.getenv("SESSIONS_DB_PATH", "./data/sessions.db")

# Ensure the data directory exists
pathlib.Path(SESSIONS_DB_PATH).parent.mkdir(parents=True, exist_ok=True)

session_service = SqliteSessionService(db_path=SESSIONS_DB_PATH)

adk_agent = ADKAgent(
    adk_agent=master_agent,
    app_name="si_mapper",
    user_id="demo_user",
    session_service=session_service,   # ← replaces InMemorySessionService
    use_in_memory_services=True,       # ← kept for artifact/memory/credential
    session_timeout_seconds=3600,
    execution_timeout_seconds=1800,
    tool_timeout_seconds=900,
)
```

#### 2. `agent/main.py` — session management endpoints

Add four new endpoints:

**`GET /sessions`** — list sessions, optionally filtered by `system_id`:
```
GET /sessions?system_id=sys-aaa111
→ [{ session_id, session_name, system_id, project_id, created_at, last_update_time }, ...]
```

**`POST /sessions`** — create a new named session and make it active:
```
POST /sessions  { "session_name": "Run 3", "system_id": "sys-aaa111", "project_id": "proj-abc123" }
→ { session_id, session_name }
```

**`POST /sessions/{session_id}/restore`** — restore a saved session (make it the active session):
```
POST /sessions/{session_id}/restore
→ { session_id, session_name }
```
Restoring a session repopulates `GLOBAL_SESSION_STORE` by replaying the saved `Session.state` into the real-time UI mirror.

**`DELETE /sessions/{session_id}`** — delete a session:
```
DELETE /sessions/{session_id}
→ 204 No Content
```

**`PATCH /sessions/{session_id}`** — rename a session:
```
PATCH /sessions/{session_id}  { "session_name": "New name" }
→ { session_id, session_name }
```

#### 3. `agent/utils/session_utils.py` — new helper

Contains:
- `compress_state(state) → dict` and `decompress_state(state) → dict` (optional, add in Milestone 2)
- `format_session_summary(session) → dict` — formats a `Session` object into the flat summary dict used by `GET /sessions`
- `rebuild_global_store(session_id, session_state)` — repopulates `GLOBAL_SESSION_STORE` from a restored session's state

#### 4. `agent/docker.env.example` — document new env var

```dotenv
# Path to the SQLite sessions database.
# In Docker, ensure this path is on a named volume for persistence.
SESSIONS_DB_PATH=./data/sessions.db
```

---

### Mapper side (`mapper/`)

#### 5. `mapper/src/lib/projects.ts` — extend `System` interface

Add `SessionRef` interface and `sessions: SessionRef[]` field to `System` (see *System Data Model Extension* above). Update `createSystemOnDisk` to initialise `sessions: []`. No migration needed — `JSON.parse` will default missing field to `undefined`; the storage layer treats `undefined` as `[]`.

#### 6. `mapper/src/types/index.ts` — mirror the new types

Add `SessionRef` and update the `System` interface to match `projects.ts`.

#### 7. `mapper/src/app/api/projects/[id]/systems/[sysId]/sessions/route.ts` — new mapper API route

Handles `GET` (returns `activeSystem.sessions` from `system.json`), `POST` (creates session via agent then updates `system.json`). Coordinates both sides atomically.

#### 8. `mapper/src/app/api/projects/[id]/systems/[sysId]/sessions/[sessionId]/route.ts` — new mapper API route

Handles `DELETE` and `PATCH` (rename). Each calls the agent API first, then updates `system.json`.

#### 9. `mapper/src/app/api/projects/[id]/systems/[sysId]/sessions/[sessionId]/restore/route.ts` — restore endpoint

`POST` — calls agent `POST /sessions/{id}/restore`. No `system.json` write needed.

#### 10. `mapper/src/app/api/projects/[id]/systems/[sysId]/route.ts` — extend DELETE

Before `deleteSystemFromDisk`, call `DELETE /sessions/{session_id}` on the agent for every `SessionRef` in `system.sessions` to prevent orphaned rows in SQLite.

#### 11. `mapper/src/components/SessionSelector.tsx` — new component

A rich dropdown modelled after `SystemSelector.tsx`, placed in the navbar after the system selector.

**Features:**
- Reads `activeSystem?.sessions ?? []` from `WorkspaceContext` — **no agent API call for the list**
- Displays session name + relative created time ("created 3 hours ago")
- Active session highlighted (matched by `activeSession.session_id` from context)
- **Actions per session:**
  - Click → `POST /api/projects/{proj}/systems/{sys}/sessions/{id}/restore` → updates `activeSession` in context
  - Rename (pencil icon) → `PATCH /api/projects/{proj}/systems/{sys}/sessions/{id}` → `refreshSystems()`
  - Delete with confirmation → `DELETE /api/projects/{proj}/systems/{sys}/sessions/{id}` → `refreshSystems()`
- **"New session"** button → `POST /api/projects/{proj}/systems/{sys}/sessions` → `refreshSystems()`
- Pulsing "saving…" indicator while agent status is active

#### 12. `mapper/src/app/page/components/AgentNavbar.tsx` — add `SessionSelector`

```tsx
<ProjectSelector />
<span>/</span>
<SystemSelector />
<span>/</span>
<SessionSelector />   {/* ← new */}
```

#### 13. `mapper/src/context/WorkspaceContext.tsx` — add `activeSession`

Add only `activeSession` and `setActiveSession` to the context — the session **list** is already carried by `activeSystem.sessions`. `refreshSystems()` (already exists) is the mechanism to reload the list after any mutation.

```typescript
// New fields only — sessions list is activeSystem.sessions
activeSession: SessionRef | null;
setActiveSession: (session: SessionRef) => void;
```

`activeSession` is persisted in `localStorage` under `"active-session-id"`. On mount, the context resolves the stored ID against `activeSystem.sessions`; if not found, defaults to the first session (or null).

#### 14. `mapper/src/hooks/useAgentPolling.ts` — use `activeSession.session_id`

Replace the hardcoded `session_id` from `/session_info` with `activeSession?.session_id` from `WorkspaceContext`. The polling hook already has a `sessionInfo` state — wire it to context instead.

---

## Session Lifecycle

```
System selected in UI
  │
  ├─ If sessions exist for this system → show list → user picks one or starts new
  │     └─ POST /sessions/{id}/restore → session_id changes → polling picks up new state
  │
  └─ No sessions → auto-create one with default name → POST /sessions
        └─ session_id returned → saved in localStorage → agent starts fresh
```

```
Active session running
  │
  ├─ Every LLM event → SqliteSessionService.append_event() → persisted ✓  (ADK handles this)
  ├─ Every state mutation → session state upserted ✓                       (ADK handles this)
  └─ User renames session → PATCH /sessions/{id} → state key updated ✓
```

```
Process restart
  │
  └─ Frontend calls GET /session_info → gets session_id
        │
        ├─ If last session_id exists in SQLite → restore automatically
        └─ If not → create new session
```

---

## Implementation Plan

### Milestone 1 — SQLite backend (agent only, no UI change)

**Steps:**
1. Add `SESSIONS_DB_PATH` env var to `agent/docker.env.example` and load it in `main.py`.
2. Create `./data/` directory on startup.
3. Replace `use_in_memory_services=True` with injected `SqliteSessionService` in `ADKAgent` constructor.
4. Verify: restart the agent process, send a message, restart again — confirm session state and events are restored automatically via `GET /session_state`.
5. Verify: no regression on existing endpoints (`/session_info`, `/session_state`, `/health`).

> This milestone alone delivers persistence — no UI changes. Estimated scope: ~20 lines in `main.py`.

---

### Milestone 2 — Session management API (agent)

**Steps:**
1. Create `agent/utils/session_utils.py` with `format_session_summary` and `rebuild_global_store`.
2. Add `GET /sessions` — calls `session_service.list_sessions()`, filters by `system_id` from query param, returns summaries.
3. Add `POST /sessions` — creates a new ADK session with `session_name`, `system_id`, `project_id` in initial state; makes it active by updating module-level `session_id`.
4. Add `POST /sessions/{session_id}/restore` — calls `session_service.get_session()`, repopulates `GLOBAL_SESSION_STORE`, updates active `session_id`.
5. Add `DELETE /sessions/{session_id}` — calls `session_service.delete_session()`.
6. Add `PATCH /sessions/{session_id}` — updates `session_name` key in session state.
7. Test all five endpoints manually.

---

### Milestone 3 — System data model + mapper API routes + session selector UI

**Steps:**
1. Add `SessionRef` to `mapper/src/lib/projects.ts` and update `System` interface with `sessions: SessionRef[]`. Update `createSystemOnDisk` to initialise `sessions: []`. Mirror in `mapper/src/types/index.ts`.
2. Add mapper API routes:
   - `POST /api/projects/{proj}/systems/{sys}/sessions` — create session (calls agent + updates `system.json`)
   - `DELETE /api/projects/{proj}/systems/{sys}/sessions/{id}` — delete session (calls agent + updates `system.json`)
   - `PATCH /api/projects/{proj}/systems/{sys}/sessions/{id}` — rename session (calls agent + updates `system.json`)
   - `POST /api/projects/{proj}/systems/{sys}/sessions/{id}/restore` — restore session (calls agent only)
3. Extend the existing system `DELETE` route to cascade-delete all sessions from the agent's SQLite before removing the folder.
4. Add `activeSession` and `setActiveSession` to `WorkspaceContext`. Resolve from `activeSystem.sessions` on mount (using `localStorage` key `"active-session-id"`). Session list is `activeSystem.sessions` — no new fetch.
5. Create `mapper/src/components/SessionSelector.tsx` reading from `activeSystem.sessions`.
6. Add `SessionSelector` to `AgentNavbar.tsx`.
7. Update `useAgentPolling.ts` to use `activeSession?.session_id` from context.
8. Test end-to-end: create session → appears in `system.json` → restore → polling switches → rename → reflected in dropdown → delete → cascade confirmed in SQLite.

---

### Milestone 4 — Compression (optional, performance)

**Steps:**
1. Add `compress_state` / `decompress_state` to `agent/utils/session_utils.py`.
2. Wrap state writes in `compress_state` before persisting, `decompress_state` on read.
3. Benchmark: measure SQLite file size before and after for a long session (50+ turns).
4. Gate behind `SESSIONS_COMPRESS_STATE=true` env var so it can be disabled for debugging.

> Skip if storage is not a concern. Add only after Milestones 1–3 are stable.

---

## Acceptance Criteria

**Persistence (Milestones 1–2):**
- [ ] Agent process can be restarted and the last session's state and conversation history are automatically available via `/session_state`.
- [ ] `SqliteSessionService` is used; `InMemorySessionService` is no longer the session backend.
- [ ] `SESSIONS_DB_PATH` is configurable via env var; defaults to `./data/sessions.db`.
- [ ] `GET /sessions?system_id=sys-xxx` returns a list of sessions for that system.
- [ ] `POST /sessions` creates a new named session and makes it active; returns `session_id`.
- [ ] `POST /sessions/{id}/restore` switches the active session; `/session_state` reflects restored state.
- [ ] `DELETE /sessions/{id}` removes the session from SQLite.
- [ ] `PATCH /sessions/{id}` renames the session (updates `session_name` in state).
- [ ] `session_name`, `system_id`, and `project_id` are stored in session state and survive restart.

**Auto-save (included in Milestone 1):**
- [ ] Every LLM turn is persisted incrementally — no explicit save action required.
- [ ] A session interrupted mid-turn (process kill) retains all events completed before the kill.

**System–session association (Milestone 3):**
- [ ] `System` interface and `system.json` include a `sessions: SessionRef[]` field.
- [ ] `createSystemOnDisk` initialises `sessions: []` for new systems.
- [ ] Creating a session via `POST /api/.../sessions` adds a `SessionRef` to `system.json` atomically.
- [ ] Renaming a session via `PATCH /api/.../sessions/{id}` updates `session_name` in `system.json` and in ADK session state.
- [ ] Deleting a session via `DELETE /api/.../sessions/{id}` removes it from `system.json` and from SQLite.
- [ ] Deleting a **system** cascade-deletes all its sessions from SQLite before removing the folder — no orphaned rows.
- [ ] One session belongs to exactly one system — `system_id` is stored in `Session.state` and `SessionRef` lives in that system's `system.json` only.

**UI (Milestone 3):**
- [ ] `SessionSelector` dropdown appears in the navbar next to `SystemSelector`.
- [ ] Session list is read from `activeSystem.sessions` — **no direct agent API call** for the list.
- [ ] Switching active system immediately shows that system's sessions (from the already-loaded `system.json`).
- [ ] Selecting a session restores it; the conversation and state panels update.
- [ ] Renaming a session updates the name in the dropdown immediately (via `refreshSystems()`).
- [ ] Deleting a session removes it from the list; confirms before deleting.
- [ ] "New session" button creates a fresh session and makes it active.
- [ ] The active session ID is persisted in `localStorage` under `"active-session-id"` and restored on page reload.

---

## Notes & Decisions

- **`SqliteSessionService` is the standard ADK persistence path** — it ships with `google-adk` and is documented as the recommended non-memory backend for development and single-process production. No extra dependencies.
- **Incremental saving is free**: ADK's event loop calls `append_event()` after every event. There is nothing to implement here — switching the session service is sufficient.
- **`GLOBAL_SESSION_STORE` does not need persistence**: it is a real-time read-model derived from ADK session events. On restore, `rebuild_global_store` replays `Session.state` into the store, giving the UI its thoughts, tool_calls, and events.
- **Two-layer ownership model**: the mapper owns the session *index* (`system.json → sessions[]`) and the agent owns the session *data* (SQLite events and state). Every mutation goes through a mapper API route that coordinates both sides atomically. This is the same pattern as project/system creation (mapper writes JSON, mapper calls Graphivac).
- **The session list requires no agent API call**: `activeSystem.sessions` is already loaded in `WorkspaceContext` when the system is selected. The `SessionSelector` reads it directly — only restore, create, rename, and delete trigger agent calls.
- **One session belongs to exactly one system**: enforced by `SessionRef` living in one `system.json` only, and `system_id` being stored in `Session.state`. A session cannot appear in two systems' `sessions` arrays.
- **Cascade delete is mandatory**: deleting a system without cleaning up its SQLite sessions would leave orphaned rows that can never be reached again. `deleteSystemFromDisk` must call `DELETE /sessions/{id}` for each `SessionRef` before `rm -rf`.
- **Session naming defaults to ISO datetime** — `"Session {YYYY-MM-DD HH:MM}"` — and can be renamed by the user at any time.
- **The `SessionSelector` mirrors `SystemSelector`** in structure and UX — rich dropdown, inline rename, delete with confirmation — to keep the UI consistent.
- **`DatabaseSessionService` is the upgrade path** — if the deployment moves to a shared multi-process setup, replace `SqliteSessionService(db_path=...)` with `DatabaseSessionService(db_url="postgresql+asyncpg://...")` and the rest of the code is unchanged.
- **Compression is deferred to Milestone 4** — the 3.4% ratio is compelling but the implementation complexity is non-trivial. Milestones 1–3 deliver all user-visible value without it.
- **`active-session-id` in localStorage** — consistent with `active-project-id` and `active-system-id` already used by `WorkspaceContext`.
- **Session restore does not restart the agent** — it only changes the active `session_id` pointer. The agent tree stays intact; the ADK runner uses the restored session's event history as conversation context for the next turn.

