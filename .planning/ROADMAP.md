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
| REFAC-01 | Phase 6 | Completed |
| REFAC-02 | Phase 6 | Completed |
| REFAC-03 | Phase 6 | Completed |
| REFAC-04 | Phase 6 | Completed |
| P10-01 | Phase 10 | Completed |
| P10-02 | Phase 10 | Completed |
| P10-03 | Phase 10 | Completed |
| P10-04 | Phase 10 | Completed |
| P10-05 | Phase 10 | Completed |
| P11-01 | Phase 11 | Planned |
| P11-02 | Phase 11 | Planned |
| P11-03 | Phase 11 | Planned |
| P11-04 | Phase 11 | Planned |
| P13-01 | Phase 13 | Planned |
| P13-02 | Phase 13 | Planned |
| P13-03 | Phase 13 | Planned |
| P13-04 | Phase 13 | Planned |
| P13-05 | Phase 13 | Planned |
| P13-06 | Phase 13 | Planned |
| P13-07 | Phase 13 | Planned |
| R14-01 | Phase 14 | Planned |
| R14-02 | Phase 14 | Planned |
| R14-03 | Phase 14 | Planned |
| R14-04 | Phase 14 | Planned |
| R14-05 | Phase 14 | Planned |
| R14-06 | Phase 14 | Planned |
| R14-07 | Phase 14 | Planned |
| P15-01 | Phase 15 | Planned |
| P15-02 | Phase 15 | Planned |
| P15-03 | Phase 15 | Planned |
| P15-04 | Phase 15 | Planned |
| P15-05 | Phase 15 | Planned |
| P15-06 | Phase 15 | Planned |
| P15-07 | Phase 15 | Planned |
| P15-08 | Phase 15 | Planned |
| P15-09 | Phase 15 | Planned |
| P15-10 | Phase 15 | Planned |
| P16-01 | Phase 16 | Planned |
| P16-02 | Phase 16 | Planned |
| P16-03 | Phase 16 | Planned |
| P16-04 | Phase 16 | Planned |
| P16-05 | Phase 16 | Planned |
| P16-06 | Phase 16 | Planned |
| P16-07 | Phase 16 | Planned |
| P16-08 | Phase 16 | Planned |
| P16-09 | Phase 16 | Planned |
| P16-10 | Phase 16 | Planned |
| P16-11 | Phase 16 | Planned |
| P16-12 | Phase 16 | Planned |
| P16-13 | Phase 16 | Planned |
| P17-01 | Phase 17 | Planned |
| P17-02 | Phase 17 | Planned |
| P17-03 | Phase 17 | Planned |
| P17-04 | Phase 17 | Planned |
| P17-05 | Phase 17 | Planned |
| P17-06 | Phase 17 | Planned |
| P17-07 | Phase 17 | Planned |
| P19-01 | Phase 19 | Planned |
| P19-02 | Phase 19 | Planned |
| P19-03 | Phase 19 | Planned |
| P19-04 | Phase 19 | Planned |
| P19-05 | Phase 19 | Planned |
| P19-06 | Phase 19 | Planned |
| P19-07 | Phase 19 | Planned |
| P19-08 | Phase 19 | Planned |
| P19-09 | Phase 19 | Planned |

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

## Phase 5: Agent-Frontend Interface & Performance Metrics (Completed)
**Goal:** Establish a robust communication layer between the reasoning agent and the React frontend, ensuring transparency of thoughts, tool calls, and performance metrics.

- **Phase 5.1: Communication Layer Audit**
    - [x] Map all callbacks (pre-model, post-model) between Agent and Frontend.
    - [x] Simplify internal agent communication logic.
- **Phase 5.2: UI Rendering of Agent State**
    - [x] Implement rendering for agent "thoughts" and "instructions".
    - [x] Ensure real-time tool call status visibility on the HUD.
- **Phase 5.3: Performance Metrics Dashboard**
    - [x] Identify and extract key performance metrics (latency, token usage, success rate).
    - [x] Render metrics in a frontend dashboard/HUD for developer visibility.

### Phase 6: Refactor Graphivac API (Completed)

**Goal:** Decouple agent from direct MCP calls by introducing an internal state layer (ToolContext.state) and a standalone sync service that replicates state to Graphivac via existing MCP server.
**Requirements**: [REFAC-01, REFAC-02, REFAC-03, REFAC-04]
**Depends on:** Phase 5
**Plans:** 3/3 plans complete

Plans:
- [x] 06-01-PLAN.md — Internal grid tools (ToolContext.state CRUD) + agent wiring
- [x] 06-02-PLAN.md — Standalone sync service (poll, diff, MCP replication)
- [x] 06-03-PLAN.md — Unit tests + end-to-end verification

### Phase 7: Replace MCP sync-out with direct REST PUT via bidirectional EDN-JSON translator (Completed)

**Goal:** Eliminate the MCP server from the sync lifecycle. Build a hardcoded bidirectional EDN-JSON translator so the before_agent_callback saves the raw EDN grid, and the after_agent_callback rebuilds full comps and PUTs the grid back in a single REST call. Also fixes the `:rot` vs `:rotation` bug in fan/damper rotation parsing.
**Depends on:** Phase 6
**Plans:** 3/3 plans complete

