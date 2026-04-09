# Phase 15: Refactor coding skills and standardize agent architecture - Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Three distinct workstreams delivered together:

1. **Full deletion of `agent/sub_agents/`** — every file, every test, every utility that is only referenced by sub-agents. The master agent does not import from sub_agents at all; deletion is clean.

2. **File layout standardization** — root `223p/` moves inside `agent/223p/`. Clear rule: files visible only to the agent stay inside `agent/`; files that need to be visible to both agent and human go to `mapper/uploads/`. Every Python and TTL iteration now writes to `mapper/uploads/` in real-time so the human can observe and guide the agent throughout the session.

3. **Coding skill refactor** — `skill-read-code` is deleted and its functionality absorbed into `skill-ontology-generation` + a new `extract_lessons` tool. `skill-ontology-generation` and `skill-ontology-validation` are audited and updated: path references fixed, LESSONS.md reading embedded, BACnet metadata awareness added.

**Out of scope:**
- Any changes to the master agent loop or master_instruction.md structure beyond skill references
- Frontend component changes (CodeWindow already supports multi-file display by polling mapper/uploads/)
- Any new ontology capabilities

</domain>

<decisions>
## Implementation Decisions

### sub_agents/ deletion
- Delete `agent/sub_agents/` entirely — no file is preserved.
- Included in the deletion:
  - `_223p/` and all its contents (tool.py is a duplicate of `tools/ontology_tools.py`; agents are dead code)
  - `ontology_generator/` and `ontology_validator/` (kept as backup after Phase 13; no longer needed)
  - `bacnet/`, `control/`, `electricity/`, `equipment/`, `horizontal_ducts/`, `vertical_ducts/`
  - `loop_agents/` (loop_wrapper.py, level_shared_utils.py — not used by master)
  - `tools/` inside sub_agents (ingest_category_tool.py, loop_exit_tools.py — only used by sub_agents)
  - `__init__.py`
- Tests that exclusively import from sub_agents are **deleted**:
  - `agent/tests/test_223p_tools.py`
  - `agent/tests/test_ontology_generator_agent.py`
  - `agent/tests/test_ontology_generator_exit_tools.py`
  - `agent/tests/test_ontology_validator_agent.py`
  - `agent/tests/test_ontology_validator_exit_tools.py`
- `agent/tests/test_create_master_agent.py` is **updated** — remove the two assertions that check for sub_agents import strings (they now test dead paths).

### 223p/ folder relocation
- Root `223p/` is deleted after all contents are migrated to `agent/223p/`.
- New canonical structure inside `agent/223p/`:
  ```
  agent/223p/
  ├── ref/
  │   ├── code/            ← moved from 223p/ref/code/ (static reference implementations)
  │   └── 223standard/     ← moved from 223p/ref/223standard/ (ASHRAE standard)
  ├── mappings/            ← moved from agent/skills/skill-read-code/assets/mappings/
  │   ├── classes_bob.jsonl
  │   └── classes_scratch.jsonl
  ├── python_iterations/   ← NEW — per-session archives
  │   ├── session_1/
  │   └── session_2/
  ├── ttl_iterations/      ← NEW — per-session TTL archives
  │   ├── session_1/
  │   └── session_2/
  ├── LESSONS.md           ← moved from agent/skills/skill-read-code/LESSONS.md
  ├── ontology.py          ← working scratch file (overwritten every iteration)
  └── ontology.ttl         ← working TTL scratch (overwritten after each execution)
  ```
- The `mapper/uploads/python/` and `mapper/uploads/ttl/` directories remain unchanged — they are the human-visible locations.

### Session tracking
- A new ADK state key `ontology_session_id` (integer) identifies the current generation session.
- Session ID is set once when a new generation begins (e.g., from 0 → 1 on first call, then incremented each new top-level generation request).
- Iteration files inside a session folder are named with a zero-padded counter: `ontology_001.py`, `ontology_002.py`, etc. — using the existing `ontology_code_iteration_count` state key.

### write_ontology behavior (three-write pattern)
Every `write_ontology` call writes to **three locations**:
1. `agent/223p/ontology.py` — scratch file that `execute_ontology` runs.
2. `agent/223p/python_iterations/session_<N>/ontology_<iter>.py` — permanent archive for lesson extraction.
3. `mapper/uploads/python/ontology_<timestamp>.py` — immediately visible in the frontend CodeWindow.

This replaces the old pattern where only exit tools wrote to mapper/uploads/. Human can now see every iteration in real-time as the agent works.

