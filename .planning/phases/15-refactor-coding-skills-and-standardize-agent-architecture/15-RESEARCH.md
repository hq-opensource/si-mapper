# Phase 15: Refactor Coding Skills and Standardize Agent Architecture - Research

**Researched:** 2026-04-02
**Domain:** Python agent refactoring, file layout standardization, ADK skill authoring
**Confidence:** HIGH

## Summary

Phase 15 is a pure refactoring phase with three distinct, independently-executable workstreams. The work is entirely within the `agent/` directory (plus the root `223p/` migration). No new business logic is introduced — the goal is removing dead code, standardizing file locations, and enhancing the two ontology skills. The decision context is fully locked with minimal discretion areas, making this a straightforward planning target.

All paths are confirmed against the live codebase. Two test assertions in `test_create_master_agent.py` are already stale (checking for old sub_agents import strings that no longer exist after Phase 13) — they must be removed as part of Workstream 1, not treated as failures. The `read_prompt` tool's `_PROMPT_MD` constant still points to the about-to-be-deleted `sub_agents/_223p/generator/prompt.md` — this is the only functional breakage introduced by sub_agents deletion, and it must be fixed as part of Workstream 3.

The three-write pattern in `write_ontology` and `execute_ontology` is the most consequential code change: both functions currently write to one location only (the scratch file / TTL dir). Extending them to also write to session-scoped archives and `mapper/uploads/` follows the same pattern already established in `_persist_python` and `_persist_ttl` from `ontology_exit_tools.py`.

**Primary recommendation:** Execute workstreams in order — (1) delete sub_agents and fix tests, (2) migrate 223p/ folder and update path constants, (3) refactor skills. Each workstream is self-contained and can be verified independently.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### sub_agents/ deletion
- Delete `agent/sub_agents/` entirely — no file is preserved.
- Included in the deletion:
  - `_223p/` and all its contents
  - `ontology_generator/` and `ontology_validator/`
  - `bacnet/`, `control/`, `electricity/`, `equipment/`, `horizontal_ducts/`, `vertical_ducts/`
  - `loop_agents/`
  - `tools/` inside sub_agents
  - `__init__.py`
- Tests that exclusively import from sub_agents are **deleted**:
  - `agent/tests/test_223p_tools.py`
  - `agent/tests/test_ontology_generator_agent.py`
  - `agent/tests/test_ontology_generator_exit_tools.py`
  - `agent/tests/test_ontology_validator_agent.py`
  - `agent/tests/test_ontology_validator_exit_tools.py`
- `agent/tests/test_create_master_agent.py` is **updated** — remove the two assertions that check for sub_agents import strings.

#### 223p/ folder relocation
- Root `223p/` is deleted after all contents are migrated to `agent/223p/`.
- New canonical structure inside `agent/223p/`:
  ```
  agent/223p/
  ├── ref/
  │   ├── code/
  │   └── 223standard/
  ├── mappings/
  │   ├── classes_bob.jsonl
  │   └── classes_scratch.jsonl
  ├── python_iterations/
  │   ├── session_1/
  │   └── session_2/
  ├── ttl_iterations/
  │   ├── session_1/
  │   └── session_2/
  ├── LESSONS.md
  ├── ontology.py
  └── ontology.ttl
  ```
- `mapper/uploads/python/` and `mapper/uploads/ttl/` remain unchanged.

#### Session tracking
- New ADK state key `ontology_session_id` (integer) identifies the current generation session.
- Session ID is set once when a new generation begins (0 → 1 on first call, then incremented each new top-level generation request).
- Iteration files named with zero-padded counter: `ontology_001.py`, `ontology_002.py`, etc.

#### write_ontology behavior (three-write pattern)
Every `write_ontology` call writes to:
1. `agent/223p/ontology.py` — scratch file that `execute_ontology` runs.
2. `agent/223p/python_iterations/session_<N>/ontology_<iter>.py` — permanent archive.
3. `mapper/uploads/python/ontology_<timestamp>.py` — immediately visible in the frontend.

#### execute_ontology behavior (three-write pattern)
Every successful `execute_ontology` call writes the TTL to:
1. `agent/223p/ontology.ttl` — scratch.
2. `agent/223p/ttl_iterations/session_<N>/ontology_<iter>.ttl` — permanent archive.
3. `mapper/uploads/ttl/ontology_<timestamp>.ttl` — immediately visible in the frontend.

