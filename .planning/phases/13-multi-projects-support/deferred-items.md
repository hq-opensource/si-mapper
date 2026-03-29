# Phase 13 — Deferred Items

Items that were explicitly considered during Phase 13 planning but are out of scope for this phase. Each entry records **what** was deferred, **why**, and **what a future implementation would require**.

---

## D-01 — Dynamic Per-Request Grid Targeting in the MCP Server

**Deferred from:** `13-99`
**Category:** Architecture

### What was deferred

Making the MCP server target different Graphivac grids (= different SI-Mapper **systems**) on a per-tool-call basis, so that switching systems in the UI instantly affects all MCP canvas operations without a server restart.

### Why deferred

The MCP server initialises all manager classes (`DuctManager`, `PipeManager`, `GridManager`, etc.) as **singletons at startup** with a fixed set of Graphivac coordinates. The current MCP protocol does not provide a standard mechanism for injecting per-call context (such as `grid_id`) outside of explicit tool parameters.

Implementing dynamic targeting would require:

1. **Manager refactor**: change every manager class to accept `grid_id` (and `project_id`) as method-level parameters rather than constructor arguments.
2. **Tool parameter additions**: every registered MCP tool would need a `grid_id` parameter, making the tool surface more complex for the AI caller.
3. **Protocol evaluation**: determine whether FastMCP / the MCP protocol supports per-call metadata injection as an alternative to explicit parameters.
4. **State propagation**: the active system's grid ID would need to travel from the frontend → agent session → MCP tool call on every invocation. This crosses three process boundaries.

### Phase 13 mitigation

- The MCP server targets one system's grid per deployment, configured via `GRAPHIVAC_GRID_ID` in `mcp.env`.
- Switching systems requires updating `GRAPHIVAC_GRID_ID` (and `GRAPHIVAC_PROJECT_ID` if the project also changed) and restarting the MCP container.
- A `/config` health endpoint and a frontend mismatch warning banner (see `13-99`) make the manual process safe and observable.
- `GRAPHIVAC_ORG_ID` **never** needs to change — it is a deployment-wide constant.

### What a future phase would require

- Evaluate FastMCP's support for per-session or per-request context.
- Refactor all manager classes to accept `grid_id` as a call-time argument.
- Update all tool registrations in `duct_tools.py`, `pipe_tools.py`, `grid_tools.py`, etc.
- Update the agent's internal grid → Graphivac sync flow to pass the active system's `grid_id` at call time.
- Remove the mismatch warning banner (no longer needed once switching is instant).

---

## D-02 — Mid-Session System Switching for the Agent

**Deferred from:** `13-09`
**Category:** UX / Agent Architecture

### What was deferred

Allowing the user to switch the active system while an agent session is already in progress, with the agent immediately picking up the new system's model for its next task.

### Why deferred

The ADK agent is created once per session in `create_app()`. The model name is fixed at session creation time. If the user switches to a system with a different `ai_model_name`, the agent continues using the old model until the session is restarted.

For all other system-level values read at tool call time (Graphivac grid ID, folder path), mid-session switching works correctly — the updated `active_system` in state is read on the next tool call. The model is the only session-fixed value.

### Phase 13 mitigation

- Graphivac coordinates and folder paths switch immediately (read from state at call time).
- Model switching requires a page refresh to start a new session.
- The system selector UI can display a note: "Model changes take effect on the next session."

### What a future phase would require

- Evaluate whether ADK supports hot-swapping the model mid-session.
- Alternatively, trigger a clean session restart (disconnect + reconnect CopilotKit) when the user switches to a system with a different model.

---

## D-03 — Graphivac Grid and Project Deletion via API

**Deferred from:** `13-05`, `13-06`
**Category:** Graphivac API

### What was deferred

Automatically deleting the Graphivac Grid when a system is deleted, and the Graphivac Project when a project is deleted.

### Why deferred

The Graphivac REST API's support for grid and project deletion was not confirmed at planning time. `mcp_server/graphivac/api.json` must be inspected to verify whether `DELETE` endpoints exist for both resources.

### Phase 13 mitigation

- `deleteGrid` and `deleteGraphivacProject` in `mapper/src/lib/graphivac-client.ts` log a warning and resolve normally if the endpoint is unavailable or returns 404.
- Deleting a system or project may leave orphaned Graphivac Grids/Projects that the operator must clean up manually via the Graphivac UI.
- The delete API routes document this limitation in a `warnings` field in the JSON response.

### What a future phase would require

