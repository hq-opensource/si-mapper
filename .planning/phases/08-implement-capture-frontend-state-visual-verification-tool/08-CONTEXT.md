# Phase 8: capture_frontend_state Visual Verification Tool — Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a single new agent tool (`capture_frontend_state`) that takes an on-demand Playwright screenshot of the live GraphyVAC canvas, saves it as a session artifact, and returns a confirmation dict. The agent then calls the existing `load_artifacts` tool to inject the image inline into its context window, enabling visual comparison against the reference image.

This closes the self-correction loop: the agent can verify what it actually built, not just what it told `internal_grid`. No callbacks, no new infrastructure — piggybacks entirely on the existing artifact system.

</domain>

<decisions>
## Implementation Decisions

### View URL construction
- Build the GraphyVAC view URL from the 4 existing env vars already in `.env`:
  `GRAPHIVAC_BASE_URL`, `GRAPHIVAC_ORG_ID`, `GRAPHIVAC_PROJECT_ID`, `GRAPHIVAC_GRID_ID`
- Use the **view-only mode**, not the editor — appending `?iframe=t&init-zoom=t` to the constructed URL.
  Format: `https://graphivac.hvac.io/o/{ORG_ID}/p/{PROJECT_ID}/g/{GRID_ID}?iframe=t&init-zoom=t`
- No new `GRAPHIVAC_VIEW_URL` env var — construct it at tool runtime from existing vars.
- No auth headers needed — the view URL is public (same URL already used in the frontend iframe).

### Playwright startup timing
- **No explicit sleep/wait** inside the tool before capture.
- The Playwright browser launch + page navigation + `networkidle` wait is itself enough time for the GraphyVAC REST PUT (fired by `after_model_callback`) to complete.
- The agent calling the tool creates natural latency — by the time Chromium starts and the page loads, the canvas will reflect the latest `internal_grid` state.

### Verification trigger — when the agent calls this tool
- The agent calls `capture_frontend_state` **when it believes it has finished a task** (e.g., "I've placed all 25 equipment components").
- `master_instruction.md` must include an explicit instruction: *"When you believe you have finished placing all components for a phase, call `capture_frontend_state()` to get a visual snapshot of the canvas. Then call `load_artifacts(artifact_names=['verification/latest_snapshot.png'])` to inspect it. Use the image to verify your work against the reference before declaring the task complete."*
- This prevents false "done" declarations — the agent must see the canvas, not just trust `internal_grid`.

### Failure behavior
- If Playwright fails for any reason (browser crash, page timeout, canvas not loaded): return `{"status": "error", "message": "Could not capture canvas snapshot: <reason>"}`.
- The agent should treat this as a soft failure — log it, proceed with finishing the task, and mark work as done without visual verification.
- No retry logic. No retry on failure. Simple error return.

### Tool registration
- New file: `agent/master_architecture/tools/capture_frontend_state_tool.py`
- Registered in `task_tools` list in `agent/master_architecture/create_master_agent.py` alongside existing tools.
- Follows same `BaseTool` subclass pattern as `ingest_category_files_tool.py`.

### Playwright dependency
- Add `playwright` to `agent/pyproject.toml` dependencies.
- Chromium must be installed: `playwright install chromium` (add to dev setup docs or a setup script).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing artifact pattern to mirror
- `agent/master_architecture/tools/ingest_category_tool.py` — The exact pattern to follow: `BaseTool` subclass, `run_async` calls `await tool_context.save_artifact(filename, part)`, returns a JSON dict. This is the template.
- `agent/.venv/lib/python3.13/site-packages/google/adk/tools/load_artifacts_tool.py` — How `load_artifacts` processes the function response in `process_llm_request` to inject artifact Parts into `llm_request.contents`. Confirms that `image/png` passes through untouched.

### Tool registration
- `agent/master_architecture/create_master_agent.py` — Where to add the new tool to `task_tools` list.

### Agent instruction to update
- `agent/master_architecture/prompts/master_instruction.md` — Add the Visual Verification Protocol section explaining the 2-step call sequence.

### GraphyVAC view URL pattern
- `mapper/src/app/page/components/ExternalPageIframe.tsx` — Reference for the iframe URL format (`?iframe=t&init-zoom=t`). The view-only URL is what Playwright navigates to.
- `agent/.env` (or `.env.example`) — Existing env vars: `GRAPHIVAC_BASE_URL`, `GRAPHIVAC_ORG_ID`, `GRAPHIVAC_PROJECT_ID`, `GRAPHIVAC_GRID_ID`.

### Dependency management
- `agent/pyproject.toml` — Add `playwright` here.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `agent/master_architecture/tools/ingest_category_tool.py`: Direct template — copy the `BaseTool` subclass structure, `_get_declaration()`, and `run_async()` shape. Replace file-loading logic with Playwright capture + `save_artifact`.
- `google.genai.types.Part` + `types.Blob`: Already used in `ingest_category_tool.py` for images (`load_image_part`). Same `types.Part(inline_data=types.Blob(mime_type="image/png", data=bytes))` pattern applies here.
- Existing env var reading pattern: `os.getenv("GRAPHIVAC_ORG_ID")` etc. — already established across the codebase.

### Established Patterns
- `task_tools` list in `create_master_agent.py` is the registration point for all agent-callable tools — no other wiring needed.
- `artifact_names` (not `filenames`) is the parameter the agent passes to `load_artifacts` — this must appear verbatim in the `master_instruction.md` snippet.

### Integration Points
- Tool plugs into `task_tools` list — zero changes to callbacks, MCP server, or CopilotKit integration.
- `master_instruction.md` updated with a "Visual Verification Protocol" section below the existing operational instructions.
- No changes to `level_3_master_main_llm.py` or any callback.

</code_context>

<specifics>
## Specific Ideas

- The view URL format (confirmed from frontend iframe): `https://graphivac.hvac.io/o/{ORG_ID}/p/{PROJECT_ID}/g/{GRID_ID}?iframe=t&init-zoom=t` — but GRAPHIVAC_BASE_URL is `https://graphivac.hvac.io/api/v1`, so the view URL is constructed separately (not from BASE_URL — strip `/api/v1` and append the web path).
- The Playwright capture should use `wait_until="networkidle"` to ensure the canvas SVG/WebGL is fully rendered before screenshot.
- Artifact saved as `"verification/latest_snapshot.png"` — overwritten every time (no versioning needed; only the latest snapshot is useful).
- The 2-step protocol in master_instruction.md should be presented as a numbered list so the agent treats it as a strict sequence: (1) call `capture_frontend_state()`, (2) call `load_artifacts(artifact_names=["verification/latest_snapshot.png"])`.

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope.

</deferred>

---

*Phase: 08-implement-capture-frontend-state-visual-verification-tool*
*Context gathered: 2026-03-19*