#### ontology_tools.py path constants (must be updated)
- `ONTOLOGY_FILE` → `agent/223p/ontology.py`
- `TTL_OUTPUT_DIR` → `agent/223p/` (TTL scratch: `agent/223p/ontology.ttl`)
- `_MAPPINGS_DIR` → `agent/223p/mappings/`
- `subprocess.run` cwd → `agent/223p/`
- Add new constants: `PYTHON_ITERATIONS_DIR`, `TTL_ITERATIONS_DIR`, `LESSONS_FILE`

#### skill-read-code deletion
- Delete `agent/skills/skill-read-code/` entirely (after migrating LESSONS.md and mappings/).
- LESSONS.md reading embedded as instruction in `skill-ontology-generation`: "Before generating, read `agent/223p/LESSONS.md`. If the file is empty or absent, proceed without it."
- New `extract_lessons()` tool in `tools/ontology_tools.py`.
- `extract_lessons` is HITL-gated.
- `extract_lessons` is added to master's tool list in `create_master_agent.py`.

#### skill-ontology-generation enhancements
- Fix path reference: `../223p/ref/code` → absolute path using `agent/223p/ref/code`.
- Add LESSONS.md reading step at the very beginning of the workflow.
- Add `extract_lessons` usage instruction (HITL gate: only when user asks).
- Add BACnet metadata awareness: components in `read_internal_grid` may now have a `custom_fields` key with BACnet points.
- Full workflow audit: verify each step references correct tool names, correct paths, correct exit tool behavior.

#### skill-ontology-validation enhancements
- Fix path references to match new `agent/223p/` structure.
- Remove all references to `skill-read-code`.
- Full workflow audit: verify execution path, TTL read-back, exit tool calls.

#### Skill enhancement methodology
- Before writing any changes: read and analyze the current skill in full, verify each tool call in the workflow exists and works correctly.
- Changes are applied after analysis confirms what is correct vs what needs fixing.
- One skill at a time.

### Claude's Discretion
- What to do with historical content in root `223p/`: `results/` folder (5 run archives), `src/ontology_1.py` through `ontology_39.py` (accumulated backups) — archive into `agent/223p/` or delete outright.
- `run_validation.py` at root `223p/` (standalone runner, not used by master) — archive or delete.
- Exact behavior of exit tools after the three-write pattern change — whether `exit_generator_success` / `exit_validator_success` still write a final copy to uploads or defer entirely to `write_ontology`.
- Whether to add a cleanup utility for old session folders beyond a retention threshold.

### Deferred Ideas (OUT OF SCOPE)
- Automatic session cleanup / retention policy (keep last N sessions)
- Frontend session selector in CodeWindow
- Automated lesson extraction trigger (extract after every completed validation)
</user_constraints>

---

## Standard Stack

### Core (all already in the project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| google-adk | installed in agent/.venv | Agent framework, ToolContext, LoopAgent | Already the entire runtime |
| pytest | 9.0.2 | Test runner | Already configured in pyproject.toml |
| pathlib.Path | stdlib | File path manipulation | Used throughout agent/tools/ |
| shutil | stdlib | File copy/move operations | Used in `_backup_file` |
| subprocess | stdlib | Running ontology.py | Already used in `execute_ontology` |

### No New Dependencies Required
All functionality (session-scoped archives, three-write pattern, extract_lessons) uses the standard library only. The write pattern follows `_persist_python` / `_persist_ttl` already established in `ontology_exit_tools.py`.

---

## Architecture Patterns

