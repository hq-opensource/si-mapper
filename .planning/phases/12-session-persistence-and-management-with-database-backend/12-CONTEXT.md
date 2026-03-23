# Phase 12: Session persistence and management with database backend — Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Persist all session data to a database backend so that sessions survive restarts and can be reloaded in full. Add a session selector to the frontend chat component that allows switching between past sessions, restoring all 12 tabs (chat, thoughts, tools, state, performance, artifacts, python, ttl, graph, view, edit, files).

Scope:
1. Add PostgreSQL (ADK DatabaseSessionService) for chat message history
2. Add Redis for all frontend tab data (thoughts, tools, state, performance, artifacts, python snapshots, ttl snapshots)
3. Use Neo4j named graphs per session for the graph tab
4. Add `GET /sessions` backend endpoint to list available sessions
5. Add session selector UI at the top of the chat component
6. Wire Redis saving into the existing callback pipeline alongside the frontend streaming

**Out of scope for Phase 12:**
- Session cleanup/deletion policy (deferred — persist everything forever for now)
- Access control or multi-user session isolation
- Session search or filtering beyond the dropdown list

</domain>

<decisions>
## Implementation Decisions

### Database architecture — three stores
- **PostgreSQL**: ADK message history via `DatabaseSessionService` (swap `use_in_memory_services=True` for a Postgres URL). Handles chat messages, turn history, and session metadata natively. Research ADK docs for how `DatabaseSessionService` exposes session listing.
- **Redis**: All frontend tab data. Separate key per tab per session: `session:{id}:thoughts`, `session:{id}:tools`, `session:{id}:state`, `session:{id}:performance`, `session:{id}:artifacts`, `session:{id}:python_snapshots`, `session:{id}:ttl_snapshots`. All entries persist forever (no TTL/expiry set). No cleanup policy in this phase.
- **Neo4j**: Graph data per session via named graphs (or session_id-labeled nodes — researcher to determine best Neo4j 5 approach). The `/api/graph` endpoint must accept `session_id` and return the correct graph for that session.

### What to persist and when
- **Real-time streaming**: Every event that currently streams to the frontend via the callback pipeline ALSO saves to Redis in the same callback call. No separate background job — save and stream are one operation.
- **Chat messages**: Persisted automatically by ADK's `DatabaseSessionService` to PostgreSQL on every turn.
- **All Redis data persists forever** — no expiry, no cleanup in this phase.

### Callback integration
- Saving happens inside the existing `callback_utils.py` pipeline (same `GLOBAL_SESSION_STORE` pattern).
- When an event is emitted (thought, tool call, state update, performance metric, artifact, python snapshot, ttl snapshot), it is simultaneously:
  1. Streamed to the frontend (existing behavior)
  2. Appended/written to Redis under `session:{session_id}:{tab_key}`
- No new callbacks — extend the existing ones.

### Session selector UI
- **Location**: Top of the chat component (above the message list)
- **Content per session entry**: Date/time + first user message as the session name (auto-generated label)
- **Controls**: Dropdown selector + a `+ New Session` button alongside it
- **New Session behavior**: Stops the current agent, generates a new session ID, restarts the agent clean. Current session is already saved (real-time), so no data is lost.

### Session restoration when switching
- **Chat (priority)**: Loads immediately on session switch — fetched from PostgreSQL via ADK session history
- **Other tabs (lazy)**: Load in the background after chat appears — thoughts, tools, state, performance, artifacts, python, ttl each fetched from Redis on demand as they become visible
- **Graph tab**: Fetches from Neo4j using the session's named graph ID. Same lazy-load timing as other tabs.

### Resumable past sessions
- **All past sessions are resumable** (not read-only). The user can select any past session and continue chatting.
- **Mechanism**: Frontend passes the `session_id` with each message (CopilotKit/ag-ui thread ID maps to ADK `session_id`). ADK `DatabaseSessionService` loads the full session history by ID when the agent receives a message.
- No `/set-active-session` endpoint needed — session is implicit in the message.

### Session listing API
- New endpoint: `GET /sessions` — returns a list of all sessions from PostgreSQL.
- Per-session metadata: `{ session_id, created_at, name (first user message), message_count }`.
- Research required: check how ADK `DatabaseSessionService` exposes session enumeration (may need direct Postgres query or ADK internal API).

### Docker Compose additions
- Add `postgres` service to existing `docker-compose.yml` (alongside Neo4j, Portainer, etc.)
- Add `redis` service to existing `docker-compose.yml`
- Both use standard profiles (e.g., `db` profile or folded into existing `deploy` profile — researcher to recommend)
- All credentials (Postgres URL, Redis URL) stored in environment variables / `.env` file. No hardcoded credentials.