### execute_ontology behavior (three-write pattern)
Every successful `execute_ontology` call writes the TTL to:
1. `agent/223p/ontology.ttl` — scratch (overwritten each run, used to read TTL content back).
2. `agent/223p/ttl_iterations/session_<N>/ontology_<iter>.ttl` — permanent archive.
3. `mapper/uploads/ttl/ontology_<timestamp>.ttl` — immediately visible in the frontend TTL tab.

### ontology_tools.py path constants
These path anchors must be updated:
- `ONTOLOGY_FILE` → `agent/223p/ontology.py`
- `TTL_OUTPUT_DIR` → `agent/223p/` (TTL scratch: `agent/223p/ontology.ttl`)
- `_MAPPINGS_DIR` → `agent/223p/mappings/`
- `subprocess.run` cwd → `agent/223p/`
- Add new constants: `PYTHON_ITERATIONS_DIR`, `TTL_ITERATIONS_DIR`, `LESSONS_FILE`

### skill-read-code deletion
- Delete `agent/skills/skill-read-code/` entirely (after migrating LESSONS.md and mappings/).
- **Reading LESSONS.md** — automatic, no separate tool needed:
  - Instruction embedded directly in `skill-ontology-generation`: "Before generating, read `agent/223p/LESSONS.md`. If the file is empty or absent, proceed without it."
- **Extracting lessons** — new tool `extract_lessons()` in `tools/ontology_tools.py`:
  - Reads all Python iteration files from `agent/223p/python_iterations/` across all sessions.
  - The agent (LLM) analyzes the sequence of iterations, identifies what patterns caused errors in earlier versions and how later versions fixed them.
  - Writes the updated `agent/223p/LESSONS.md` (structured by error category).
  - This tool is **HITL-gated**: only executed when the user explicitly asks (e.g. "extract lessons", "update lessons").
  - Instruction to call this tool when user asks is embedded in `skill-ontology-generation`.
  - `extract_lessons` is added to the master's tool list in `create_master_agent.py`.

### skill-ontology-generation enhancements (step-by-step, details in planning)
- Fix path reference: `../223p/ref/code` → absolute path using `agent/223p/ref/code`.
- Add LESSONS.md reading step at the very beginning of the workflow.
- Add `extract_lessons` usage instruction (HITL gate: only when user asks).
- Add BACnet metadata awareness: components in `read_internal_grid` may now have a `custom_fields` key with BACnet points — the agent should include these when modeling sensors and equipment in the ontology.
- Full workflow audit: verify each step references correct tool names, correct paths, correct exit tool behavior.

### skill-ontology-validation enhancements (step-by-step, details in planning)
- Fix path references to match new `agent/223p/` structure.
- Full workflow audit: verify execution path, TTL read-back, exit tool calls.

### Skill enhancement methodology
- Before writing any changes: read and analyze the current skill in full, verify each tool call in the workflow exists and works correctly.
- Changes are applied after analysis confirms what is correct vs what needs fixing.
- One skill at a time.

### Claude's Discretion
- What to do with historical content in root `223p/`: `results/` folder (5 run archives), `src/ontology_1.py` through `ontology_39.py` (accumulated backups) — archive into `agent/223p/` or delete outright.
- `run_validation.py` at root `223p/` (standalone runner, not used by master) — archive or delete.
- Exact behavior of exit tools after the three-write pattern change — whether `exit_generator_success` / `exit_validator_success` still write a final copy to uploads or defer entirely to `write_ontology`.
- Whether to add a cleanup utility for old session folders beyond a retention threshold (e.g., keep last 10 sessions).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Current tools (to be updated)
- `agent/tools/ontology_tools.py` — all path constants, write_ontology, execute_ontology, scan_python_files_filtered, search_class_mapping; every path anchor needs updating
- `agent/tools/ontology_exit_tools.py` — exit tool behavior; may need updates after three-write pattern change

### Current skills (to be updated or deleted)
- `agent/skills/skill-ontology-generation/SKILL.md` — full audit + enhancement in this phase
- `agent/skills/skill-ontology-validation/SKILL.md` — full audit + path fixes
- `agent/skills/skill-read-code/SKILL.md` — READ before deleting to understand what must be preserved

### Master agent wiring (to be updated)
- `agent/master_architecture/create_master_agent.py` — add `extract_lessons` to tool list; no sub_agents imports to clean (already clean)