### Recommended Project Structure (Post-Phase-15)
```
agent/
├── 223p/                          ← NEW (migrated from root 223p/)
│   ├── ref/
│   │   ├── code/                  ← from 223p/ref/code/
│   │   └── 223standard/           ← from 223p/ref/223standard/
│   ├── mappings/                  ← from agent/skills/skill-read-code/assets/mappings/
│   │   ├── classes_bob.jsonl
│   │   └── classes_scratch.jsonl
│   ├── python_iterations/         ← NEW session archives
│   │   └── session_1/
│   ├── ttl_iterations/            ← NEW session archives
│   │   └── session_1/
│   ├── LESSONS.md                 ← from skill-read-code/LESSONS.md
│   ├── ontology.py                ← scratch (from 223p/src/ontology.py)
│   └── ontology.ttl               ← scratch
├── skills/
│   ├── skill-ontology-generation/ ← enhanced
│   ├── skill-ontology-validation/ ← enhanced
│   └── (skill-read-code DELETED)
├── tools/
│   ├── ontology_tools.py          ← path constants + extract_lessons added
│   └── ontology_exit_tools.py     ← may need exit tool adjustment
├── master_architecture/
│   └── create_master_agent.py     ← extract_lessons added to task_tools
└── tests/
    ├── (5 sub_agents tests DELETED)
    └── test_create_master_agent.py ← 2 stale assertions removed
```

### Pattern 1: Three-Write Pattern (new `write_ontology`)
**What:** Every write goes to scratch + session archive + uploads simultaneously.
**When to use:** Every `write_ontology` call and every successful `execute_ontology` call.
**Example (modeled on `_persist_python` in `ontology_exit_tools.py`):**
```python
# Source: agent/tools/ontology_exit_tools.py (existing _persist_python)
def _persist_python(code: str, label: str) -> None:
    _UPLOADS_PYTHON.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    versioned = _UPLOADS_PYTHON / f"ontology_{ts}.py"
    latest = _UPLOADS_PYTHON / "latest_ontology.py"
    versioned.write_text(code, encoding="utf-8")
    latest.write_text(code, encoding="utf-8")
```
New `write_ontology` adds:
1. Write to `ONTOLOGY_FILE` (scratch, same as before)
2. Ensure `ontology_session_id` is set in state; initialize to 1 if absent
3. Use `ontology_code_iteration_count` to name the archive file as zero-padded `ontology_001.py`
4. Write to `PYTHON_ITERATIONS_DIR / f"session_{session_id}" / f"ontology_{iter:03d}.py"`
5. Write to uploads (same as `_persist_python`)

### Pattern 2: Session ID Management
**What:** `ontology_session_id` in ADK state tracks which generation session is active.
**Rules:**
- On `write_ontology` call: if `ontology_session_id` not in state, set it to 1.
- "New session" increment: this is done by the skill instruction — when a new top-level generation request starts, the skill instructs the agent to increment `ontology_session_id` via a state write (or `write_ontology` detects a reset of `ontology_code_iteration_count` back to 0 as the signal).
- The planner should decide: is session increment automatic (detected by iteration count reset) or explicit (agent calls a tool)? The CONTEXT leaves this to Claude's discretion.

**Recommendation for session increment:** Detect inside `write_ontology`: if `ontology_code_iteration_count` is 0 (or absent), this is the first write of a new session. Increment `ontology_session_id` at this point. This avoids requiring a separate tool call.

### Pattern 3: `extract_lessons` Tool
**What:** A new Python function in `ontology_tools.py` that reads all session iteration files and synthesizes LESSONS.md.
**When to use:** HITL-gated only.
```python
def extract_lessons(tool_context: Optional[ToolContext] = None) -> str:
    """
    Read all python_iterations/ files across sessions, present them
    to the agent for analysis, write structured LESSONS.md.
    Returns JSON: {"success": bool, "lessons_file": str, "sessions_read": int}
    """
    # Walk PYTHON_ITERATIONS_DIR, collect all .py files in session order
    # Return file contents for LLM analysis + write LESSONS.md
```
Note: `extract_lessons` reads files and returns their content to the LLM — the LLM does the analysis and calls a follow-up write. OR: the tool reads + the agent synthesizes + calls a separate `write_lessons` helper. The simpler approach: `extract_lessons` returns a structured JSON with all session files, and the agent writes LESSONS.md via `_read_text_file` pattern. The planner should define the exact interface.