### Claude's Discretion
- Exact Redis client library for Python (`redis-py` is the standard)
- Neo4j named graph implementation detail (named graph API vs session_id node property — whichever is supported in Neo4j 5 + Neosemantics without breaking existing queries)
- Postgres port and credentials naming convention
- Redis port (default 6379)
- Background lazy-load polling interval for tabs (frontend implementation detail)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing session handling
- `agent/main.py` — current session creation pattern (`use_in_memory_services=True`, `GLOBAL_SESSION_STORE`, `session_id` generation, `/session_state` and `/session_info` endpoints)
- `agent/utils/callback_utils.py` — `GLOBAL_SESSION_STORE`, existing callback hooks, event emission pipeline — Redis saving must be added here
- `agent/master_architecture/create_master_agent.py` — `session_id` passed to master agent; `DatabaseSessionService` wired here

### Frontend session / state
- `mapper/src/app/page/components/YourMainContent.tsx` — all 12 tab render cases; session context must flow here
- `mapper/src/app/api/copilotkit/` — CopilotKit endpoint; session_id threading from frontend to backend
- `mapper/src/app/page/components/AgentNavbar.tsx` — existing tab navigation; session selector may need to be aware of active tab

### Graph tab
- `mapper/src/app/api/graph/` — existing `/api/graph` route; must be extended to accept `session_id` parameter
- `mapper/src/app/page/components/GraphWindow.tsx` — existing graph component; must pass `session_id` when fetching

### Infrastructure
- `docker-compose.yml` — existing Neo4j + Portainer service definitions; Postgres and Redis added here

### External ADK documentation (researcher must check)
- ADK `DatabaseSessionService` — how to initialize with a Postgres URL, how sessions are stored, and whether it exposes a session listing API
- ADK session ID threading — how `session_id` flows from the ag-ui/CopilotKit layer through ADK to the agent

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable assets
- `GLOBAL_SESSION_STORE` in `callback_utils.py` — already the central in-memory store; Redis saving plugs in alongside existing store writes
- `ADKAgent` in `main.py` — `_session_manager` attribute used in `/session_state`; `DatabaseSessionService` replaces the in-memory service
- `GraphWindow.tsx` — already fetches from `/api/graph`; needs `?session_id=` query param added
- `docker-compose.yml` — existing service pattern to follow for adding Postgres and Redis

### Established patterns
- Tab data flows: agent callback → `GLOBAL_SESSION_STORE` → `/session_state` → frontend poll
- New pattern: agent callback → `GLOBAL_SESSION_STORE` + Redis write → `/session_state` → frontend poll (for live session) OR Redis read → frontend (for past session)
- All agent tools follow `BaseTool` subclass pattern — no new tools needed for this phase (persistence is infrastructure, not agent-facing)
- Docker services use profiles and standard port mapping (not host networking)

### Integration points
- `main.py` `create_app()` — swap `use_in_memory_services=True` → `DatabaseSessionService(db_url=POSTGRES_URL)`
- `callback_utils.py` event emission — add Redis append calls
- `YourMainContent.tsx` — pass active `session_id` to all tab components that fetch data
- `app/api/graph/route.ts` — add `session_id` query param, route to correct Neo4j named graph

</code_context>

<specifics>
## Specific Ideas

- The user's intent: "All those things should be connected to the session itself" — the session_id is the single key that ties chat + all tab data + graph together
- Redis over MongoDB chosen for speed and simplicity; data model (flat key-value with session-scoped keys) fits Redis perfectly
- Lazy load priority: chat first (user sees conversation immediately), then tabs load silently in the background — UX should feel instant for chat, progressive for tabs
- The callback "save and stream" duality: the same moment that a thought/tool call/snapshot reaches the frontend, it is durably written to Redis — no separate flush step
- Neo4j named graphs: the researcher should verify Neo4j 5 + Neosemantics support. If named graphs aren't suitable, session_id as a node/relationship property with filtered queries is the fallback

</specifics>

<deferred>
## Deferred Ideas

- **Session deletion/cleanup policy** — user said persist forever for now; cleanup UI (delete session, set retention) is a future phase
- **Session search and filtering** — search sessions by content or date range; future phase
- **Multi-user isolation** — currently `user_id = "demo_user"` hardcoded; proper auth and per-user session isolation is a future concern
- **Session export** — export a session as JSON/PDF; not in scope

</deferred>

---

*Phase: 12-session-persistence-and-management-with-database-backend*
*Context gathered: 2026-03-23*
