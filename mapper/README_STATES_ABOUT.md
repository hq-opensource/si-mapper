# State Management — SI-Mapper Frontend

This document explains how agent state flows from the Python backend into the React frontend, how two independent state sources are merged, and how UI components consume the result.

---

## Why Two Sources Exist

The frontend bridges **two separate state management systems** that do not automatically synchronise:

| System | Owner | Transport |
|---|---|---|
| **CopilotKit protocol** | CopilotKit SDK | WebSocket / HTTP streaming |
| **ADK session manager** | Google Agent Development Kit (Python) | HTTP polling (custom endpoints) |

CopilotKit only surfaces what the Python agent explicitly pushes back through the CopilotKit SDK. The ADK maintains its own richer session store internally — persisted keys like `detailed_equipment`, `boilers`, `fans`, `pumps`, `llm_model`, structured event logs — that never flow through CopilotKit. **Both are needed to get the full picture.**

---

## Source 1 — CopilotKit → `agentState`

**Hook:** `useCoAgent<AgentState>({ name: "my_agent" })` in `src/app/page.tsx`

The agent declares its state shape (`AgentState`) and CopilotKit streams it to the frontend in real-time during an active chat turn. Updates arrive as diffs over the streaming protocol. The hook also exposes a `running` boolean that is the canonical "turn active" flag.

```ts
// AgentState shape (page.tsx)
type AgentState = {
  status: string;
  current_step: string;
  observed_steps: string[];
  data: Record<string, unknown>;   // agent's own nested data dict
  active_agent?: string;
  thoughts?: Thought[];
  tool_calls?: ToolCall[];
  events?: AgentEvent[];
  active_project?: { ... } | null;
  active_system?: { ... } | null;
};

const { state: agentState, setState: setAgentState, running: isCopilotTurnActive } = useCoAgent<AgentState>({ name: "my_agent" });
```

**Characteristics:**
- Updates only while a chat turn is in progress
- Limited to what the agent explicitly returns via the CopilotKit SDK
- The only authoritative source for `active_project` and `active_system` (written by the frontend from `WorkspaceContext`)
- `running` is the primary turn-active signal; `status` vocabulary check is the fallback

---

## Source 2 — ADK Backend Polling → `pooledState`

**Hook:** `useAgentPolling<AgentState>(pollingConfig)` in `src/hooks/useAgentPolling.ts`

A custom polling loop that calls two FastAPI endpoints on the Python agent backend.

### Step 1 — Session bootstrap (with automatic retry)

```
GET /session_info
→ { app_name, user_id }
```

Fetched immediately on activation and retried on every interval tick until a response is received (so the hook self-heals if the backend starts after the page). Re-fetched automatically every **15 poll cycles** and immediately after **3 consecutive errors**, making the hook resilient to backend restarts.

> `session_id` is **not** returned by `/session_info`. Session identity is carried entirely by `threadId` (from `useCopilotContext()`), which is passed as `request_session_id` on every state poll.

### Step 2 — State polling (variable interval)

```
GET /session_state?request_session_id={threadId}&app_name=si_mapper&user_id=demo_user
→ full AgentState + domain keys
```

The interval is **adaptive**:
- **2 000 ms** while the agent is in an active state
- **10 000 ms** when `agentState.status` is `"idle"` or `"complete"`

Polling is also **suspended** whenever the browser tab is hidden (`visibilitychange`), reducing background load to zero when the user switches away.

Any in-flight request is aborted via `AbortController` before the next tick starts, preventing stale responses from overwriting fresh ones.

`pooledState` is cleared to `null` **immediately** whenever `threadId` changes (before the next poll resolves), preventing stale data from the old session from briefly appearing in the new session's panels.

The backend endpoint merges two sub-sources before returning:

```python
# agent/main.py — /session_state
state = await sm.get_session_state(...)           # ADK SessionManager (persisted to DB)
real_time_updates = GLOBAL_SESSION_STORE.get(target_session_id)   # in-memory overlay
if real_time_updates:
    base_state.update(real_time_updates)
return base_state
```

If the session is not found by its direct ID, the backend performs a secondary lookup using the supplied `request_session_id` as a thread ID (`get_latest_session_by_thread_id_async`), making the endpoint resilient to session ID mismatches.

