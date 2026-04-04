---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_phase: 25
status: unknown
last_updated: "2026-04-04T19:47:30.249Z"
progress:
  total_phases: 25
  completed_phases: 18
  total_plans: 51
  completed_plans: 49
---

# State: HVAC Reconstruction Project

## Project Progress

- **Current Phase:** 25
- **Overall Completion:** [██████████] 96%
- **Active Plan:** 25-02 (complete)
- **Last Completed:** 25-02 (01-introduction.tex and 02-problem.tex fully translated to French; all LaTeX labels, cite keys, and code strings preserved; Virtual Power Plants -> centrales électriques virtuelles; GTB/BMS/GTB/BAS terminology used on first mention)

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
- **Decision (11-02):** search_class_mapping uses case-insensitive substring OR logic across keywords — consistent with scan_python_files_filtered pattern from 11-01.
- **Decision (11-02):** _MAPPINGS_DIR uses _PROJECT_ROOT anchor (not relative path) for portability; tests use real JSONL files (not mocks) since they are small static repo fixtures; _mapping_cache is module-level for lazy JSONL loading.
- **Decision (11-03):** Tool swap complete — both ontology agents now import only scan_python_files_filtered + search_class_mapping; list_library_classes, get_class_details, scan_python_files removed from both agents.
- **Decision (11-03):** full_bob.jsonl and full_scratch.jsonl deleted — superseded by classes_*.jsonl + path field returned by search_class_mapping; generator workflow updated to 9-step sequence with explicit class lookup step.
- **Decision (13-01):** Inlined checkpoint_code logic in exit_validator_success to avoid cross-module import — checkpoint_code stays in original sub_agents/ontology_validator/exit_tools.py for plan 02 to import directly.
- **Decision (13-01):** EXIT_LEVEL_2 pattern: master-level exit tools set EXIT_LEVEL_2 + actions.escalate=True so MasterMainLoopAgent.is_loop_finished terminates correctly.
- **Decision (13-02):** all_subagents = subagents or [] — ontology agents removed from sub-agents list entirely; master now runs generation/validation directly.
- **Decision (13-02):** max_iterations increased from 10 to 100 — multi-step ontology generation/validation loops require more iterations than standard task flows.
- **Decision (15-02):** Root 223p/ deleted entirely (historical ontology_1-39.py, results/, run_validation.py, bin/, ttl/) — no lessons distilled, predates session-archive pattern.
- **Decision (15-02):** TTL_OUTPUT_DIR = _223P_DIR — ontology.ttl written as agent/223p/ontology.ttl directly, not a subdirectory.
- **Decision (15-02):** Three-write pattern established: write_ontology and execute_ontology write to scratch + session_N archive + mapper/uploads/ for real-time frontend visibility.
- **Decision (15-02):** Session ID auto-detects from disk (len(existing_sessions)+1) to avoid drift after state reset.
- **Decision (15-03):** skill-read-code mention removed even from "do not use" warning text in Step 0 to satisfy grep-count acceptance criterion (0 matches required).
- **Decision (15-03):** BACnet custom_fields bullet placed in Equipment modeling guidelines (not Sensors) since custom_fields is a key in components returned by read_internal_grid.
- **Decision (16-01):** _persist_python and _persist_ttl deleted — write_ontology already owns primary Python writes to ONTOLOGY_FILE; session archive handles versioning; no duplicate writes needed.
- **Decision (16-01):** execute_ontology _persist_ttl call removed — script writes latest_ontology.ttl directly to TTL_OUTPUT_DIR via cwd; session archive handles versioning.
- **Decision (16-02):** exit_generator_success and exit_validator_success take only (tool_context, summary) — clean break, code= removed entirely.
- **Decision (16-02):** write_ontology auto-increments ontology_code_iteration_count after each archive write — checkpoint_code tool eliminated.
- **Decision (16-02):** exit_validator_success reads TTL from _TTL_LATEST (Path anchor from __file__) — no ttl_content parameter.
- **Decision (16-02):** scan_python_folder caps at 10 files with force=True escape hatch; returns message-only above cap.
- **Decision (16-02):** execute_ontology checks Linux bin/python venv path first, then Windows Scripts/python.exe, then sys.executable.
- **Decision (16-03):** grep-0 criterion for code= in validation SKILL.md requires rewriting "do not pass code=" warnings to "pass only the summary string" to avoid the literal string appearing in the file.
- **Decision (17-01):** explode_bacnet_points placed in agent/utils/bacnet_helpers.py (not inlined in _apply_metadata) for reuse across both ADK write paths; MCP server gets an inlined _explode_bacnet_points copy due to separate package boundary (cannot import from agent/utils/).
- **Decision (17-01):** Single insertion point in _apply_metadata covers both write_metadata and write_metadata_batch in metadata_tools.py — no need to modify those two functions directly.
- **Decision (17-02):** EDN translator required no code changes — generic key iteration in custom_fields deserialization/serialization already handles any string key (including bacnet_N) without modification.
- **Decision (17-02):** Live test SAMPLE_BACNET_POINTS passes flat bacnet_N keys directly as top-level metadata keys (no 'bacnet' wrapper), consistent with how plan 17-01 updated the write paths.