### Source files being deleted
- `agent/sub_agents/` — entire directory; verify no master imports before deleting
- `agent/tests/test_223p_tools.py` — delete
- `agent/tests/test_ontology_generator_agent.py` — delete
- `agent/tests/test_ontology_generator_exit_tools.py` — delete
- `agent/tests/test_ontology_validator_agent.py` — delete
- `agent/tests/test_ontology_validator_exit_tools.py` — delete
- `agent/tests/test_create_master_agent.py` — update (remove sub_agents assertions)

### Static files being relocated
- `agent/skills/skill-read-code/assets/mappings/classes_bob.jsonl` → `agent/223p/mappings/classes_bob.jsonl`
- `agent/skills/skill-read-code/assets/mappings/classes_scratch.jsonl` → `agent/223p/mappings/classes_scratch.jsonl`
- `agent/skills/skill-read-code/LESSONS.md` → `agent/223p/LESSONS.md`
- `223p/ref/code/` → `agent/223p/ref/code/`
- `223p/ref/223standard/` → `agent/223p/ref/223standard/`

### Prior phase decisions (still binding)
- `.planning/phases/11-optimization-of-the-coding-agent/11-CONTEXT.md` — scan_python_files_filtered and search_class_mapping canonical patterns
- `.planning/phases/13-migrate-ontologygenerator-and-ontologyvalidator-sub-agents-to-master-agent-skills/13-CONTEXT.md` — EXIT_LEVEL_2 pattern, skill auto-loading loop

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tools/ontology_tools.py` — already contains all functions from deleted `_223p/tool.py`; only path constants change
- `ontology_exit_tools.py:_persist_python` and `_persist_ttl` — reusable helpers; `write_ontology` can use the same pattern to write to uploads on every call
- `create_master_agent.py:57-72` — skill auto-loading loop picks up any new `SKILL.md`; no wiring changes needed for skill updates
- `CodeWindow.tsx` — already polls `mapper/uploads/python/` and `mapper/uploads/ttl/` every 3s; shows all timestamped files automatically; no frontend changes needed

### Established Patterns
- Master imports zero things from `agent/sub_agents/` — confirmed by grep. Deletion has no master-side impact.
- `_persist_python` / `_persist_ttl` in `ontology_exit_tools.py` show the correct pattern for writing to `mapper/uploads/`; `write_ontology` should follow the same pattern (mkdir + write versioned + overwrite latest).
- `ontology_code_iteration_count` already in ADK state — reuse for naming iteration files within a session.
- Session counter pattern: new state key `ontology_session_id`, initialized to 1 on first write if absent.

### Integration Points
- `tools/ontology_tools.py` path constants — single file to update for all path changes; downstream tools (write_ontology, execute_ontology, search_class_mapping) all read from these constants.
- `create_master_agent.py:task_tools` list — add `extract_lessons` here.
- `skill-ontology-generation/SKILL.md` — add two instruction blocks: (1) read LESSONS.md at start, (2) call extract_lessons when user asks.

### What NOT to touch
- `mapper/uploads/` structure — human-visible directories unchanged
- `CodeWindow.tsx` and all frontend components — no changes needed
- `agent/tools/internal_grid_tools.py` and grid tools — out of scope

</code_context>

<specifics>
## Specific Ideas

- The three-write pattern in `write_ontology` makes every iteration immediately visible in CodeWindow. The human can say "iteration 3 was going in the right direction, go back to that" because they can see all files in the tab.
- Session folders named `session_1`, `session_2` etc. make it easy to tell the agent "extract lessons from session 3" by referring to a specific past run.
- `extract_lessons` is a full LLM-powered distillation: the agent reads the sequence of iteration files in order, identifies the delta between each failed attempt and the fix that followed, and writes structured patterns into LESSONS.md — same categories as before (Imports, Instantiation, Connection wiring, Sensor API, Serialization, Structural approach).
- LESSONS.md reading at generation start is just `read_ontology`-style file read, no special tool needed — the skill instructs the agent to call `scan_python_files_filtered` or a direct file read on `agent/223p/LESSONS.md`.

</specifics>

<deferred>
## Deferred Ideas

- Automatic session cleanup / retention policy (keep last N sessions) — could be added later if iteration folders grow large
- Frontend session selector in CodeWindow (currently shows all files in one flat list; grouping by session could improve navigation) — own phase
- Automated lesson extraction trigger (e.g., extract after every completed validation) — currently HITL-only; auto-trigger is a separate decision

</deferred>

---

*Phase: 15-refactor-coding-skills-and-standardize-agent-architecture*
*Context gathered: 2026-04-02*