**Characteristics:**
- Always running (when tab is visible), independent of chat activity
- Contains the full ADK session dictionary — domain keys that never appear in `agentState`
- `pooledState` is the authoritative source for `status`, `current_step`, `active_agent` **at rest**
- Uses structural deep equality (`deepEqual` from `@/utils/deepEqual`) for change detection — order-insensitive, prevents phantom re-renders from dict key-order changes
- Returns `error` string when polling fails; consumed by `page.tsx` as a UI banner

### Polling error visibility

`useAgentPolling` sets its `error` state on any network or HTTP failure. `page.tsx` consumes it and displays a **dismissable bottom banner** when the backend is unreachable:

```tsx
const { pooledState, error: pollingError } = useAgentPolling<AgentState>(pollingConfig);

{showErrorBanner && (
  <div className="fixed bottom-0 ...">
    Agent backend unreachable — State panel may show stale data
    <button onClick={() => setBannerDismissed(true)} />
  </div>
)}
```

The banner re-appears automatically if a new error arrives after dismissal.

---

## Merge Point 1 — `combinedState` (direct prop)

Computed inline in `page.tsx`, immediately after both hooks are called:

```ts
// Which source wins for lifecycle keys depends on whether a CopilotKit turn is active.
// `running` from useCoAgent is the primary signal; the status vocabulary set is the fallback.
const isActiveTurn = isCopilotTurnActive ??
  (ACTIVE_TURN_STATUSES as readonly string[]).includes(agentState.status);

const combinedState = {
  ...agentState,
  ...(pooledState || {}),
  // Lifecycle keys: CopilotKit stream wins during active turns; poll wins at rest
  status:       isActiveTurn ? agentState.status       : (pooledState?.status       ?? agentState.status),
  current_step: isActiveTurn ? agentState.current_step : (pooledState?.current_step ?? agentState.current_step),
  active_agent: isActiveTurn ? agentState.active_agent : (pooledState?.active_agent ?? agentState.active_agent),
  // Frontend is always authoritative — never let the backend overwrite workspace selection
  active_project: agentState.active_project,
  active_system:  agentState.active_system,
} as AgentState;
```

`combinedState` is passed **as a prop** directly to `<YourMainContent agentState={combinedState}>`.

**Who uses it:** `YourMainContent` → `AgentNavbar` (for status overlays, active agent name, session controls).

---

## Merge Point 2 — `<StateSyncer>` → `ThoughtsContext`

`<StateSyncer>` is an invisible component rendered inside `<ThoughtsProvider>` in `page.tsx`. Its only job is to run a `useEffect` that reacts to both `pooledState` and `agentState` and writes the merged result into `ThoughtsContext`.

```ts
// page.tsx — StateSyncer useEffect
const combinedThoughts  = [...(agentState.thoughts  || []), ...(pooledState?.thoughts  || [])];
const combinedToolCalls = [...(agentState.tool_calls || []), ...(pooledState?.tool_calls || [])];
const combinedEvents    = [...(agentState.events    || []), ...(pooledState?.events    || [])];

syncThoughts(combinedThoughts);
syncToolCalls(combinedToolCalls);
syncEvents(combinedEvents);

// Build merged data bag — pooledRest overwrites agentRest on key conflicts
// Keys are filtered through constants from @/constants/agentState
const agentRest  = Object.fromEntries(Object.entries(agentState).filter(not excluded));
const pooledRest = Object.fromEntries(Object.entries(pooledState).filter(not excluded));

const customData = {
  ...agentRest,
  ...pooledRest,                       // pooledState wins
  adkData:     pooledState.data,       // ADK nested data dict   → keyed as "adkData"
  copilotData: agentState.data,        // CopilotKit data dict   → keyed as "copilotData"
};
// Snapshot passed so stale keys are pruned when the backend removes them
syncData(customData, Object.keys(customData));
```

**Key filtering** uses named constants from `@/constants/agentState`:

- `EXCLUDED_SYNC_KEYS` — keys handled by dedicated sync functions or frontend-owned: `status`, `current_step`, `observed_steps`, `active_agent`, `thoughts`, `tool_calls`, `events`, `active_project`, `active_system`
- `FILTERED_STATE_KEY_PREFIXES` — keys whose prefix marks them as backend lifecycle artefacts and should be dropped entirely: `EXIT_`