### Next Steps

1. Phase 16 complete — all 4 plans done (refactoring + cleanup + SKILL.md updates + test updates)

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
- **2026-03-22:** Completed 11-02-PLAN.md. Added search_class_mapping (TDD, 7 tests) to tool.py with SEARCH_CLASS_MAPPING_SCHEMA, __all__ export, _load_mapping helper, and _mapping_cache. Single-call JSONL grep replaces expensive two-call list_library_classes + get_class_details workflow. 14 tests pass total.
- **2026-03-22:** Completed 11-03-PLAN.md. Swapped old tools to scan_python_files_filtered + search_class_mapping in both ontology_generator and ontology_validator agent.py files. Rewrote both prompt.md files with new targeted workflow. Extended agent tests (4 new tests). Deleted full_bob.jsonl and full_scratch.jsonl. 12 agent tests pass.
- **2026-03-23:** Completed 13-01-PLAN.md. Created ontology_exit_tools.py (4 functions, EXIT_LEVEL_2). Created skill-ontology-generation/SKILL.md and skill-ontology-validation/SKILL.md — auto-discoverable skills for master agent. Original sub-agent files untouched.
- **2026-03-23:** Completed 13-02-PLAN.md. Removed OntologyGeneratorAgent and OntologyValidatorAgent sub-agent wrappers. Wired 11 ontology tools directly into MasterLlmAgent task_tools. Raised max_iterations to 100. Updated ASHRAE protocol to reference skills. 8 new architecture tests pass. Phase 13 complete.
- **2026-03-25:** Completed 14-01-PLAN.md. Created LaTeX skeleton (main.tex + 6 section stubs) with full preamble. Compiled via Docker texlive:latest (0 errors, 2-page PDF). Rendered 3 Mermaid diagrams (pipeline, architecture, experiment-progression) to PNG via mmdc v10.6.1. Decision: LaTeX via Docker (no local texlive/no sudo); mmdc via ~/.npm-global for Node 18 compat.
- **2026-03-25:** Completed 14-03-PLAN.md. Wrote Section 4 (Implementation, 305 lines): 9-iteration experiment narrative, final architecture with 2 diagram includes, 6-row skills table, 10-category tools table, key technology decisions. Wrote Section 5 (Results placeholder, 120 lines, 31 \\todo{} markers): 5 subsections, 4 booktabs tables, screenshot placeholders. Decision: Tools table uses 10 categories covering all ~25 tools; skill-control-points excluded (placeholder not fully defined). 0 LaTeX compile errors.
- **2026-03-25:** Completed 14-04-PLAN.md. Wrote Section 6 (Conclusions, 129 lines): Summary of Contributions (4 paragraphs synthesizing problem/approach/dev-process/tech-stack), Limitations (model dependency, validation scope, domain specificity, ASHRAE 223P maturity), Future Work (production validation, multi-system, VPP pilot, automated metrics, multi-language). Full 18-page PDF compiled with 0 LaTeX errors. Phase 14 complete — research report draft-complete pending experiment data.
- **2026-04-02:** Completed 15-02-PLAN.md. Migrated all 223p assets to agent/223p/; implemented three-write pattern for write_ontology and execute_ontology; added extract_lessons tool wired into master agent; deleted root 223p/ (432 files) and skill-read-code/. 21 tests pass (15 new + 6 existing).
- **2026-04-02:** Completed 15-03-PLAN.md. Audited and updated skill-ontology-generation/SKILL.md (LESSONS.md Step 0, BACnet custom_fields, extract_lessons HITL section, path fix) and skill-ontology-validation/SKILL.md (removed 3 skill-read-code refs, updated Preparation, fixed paths). Phase 15 complete.
- **2026-04-03:** Completed 16-01-PLAN.md. Deleted _persist_python and _persist_ttl helpers from ontology_exit_tools.py (functions, constants, datetime/Path imports, 3 call sites). Removed import and _persist_ttl call from ontology_tools.py. Zero _persist references remain in agent/tools/ source files.
- **2026-04-03:** Completed 16-02-PLAN.md. Rewrote exit_generator_success and exit_validator_success to 2-param signatures. Added _TTL_LATEST module constant; exit_validator_success reads TTL from disk. Deleted checkpoint_code function. Folded checkpoint logic into write_ontology (auto-increment). Fixed execute_ontology Linux venv path. Added scan_python_folder cap (10 files, force=True escape). Removed checkpoint_code from create_master_agent.py.
- **2026-04-03:** Completed 16-03-PLAN.md. Updated skill-ontology-generation/SKILL.md (Exit Protocol, clean exit call), skill-ontology-validation/SKILL.md (Step 0, clean exit, no checkpoint_code, correct paths, root-cause batch strategy, Operator Reference section), and skill-ontology-lessons/SKILL.md (unambiguous % operator lesson: sensor%equipment correct, sensor%property wrong).
- **2026-04-03:** Completed 16-04-PLAN.md. Updated test_ontology_tools.py: removed all _persist_python/_persist_ttl mocks, renamed two-write pattern tests, added 6 new tests (auto-increment, exit signatures, TTL-from-disk, Linux venv order, scan cap/force). 31 tests pass. Phase 16 complete.
- **2026-04-03:** Completed 17-01-PLAN.md. Created explode_bacnet_points helper in agent/utils/bacnet_helpers.py (6 unit tests all pass, TDD). Wired explosion calls into all 4 write-path functions: update_component_metadata, update_component_metadata_batch (internal_grid_tools.py), _apply_metadata (metadata_tools.py), MetadataManager.write_metadata + write_metadata_batch (mcp_server/graphivac/metadata_manager.py, inlined copy). Flat bacnet_N format guaranteed at every write site.
- **2026-04-03:** Completed 17-02-PLAN.md. Verified EDN translator has zero hard-coded 'bacnet' logic (generic key iteration). Created test_grid_edn_translator.py (7 tests, all pass). Rewrote skill-bacnet-points/SKILL.md sections 3 and 4 and Rules to flat bacnet_N format. Updated live test SAMPLE_BACNET_POINTS to bacnet_1 through bacnet_5 with address fields, removed 'bacnet' wrapper from updates dict, rewrote verification logic per-key.
- **2026-04-03:** Completed 19-01-PLAN.md. Replaced 5 fragmented exit tools with 2 generic ones (exit_with_success/exit_with_failure). Moved snapshot patching (python_code_snapshots Final/validated, ttl_code_snapshots TTL label) from exit_validator_success into execute_ontology. Updated MasterLlmAgent.default_tools. Removed ontology_exit_tools from create_master_agent.py. Deleted loop_exit_tools.py and ontology_exit_tools.py.
- **2026-04-03:** Completed 19-02-PLAN.md. Updated all 5 skills to call exit_with_success/exit_with_failure with domain-specific summary requirements. Added one-task-at-a-time Task Execution Rule to master_instruction.md. Removed all old exit tool name references (exit_generator_success/failure, exit_validator_success/failure, checkpoint_code) from master instruction. Phase 19 complete.
- **2026-04-03:** Completed 19-03-PLAN.md. Updated test_ontology_tools.py: replaced ontology_exit_tools import with exit_tools, added generic exit tool tests (EXIT_LEVEL_2 pattern), execute_ontology snapshot patching test, and level_3_master_main_llm.py wiring test. Fixed pre-existing read_python_files and scan_python_folder tests for current grep-style API. 33 tests pass. Phase 19 complete.
- **2026-04-03:** Completed 18-01-PLAN.md (executed after phase 19). Rewrote skill-ontology-validation/SKILL.md with all 11 optimizations: Exit Protocol elevated to line 12, sub-steps 4a-4d for class lookup, Retry Escalation 3/5/10 tiers, inline error classification, minimum-change constraint, root-cause ordering, pre-write advisory, mid-loop lessons trigger, scan_python_folder in Step 0. Added targeted consultation note to skill-ontology-lessons/SKILL.md. Zero deprecated references. No new test failures.
- **2026-04-03:** Completed 20-01-PLAN.md. Created agent/utils/session_logger.py (log_events function, JSONL append, OSError silencing, lazy dir creation). Created agent/tests/test_session_logger.py (7 TDD tests, all pass). Wired log_events into shared_model_callback in callback_utils.py after state events update. Added logs/ to agent/.gitignore. 7 new tests pass + 59 existing pass.
- **2026-04-03:** Completed 21-01-PLAN.md. Removed useCoAgent from mapper/src/app/page.tsx. Added DEFAULT_AGENT_STATE module-level constant. Simplified combinedState to pooledState ?? DEFAULT_AGENT_STATE one-liner. Rewrote StateSyncer to accept only pooledState prop (no agentState). TypeScript compiles clean, Next.js build succeeds. Fixes "Maximum update depth exceeded" render loop.
- **2026-04-03:** Completed 22-01-PLAN.md. Added enrich_bacnet_point (converts raw BACnet address to bacnet:// URI, sets code/ref_type), _parse_bacnet_address, enrich_flat_bacnet_points (idempotent) to agent/utils/bacnet_helpers.py. Extended explode_bacnet_points with optional component_type param. 23 tests pass (17 new + 6 updated existing). TDD: RED (import error) → GREEN (all pass).
- **2026-04-04:** Completed 22-02-PLAN.md. Wired enrich_flat_bacnet_points into all 4 write paths with component_type extraction. internal_grid_tools: moved explode inside for-loop + added enrichment at both write sites. metadata_tools: added enrichment in _apply_metadata via EDN Keyword('type'). metadata_manager: added import re, 3 constants (_BACNET_TYPE_MAP, _SKIP_TYPES, _SENSOR_COMPONENT_TYPES), 3 inlined functions (_parse_bacnet_address, _enrich_bacnet_point, _enrich_flat_bacnet_points), wired comp_type into both write methods. 87 tests pass.
- **2026-04-03:** Completed 22-03-PLAN.md. Updated skill-ontology-generation, skill-ontology-validation, and skill-ontology-lessons SKILL.md files. Generation and validation skills document pre-computed bacnet_N fields (code, address, ref_type) and instruct agents to use address URI directly. Lessons skill adds Phase 22 update note at top of BACnet section while preserving all legacy parsing rules as fallback.
- **2026-04-04:** Completed 23-01-PLAN.md. Created 4 Cypher query tools in agent/tools/neo4j_query_tools.py: ExecuteCypherTool (single query, 500-row cap), ExecuteCypherBatchTool (ThreadPoolExecutor parallel, ordered results, partial failure), GetGraphSchemaTool (labels/rel_types/prop_keys), SearchGraphEntitiesTool (case-insensitive substring). 15 unit tests pass.
- **2026-04-04:** Completed 23-02-PLAN.md. Wired all 4 Cypher query tools into create_master_agent.py task_tools. Added Neo4j Query Protocol section to master_instruction.md with write-gate rule, recommended exploration sequence (schema -> search -> query -> batch), n10s namespace verbatim-preservation warning, and 500-row result cap documentation. 102 tests pass. Phase 23 complete.
- **2026-04-04:** Completed 24-01-PLAN.md. Deleted capture_frontend_state_tool.py + 2 test files. Removed import/registration from create_master_agent.py. Removed playwright>=1.40.0 from pyproject.toml. Simplified skill-ductwork/SKILL.md (5 steps: no verification loop) and skill-hvac-equipments/SKILL.md (6 steps: no verification loop). Added regression guard test. 7 master agent tests pass. Phase 24 complete.
- **2026-04-04:** Completed 25-01-PLAN.md. Created report_french/ (21 files: 5 sections, 11 figures, 3 diagrams, main.tex, references.bib). Added babel[french] to preamble; translated title, abstract, date in main.tex. Translated all 19 bib entry titles and notes in references.bib. All entry keys, structure, and section files preserved verbatim.
- **Decision (19-01):** exit_with_success and exit_with_failure are fully generic — no domain state keys; EXIT_LEVEL_2 + actions.escalate only.
- **Decision (19-01):** Snapshot patching moved from exit_validator_success into execute_ontology — domain logic belongs in the artifact-generating tool.
- **Decision (19-01):** Exit tools come through MasterLlmAgent default_tools only, not task_tools.
- **Decision (19-02):** All 5 skills now instruct agents to call exit_with_success/exit_with_failure with domain-specific summary requirements (duct counts, equipment counts, BACnet points/matched/unmatched).
- **Decision (19-02):** One-task-at-a-time rule added to master instruction — prevents unprompted skill chaining after exit tool fires.
- **Decision (19-02):** checkpoint_code removed from master instruction ASHRAE Sequence step 3 tool list — no longer exists as a tool.
- **Decision (19-03):** Pre-existing read_python_files tests updated to grep-style API (full_content=True, array response) — auto-fix since import failure blocked entire test run.
- **Decision (19-03):** scan_python_folder files field is a list not dict — tests updated to assert membership via list comprehension and empty list assertion.
- **Decision (20-01):** log_events uses model_dump(mode='json') to serialize EventType Enum as plain string, not Python Enum object.
- **Decision (20-01):** Only new_events (fresh batch per callback) are persisted — not full events_history (truncated to 200).
- **Decision (20-01):** OSError caught silently in session_logger — write failures must never crash the agent callback.
- **Decision (21-01):** useCoAgent removed entirely — agentState was always empty at runtime (data flows via ADK callbacks, not CopilotKit streaming); pooledState is now the sole source of truth for combinedState.
- **Decision (21-01):** DEFAULT_AGENT_STATE is a module-level constant (not created inside component) to provide a stable reference that never causes re-renders.
- **Decision (21-01):** StateSyncer simplified to single-source sync — no array merging, no agentRest, no adkData; early return when pooledState is null eliminates spurious context updates.
- **Decision (22-01):** enrich_bacnet_point does NOT mutate input dict — shallow copy first; existing 6 tests updated to check code==raw_address and address==URI since explode_bacnet_points now enriches at explosion time.
- **Decision (22-01):** explode_bacnet_points backward compatible via optional component_type="" — callers without arg receive ref_type="property" for all points.
- **Decision (22-02):** explode_bacnet_points moved inside for-loop in update_component_metadata so component_type is available from the matched component before explosion — enrichment needs type to determine sensor vs property ref_type.
- **Decision (22-02):** MCP inlined _explode_bacnet_points updated to accept component_type and delegate to _enrich_bacnet_point — explosion and enrichment handled atomically in one function call.
- **Decision (22-02):** EDN Keyword('type') used to extract component type inside MetadataManager action closures where mutable value dict is available.
- **Decision (22-03):** Pre-computed bacnet_N fields (code, address, ref_type) documented across all three ontology skills — agents consume address URI directly without manual parsing.
- **Decision (22-03):** Lessons skill retains all existing address-parsing content as legacy fallback while Phase 22 update note is prepended at the top of the BACnet section.
- **Decision (23-01):** _run_query is module-level (not a method) so ThreadPoolExecutor workers can call it without holding a class reference — avoids serialisation issues with bound methods.
- **Decision (23-01):** ThreadPoolExecutor created INSIDE `with GraphDatabase.driver(...)` context to ensure driver stays open while threads execute queries.
- **Decision (23-01):** future_to_index dict maps each Future to its original query index; as_completed fires in completion order, so index restores ordered batch results.
- **Decision (23-01):** Batch mock uses side_effect function keyed on query string (not side_effect list) — side_effect list is not thread-safe across concurrent ThreadPoolExecutor workers.
- **Decision (23-02):** 4 Cypher tool singletons placed in task_tools after load_ttl_to_neo4j_tool with # Neo4j query tools comment — consistent with other Neo4j tooling grouping.
- **Decision (23-02):** Neo4j Query Protocol section inserted immediately after Neo4j Import Protocol in master_instruction.md — logical grouping keeps all Neo4j guidance co-located.
- **Decision (23-02):** Write-gate rule uses explicit list of write keywords (CREATE, MERGE, DELETE, SET, REMOVE) for clarity; n10s namespace warning uses concrete label examples so agent knows exact format from get_graph_schema output.
- **Decision (24-01):** Playwright removed entirely — screenshot verification expensive and unreliable; new philosophy is place-sync-exit (human inspects manually).
- **Decision (24-01):** Skill exit summaries simplified to component count + sync confirmation only (correction counts and verification pass/fail removed).
- **Decision (25-01):** report_french/ section files copied verbatim in plan 01 — each section translated independently in plans 25-02 through 25-05; isolation enables clean per-section commits.
- **Decision (25-01):** All bib entry keys unchanged so \\cite{} commands in section files need no modification during translation — only title/note fields translated.
- **Decision (25-01):** babel[french] placed immediately after \\usepackage[utf8]{inputenc} following standard LaTeX preamble ordering.
- **2026-04-04:** Completed 25-02-PLAN.md. Translated 01-introduction.tex (138 lines) and 02-problem.tex (278 lines) to French. All section headings, subsection headings, tables, and prose translated. All \\label{}, \\ref{}, \\cite{}, \\texttt{} preserved verbatim. GTB/BMS/GTB/BAS used on first mention; CVC (HVAC) on first HVAC mention; centrales électriques virtuelles for Virtual Power Plants.
- **Decision (25-02):** French guillemets written using \\og and \\fg macros (babel[french] convention) rather than English double-quote markup.
- **Decision (25-02):** CVC (HVAC) used on first HVAC mention in 01-introduction.tex; GTB/BMS on first BMS mention; GTB/BAS on first BAS mention in 02-problem.tex.
- **Decision (25-02):** Virtual Power Plants -> centrales électriques virtuelles on first use; centrales virtuelles acceptable for brevity in subsequent uses.

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
- Phase 12 added: Session persistence and management with database backend
- Phase 13 added: Migrate OntologyGenerator and OntologyValidator sub-agents to master agent skills
- Phase 14 added: Write comprehensive research report on SI-Mapper development
- Phase 15 added: Refactor coding skills and standardize agent architecture

### Roadmap Evolution

- Phase 16 added: optimize ontology skills
- Phase 17 added: Restructure BACnet custom fields to flat numbered entries
- Phase 18 added: optimize skill for ontology validation
- Phase 19 added: Standardize agent exit tools across all skills
- Phase 21 added: delete-usecoagent-switch-to-polling-only
- Phase 22 added: enhance-bacnet-parsing
- Phase 23 added: Add Cypher query tool for Neo4j agent exploration
- Phase 24 added: remove screenshots to the front end
- Phase 25 added: Translate report to French