Plans:
- [x] 07-01-PLAN.md — Bidirectional EDN-JSON translator module + unit tests (TDD)
- [x] 07-02-PLAN.md — Rewrite sync callbacks (before: translator + _raw_edn_grid, after: full rebuild + REST PUT)
- [x] 07-03-PLAN.md — Integration test against real Graphivac + human verification

### Phase 8: Implement capture_frontend_state visual verification tool (Completed)

**Goal:** Upgrade the Master Agent from a "data-blind" command issuer into a "vision-guided" engineer by adding a two-tool visual verification loop. The agent will be able to take an on-demand screenshot of the live Graphivac CAD canvas (via Playwright headless capture), save it as a session artifact, and then use the existing `load_artifacts` tool to inject the image inline into its context — allowing it to visually compare the canvas against the original HVAC reference image and self-correct before declaring a phase complete.

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
**Plans:** 2/2 plans complete

Plans:
- [x] 08-01-PLAN.md — capture_frontend_state tool + playwright setup + agent registration
- [x] 08-02-PLAN.md — master_instruction.md verification protocol + end-to-end test

### Phase 9: Integrate _223P agent into master architecture via sub-agent or skills

**Goal:** Promote the existing 223P ontology pipeline from a standalone runner into two flat, independent sub-agents (ontology_generator and ontology_validator) that the Master Agent can delegate to directly, with code snapshot versioning in ToolContext.state and a new frontend Code tab for browsing generated ontology code iterations.
**Requirements**: [P9-01, P9-02, P9-03, P9-04, P9-05, P9-06, P9-07, P9-08]
**Depends on:** Phase 8
**Plans:** 4/4 plans complete

Plans:
- [x] 09-01-PLAN.md — Exit tools + checkpoint_code tool (generator + validator exit tools with state snapshots)
- [x] 09-02-PLAN.md — Agent files (OntologyGeneratorAgent + OntologyValidatorAgent LoopWrappers + prompts)
- [x] 09-03-PLAN.md — Wire into master architecture (create_master_agent.py + master_instruction.md)
- [x] 09-04-PLAN.md — Frontend TTL/Python tabs (CodeWindow.tsx + navbar/content wiring)

### Phase 10: TTL to Neo4j database integration with frontend graph visualization

**Goal:** Load the generated `ontology.ttl` into a Neo4j graph database (with Neosemantics plugin) via a new master agent tool, expose it through a Next.js API route, and render an interactive Sigma.js WebGL graph visualization in the existing Graph tab with ForceAtlas2 layout, hover/click interactions, zoom-triggered labels, and a toolbar overlay.
**Requirements**: [P10-01, P10-02, P10-03, P10-04, P10-05]
**Depends on:** Phase 9
**Plans:** 4/4 plans complete

Plans:
- [x] 10-01-PLAN.md — Docker Neo4j service + Python load_ttl_to_neo4j tool + master agent wiring + tests
- [x] 10-02-PLAN.md — npm deps (Sigma.js, graphology, neo4j-driver) + GET /api/graph API route
- [x] 10-03-PLAN.md — GraphWindow.tsx (Sigma.js + ForceAtlas2 + interactions + toolbar) + tab wiring
- [x] 10-04-PLAN.md — End-to-end human verification (Neo4j + import + API + graph visualization)

### Phase 11: optimization of the coding agent

**Goal:** Reduce context window consumption in the Ontology Generator and Validator agents by replacing three expensive, unconditional operations with cheaper, targeted alternatives: keyword-filtered file scanning, grep-like JSONL class lookup, and LESSONS.md-first skill reading.
**Requirements**: [P11-01, P11-02, P11-03, P11-04]
**Depends on:** Phase 10
**Plans:** 4/4 plans complete

Plans:
- [ ] 11-01-PLAN.md — TDD: scan_python_files_filtered tool + unit tests
- [ ] 11-02-PLAN.md — TDD: search_class_mapping tool + unit tests
- [ ] 11-03-PLAN.md — Agent tool swap + prompt rewrites + agent tests + JSONL cleanup
- [ ] 11-04-PLAN.md — SKILL.md LESSONS.md-first logic + LESSONS.md skeleton

### Phase 12: Session persistence and management with database backend

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 11
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 12 to break down)

### Phase 13: Migrate OntologyGenerator and OntologyValidator sub-agents to master agent skills

**Goal:** Remove OntologyGeneratorAgent and OntologyValidatorAgent as AgentTool-wrapped sub-agents, give all ontology tools directly to MasterLlmAgent, and convert sub-agent prompts into two ADK skills (skill-ontology-generation and skill-ontology-validation) so the master runs generation and validation in its own loop, fixing sub-agent event streaming issues.
**Requirements**: [P13-01, P13-02, P13-03, P13-04, P13-05, P13-06, P13-07]
**Depends on:** Phase 12
**Plans:** 2/2 plans complete

