# Roadmap: HVAC Reconstruction & Mapping

## Phase 1: Sequential Topological Reconstruction (Completed)
**Goal:** Build the foundation by extracting and placing geometry in the frontend.

- **Phase 1.1: Horizontal Duct Extraction**
    - [x] Create/Refine specialized agent for primary horizontal trunk identification.
    - [x] Implement "Grid Reading" tool for agents to understand current frontend state.
- **Phase 1.2: Vertical Duct & Connection Extraction**
    - [x] Create agent for mixing zones and vertical branches.
    - [x] Implement placement logic relative to horizontal trunks.
- **Phase 1.3: Equipment Placement & Alignment**
    - [x] Extract Fans, Coils, Humidifiers.
    - [x] Enforce grid alignment (Y-coordinate matching with parent ducts).
- **Phase 1.4: Engineering Review & Verification**
    - [x] Implement Review Agent to check connectivity (e.g., flow direction, sequence).
    - [x] Human-in-the-loop (HITL) verification pattern for final topology approval.

## Phase 2: Raw Information Extraction & Mapping (Current Focus)
**Goal:** Extract technical data from source files and map them as raw components to the frontend for human verification.

- **Phase 2.1: Infrastructure & MCP Tools**
    - [x] Implement `write_metadata` tool in `mcp_server/graphivac/metadata_tools.py`.
    - [x] Create `MetadataManager` in `mcp_server/graphivac/metadata_manager.py`.
    - [x] Verify `read_grid` integration with multimodal sub-agents.
    - [x] Implement `save_agent_state` in `agent/tools/state_tools.py` using `ToolContext.state`.
- **Phase 2.2: Specialized Raw Data Agents (Multimodal)**
    - [x] Create Bacnet Sub-Agent.
    - [x] Create Control Sub-Agent.
    - [x] Create Electricity Sub-Agent.
- **Phase 2.3: Iterative Technical Mapping Loop**
    - [ ] Implement the loop to process all grid equipment and attach raw technical metadata.
- **Phase 2.4: Human Verification (HITL)**
    - [ ] Human review of extracted raw data on the frontend before semantic processing.

## Phase 3: Semantic Graph Generation
**Goal:** Transform verified raw data into standardized ontologies (ASHRAE 223P, Haystack).

- **Phase 3.1: Ontology Mapping & Graph Construction**
- **Phase 3.2: Export Logic & Validation**


# Requirements Mapping
| Req ID | Phase | Plan Status |
| :--- | :--- | :--- |
| REQ-1 | Phase 2.1 | Completed |
| REQ-2 | Phase 1.1, 1.2, 1.3 | Completed |
| REQ-3 | Phase 1.1 | Completed |
| REQ-4 | Phase 1.4 | Completed |
| REQ-5 | Phase 2.3 | Pending |
| REQ-6 | Phase 3.1 | Pending |
| REFAC-01 | Phase 6 | Planned |
| REFAC-02 | Phase 6 | Planned |
| REFAC-03 | Phase 6 | Planned |
| REFAC-04 | Phase 6 | Planned |

## Phase 4: Dependency Modernization & UI Optimization (SVAR Migration)
**Goal:** Remove legacy dependencies (Chonky, Material UI v4) and replace with SVAR React File Manager to ensure compatibility with React 19 and Next.js 16.

- **Phase 4.1: Remove Chonky Legacy Layers**
    - [x] Uninstall `chonky` and `chonky-icon-fontawesome`.
    - [ ] Strip out `@material-ui/core` and related v4 dependencies.
- **Phase 4.2: Implement SVAR React File Manager**
    - [ ] Install `@svar/react-file-manager`.
    - [ ] Replace `Chonky` file explorer with `SVAR File Manager` in the frontend.
- **Phase 4.3: Compatibility Verification**
    - [ ] Verify that the application builds and runs without peer dependency warnings.
    - [ ] Ensure full React 19 / Next.js 16 functionality.

## Phase 5: Agent-Frontend Interface & Performance Metrics
**Goal:** Establish a robust communication layer between the reasoning agent and the React frontend, ensuring transparency of thoughts, tool calls, and performance metrics.

- **Phase 5.1: Communication Layer Audit**
    - [ ] Map all callbacks (pre-model, post-model) between Agent and Frontend.
    - [ ] Simplify internal agent communication logic.
- **Phase 5.2: UI Rendering of Agent State**
    - [ ] Implement rendering for agent "thoughts" and "instructions".
    - [ ] Ensure real-time tool call status visibility on the HUD.
- **Phase 5.3: Performance Metrics Dashboard**
    - [ ] Identify and extract key performance metrics (latency, token usage, success rate).
    - [ ] Render metrics in a frontend dashboard/HUD for developer visibility.