- Confirm `DELETE` endpoints from `api.json` or Graphivac documentation.
- Implement `deleteGrid` and `deleteGraphivacProject` fully once endpoints are confirmed.
- Remove the orphaned-resource warning from delete responses.

---

## D-04 — Agent Scoped to an Entire Project (Multi-System)

**Deferred from:** `13-09`
**Category:** Agent Architecture

### What was deferred

Allowing the agent to operate across all systems within a project simultaneously (e.g. cross-reference BACnet points from multiple systems, generate a multi-system ontology).

### Why deferred

The agent is currently scoped to a single active system. Cross-system operation requires the agent to manage multiple Graphivac grid connections, multiple file folder scopes, and potentially multiple models. This complexity is out of scope for Phase 13.

### Phase 13 mitigation

The agent works on one system at a time. Cross-system tasks must be performed by the user switching systems between agent sessions.

### What a future phase would require

- Extend the agent state to support a list of active systems.
- Add a multi-system path resolver (`get_project_path` at the project level).
- Allow the agent to call Graphivac tools parameterised with different grid IDs within the same session.

---

## D-05 — Dark / Light Mode Support for the Project Management UI

**Deferred from:** `13-UI` (Project Management page redesign, Phase 13)
**Category:** Frontend / UX

### What was deferred

Full dark-mode support for the `/projects` page and its sub-components (`SystemFilePanel`, `ProjectCard`, `SystemCard`, `ProjectEditDialog`, `SystemEditDialog`), consistent with the rest of the application's theme system.

### Why deferred

The project management UI was redesigned late in Phase 13 to adopt a two-panel layout (left sidebar for projects, system tabs at the top, `SystemFilePanel` as the main content area). During that redesign the file/folder cards were styled with hardcoded `bg-white`, `text-slate-*`, and `border-slate-*` classes that do not respond to the application's CSS-variable theme system.

A secondary issue was discovered: Tailwind v4 (`@import "tailwindcss"`) defaults to the **media** dark-mode strategy (OS preference), not the **class** strategy. This caused `dark:` utility variants to apply based on the user's operating-system dark-mode preference rather than the application's own `className="light"` toggle on `<html>`, producing black card backgrounds on systems with OS dark mode enabled regardless of the in-app theme. The short-term fix was to **remove all `dark:` variants** and use CSS variables exclusively, which hardcodes the panel to light-mode appearance only.

### Phase 13 mitigation

- All `dark:` variants were removed from `SystemFilePanel`, `ProjectCard`, `SystemCard`, and related components.
- Every colour now uses the app's CSS custom properties (`--background`, `--foreground`, `--muted-foreground`, `--accent`) so the file/folder panel is theme-neutral — it adapts to the current CSS variable values.
- The Tailwind dark-mode strategy has **not** been switched to `class`; this would be a project-wide change that could break existing `dark:` usages in other components that correctly rely on the media strategy.
- The application currently ships with a hardcoded `className="light"` on `<html>` (`app/layout.tsx`), so end-users are not exposed to a broken dark mode.

### What a future phase would require

1. **Decide on a dark-mode strategy**: switch Tailwind's `darkMode` config to `'class'` (in `tailwind.config.ts` or via the `@custom-variant dark` directive in `globals.css`) so that `dark:` variants are controlled by the application toggle, not the OS preference.
2. **Audit all components** for `dark:` usage to confirm they behave correctly after the strategy change.
3. **Restore dark-mode card styles** in `SystemFilePanel`:
   - Folder / file cards: `bg-[var(--background)] → dark variant` or keep using CSS variables if `--background` is correctly set for dark mode.
   - Card borders: use `border-[var(--muted-foreground)]/15` (already done — no change needed).
   - Dropdown menus and conflict modals: use `bg-[var(--background)]` (already done).
4. **Verify the folder SVG icon** (`FolderSvg`) — the fill colour `#1e293b` (slate-800) is readable on a light background but nearly invisible on a dark background. It should switch to a lighter value (e.g. `#94a3b8` or `#cbd5e1`) in dark mode.
5. **Test** the full `/projects` page in both light and dark mode across the major browser / OS combinations.

---

## D-06 — "In Progress" Agent Status Indicator in the Performance Tab

**Deferred from:** `13-UI` (Performance tab, Phase 13)
**Category:** Frontend / UX

### What was deferred

Displaying a **live "in progress" status** in the Performance tab that indicates whether an agent is currently executing a task. The tab currently only surfaces **past** events (completed tool calls, finished agent runs, historical timings). There is no real-time signal telling the user that work is actively happening right now.