Plans:
- [ ] 13-01-PLAN.md — Adapted exit tools (EXIT_LEVEL_2) + two new SKILL.md files
- [ ] 13-02-PLAN.md — Rewire create_master_agent.py + max_iterations=100 + master_instruction.md update + tests

### Phase 14: Write comprehensive research report on SI-Mapper development

**Goal:** Produce a complete LaTeX research report documenting the SI-Mapper project from theoretical background (building ontologies, ASHRAE 223P) through the BACnet mapping problem, the agentic AI solution, nine experimental iterations, and the final skills-based architecture, with placeholder tables for experiment results comparing AI vs human engineer performance.
**Requirements**: [R14-01, R14-02, R14-03, R14-04, R14-05, R14-06, R14-07]
**Depends on:** Phase 13
**Plans:** 4/4 plans complete

Plans:
- [ ] 14-01-PLAN.md — LaTeX skeleton (main.tex + 6 section stubs) + 3 Mermaid diagrams rendered to PNG
- [ ] 14-02-PLAN.md — Sections 1 (Introduction), 2 (Problem), 3 (Solution)
- [ ] 14-03-PLAN.md — Section 4 (Implementation) + Section 5 (Results placeholder)
- [ ] 14-04-PLAN.md — Section 6 (Conclusions) + final compilation verification

### Phase 15: Refactor coding skills and standardize agent architecture

**Goal:** Delete dead sub_agents/ code, migrate root 223p/ into agent/223p/ with session-scoped archives, implement three-write pattern for real-time CodeWindow visibility, add extract_lessons tool, and audit both ontology skills for correct paths and enhanced workflows.
**Requirements**: [P15-01, P15-02, P15-03, P15-04, P15-05, P15-06, P15-07, P15-08, P15-09, P15-10]
**Depends on:** Phase 14
**Plans:** 3/3 plans complete

Plans:
- [ ] 15-01-PLAN.md — Delete sub_agents/ directory + clean up stale tests
- [ ] 15-02-PLAN.md — Migrate 223p/ files + update path constants + three-write pattern + extract_lessons tool
- [ ] 15-03-PLAN.md — Audit and enhance skill-ontology-generation and skill-ontology-validation

### Phase 16: Optimize ontology skills

**Goal:** Fix 21 identified issues across the ontology pipeline: delete redundant _persist helpers, clean exit tool signatures (remove code=/ttl_content= params), fold checkpoint_code into write_ontology, fix Linux venv detection, add scan_python_folder cap, and update all three SKILL.md files for accuracy.
**Requirements**: [P16-01, P16-02, P16-03, P16-04, P16-05, P16-06, P16-07, P16-08, P16-09, P16-10, P16-11, P16-12, P16-13]
**Depends on:** Phase 15
**Plans:** 4/5 plans complete

Plans:
- [ ] 16-01-PLAN.md — Delete _persist_python and _persist_ttl helpers + remove all call sites
- [ ] 16-02-PLAN.md — Clean exit signatures, fold checkpoint_code, fix venv path, add scan cap, update docstrings
- [ ] 16-03-PLAN.md — Update generation, validation, and lessons SKILL.md files
- [ ] 16-04-PLAN.md — Update tests for all changed behavior

### Phase 17: Restructure BACnet custom fields to flat numbered entries

**Goal:** Replace the `{"bacnet": {"ADDR": {...}}}` custom_fields structure with a flat numbered format `{"bacnet_1": {"address": "ADDR", ...}, "bacnet_2": {...}}` across all write paths (internal grid tools, ADK metadata tools, MCP metadata manager), the EDN translator, the BACnet skill documentation, and the live integration test.
**Requirements**: [P17-01, P17-02, P17-03, P17-04, P17-05, P17-06, P17-07]
**Depends on:** Phase 16
**Plans:** 2/2 plans complete

Plans:
- [ ] 17-01-PLAN.md — Create explode_bacnet_points helper + wire into all 4 write-path files
- [ ] 17-02-PLAN.md — Update EDN translator verification + SKILL.md + live integration test

### Phase 18: optimize skill for ontology validation

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 17
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 18 to break down)

### Phase 19: Standardize agent exit tools across all skills

**Goal:** Replace 5 fragmented exit tools with 2 generic ones (`exit_with_success`, `exit_with_failure`), move TTL snapshot patching into `execute_ontology`, update all registrations, add exit steps to all 5 skills, and add one-task-at-a-time rule to master instruction.
**Requirements**: [P19-01, P19-02, P19-03, P19-04, P19-05, P19-06, P19-07, P19-08, P19-09]
**Depends on:** Phase 18
**Plans:** 3 plans

Plans:
- [ ] 19-01-PLAN.md — Create exit_tools.py + move snapshot patching to execute_ontology + update registrations + delete old files
- [ ] 19-02-PLAN.md — Update all 5 skills with exit_with_success/exit_with_failure + master instruction one-task-at-a-time rule
- [ ] 19-03-PLAN.md — Update tests for new exit tools, snapshot patching, and wiring