### Phase 6: Refactor GraphyVAC API

**Goal:** Decouple agent from direct MCP calls by introducing an internal state layer (ToolContext.state) and a standalone sync service that replicates state to GraphyVAC via existing MCP server.
**Requirements**: [REFAC-01, REFAC-02, REFAC-03, REFAC-04]
**Depends on:** Phase 5
**Plans:** 3/3 plans complete

Plans:
- [ ] 06-01-PLAN.md — Internal grid tools (ToolContext.state CRUD) + agent wiring
- [ ] 06-02-PLAN.md — Standalone sync service (poll, diff, MCP replication)
- [ ] 06-03-PLAN.md — Unit tests + end-to-end verification

### Phase 7: Replace MCP sync-out with direct REST PUT via bidirectional EDN-JSON translator

**Goal:** Eliminate the MCP server from the sync lifecycle. Build a hardcoded bidirectional EDN-JSON translator so the before_agent_callback saves the raw EDN grid, and the after_agent_callback rebuilds full comps and PUTs the grid back in a single REST call. Also fixes the `:rot` vs `:rotation` bug in fan/damper rotation parsing.
**Depends on:** Phase 6
**Plans:** 2/3 plans executed

Plans:
- [ ] 07-01-PLAN.md — Bidirectional EDN-JSON translator module + unit tests (TDD)
- [ ] 07-02-PLAN.md — Rewrite sync callbacks (before: translator + _raw_edn_grid, after: full rebuild + REST PUT)
- [ ] 07-03-PLAN.md — Integration test against real GraphyVAC + human verification

### Phase 8: Implement capture_frontend_state visual verification tool

**Goal:** Upgrade the Master Agent from a "data-blind" command issuer into a "vision-guided" engineer by adding a two-tool visual verification loop. The agent will be able to take an on-demand screenshot of the live GraphyVAC CAD canvas (via Playwright headless capture), save it as a session artifact, and then use the existing `load_artifacts` tool to inject the image inline into its context — allowing it to visually compare the canvas against the original HVAC reference image and self-correct before declaring a phase complete.

**Architecture:**
The implementation leverages the existing ADK artifact system already in use by `ingest_category_files` and `load_artifacts`. The two-step verification loop is entirely agent-driven (no callbacks required):

1. `capture_frontend_state()` — new `BaseTool` subclass that:
   - Launches a Playwright headless Chromium instance
   - Navigates to `GRAPHIVAC_VIEW_URL` (env var, same URL as the iframe view mode)
   - Waits for canvas `networkidle` + 2s render buffer
   - Takes a full-viewport PNG screenshot
   - Wraps bytes as `types.Part(inline_data=types.Blob(mime_type="image/png", data=png_bytes))`
   - Calls `await tool_context.save_artifact("verification/latest_snapshot.png", part)`
   - Returns `{"status": "success", "artifact": "verification/latest_snapshot.png"}`

2. Agent then calls the existing `load_artifacts(artifact_names=["verification/latest_snapshot.png"])` — the ADK `LoadArtifactsTool.process_llm_request` detects the function response, loads the `image/png` Part from the artifact service, and appends it directly to `llm_request.contents` as inline bytes. The model sees the pixels.

**Key constraints validated from ADK source:**
- Tool return values must be `dict` — binary cannot be returned directly from `run_async` (ADK wraps non-dict returns as `{'result': value}`)
- `image/png` MIME type passes through `_as_safe_part_for_llm` unchanged (it is in `_GEMINI_SUPPORTED_INLINE_MIME_PREFIXES`)
- `ToolContext.save_artifact` / `load_artifact` are available — artifact service is already configured via CopilotKit wrapper
- `load_artifacts` parameter is `artifact_names` (array), NOT `filenames`
- No `before_model_callback` needed — the existing `LoadArtifactsTool.process_llm_request` handles the injection automatically

**Files to create/modify:**
- `agent/master_architecture/tools/capture_frontend_state_tool.py` — new tool (mirrors pattern of `ingest_category_files_tool.py`)
- `agent/master_architecture/create_master_agent.py` — register new tool
- `agent/master_architecture/prompts/master_instruction.md` — add Visual Verification Protocol section
- `agent/pyproject.toml` (or requirements) — add `playwright` dependency + `playwright install chromium`

**Depends on:** Phase 7
**Plans:** 2 plans

Plans:
- [ ] 08-01-PLAN.md — capture_frontend_state tool + playwright setup + agent registration
- [ ] 08-02-PLAN.md — master_instruction.md verification protocol + end-to-end test