### Pattern 4: Path Constant Update (ontology_tools.py)
**Current constants** (need replacing):
```python
# Current — WRONG after phase 15
ONTOLOGY_FILE = os.path.join(_PROJECT_ROOT, "223p", "src", "ontology.py")
TTL_OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "223p", "ttl")
_MAPPINGS_DIR = os.path.join(_PROJECT_ROOT, "agent", "skills", "skill-read-code", "assets", "mappings")
_PROMPT_MD = os.path.join(_PROJECT_ROOT, "agent", "sub_agents", "_223p", "generator", "prompt.md")
run_cwd = os.path.join(_PROJECT_ROOT, "223p")  # in execute_ontology
```
**Target constants** (post-phase-15):
```python
_AGENT_ROOT = os.path.abspath(os.path.join(_HERE, ".."))  # agent/
_223P_DIR = os.path.join(_AGENT_ROOT, "223p")
ONTOLOGY_FILE = os.path.join(_223P_DIR, "ontology.py")
TTL_OUTPUT_DIR = _223P_DIR  # ontology.ttl written to agent/223p/ontology.ttl
_MAPPINGS_DIR = os.path.join(_223P_DIR, "mappings")
PYTHON_ITERATIONS_DIR = os.path.join(_223P_DIR, "python_iterations")
TTL_ITERATIONS_DIR = os.path.join(_223P_DIR, "ttl_iterations")
LESSONS_FILE = os.path.join(_223P_DIR, "LESSONS.md")
# read_prompt: prompt.md no longer lives in sub_agents — needs new location
# Options: agent/223p/ref/code/prompt.md OR embed in skill SKILL.md directly
```

### Anti-Patterns to Avoid
- **Leaving `_PROMPT_MD` pointing to deleted sub_agents path:** `read_prompt` tool will silently return an error after sub_agents deletion. Fix path or deprecate `read_prompt` if it's no longer needed.
- **Writing session archive without mkdir:** Session directories don't exist until first write. Always call `os.makedirs(..., exist_ok=True)` before writing.
- **Storing session ID only in ADK state without fallback:** If state is reset between sessions, counter restarts. Archive folder names provide ground truth — `extract_lessons` should detect highest existing session number if state is absent.
- **Deleting root 223p/ before path constants are updated:** Will cause immediate runtime breakage. Path update must precede deletion.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Writing versioned files to uploads | Custom timestamp logic | `_persist_python` / `_persist_ttl` pattern from `ontology_exit_tools.py` | Already handles mkdir + versioned + latest write |
| State mutation (snapshots list) | Direct list mutation | Read-copy-write: `list(state.get(..., []))` then reassign | ADK session mutation bug avoidance (Decision 09-01) |
| Finding highest session number | Custom glob sort | `sorted(Path(PYTHON_ITERATIONS_DIR).glob("session_*"))` | stdlib glob+sort is sufficient |
| Backing up files | Custom copy logic | Existing `_backup_file` in `ontology_tools.py` | Already handles numbered backups |

---

## Common Pitfalls

### Pitfall 1: Stale Test Assertions in test_create_master_agent.py
**What goes wrong:** `test_imports_ontology_tools_from_223p` and `test_imports_checkpoint_code_from_validator` already fail because they check for old sub_agents import strings. If left in place, they will continue failing and block CI.
**Why it happens:** The tests were written for the Phase 13 intermediate state; Phase 13 completed the migration but these two assertions were not updated.
**How to avoid:** Remove exactly these two test functions as part of Workstream 1. The other 6 tests in this file pass and must be preserved.
**Warning signs:** Running `pytest tests/test_create_master_agent.py` shows 2 FAILED immediately.

### Pitfall 2: prompt.md Orphaned After sub_agents Deletion
**What goes wrong:** `read_prompt()` in `ontology_tools.py` has `_PROMPT_MD` pointing to `agent/sub_agents/_223p/generator/prompt.md`. After sub_agents deletion, calling `read_prompt` returns `{"error": "File not found: ..."}`.
**Why it happens:** The `read_prompt` tool was not updated in Phase 13.
**How to avoid:** Either (a) move `prompt.md` to `agent/223p/ref/code/prompt.md` and update `_PROMPT_MD`, or (b) if the skill SKILL.md already contains the generation guidelines, deprecate `read_prompt` entirely. Check whether `skill-ontology-generation/SKILL.md` or `skill-ontology-validation/SKILL.md` currently instructs agents to call `read_prompt`.
**Current status:** `skill-ontology-validation/SKILL.md` instructs: "read_prompt tool for original generation guidelines." So the tool is still used. Move the file, update the constant.

