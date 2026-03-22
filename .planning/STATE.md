---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_phase: 11
status: unknown
last_updated: "2026-03-22T18:21:31.098Z"
progress:
  total_phases: 11
  completed_phases: 5
  total_plans: 20
  completed_plans: 18
---

# State: HVAC Reconstruction Project

## Project Progress

- **Current Phase:** 11
- **Overall Completion:** [█████████░] 85%
- **Active Plan:** 11-04 (complete)
- **Last Completed:** 11-04 (LESSONS.md-first reading logic via Step 0 + Distillation Protocol in SKILL.md + LESSONS.md skeleton)

## Milestone Status (v2.0: Raw Mapping)

- [x] Metadata Infrastructure (MCP) ✅
- [x] Grid Read Verification ✅
- [x] Bacnet Agent (Verified 2.2.1) ✅
- [x] Control Agent (Verified 2.2.2) ✅
- [x] Electricity Agent (Verified 2.2.3) ✅

## Performance Metrics

- **Success Rate (Extraction):** N/A
- **Average Accuracy (Geometry):** N/A
- **Time to Reconstruct:** N/A

## Session Continuity (2026-02-17)

### Recent Decisions

- Defined the 3-Step core mission (Replicate -> Extract -> Graph).
- Verified `read_grid` and MCP tool synchronization.
- **Decision:** Aborted Agentic Vision Pilot due to model configuration complexity and performance trade-offs; reverting to stable Phase 2 goal.
- **Decision:** Completed Bacnet Agent Logic and Verification (2.2.1).
- **Decision (06-01):** Internal grid state lives at ToolContext.state['internal_grid']; line types (duct/pipe) use start/end coords, point types use single coord; metadata remains MCP-only.
- **Decision (06-02):** Sync service diffs internal_grid by component name; deletes before creates to avoid name collisions; one streamablehttp_client session per MCP call (mirrors ADK parallel pattern); purely additive standalone service, no MCP server or agent modifications.
- **Decision (06-03):** Tests use MockToolContext (no ADK runtime) and sys.modules stubs before import; call_tool mocked with async recorder for MCP mapping tests; asyncio.run() preferred over deprecated get_event_loop().run_until_complete().
- **Decision (07-01):** Rotation uses Keyword('rot') not Keyword('rotation') — pre-existing bug fixed in new translator; edn_to_mutable.py is a standalone local copy; SYMBOL_TO_AGENT has 23 entries; unknown EDN symbols silently dropped with warning log.
- **Decision (07-02):** No diff, no snapshot: after_callback does full comps rebuild from internal_grid every turn; only comps key replaced in _raw_edn_grid preserving title/font metadata; retry-once on PUT failure with types.Content error injection on unrecoverable failure.
- **Decision (08-01):** Playwright imported lazily inside run_async (not top-level) so the module loads at agent startup even before chromium is installed; artifact path fixed to verification/latest_snapshot.png for predictable load_artifacts calls.
- **Decision (08-02):** Visual Verification Protocol inserted BEFORE the STOP block in master_instruction.md to maintain operational instruction doc structure; test_url_construction kept as separate test function for intent clarity.
- **Decision (09-01):** checkpoint_code is the ONLY exit tool that does NOT set actions.escalate — loop continuation is the key invariant for the validator iteration cycle.
- **Decision (09-01):** Read-copy-write pattern enforced for all list mutations in ToolContext.state to avoid ADK session mutation issues: list(state.get(..., [])) → append → reassign.
- **Decision (09-02):** Internal agent names use short suffix (OntologyGeneratorInternal / OntologyValidatorInternal), not the longer *AgentInternal pattern from _223p.
- **Decision (09-02):** LoopWrapper stores sub-agent in sub_agents[0] (inherited from LoopAgent) — tests access internal agent via agent.sub_agents[0].name.
- **Decision (09-04):** User renamed 'code' tab to 'TTL' and added separate 'Python' tab — accepted as intentional UX improvement reflecting distinct data artifacts (python_code_snapshots vs ttl_code_snapshots). CodeWindow accepts type prop to serve both tabs.
- **Decision (09-03):** ASHRAE 223P Code Generation Protocol requires explicit human instruction — no auto-trigger to prevent unintended ontology generation.
- **Decision (09-03):** all_subagents = (subagents or []) + ontology_subagents preserves existing caller interface while always including ontology sub-agents.
- **Decision (10-01):** neo4j Docker service uses NEO4J_PLUGINS (not deprecated NEO4JLABS_PLUGINS) for Neo4j 5 compatibility; graph profile isolates it from deploy/tools profiles.
- **Decision (10-01):** load_ttl_to_neo4j is HITL-gated — Do NOT auto-trigger; explicit human instruction required to prevent accidental wipe of Neo4j graph.
- **Decision (10-01):** Path mock chain for multi-segment paths: set __truediv__ on both root and leaf to return the same leaf MagicMock — ensures all 4 path segments resolve to the controllable mock.
- **Decision (10-02):** Jest config uses .js extension (not .ts) to avoid ts-node dependency on Jest 30.
- **Decision (10-02):** Neo4j mock uses globalThis bridge to expose mock fn from hoisted jest.mock() factory, avoiding temporal dead zone caused by global driver singleton being created at module import time.
- **Decision (10-03):** Dynamic sigma.setSetting(nodeReducer) inside useEffect avoids stale closure over React state — do NOT pass reducers as SigmaContainer props.
- **Decision (10-03):** SigmaContent coordinator groups all SigmaContainer children (GraphLoader, GraphEvents, ToolbarInner, NodeInfoCardInner) to share isRunning/layoutControls/activeNode state via callbacks without a context provider.
- **Decision (10-04):** n10s void stored procedures (e.g. n10s.graphconfig.drop()) do not support YIELD — omit YIELD clause entirely.
- **Decision (10-04):** GraphWindow must use Next.js dynamic() with ssr:false — WebGL2RenderingContext is undefined in Node.js SSR.
- **Decision (10-04):** n10s always inserts "Resource" as the first label; skip it and use the second label as the node display type for color coding.
- **Decision (10-04):** TTL persisted to uploads/ttl/latest_ontology.ttl so agent tool can reload without re-upload from user.
- **Decision (11-04):** LESSONS.md is authoritative when present — no fallback to raw asset walk; Step 0 in Reading Protocol has a hard stop to reduce context consumption.
- **Decision (11-04):** Distillation is HITL-gated — explicit human instruction only, never auto-trigger.
- **Decision (11-01):** scan_python_files_filtered uses case-insensitive substring matching (any kw in content.lower()) — OR logic across keywords.
- **Decision (11-01):** Files with OSError during read are skipped in filtered results rather than included with error placeholder — simpler and avoids returning noise.