### Why deferred

Surfacing a live agent status requires a reliable, low-latency signal that crosses the boundary between the agent back-end and the frontend:

- The ADK/CopilotKit streaming pipeline emits events when a task starts and ends, but no dedicated "currently running" flag is stored in persistent state — the information only lives transiently in the SSE stream.
- Adding a persistent `agent_running` flag to the CopilotKit shared state raises consistency concerns: if the agent crashes mid-task the flag would remain `true` indefinitely, requiring a timeout or heartbeat mechanism to self-heal.
- The Performance tab is currently a read-only log view; making it reactive to live state requires either polling, a WebSocket/SSE subscription, or integration with the existing CopilotKit state subscription — none of which were designed into the tab during Phase 13.

### Phase 13 mitigation

- The Performance tab shows historical events only; users can infer that the agent is active by observing the chat stream or the spinner in the chat input area.
- No misleading "idle" label is shown — the tab simply omits any live-status section.

### What a future phase would require

1. **Define an `agent_status` state field** (e.g. `"idle" | "running" | "error"`) in the CopilotKit shared state, written by the agent at task start/end and guarded by a TTL/heartbeat to avoid stale `"running"` states after crashes.
2. **Emit status transitions** from the agent entry point (`main.py` / master loop) at the earliest possible moment — before the first LLM call — and reset to `"idle"` in a `finally` block.
3. **Subscribe to the state field** in the Performance tab component and render a prominent live badge (e.g. a pulsing dot labelled "Agent working…") when `agent_status === "running"`, replacing it with an "Idle" badge otherwise.
4. **Handle the error state** visually (e.g. an amber badge "Agent encountered an error — see logs") so the tab becomes the single source of truth for agent health.
5. **Test** status transitions under normal operation, mid-task page refresh, and agent crash scenarios to confirm the badge never gets stuck.

---

## D-07 — Model Picker: Dynamic Dropdown Instead of Free-Form Field

**Deferred from:** `13-10` (runtime model switching)
**Category:** Frontend / UX

### What was deferred

Replacing the free-form `ai_model_name` text input in `SystemEditDialog` with a grouped dropdown populated from a live list of available models, scoped to three providers: **Google (Gemini)**, **Anthropic (Claude)**, and **GitHub Copilot / GitHub Models**.

### Why deferred

The free-form field is functional and unblocks `13-10`. Building a live model list requires integrating with three separate provider APIs and adds a non-trivial amount of backend and frontend surface. It was set aside to keep `13-10` focused.

### What a future phase would require

**Agent backend — `GET /models`** (new router, e.g. `agent/api/routers/models.py`)
- Query each provider whose API key is present in the environment; fall back to a hardcoded curated list if the key is absent or the call fails.
- **Google**: `client.models.list()` from `google-genai` (already a dependency), filtered to `generateContent`-capable models only (to exclude embedding models and deprecated variants — the raw list is noisy).
- **Anthropic**: `client.models.list()` via the `anthropic` SDK; requires `ANTHROPIC_API_KEY`.
- **GitHub Models**: `GET https://models.inference.ai.azure.com/models` with `GITHUB_TOKEN`; LiteLLM uses the `github/` prefix for these.

**Next.js proxy — `GET /api/agent/models`**
Mirrors the pattern of `POST /api/agent/model` (browser → Next.js proxy → `AGENT_BACKEND_URL`).

**Response shape**
```json
[
  { "provider": "google",    "model": "gemini-2.0-flash",           "label": "Gemini 2.0 Flash" },
  { "provider": "anthropic", "model": "claude-3-5-sonnet-20241022", "label": "Claude 3.5 Sonnet" },
  { "provider": "github",    "model": "github/gpt-4o",              "label": "GPT-4o (GitHub)" }
]
```

**Frontend — `SystemEditDialog`**
- Fetch `GET /api/agent/models` when the dialog opens.
- Render a `<select>` grouped by provider (`<optgroup>`), pre-selected on the system's current `ai_model_name`.
- If the fetch fails or returns an empty list, fall back to the existing free-form input so editing is never blocked.

### Notes
- The `model` string in each entry is the LiteLLM-compatible name, sent to `POST /model` unchanged — no mapping needed.
- Providers with no API key configured return nothing; the dropdown shows only what is reachable from the current deployment.
- The Google list requires server-side filtering for `generateContent` support; Anthropic and GitHub lists are smaller and generally clean.
