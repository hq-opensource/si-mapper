# Phase 16: Optimize Ontology Skills — PLAN

Fix 21 identified issues across the ontology generation and validation pipeline.
Targets: correctness bugs, token waste, redundant file writes, agent clarity, and stale docs.

---

## Tasks

### 16.1 — Fix venv Python path detection (B4)
**File:** `agent/tools/ontology_tools.py`

In `execute_ontology`, check Linux path first, then Windows, then fall back to `sys.executable`:
```python
venv_python = os.path.join(_PROJECT_ROOT, "agent", ".venv", "bin", "python")
if not os.path.exists(venv_python):
    venv_python = os.path.join(_PROJECT_ROOT, "agent", ".venv", "Scripts", "python.exe")
if not os.path.exists(venv_python):
    venv_python = sys.executable
```

**Verification:** `execute_ontology` uses the venv Python on Linux without falling back to `sys.executable`.

---

### 16.2 — Delete `_persist_python` and `_persist_ttl` (R1 + R2)
**Files:** `agent/tools/ontology_exit_tools.py`, `agent/tools/ontology_tools.py`

**Why they are safe to delete:**
- `write_ontology` already writes `latest_ontology.py` to `mapper/uploads/python/` (frontend) and archives to `agent/223p/python_iterations/session_N/` (history).
- `execute_ontology` already writes `latest_ontology.ttl` to `mapper/uploads/ttl/` (via the script's own `dump()` call) and archives to `agent/223p/ttl_iterations/session_N/`.
- The two-folder structure (uploads = frontend-visible, 223p = protected history) covers everything. The timestamped copies these functions produced were a third redundant location.

**Changes:**
1. Delete `_persist_python` from `ontology_exit_tools.py`
2. Delete `_persist_ttl` from `ontology_exit_tools.py`
3. Remove `from tools.ontology_exit_tools import _persist_python, _persist_ttl` import in `ontology_tools.py`
4. Remove the `_persist_python(content, "write_ontology")` call at the bottom of `write_ontology`
5. Remove the `_persist_ttl(ttl_content)` call inside `execute_ontology`

**Verification:** `write_ontology` and `execute_ontology` still write to both expected locations (`uploads/` and `223p/`). No `_persist_python` or `_persist_ttl` calls remain in the codebase.

---

### 16.3 — Remove `code=` from `exit_generator_success` (B1 + T1)
**File:** `agent/tools/ontology_exit_tools.py`

`write_ontology` already saved the code before the agent reaches this call. The `code=` parameter forces the agent to repeat the full Python string in the exit call (~300–600 extra tokens per run).

**Changes:**
1. Remove `code: str` parameter from `exit_generator_success` signature
2. Remove the `_persist_python(code, "exit_generator_success")` call (already deleted in 16.2, but confirm it's gone)
3. Remove the `snapshots.append({"label": "Initial", "code": code, ...})` line — the snapshot was already saved by `write_ontology`
4. Update docstring

**Verification:** `exit_generator_success(tool_context, summary="...")` is the full call signature. No `code=` anywhere.

---

### 16.4 — Remove `code=` and `ttl_content=` from `exit_validator_success` (B3 + T3)
**File:** `agent/tools/ontology_exit_tools.py`

- `write_ontology` already saved the final Python code and its snapshot.
- `execute_ontology` already wrote `latest_ontology.ttl` to disk.
- The exit tool reads the TTL from `mapper/uploads/ttl/latest_ontology.ttl` internally.

**Changes:**
1. Remove `code: str` parameter from `exit_validator_success` signature
2. Remove `ttl_content: str = ""` parameter
3. Add internal TTL read: `ttl_content = Path(TTL_OUTPUT_DIR) / "latest_ontology.ttl"` read via `Path.read_text`
4. Keep the `ttl_code_snapshots` append — but read content from disk, not from parameter
5. Remove `_persist_ttl` and `_persist_python` calls (already deleted in 16.2)
6. Update docstring

**Verification:** `exit_validator_success(tool_context, summary="...")` is the full call signature. TTL tab in frontend is populated correctly.

---

### 16.5 — Fold `checkpoint_code` into `write_ontology` (T5)
**Files:** `agent/tools/ontology_exit_tools.py`, `agent/tools/ontology_tools.py`

Currently the validator must call `write_ontology` then `checkpoint_code` as two separate tool calls after every fix. `checkpoint_code` only appends a snapshot to state and increments `ontology_code_iteration_count`. Moving this into `write_ontology` saves one tool call per fix iteration.

**Changes:**
1. In `write_ontology`, after the session archive write, add the logic from `checkpoint_code`:
   - Append `{"label": f"Fix {iter_count}", "code": content, "iteration": iter_count, "status": "fix"}` to `python_code_snapshots`
   - Increment `ontology_code_iteration_count`
2. Delete `checkpoint_code` function from `ontology_exit_tools.py`
3. Remove `checkpoint_code` from the tool registration in `create_master_agent.py`

**Verification:** After each `write_ontology` call, `ontology_code_iteration_count` is incremented and `python_code_snapshots` gains a new entry. `checkpoint_code` tool no longer exists.

---

### 16.6 — Add `max_files` cap to `scan_python_folder` (T2)
**File:** `agent/tools/ontology_tools.py`

Without a cap, `scan_python_folder` can flood the context with entire source files from the reference library.

**Changes:**
1. Add `max_files: int = 10` parameter to `scan_python_folder`
2. After collecting matches, slice: `files = dict(list(files.items())[:max_files])`
3. Add `"truncated": true` key to result when matches exceed `max_files`
4. Update docstring

**Verification:** Calling with a small reference folder returns at most `max_files` results. Result includes `"truncated": true` when capped.

---

### 16.7 — Update `write_ontology` and `execute_ontology` docstrings (D1 + D2)
**File:** `agent/tools/ontology_tools.py`

**`write_ontology` docstring:**
- Replace "Overwrite `agent/223p/ontology.py`" with "Write *content* to `mapper/uploads/python/latest_ontology.py`"
- Remove "three-write pattern" and "Scratch write" and "backup" references
- Reflect the two actual writes: primary file + session archive

**`execute_ontology` docstring:**
- Remove "Scratch: `agent/223p/ontology.ttl`" line
- Update to reflect: the script writes `latest_ontology.ttl` directly to `mapper/uploads/ttl/`; session archive in `ttl_iterations/`

**Verification:** Docstrings match actual behavior.

---

### 16.8 — Update generation SKILL.md (B1+T1, B2, C5)
**File:** `agent/skills/skill-ontology-generation/SKILL.md`

**Step 10 (B1+T1):** Change from:
```
Call `exit_generator_success(summary="...")`
```
to:
```
Call `exit_generator_success(summary="...")` — no code parameter needed, files are already saved.
```

**`%` operator (B2):** In the Sensors section, replace the current line with:
```
- `%` links a sensor to the equipment it monitors: `temp_sensor % fan`. Do NOT use `%` to attach a measurement property to a sensor — use `sensor.add_property(prop)` for that.
```

**Exit Protocol (C5):** Add a `## Exit Protocol` section near the top (after the workflow overview) that states: the ONLY valid way to signal completion is to call `exit_generator_success` or `exit_generator_failure`. Do not output text after calling either tool.

**Verification:** SKILL.md contains no `code=` in the exit call, the `%` usage is unambiguous, and the exit protocol is prominently placed.

---

### 16.9 — Update validation SKILL.md (B2, B3, C1, C3, T4, T5, D3, D4)
**File:** `agent/skills/skill-ontology-validation/SKILL.md`

**Step 0 — Preparation (C3):** Add explicit numbered step before the fix loop:
```
**Step 0 (run once before the loop):** Load skill `skill-ontology-lessons` and apply every lesson to your fixing strategy.
```

**Step 2 (C1):** Change "execute source code" to:
```
2. Call `execute_ontology()`. Check `result["success"] == true` to determine the path.
```

**Step 3a success path (B3):** Change to:
```
3. `result["success"] == true` → call `exit_validator_success(summary="...")`. The tool reads the TTL from disk internally — do not pass `code=` or `ttl_content=`.
```

**`%` operator (B2):** Add same clarification as in generation SKILL.md.

**Batching errors (T4):** Change "Fix one error at a time" to:
```
Fix all errors that share the same root cause in one pass before writing. Write the corrected file once per root cause, not once per error line.
```

**Remove `checkpoint_code` instruction (T5):** Delete the line instructing the agent to call `checkpoint_code` after `write_ontology`. It no longer exists as a separate tool.

**Stale references (D3, D4):** Replace "run the current `ontology.py`" with "`mapper/uploads/python/latest_ontology.py`" and fix the role description.

**Verification:** No stale paths, no `checkpoint_code` instruction, success condition is explicit, loop boundary is clear.

---

### 16.10 — Update lessons SKILL.md (B2)
**File:** `agent/skills/skill-ontology-lessons/SKILL.md`

In the **Sensor API** section, replace the ambiguous `%` operator lesson:
- Current: *"Error: Using the `%` operator to associate a property with a sensor → Fix: Use `add_property()`"*
- New: *"Error: Using `sensor % property` to attach a measurement property to a sensor → Fix: Use `sensor.add_property(prop)`. Note: `sensor % equipment` (attaching a sensor to the thing it monitors) is correct — only `sensor % property` is wrong."*

**Verification:** Lesson is unambiguous. No contradiction with generation/validation SKILL.md.

---

### 16.11 — Update tests (T5, R1, R2, B1, B4)
**File:** `agent/tests/test_ontology_tools.py`

Update or add tests to cover:
- `write_ontology` now auto-increments `ontology_code_iteration_count` (T5)
- `write_ontology` no longer calls `_persist_python` (R1)
- `execute_ontology` no longer calls `_persist_ttl` (R2)
- `exit_generator_success` no longer accepts `code=` (B1)
- `exit_validator_success` no longer accepts `code=` or `ttl_content=`; reads TTL from disk (B3)
- `execute_ontology` uses Linux venv path first (B4)
- `scan_python_folder` respects `max_files` cap (T2)

**Verification:** All existing tests pass. New tests cover changed behavior. `checkpoint_code` tests removed.

---

## Execution order

```
16.2 (delete helpers) → 16.1, 16.3, 16.4, 16.5 (edit exit tools + ontology_tools)
→ 16.6, 16.7 (remaining code changes)
→ 16.8, 16.9, 16.10 (SKILL.md updates)
→ 16.11 (tests)
```

16.2 must go first because 16.3, 16.4, and 16.5 all depend on those helper functions being gone.

## Success criteria
- [ ] No `_persist_python` or `_persist_ttl` references remain in the codebase
- [ ] `exit_generator_success(tool_context, summary=)` — only two params
- [ ] `exit_validator_success(tool_context, summary=)` — only two params, reads TTL from disk
- [ ] `write_ontology` auto-checkpoints on every call; `checkpoint_code` tool removed
- [ ] `execute_ontology` resolves Linux venv path correctly
- [ ] `scan_python_folder` respects `max_files=10` default
- [ ] Both SKILL.md files have unambiguous `%` operator docs
- [ ] Validation SKILL.md has explicit Step 0, explicit success condition, no stale paths
- [ ] All tests pass
