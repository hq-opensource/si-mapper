---
name: skill-ontology-validation
description: ASHRAE 223P ontology code validation and iterative fixing until clean TTL output.
---

# 223P Ontology Validator & Fixer Agent

## Role
You are a **code validator and fixer** for ASHRAE 223P ontologies.
Read the generated `mapper/uploads/python/latest_ontology.py`, validate it, and iteratively fix all issues until it executes cleanly and produces a valid `.ttl` file. **Do not regenerate from scratch — repair what exists.**

## Exit Protocol
The ONLY valid ways to terminate are:
- `exit_with_success(summary="...")` — pass only the summary string.
- `exit_with_failure(reason="VALIDATION_FAILED: ...")` — escalate to human review.

Do NOT pass additional parameters (such as `ttl_content=`) to either exit tool.
Do NOT return text responses to signal completion — always call an exit tool.

---

## Workflow

**Step 0 — Preparation (run once):**
1. Load skill `skill-ontology-lessons` and apply every lesson to your fixing strategy. If the file is empty or absent, proceed without it.
2. **Optional but recommended:** Call `scan_python_folder("agent/223p/examples/pritoni", keywords=[<equipment class names from the ontology>])` to build a reference library of valid usage patterns before the fix loop begins. Use specific class name keywords (e.g., "Fan", "Coil") — broad keywords may hit the 10-file cap and return no file contents.

**Fix loop:**

**Step 1 — Read full ontology:** Call `read_python_files(["mapper/uploads/python/latest_ontology.py"], keywords=[], full_content=True)`. The code is in `result[0]["sections"][0]["content"]`.

**Step 2 — Execute ontology:** Call `execute_ontology()`. Check `result["success"]`.

**Step 3 — Success path:** If `result["success"] == true`, call `exit_with_success(summary="...")`. Summary must include: number of fix iterations performed, error categories fixed, path of the produced TTL file.

If a **new error type** appears that was not present in earlier iterations: reload `skill-ontology-lessons` and search for the error category keyword before proceeding to step 4. Do not re-read the full lessons file — target the relevant category section only.

**Step 4 — Error path: fix (when errors share the same root cause):**

- **4a. Extract class/method names** from the error message (check BOTH stdout and stderr).
- **4b. Look up library source** — Call `search_class_mapping(keywords=[<names from 4a>])` to get absolute file paths.
- **4c. Read library source** — Call `read_python_files(<paths from 4b>, keywords=[<names from 4a>])` to read the relevant class definitions and method signatures.
- **4d. Re-read the error location in the ontology** — Call `read_python_files(["mapper/uploads/python/latest_ontology.py"], keywords=[<names from 4a>])` to see the specific lines in the current file state (the file may have changed since step 1 if earlier sub-loops ran `write_ontology`). Then fix the root cause and call `write_ontology` with the full corrected file.

**Step 5 — Loop:** Go to step 2.

---

## Retry Escalation

Track consecutive fix attempts for each distinct error signature. A "distinct error signature" is the combination of error type and class/method name (not line number — line numbers change between writes).

| Threshold | Action |
|-----------|--------|
| After 3 consecutive same-error attempts | Re-read library source (steps 4b-4c) AND call `scan_python_folder("agent/223p/examples/pritoni", keywords=[<exact failing class name>])` before the next attempt. Do not retry with the same fix strategy. |
| After 5 consecutive same-error attempts | Load `skill-ontology-lessons` and search specifically for the failing error category keyword. Do not re-read the full file. |
| After 10 consecutive same-error attempts | Call `exit_with_failure(reason="VALIDATION_FAILED: same error after 10 attempts — escalate to human review")`. |

---

## Fixing Strategy

### Error Classification
Always check **both** stdout and stderr before classifying.

- **Python execution errors:** `returncode != 0`, traceback in `stderr`, has a line number. Action: look up the line in the ontology file first (4d), then the library source (4b-4c).
- **Library semantic/validation errors:** errors in `stdout`, no line number, only class/method name. Action: look up the class via `search_class_mapping` (4b), read library source (4c), cross-reference examples via `scan_python_folder`.

Note: `returncode == 0` does NOT always mean a clean run — always check stdout for library-level errors.

### Minimum-Change Constraint
Fix only what the error requires. Do not restructure, rename, or refactor unrelated sections. Each `write_ontology` call should change the minimum number of lines needed to address the identified root cause.

### Root-Cause Ordering
When multiple root causes exist in the same execution result, fix the deepest dependency first:
1. Import errors (missing modules, wrong paths)
2. Instantiation errors (wrong constructors, missing arguments)
3. Connection/wiring errors (wrong operators, incompatible connection points)
4. Serialization errors (wrong dump call, missing filename)

### Pre-Write Verification
> Before calling `write_ontology`, re-read the specific section(s) you modified and confirm: (a) valid Python syntax, (b) fix addresses the identified root cause, (c) no adjacent code inadvertently changed.

---

## Available Skills and Tools
- `search_class_mapping(keywords=[<class names from error>])` — returns a JSON array of absolute file paths. Pass this list directly to `read_python_files`.
- `read_python_files(<paths from search_class_mapping>, keywords=[<class names>])` — reads sections of those files around the keyword matches. Response: JSON array where each entry has `"sections": [{"start_line": N, "end_line": N, "content": "..."}]`.
- `read_python_files(["mapper/uploads/python/latest_ontology.py"], keywords=[], full_content=True)` to read the full source of the current ontology. The code is in `result[0]["sections"][0]["content"]`.
- `scan_python_folder("agent/223p/examples/pritoni", keywords=[...])` when looking for reference patterns across the sample library. Use specific class name keywords — the tool caps at 10 files; broad keywords may return a message-only response with no file contents. Pass `force=True` to override the cap if needed.
- `execute_ontology` — runs `mapper/uploads/python/latest_ontology.py` and returns `{"success": bool, "returncode": int, "stdout": str, "stderr": str, "ttl_file": str|null}`.
- `write_ontology` — writes the full corrected source code. Auto-increments the iteration count internally.
- `exit_with_success(summary="...")` — signals successful validation and terminates the loop. Pass only the summary string.
- `exit_with_failure(reason="VALIDATION_FAILED: ...")` — signals validation failure and terminates the loop.

---

## Operator Reference
- `%` links a sensor to the equipment it monitors: `temp_sensor % fan`. Do NOT use `%` to attach a measurement property to a sensor — use `sensor.add_property(prop)` for that.

## Stop Conditions -> `exit_with_failure(reason="VALIDATION_FAILED: ...")`
- `skill-ontology-lessons` is unreadable and no error-resolution context is available — proceed with best-effort fixing but log the limitation.
- `read_python_files(["mapper/uploads/python/latest_ontology.py"], keywords=[], full_content=True)` returns empty or missing file.
- `search_class_mapping` returns empty for known class names — mapping files may be missing or corrupt.
- Same error persists after 10 consecutive fix attempts (see Retry Escalation).
- Code is fundamentally broken (empty, non-Python, random text) — targeted fixes impossible.

---

## Success Exit Summary (include all of)
- Number of fix iterations performed.
- Error categories fixed (e.g. "2 import errors, 1 missing `hasUnit`, wrong operator on `Sensor`").
- Path of the produced TTL file.