---

## Merge Point 3 — `ThinkingMessage` (in-band chat parsing)

A third, independent write path. `ThinkingMessage` is a custom CopilotKit `AssistantMessage` renderer (`src/components/ThinkingMessage.tsx`). It parses the raw streaming chat content for embedded fenced blocks:

```
:::thought
Agent reasoning content …
:::

:::tool_call
Tool invocation content …
:::
```

These blocks are extracted client-side during streaming and written directly into `ThoughtsContext` via `addThought()` / `addToolCall()`, bypassing both merge points above. This path captures inline reasoning that may not be present in the structured `events` array.

IDs written by `ThinkingMessage` are **namespaced** with a `"chat:"` prefix to keep them disjoint from the `Thought.id` values emitted by the agent state array:

```ts
addThought(`chat:${message.id}`, thoughtContent.trim());
addToolCall(`chat:${message.id}`, toolCallContent.trim());
```

---

## `ThoughtsContext` — The Global State Store

**File:** `src/context/ThoughtsContext.tsx`

A React context that acts as the single source of truth for all debug/inspection panel components. It holds four independent slices:

| Slice | Type | Written by |
|---|---|---|
| `thoughts` | `Thought[]` | `StateSyncer` via `syncThoughts()`, `ThinkingMessage` via `addThought()` |
| `toolCalls` | `ToolCall[]` | `StateSyncer` via `syncToolCalls()`, `ThinkingMessage` via `addToolCall()` |
| `events` | `AgentEvent[]` | `StateSyncer` via `syncEvents()` |
| `data` | `Record<string, unknown>` | `StateSyncer` via `syncData()` |

All sync functions perform **merge-by-id** (not replace), sorting by timestamp, and short-circuit using structural `deepEqual` if nothing changed — preventing unnecessary re-renders from key-order differences in backend responses.

### `syncData` — snapshot-based stale-key pruning

`syncData` accepts an optional `snapshot` parameter. When provided, any key present in `data` but absent from `snapshot` is **deleted** from the store, making backend key deletions visible:

```ts
syncData: (newData: Record<string, unknown>, snapshot?: string[]) => void;
```

`StateSyncer` always passes `Object.keys(customData)` as the snapshot, so `StateWindow` reflects the current backend state exactly rather than accumulating stale keys indefinitely.

### `AgentEvent` type taxonomy

Events carry an `event_type` discriminant that determines which UI panel renders them:

| `event_type` | Panel |
|---|---|
| `BRAINSTORM` | ThoughtsWindow |
| `DELEGATION` | ThoughtsWindow |
| `ACTION_TRIGGER` | ToolCallsWindow |
| `ACTION_RESULT` | ToolCallsWindow |
| `STATE_MUTATION` | ToolCallsWindow |
| `ARTIFACT` | ArtifactsDashboard |
| _(any with `metadata.latency_s`)_ | PerformanceDashboard |

---

## Session Switching

`<ThoughtsProvider>` receives `key={threadId}`. When `threadId` changes, React fully **unmounts and remounts** the provider and all its children, resetting all four context slices (`thoughts`, `toolCalls`, `events`, `data`) to empty state instantly. `pooledState` is also cleared to `null` synchronously via a `useEffect` in `useAgentPolling`, so the old session's polled data never survives into the new session.

```tsx
// page.tsx
<ThoughtsProvider key={threadId} currentAgentName={combinedState.active_agent || "SI-MAPPER"}>
```

`activeTab` (the selected inspection panel tab) is lifted **above** `<ThoughtsProvider>` so the tab selection survives session switches without being reset.

---

## Full Data Flow