### Pitfall 3: Relative Path `../223p/ref/code` in SKILL.md
**What goes wrong:** `skill-ontology-generation/SKILL.md` step 4 instructs agents to call `scan_python_files_filtered` on `../223p/ref/code`. After root 223p/ is deleted and moved to `agent/223p/`, this relative path resolves to the wrong place.
**Why it happens:** The skill was written relative to the project root, not relative to agent/.
**How to avoid:** Replace `../223p/ref/code` with the absolute path `agent/223p/ref/code` (or `{_AGENT_ROOT}/223p/ref/code` as a literal in the SKILL.md). The CONTEXT.md explicitly calls this out as a required fix.

### Pitfall 4: OSError During Three-Write Atomicity
**What goes wrong:** `write_ontology` writes scratch first, then archives. If interrupted mid-sequence, scratch exists but archive does not.
**Why it happens:** No transaction semantics in filesystem writes.
**How to avoid:** This is acceptable — the scratch file is the operative file; archives are best-effort. Document this in code comments. Do not add retry logic for archive writes (keep it simple, log warnings on OSError as `_persist_python` already does).

### Pitfall 5: Session ID Drift Between State Resets
**What goes wrong:** If ADK state is reset (new session in the framework), `ontology_session_id` restarts from 0. This causes new iteration files to overwrite existing session_1/ archives.
**Why it happens:** State is ephemeral per ADK session; archives are permanent on disk.
**How to avoid:** When initializing `ontology_session_id`, scan `PYTHON_ITERATIONS_DIR` for the highest existing `session_N` directory and start from N+1. This makes disk the authoritative counter for session numbers.

### Pitfall 6: `test_223p_tools.py` Tests Now in `ontology_tools.py`
**What goes wrong:** The tests in `test_223p_tools.py` test `scan_python_files_filtered` and `search_class_mapping` from `sub_agents._223p.tool`. These same functions exist in `agent/tools/ontology_tools.py` and are tested there (via the same test bodies that were migrated in Phase 11). Deleting these tests leaves the `ontology_tools.py` functions covered — but planners should verify no unique coverage is lost.
**How to avoid:** Before deleting, confirm `test_ontology_tools.py` or another test file covers `scan_python_files_filtered` and `search_class_mapping` from the new module. Currently, the 14 `TestScanPythonFilesFiltered` + `TestSearchClassMapping` tests in `test_223p_tools.py` test the old module. The same tests in spirit exist (confirmed from pytest collect output).

---

## Code Examples

### Example 1: Updated path constants in ontology_tools.py
```python
# Source: agent/tools/ontology_tools.py (post-phase-15 target)
_HERE = os.path.dirname(os.path.abspath(__file__))
_AGENT_ROOT = os.path.abspath(os.path.join(_HERE, ".."))    # agent/
_PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))  # project root

_223P_DIR = os.path.join(_AGENT_ROOT, "223p")
ONTOLOGY_FILE = os.path.join(_223P_DIR, "ontology.py")
TTL_OUTPUT_DIR = _223P_DIR  # ontology.ttl written as agent/223p/ontology.ttl
_MAPPINGS_DIR = os.path.join(_223P_DIR, "mappings")
PYTHON_ITERATIONS_DIR = os.path.join(_223P_DIR, "python_iterations")
TTL_ITERATIONS_DIR = os.path.join(_223P_DIR, "ttl_iterations")
LESSONS_FILE = os.path.join(_223P_DIR, "LESSONS.md")
_PROMPT_MD = os.path.join(_223P_DIR, "ref", "code", "prompt.md")
```

### Example 2: Three-write pattern in write_ontology
```python
# Source: adapted from _persist_python in agent/tools/ontology_exit_tools.py
def write_ontology(content: str, tool_context: Optional[ToolContext] = None) -> str:
    # 1. Scratch write (existing behavior)
    os.makedirs(os.path.dirname(ONTOLOGY_FILE), exist_ok=True)
    with open(ONTOLOGY_FILE, "w", encoding="utf-8") as fh:
        fh.write(content)

    # 2. Session archive write
    if tool_context:
        session_id = tool_context.state.get("ontology_session_id")
        iter_count = tool_context.state.get("ontology_code_iteration_count", 0)
        if session_id is None:
            # Auto-detect from disk to avoid session ID drift
            existing = sorted(Path(PYTHON_ITERATIONS_DIR).glob("session_*"))
            session_id = len(existing) + 1
            tool_context.state["ontology_session_id"] = session_id
        session_dir = Path(PYTHON_ITERATIONS_DIR) / f"session_{session_id}"
        session_dir.mkdir(parents=True, exist_ok=True)
        archive = session_dir / f"ontology_{iter_count + 1:03d}.py"
        archive.write_text(content, encoding="utf-8")

    # 3. Uploads write (using established _persist_python pattern)
    _persist_python(content, "write_ontology")
```