### Next Steps

1. Phase 11 in progress — 11-04 complete (LESSONS.md-first reading logic established)
2. Remaining Phase 11 plans pending

### Session Log

- **2026-03-18:** Completed 06-01-PLAN.md. Created internal_grid_tools.py (6 functions, 25 component types). Wired into master agent.
- **2026-03-18:** Completed 06-02-PLAN.md. Created sync_service/ (McpSyncClient, SyncEngine, main.py). Standalone polling service that replicates internal_grid to Graphivac via MCP every 2s.
- **2026-03-18:** 06-03 Task 1 complete (3553d2e). 26 unit tests pass: 17 for internal_grid_tools, 9 for sync_engine. Paused at checkpoint Task 2 (human end-to-end verification).
- **2026-03-19:** Completed 07-01-PLAN.md. Created edn_to_mutable.py + grid_edn_translator.py (23-entry SYMBOL_TO_AGENT, bidirectional). 15 unit tests pass covering all 25 types. Rotation bug fix confirmed.
- **2026-03-19:** Completed 07-02-PLAN.md. Rewrote both sync callbacks. before_callback uses translator + saves _raw_edn_grid. after_callback does full comps rebuild + single REST PUT. MCP eliminated from sync lifecycle.
- **2026-03-19:** 07-03 Task 1 complete (e0596f1). Created tests/test_integration_grid_sync.py standalone integration test. Paused at checkpoint Task 2 (human visual verification in Graphivac UI).
- **2026-03-20:** Completed 08-01-PLAN.md. Created capture_frontend_state_tool.py (CaptureFrontendStateTool, headless Playwright screenshot). Registered in create_master_agent.py. Added playwright>=1.40.0 to pyproject.toml.
- **2026-03-19:** Completed 08-02-PLAN.md. Added Visual Verification Protocol to master_instruction.md. Created agent/tests/test_capture_frontend_state.py (4 unit tests, all passing, mocked Playwright).
- **2026-03-20:** Completed 09-01-PLAN.md. Created ontology_generator/exit_tools.py (2 functions) and ontology_validator/exit_tools.py (3 functions including checkpoint_code). 22 unit tests all passing. Read-copy-write pattern established for snapshot state management.
- **2026-03-21:** Completed 09-02-PLAN.md. Created OntologyGeneratorAgent (LoopWrapper, max_iterations=50) and OntologyValidatorAgent (LoopWrapper, max_iterations=100). Validator prompt adds mandatory checkpoint_code step after each write_ontology. All 30 tests pass (8 new + 22 from plan 01).
- **2026-03-21:** Completed 09-04-PLAN.md. Created CodeWindow.tsx (dual-type code viewer component). Added TTL and Python tabs to AgentNavbar and YourMainContent. Human verified tabs render correctly. User extended the plan by splitting single 'code' tab into separate 'ttl' and 'python' tabs — accepted as UX improvement.
- **2026-03-21:** Completed 09-03-PLAN.md. Wired OntologyGeneratorAgent and OntologyValidatorAgent into create_master_agent.py via all_subagents. Added ASHRAE 223P Code Generation Protocol section to master_instruction.md with explicit HITL gate and two-step delegation sequence. 30 tests pass.
- **2026-03-22:** Completed 10-01-PLAN.md. Neo4j Docker service with Neosemantics n10s plugin. Created LoadTtlToNeo4jTool (8-query Cypher wipe+reimport). 4 unit tests pass. Registered in master agent. Neo4j Import Protocol added to master_instruction.md.
- **2026-03-22:** Completed 10-02-PLAN.md. Installed Sigma.js + neo4j-driver packages (7 production + 4 dev). Created GET /api/graph API route with global Neo4j driver singleton, RDF localName stripping, blank node coalesce handling, and error handling. Set up Jest with ts-jest. 2 unit tests pass (success case + 500 error case).
- **2026-03-22:** Completed 10-03-PLAN.md. Created GraphWindow.tsx (506 lines) — Sigma.js WebGL graph with ForceAtlas2, dynamic sigma.setSetting reducers, toolbar overlay, NodeInfoCard, and empty/loading/error states. Wired into Graph tab in YourMainContent.tsx. TypeScript compiles without errors.
- **2026-03-22:** Completed 10-04-PLAN.md (E2E verification). Human approved all 5 steps. 4 bugs fixed during verification: n10s YIELD syntax removed, SSR crash fixed via dynamic import (ssr:false), FA2 iterations tuned 200→1000, node type color coding fixed by skipping n10s "Resource" label. TTL file persisted to uploads/ttl/latest_ontology.ttl. Phase 10 complete.
- **2026-03-22:** Completed 11-04-PLAN.md. Added LESSONS.md-first Step 0 to SKILL.md Reading Protocol with no-fallback rule. Added Section 7 Distillation Protocol (HITL-gated). Created LESSONS.md skeleton with 6 category headers ready for first distillation.
- **2026-03-22:** Completed 11-01-PLAN.md. Added scan_python_files_filtered (TDD, 7 tests) to tool.py with SCAN_PYTHON_FILES_FILTERED_SCHEMA and __all__ export. Keyword filtering reduces coding-agent context window consumption.

## Roadmap Evolution

- Phase 3 added: Semantic Graph Generation
- Phase 4 added: Dependency Modernization & UI Optimization (SVAR Migration)
- Phase 5 added: Agent-Frontend Interface & Performance Metrics
- Phase 6 added: refactor graphivac api
- Phase 7 added: Replace MCP sync-out with direct REST PUT via bidirectional EDN-JSON translator
- Phase 8 added: Implement capture_frontend_state visual verification tool
- Phase 9 added: Integrate _223P agent into master architecture via sub-agent or skills
- Phase 10 added: TTL to Neo4j database integration with frontend graph visualization
- Phase 11 added: optimization of the coding agent