```
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                                     PYTHON BACKEND                                           ║
║                                                                                              ║
║   ┌─────────────────────────────┐       ┌──────────────────────────────────────────────┐     ║
║   │     ADK Session Manager     │       │         CopilotKit Protocol (streaming)      │     ║
║   │  (persisted state in SQLite)│       │    Agent emits state through CopilotKit SDK  │     ║
║   └──────────────┬──────────────┘       └───────────────────────┬──────────────────────┘     ║
║                  │  merged with                                 │                            ║
║   ┌──────────────▼──────────────┐                               │                            ║
║   │     GLOBAL_SESSION_STORE    │                               │                            ║
║   │  (in-memory real-time data) │                               │                            ║
║   └──────────────┬──────────────┘                               │                            ║
║                  │ GET /session_info  (on mount, retried)       │                            ║
║                  │   → { app_name, user_id }  (no session_id)   │                            ║
║                  │ GET /session_state (adaptive: 2 s / 10 s)    │                            ║
║                  │   request_session_id = threadId              │                            ║
╚══════════════════╪══════════════════════════════════════════════╪════════════════════════════╝
                   │                                              │
                   ▼ HTTP polling (paused when tab hidden)        ▼ WebSocket / HTTP stream
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                                   page.tsx  (React root)                                     ║
║                                                                                              ║
║   useAgentPolling<AgentState>(pollingConfig)       useCoAgent<AgentState>({ name:"my_agent"})║
║   ┌──────────────────────────────────┐              ┌──────────────────────────────────┐     ║
║   │  interval = status idle ? 10 s   │              │  state:   agentState             │     ║
║   │             else       2 s       │              │  running: isCopilotTurnActive    │     ║
║   │  paused when tab hidden          │              │  {status, current_step,          │     ║
║   │  cleared on threadId change      │              │   data{}, thoughts[],            │     ║
║   │  sessionInfo refreshed every     │              │   tool_calls[], events[],        │     ║
║   │    15 ticks / 3 errors           │              │   active_project, active_system} │     ║
║   │  → pooledState                   │              └────────────────┬─────────────────┘     ║
║   │  → error (shown as banner)       │                               │                       ║
║   │  { status, current_step,         │                               │                       ║
║   │    active_agent, thoughts[],     │                               │                       ║
║   │    events[], tool_calls[],       │                               │                       ║
║   │    data{}, detailed_equipment,   │                               │                       ║
║   │    boilers, fans, ... }          │                               │                       ║
║   └────────────┬─────────────────────┘                               │                       ║
║                │                                                     │                       ║
║                └──────────────────────────┬──────────────────────────┘                       ║
║                                           │                                                  ║
║                             ┌─────────────┴─────────────┐                                    ║
║                             │                           │                                    ║
║              ┌──────────────▼──────────┐   ┌────────────▼─────────────────────────────┐      ║
║              │  MERGE 1                │   │  MERGE 2 — <StateSyncer>                 │      ║
║              │  combinedState          │   │  (invisible component)                   │      ║
║              │                         │   │                                          │      ║
║              │ { ...agentState,        │   │  thoughts:  [...agt, ...pooled]          │      ║
║              │   ...pooledState }      │   │             → syncThoughts()             │      ║
║              │                         │   │                                          │      ║
║              │ During active turn:     │   │  toolCalls: [...agt, ...pooled]          │      ║
║              │   agentState wins for   │   │             → syncToolCalls()            │      ║
║              │   lifecycle keys        │   │                                          │      ║
║              │ At rest:                │   │  events:    [...agt, ...pooled]          │      ║
║              │   pooledState wins      │   │             → syncEvents()               │      ║
║              │                         │   │                                          │      ║
║              │ Frontend always wins:   │   │  data:      { ...agentRest,              │      ║
║              │   .active_project       │   │               ...pooledRest,  ← wins     │      ║
║              │   .active_system        │   │               adkData: pooled.data,      │      ║
║              └────────┬────────────────┘   │               copilotData: agt.data }    │      ║
║                       │ prop               │  snapshot → stale keys pruned            │      ║
║                       │ agentState=        │             → syncData(data, snapshot)   │      ║
║                       │ combinedState      └──────────────────┬───────────────────────┘      ║
║                       │                                       │ writes into                  ║
║                       │               ┌───────────────────────▼───────────────────────┐      ║
║                       │               │  MERGE 3 — ThinkingMessage (chat parsing)     │      ║
║                       │               │  parses :::thought / :::tool_call blocks      │      ║
║                       │               │  IDs namespaced: "chat:{message.id}"          │      ║
║                       │               │  → addThought() / addToolCall()               │      ║
║                       │               └──────────────────┬────────────────────────────┘      ║
║                       │                                  ▼                                   ║
║                       │                   ┌──────────────────────────────────────────┐       ║
║                       │                   │   ThoughtsContext  (React Context)       │       ║
║                       │                   │   reset via key={threadId} on switch     │       ║
║                       │                   │                                          │       ║
║                       │                   │  thoughts[]   ← syncThoughts()           │       ║
║                       │                   │                  addThought()            │       ║
║                       │                   │  toolCalls[]  ← syncToolCalls()          │       ║
║                       │                   │                  addToolCall()           │       ║
║                       │                   │  events[]     ← syncEvents()             │       ║
║                       │                   │  data{}       ← syncData(d, snapshot)    │       ║
║                       │                   │               (stale keys pruned)        │       ║
║                       │                   └──────────────┬───────────────────────────┘       ║
╚═══════════════════════╪══════════════════════════════════╪═══════════════════════════════════╝
                        │ prop                             │ useThoughts()
                        ▼                                  ▼
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                                   FRONTEND COMPONENTS                                        ║
║                                                                                              ║
║  <YourMainContent agentState={combinedState}>        via useThoughts()                       ║
║  │                                                                                           ║
║  │  Passes combinedState to <AgentNavbar>         AgentNavbar      → events, data            ║
║  │  (.status, .current_step, .active_agent,       (badge dots, status pill, agent name,      ║
║  │   .active_project, .active_system)              session dropdown)                         ║
║  │                                                                                           ║
║  │  Renders tab panels:                           ThoughtsWindow   → events                  ║
║  │   • ThoughtsWindow                             (BRAINSTORM, DELEGATION)                   ║
║  │   • ToolCallsWindow                                                                       ║
║  │   • StateWindow                                ToolCallsWindow  → events                  ║
║  │   • PerformanceDashboard                        (ACTION_TRIGGER, ACTION_RESULT,           ║
║  │   • ArtifactsDashboard                          STATE_MUTATION)                           ║
║  │   • GraphWindow / CodeWindow                                                              ║
║  │   • ExternalPageIframe (Graphivac)             StateWindow      → data                    ║
║  │   • SvarFileManager                            (all keys, stale keys auto-pruned)         ║
║  │                                                                                           ║
║  │                                                PerformanceDashboard → events, data        ║
║  │                                                (latency, tokens, data.llm_model)          ║
║  │                                                                                           ║
║  └──────────────────────────────────────────────► ArtifactsDashboard → events                ║
║                                                   (ARTIFACT events only)                     ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## Design Decisions

### `pooledState` wins on lifecycle keys at rest; `agentState` wins during active turns
During a streaming CopilotKit turn, `running` (from `useCoAgent`) or the `ACTIVE_TURN_STATUSES` vocabulary set flips authority for `status`, `current_step`, and `active_agent` to the live CopilotKit stream. At rest, `pooledState` is authoritative. This prevents the 2 s polling lag from making the UI appear to be behind during agent execution.

### `agentState` is always authoritative for workspace selection
`active_project` and `active_system` are written by the frontend from `WorkspaceContext` and pinned in both `combinedState` and `EXCLUDED_SYNC_KEYS`. The backend can never overwrite the user's workspace selection.

### `adkData` / `copilotData` naming convention
The `data` sub-key from `pooledState` (the ADK session manager's nested dict) is stored in `ThoughtsContext.data` under `adkData`. The `data` sub-key from `agentState` (the CopilotKit agent's nested dict) is stored under `copilotData`. This matches the source, not the transport layer.

### Two separate merge outputs
`combinedState` (prop path) and `ThoughtsContext` (context path) serve different consumers. The prop gives `YourMainContent` a single struct suitable for status overlays and session controls. The context gives debug panel components clean, independent slices (`events`, `data`) without prop-drilling through the whole tree.

### Snapshot-based stale-key pruning in `syncData`
`StateSyncer` always passes `Object.keys(customData)` as the second argument to `syncData`. Any key in `ThoughtsContext.data` that is not in that snapshot is deleted. This makes backend key deletions immediately visible in `StateWindow` rather than persisting stale data until a page reload.

### `deepEqual` instead of `JSON.stringify`
All change-detection short-circuits use a custom `deepEqual` (`src/utils/deepEqual.ts`) that is **key-order insensitive**. `JSON.stringify` serialises `{a:1,b:2}` and `{b:2,a:1}` as different strings; Python dicts can change insertion order between calls, causing phantom re-renders. The custom implementation avoids any external dependency (compare: `fast-deep-equal` package).

### Merge-by-id, not replace
All `sync*` functions in `ThoughtsContext` merge arrays by `id` (or `trace_id` for events) and short-circuit via `deepEqual` if nothing changed. This prevents spurious re-renders from the polling cycle when state has not actually changed.

### `setAgentState` stability via ref
CopilotKit does not guarantee a stable `setAgentState` reference across renders. Storing it in a `useRef` (`setAgentStateRef`) and accessing it inside effects prevents the infinite render loop that would otherwise occur (`effect fires → state updates → new ref → effect fires again`).

### Two-speed polling with tab-visibility pause
`pollingConfig.interval` is derived from `agentState.status` via `useMemo`: 2 000 ms when the agent is active, 10 000 ms when idle or complete. Polling is also fully suspended via `visibilitychange` when the browser tab is hidden. Because `interval` is already in the polling effect's deps array, the interval changes rate automatically without extra wiring.

### Periodic `sessionInfo` refresh
`/session_info` is no longer fetched exactly once. The polling loop re-fetches it every 15 ticks (~30 s at 2 s interval) and immediately after 3 consecutive errors. This makes the hook self-healing after a backend restart without a page reload.

### No `session_id` from `/session_info`
The backend's `/session_info` endpoint returns only `{ app_name, user_id }`. Session identity is carried exclusively by `threadId` (from CopilotKit's `useCopilotContext()`), which is passed as `request_session_id` on every `/session_state` poll.

---

## File Reference

| File | Role |
|---|---|
| `src/app/page.tsx` | Root — calls both hooks, owns `combinedState`, renders `<StateSyncer>` and `<ThoughtsProvider key={threadId}>` |
| `src/hooks/useAgentPolling.ts` | HTTP polling hook — produces `pooledState`; adaptive interval, tab-visibility pause, periodic sessionInfo refresh |
| `src/context/ThoughtsContext.tsx` | Global React context — `thoughts`, `toolCalls`, `events`, `data`; `syncData` supports snapshot-based key pruning |
| `src/constants/agentState.ts` | Ownership constants — `EXCLUDED_SYNC_KEYS`, `FILTERED_STATE_KEY_PREFIXES`, `FRONTEND_OWNED_KEYS`, `LIFECYCLE_KEYS`, `ACTIVE_TURN_STATUSES` |
| `src/utils/deepEqual.ts` | Custom structural deep equality — key-order insensitive; replaces `JSON.stringify` comparisons throughout |
| `src/app/page/components/YourMainContent.tsx` | Tab shell — receives `combinedState` as prop, renders all panel components |
| `src/components/ThinkingMessage.tsx` | CopilotKit message renderer — parses `:::thought` / `:::tool_call` blocks; IDs namespaced with `"chat:"` prefix |
| `src/app/page/components/AgentNavbar.tsx` | Navbar — `agentState` prop + `useThoughts()` for badge notifications; hosts session dropdown (create / remove / switch) |
| `src/app/page/components/ThoughtsWindow.tsx` | `events` filtered to `BRAINSTORM`, `DELEGATION` |
| `src/app/page/components/ToolCallsWindow.tsx` | `events` filtered to `ACTION_TRIGGER`, `ACTION_RESULT`, `STATE_MUTATION` |
| `src/app/page/components/StateWindow.tsx` | `data` displayed as key/value cards; stale keys removed when backend drops them |
| `src/app/page/components/PerformanceDashboard.tsx` | `events` with `metadata.latency_s` + `data.llm_model` |
| `src/app/page/components/ArtifactsDashboard.tsx` | `events` filtered to `ARTIFACT` |
| `agent/main.py` | Backend — `/session_info` (app_name + user_id only) and `/session_state` (ADK + GLOBAL_SESSION_STORE merge) FastAPI endpoints |