### Example 3: Assertions to remove from test_create_master_agent.py
The following two test functions must be deleted (they test old sub_agents import strings):
```python
# DELETE: test_imports_ontology_tools_from_223p (line 52-58)
# DELETE: test_imports_checkpoint_code_from_validator (line 61-64)
```
The following test must be preserved and checked still passes:
```python
def test_imports_adapted_exit_tools():
    # Checks "from tools.ontology_exit_tools import" — still valid post-phase-15
```

### Example 4: skill-ontology-generation SKILL.md additions
```markdown
## Step 0 — Read Lessons (BEFORE EVERYTHING ELSE)
Read `agent/223p/LESSONS.md`. If the file is empty or absent, proceed without it.
Do not use `skill-read-code` — that skill no longer exists. Use only this embedded step.

## Lesson Extraction (HITL gate)
If the user explicitly says "extract lessons" or "update lessons":
- Call `extract_lessons()` tool.
- Do NOT auto-trigger this step.
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Ontology tools in sub_agents/_223p/tool.py | Tools in agent/tools/ontology_tools.py | Phase 13 | sub_agents is now dead code |
| 223p at project root | 223p inside agent/ | Phase 15 | Cleaner agent encapsulation |
| skill-read-code provides lessons | LESSONS.md embedded in agent/223p/ | Phase 15 | No separate skill for reading code |
| Exit tools write to uploads | write_ontology writes to uploads on every call | Phase 15 | Real-time iteration visibility in CodeWindow |
| Lessons distilled via skill-read-code workflow | `extract_lessons` tool HITL-gated | Phase 15 | LLM-powered distillation, no manual walk |

**Deprecated/outdated after Phase 15:**
- `agent/sub_agents/` — entire directory, zero references from master
- `agent/skills/skill-read-code/` — functionality absorbed into LESSONS.md + extract_lessons
- Root `223p/` — moved entirely into agent/

---

## Open Questions

1. **Disposition of `read_prompt` tool**
   - What we know: `skill-ontology-validation/SKILL.md` instructs agents to call `read_prompt`. The prompt.md lives at `agent/sub_agents/_223p/generator/prompt.md`.
   - What's unclear: After sub_agents deletion, should prompt.md be moved to `agent/223p/ref/code/prompt.md` (and `_PROMPT_MD` updated), or should the validator skill be rewritten to not need it?
   - Recommendation: Move prompt.md to `agent/223p/ref/code/prompt.md`, update `_PROMPT_MD` constant. This is the minimal-change approach and keeps `read_prompt` functional.

2. **Exit tool behavior after three-write pattern**
   - What we know: `exit_generator_success` calls `_persist_python` (uploads write). `write_ontology` will now also write to uploads on every call.
   - What's unclear: Should `exit_generator_success` still call `_persist_python`? This would cause a duplicate uploads write on success. Is that acceptable (harmless) or should the exit tools skip the uploads write and rely on `write_ontology` having already done it?
   - Recommendation: Keep `exit_generator_success` calling `_persist_python` — the final exit upload is a deliberate "seal" of the generation. The duplicate write is harmless (same content, different timestamp). Simplest approach with no behavioral regression.

3. **Historical 223p/src/ backups (ontology_1.py ... ontology_39.py)**
   - What we know: 39 accumulated backup files + ontology.py scratch exist in root `223p/src/`. Also `results/` folder has 5 dated run archives.
   - What's unclear: CONTEXT leaves this to Claude's discretion — archive or delete.
   - Recommendation: Delete the `src/` backup files (they predate the session-archive pattern and have no LESSONS.md distillation). Move `results/` into `agent/223p/python_iterations/` as `session_0/` through `session_4/` (preserving historical run data for possible future `extract_lessons` calls). Move `run_validation.py` to `agent/223p/` (archive, not delete — it's a useful standalone runner).

---

## Validation Architecture

> workflow.nyquist_validation is not set in .planning/config.json — treating as enabled.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `agent/pyproject.toml` |
| Quick run command | `cd agent && .venv/bin/python -m pytest tests/test_create_master_agent.py -v` |
| Full suite command | `cd agent && .venv/bin/python -m pytest tests/ -v --ignore=tests/test_capture_frontend_state_live.py --ignore=tests/test_write_metadata_batch_live.py` |

### Phase Requirements → Test Map

| Area | Behavior | Test Type | Automated Command | Notes |
|------|----------|-----------|-------------------|-------|
| sub_agents deletion | No imports from sub_agents in master | static analysis | `pytest tests/test_create_master_agent.py::test_no_ontology_subagents_list` | Existing test, already passes |
| test cleanup | Stale assertions removed | unit | `pytest tests/test_create_master_agent.py -v` — all 6 remaining pass | 2 functions deleted |
| path constants | ONTOLOGY_FILE points to agent/223p/ | unit | New test: `pytest tests/test_ontology_tools.py::test_path_constants` | Wave 0 gap |
| three-write pattern | write_ontology writes to uploads + archive | unit | New test: `pytest tests/test_ontology_tools.py::test_write_ontology_three_writes` | Wave 0 gap |
| session archive | archive files named correctly | unit | New test: `pytest tests/test_ontology_tools.py::test_session_archive_naming` | Wave 0 gap |
| extract_lessons | tool returns session files | unit | New test: `pytest tests/test_ontology_tools.py::test_extract_lessons` | Wave 0 gap |
| search_class_mapping | still works from new mappings dir | unit | `pytest tests/test_ontology_tools.py -k "search_class"` | Existing tests, path change needed |
| skill generation | SKILL.md has LESSONS.md step + correct paths | content audit | manual review of SKILL.md | Manual-only |
| skill validation | SKILL.md has no skill-read-code references | content audit | manual review of SKILL.md | Manual-only |

### Sampling Rate
- **Per task commit:** `cd agent && .venv/bin/python -m pytest tests/test_create_master_agent.py tests/test_ontology_tools.py -v`
- **Per wave merge:** `cd agent && .venv/bin/python -m pytest tests/ -v --ignore=tests/test_capture_frontend_state_live.py --ignore=tests/test_write_metadata_batch_live.py`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `agent/tests/test_ontology_tools.py` — needs new tests for updated path constants, three-write behavior, session archive naming, and extract_lessons. The existing `test_223p_tools.py` tests the OLD module; the new tests should cover the same functions from `ontology_tools.py` (with new behavior).

Note: `test_223p_tools.py` currently contains 14 tests covering `scan_python_files_filtered` and `search_class_mapping` from the sub_agents module. These same functions exist in `ontology_tools.py` and are already used by the master. Confirm coverage before deleting.

---

## Sources

### Primary (HIGH confidence)
- Direct file reads: `agent/tools/ontology_tools.py`, `agent/tools/ontology_exit_tools.py`, `agent/master_architecture/create_master_agent.py`, all SKILL.md files
- Direct file inspection: `agent/sub_agents/` directory tree, `223p/` directory tree, `agent/tests/` directory
- Pytest execution: `test_create_master_agent.py` run confirmed 2 failing, 6 passing

### Secondary (MEDIUM confidence)
- Pattern inference: three-write behavior derived from existing `_persist_python` / `_persist_ttl` patterns which are confirmed in code
- Session ID disk-based initialization derived from stated pitfall about state reset, consistent with the established "never rely on ephemeral state for permanent naming" principle

### Tertiary (LOW confidence)
- None — all claims are backed by direct code inspection of the live repository

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries are already in use, no new dependencies
- Architecture: HIGH — all patterns derived from existing code confirmed via file reads
- Pitfalls: HIGH — 3 of 6 pitfalls confirmed by live test run or direct code inspection; 3 are derived from established ADK patterns

**Research date:** 2026-04-02
**Valid until:** 2026-05-02 (stable codebase, no external dependencies changing)
