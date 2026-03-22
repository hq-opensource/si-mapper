# Phase 11: Optimization of the Coding Agent - Research

**Researched:** 2026-03-22
**Domain:** Python agent optimization — tool replacement and prompt surgery in Google ADK sub-agent architecture
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Lessons distillation (skill-read-code)
- `LESSONS.md` lives at `agent/skills/skill-read-code/LESSONS.md` — next to `SKILL.md` and the `assets/` archive.
- Raw iteration files in `assets/` are **kept as permanent archive** — never deleted or moved.
- **Trigger:** explicit human instruction to the master agent. Master uses the LLM to walk the raw asset files, identify deltas, and rewrite `LESSONS.md` with structured error-to-fix categories. Same HITL pattern as ontology generation.
- **Distillation is LLM-powered:** the master agent reads raw files using `skill-read-code`, synthesizes lessons, and writes `LESSONS.md`.
- **SKILL.md update:** if `LESSONS.md` exists → read it only, stop there. If it doesn't exist → walk `assets/` as today. **No fallback once LESSONS.md is created** — LESSONS.md only, no fallback.
- Applies to both generator and validator (both call the same skill).

#### Reference code filtering (scan_python_files)
- Add `scan_python_files_filtered(path, keywords: list[str])` to `agent/sub_agents/_223p/tool.py`.
- Returns only `.py` files whose **content** contains at least one keyword (case-insensitive substring match).
- **Applied to ALL `scan_python_files` calls** in both agent prompts — not just the `223p/ref/code` path.
- Workflow in prompt: agent extracts equipment class names from `read_grid` output → passes them as `keywords` to `scan_python_files_filtered`. Only files mentioning those classes are returned.
- Both `ontology_generator/prompt.md` and `ontology_validator/prompt.md` updated to use `scan_python_files_filtered`.

#### Scope: both agents
- Every optimization (lessons, filtering, class mapping) applies to **both** `ontology_generator` and `ontology_validator`.
- New tools added to shared `_223p/tool.py` so both agents import from the same location.
- Prompt changes made independently to each agent's `prompt.md` (separate files, same structural updates).

#### Static class mapping (replaces list_library_classes + get_class_details)
- **Mapping files** at `agent/skills/skill-read-code/assets/mappings/`:
  - Keep: `classes_bob.jsonl` (752 entries: `class_name`, `path`, `types`)
  - Keep: `classes_scratch.jsonl` (99 entries: same structure)
  - **Remove:** `full_bob.jsonl` and `full_scratch.jsonl` — redundant.
- **New tool:** `search_class_mapping(keywords: list[str])` — grep-like search across both `classes_*.jsonl` files. Returns all matching lines as a list of dicts `{class_name, path, types, library}`. Match is case-insensitive substring on `class_name`.
- **Replaces `list_library_classes` entirely.** Replaces most `get_class_details` calls: agent uses `path` from mapping results to read the actual Python source file directly (via `scan_python_files_filtered`), getting full class details without a catalog dump.
- `list_library_classes` and `get_class_details` remain in `tool.py` but are removed from the agent tool lists and prompts.
- Tool added to `_223p/tool.py`, imported into both `ontology_generator/agent.py` and `ontology_validator/agent.py`.

### Claude's Discretion
- Whether `search_class_mapping` searches both JSONL files in a single call or takes a `library` parameter — implementation detail.
- Exact keyword matching strategy (class name only vs. also matching on `types` field).
- How the prompt instructs the agent to derive keywords from `read_grid` output.

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope.
</user_constraints>

---

## Summary

Phase 11 is a pure Python backend optimization with zero frontend changes. Three expensive agent operations are replaced by cheaper, targeted alternatives that reduce context window consumption. All changes touch two files in the shared tool layer (`_223p/tool.py`) and four prompt/agent files split evenly between the generator and validator sub-agents.

The code is well-structured for this work. The existing `scan_python_files` function at line 315 of `tool.py` is a direct template for `scan_python_files_filtered` — the walk logic is identical, filtered by a keyword check on file content before inclusion. The `_library_cache` dict at line 144 shows the established module-level caching pattern to follow for JSONL loading in `search_class_mapping`. Both agent constructors deduplicate tools by name, so adding new tools and removing old ones is a straightforward list edit.

The three optimizations are independent and can be planned as three separate tasks (one per optimization), each touching the same set of files: `tool.py`, both `agent.py` files, and both `prompt.md` files. A fourth task handles `SKILL.md` update and `LESSONS.md` skeleton creation. File deletion (`full_bob.jsonl`, `full_scratch.jsonl`) is a cleanup task at the end.

**Primary recommendation:** Implement as four sequential tasks — (1) `scan_python_files_filtered` tool + prompt wiring, (2) `search_class_mapping` tool + prompt wiring + agent.py tool list swap, (3) `SKILL.md` LESSONS.md-first logic + LESSONS.md skeleton, (4) delete redundant JSONL files.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib: `json`, `os` | built-in | JSONL parsing, file I/O | Already used throughout `tool.py` |
| Google ADK `ToolContext` | >=1.18.0 | Optional tool context param pattern | Matches existing tool signatures |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | >=9.0.2 | Unit tests for new tool functions | All new functions need test coverage |
| `unittest.mock` (stdlib) | built-in | Mock file I/O and ToolContext in tests | Same pattern as existing agent tests |

**Installation:** No new dependencies required. All tools use stdlib only.

---

## Architecture Patterns

### Recommended Project Structure
No new files or directories are added. All changes are in-place edits to existing files, plus two new functions in `tool.py`, one new file `LESSONS.md`, and deletion of two JSONL files.

```
agent/sub_agents/_223p/tool.py          # +2 new functions, +2 schemas, __all__ additions
agent/sub_agents/ontology_generator/
    agent.py                            # tool list: +scan_python_files_filtered, +search_class_mapping, -list_library_classes, -get_class_details
    prompt.md                           # workflow steps updated
agent/sub_agents/ontology_validator/
    agent.py                            # same tool list changes
    prompt.md                           # same workflow updates
agent/skills/skill-read-code/
    SKILL.md                            # LESSONS.md-first logic in Reading Protocol
    LESSONS.md                          # new file (skeleton)
    assets/mappings/
        full_bob.jsonl                  # DELETE
        full_scratch.jsonl              # DELETE
agent/tests/
    test_223p_tools.py                  # new test file for scan_python_files_filtered + search_class_mapping
```

### Pattern 1: scan_python_files_filtered
**What:** Same directory walk as `scan_python_files`, but before including a file reads its content and checks if any keyword appears (case-insensitive substring). Returns the same JSON shape as the original.
**When to use:** When the agent knows class names from `read_grid` output and only needs files that reference those classes.
**Example:**
```python
# Source: agent/sub_agents/_223p/tool.py:315 (template)
def scan_python_files_filtered(path: str, keywords: list[str]) -> str:
    """
    Recursively scan a directory and return only .py files whose content
    contains at least one of the given keywords (case-insensitive substring).

    Returns the same JSON shape as scan_python_files:
        {"root": ..., "files": {"rel/path.py": "<source>"}, "error": ...}
    """
    resolved = os.path.realpath(os.path.expanduser(path))
    if not os.path.exists(resolved):
        return json.dumps({"error": f"Path not found: {resolved!r}", "root": resolved, "files": {}})
    if not os.path.isdir(resolved):
        return json.dumps({"error": f"Path is not a directory: {resolved!r}", "root": resolved, "files": {}})

    lower_keywords = [kw.lower() for kw in keywords]
    files: dict[str, str] = {}
    for dirpath, _dirnames, filenames in os.walk(resolved):
        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue
            abs_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(abs_path, resolved).replace("\\", "/")
            try:
                with open(abs_path, "r", encoding="utf-8", errors="replace") as fh:
                    content = fh.read()
                content_lower = content.lower()
                if any(kw in content_lower for kw in lower_keywords):
                    files[rel_path] = content
            except OSError as exc:
                files[rel_path] = f"<ERROR reading file: {exc}>"

    return json.dumps({"root": resolved, "files": files}, ensure_ascii=False, indent=2)
```

### Pattern 2: search_class_mapping
**What:** Loads both `classes_bob.jsonl` and `classes_scratch.jsonl` from the mappings directory, finds all entries where `class_name` contains any keyword (case-insensitive), returns matches with a `library` field added.
**When to use:** When the agent needs to locate which file a class lives in, before calling `scan_python_files_filtered` to read that file.
**Example:**
```python
# Source: derived from _library_cache pattern at tool.py:144
_MAPPINGS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..",  # -> project root
    "agent", "skills", "skill-read-code", "assets", "mappings"
)
_JSONL_FILES = {
    "bob": "classes_bob.jsonl",
    "scratch": "classes_scratch.jsonl",
}
_mapping_cache: dict[str, list[dict]] = {}

def _load_mapping(library: str) -> list[dict]:
    if library not in _mapping_cache:
        path = os.path.join(_MAPPINGS_DIR, _JSONL_FILES[library])
        entries = []
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        _mapping_cache[library] = entries
    return _mapping_cache[library]

def search_class_mapping(keywords: list[str]) -> str:
    """
    Grep-like search across classes_bob.jsonl and classes_scratch.jsonl.
    Returns entries where class_name contains any keyword (case-insensitive).
    Each result includes a 'library' field ('bob' or 'scratch').
    """
    lower_keywords = [kw.lower() for kw in keywords]
    results = []
    for library in ("bob", "scratch"):
        for entry in _load_mapping(library):
            name_lower = entry["class_name"].lower()
            if any(kw in name_lower for kw in lower_keywords):
                results.append({**entry, "library": library})
    return json.dumps(results, ensure_ascii=False, indent=2)
```

**Note on MAPPINGS_DIR path:** The `_HERE` variable in `tool.py` points to `agent/sub_agents/_223p/`. The mappings are at `agent/skills/skill-read-code/assets/mappings/`. The relative path from `_HERE` is `../../skills/skill-read-code/assets/mappings`. Use `_PROJECT_ROOT` (already defined at line 393) + `agent/skills/...` to avoid fragile relative paths.

### Pattern 3: SKILL.md LESSONS.md-first logic
**What:** Insert a conditional at the top of the Reading Protocol (Section 3) in `SKILL.md`. If `LESSONS.md` exists in the skill directory, read it and stop — do not walk `assets/`. If it does not exist, proceed with the current algorithm.
**When to use:** This is a text edit to `SKILL.md` — the LLM that reads this skill follows it as instruction.
**Example (new Section 3 opening):**
```markdown
## 3. Reading Protocol

**Step 0 — Check for LESSONS.md first:**
If `LESSONS.md` exists in this skill's directory (next to `SKILL.md`):
- Read `LESSONS.md` only.
- Do NOT walk `assets/` or read any `_N.py` files.
- LESSONS.md is authoritative — treat it as the complete set of lessons.
- Proceed directly to applying the lessons.

If `LESSONS.md` does not exist, continue with Steps 1–5 below (raw asset walk).

[existing Step 1–5 content follows unchanged]
```

### Pattern 4: LESSONS.md skeleton
**What:** Create an empty skeleton at `agent/skills/skill-read-code/LESSONS.md` with the six category headers from `SKILL.md §4`. Populated on first explicit distillation run by the master agent.
**Example:**
```markdown
# Skill: Error-Resolution Lessons

> Auto-generated by master agent on explicit distillation request.
> Format mirrors SKILL.md §4 categories.

## Imports
<!-- Modules added, removed, or moved between bob and scratch -->

## Instantiation pattern
<!-- Constructor arguments that changed -->

## Connection wiring
<!-- >> chain restructured or explicit port names introduced -->

## Sensor API
<!-- Method used to attach a property or observation changed -->

## Serialization
<!-- Function used to write the output file changed -->

## Structural approach
<!-- Class hierarchy replaced with flat pattern (or vice versa) -->
```

### Anti-Patterns to Avoid

- **Do not modify `_223p/` source code** — only append new functions to `tool.py`. The folder constraint is firm.
- **Do not add `library` parameter to `search_class_mapping`** — the tool searches both files unconditionally (per the "grep across both" intent from CONTEXT.md). Filtering by library can always be done on the result client-side.
- **Do not use `os.path.relpath` with `_MAPPINGS_DIR`** for the JSONL path — use `_PROJECT_ROOT` already defined in `tool.py` at line 393 to construct an absolute path to the mappings directory.
- **Do not apply `scan_python_files_filtered` only to `223p/ref/code`** — the decision is to replace ALL `scan_python_files` calls in both prompts, not just the reference code scan.
- **Do not remove `list_library_classes` and `get_class_details` from `tool.py`** — only remove them from the agent `local_tools` lists and prompts. The functions remain in the module.
- **Do not add a fallback to LESSONS.md-first logic** — once LESSONS.md exists, the raw asset walk is never used again. The user explicitly chose "no fallback".

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSONL file reading | Custom streaming parser | `json.loads()` per line | JSONL is newline-delimited JSON; stdlib handles it trivially |
| Case-insensitive search | Regex or custom normalizer | `str.lower()` + `in` | Keyword matching requirements are simple substring; regex adds no value here |
| Module-level caching | External cache library | Dict at module scope (matches `_library_cache` pattern) | Already established pattern in `tool.py`; zero dependencies |

**Key insight:** All three new capabilities are O(N) scans over small datasets (851 total JSONL entries, one file directory walk). No sophisticated indexing or search infrastructure is needed.

---

## Common Pitfalls

### Pitfall 1: _MAPPINGS_DIR path construction
**What goes wrong:** Constructing the path to the mappings directory using relative paths from `_HERE` produces incorrect paths when the process CWD differs from the project root.
**Why it happens:** `tool.py` sets `_HERE = os.path.dirname(os.path.abspath(__file__))` (i.e., `agent/sub_agents/_223p/`) and `_PROJECT_ROOT` pointing three levels up. The mappings are at `agent/skills/...`, not under `_223p/`.
**How to avoid:** Use `_PROJECT_ROOT` (already defined at line 393 in `tool.py`) as the anchor:
```python
_MAPPINGS_DIR = os.path.join(_PROJECT_ROOT, "agent", "skills", "skill-read-code", "assets", "mappings")
```
**Warning signs:** Tests fail with `FileNotFoundError` on JSONL load when run from a directory other than the project root.

### Pitfall 2: `__all__` not updated
**What goes wrong:** New tool functions and schemas added to `tool.py` are not exported, causing `ImportError` when `agent.py` tries to import them.
**Why it happens:** `tool.py` has an explicit `__all__` list at lines 37–57. Forgetting to add new names there is a silent import issue.
**How to avoid:** Add `scan_python_files_filtered`, `SCAN_PYTHON_FILES_FILTERED_SCHEMA`, `search_class_mapping`, `SEARCH_CLASS_MAPPING_SCHEMA` to `__all__`.
**Warning signs:** `ImportError: cannot import name 'scan_python_files_filtered' from 'sub_agents._223p.tool'`.

### Pitfall 3: Tool deduplication by `__name__`
**What goes wrong:** The agent constructors deduplicate tools by `t.__name__`. If two tools share the same function name, only the first is kept.
**Why it happens:** Both agents use `{(t.__name__ if hasattr(t, "__name__") else str(t)): t for t in all_tools}`. New tool function names must be unique.
**How to avoid:** Name new functions exactly `scan_python_files_filtered` and `search_class_mapping` — no collisions with existing names.
**Warning signs:** Tool appears in the list passed to `local_tools` but the agent never calls it; the old tool with the same name is called instead.

### Pitfall 4: Removing tools from agent.py imports but not local_tools (or vice versa)
**What goes wrong:** `list_library_classes` and `get_class_details` are removed from `local_tools` but the import statement at the top of `agent.py` still lists them, causing an unused-import situation. Or, they are removed from the import but `local_tools` still references the name, causing `NameError`.
**Why it happens:** Two separate edit locations per file — the `from sub_agents._223p.tool import (...)` block and the `local_tools` list inside `__init__`.
**How to avoid:** In both `ontology_generator/agent.py` and `ontology_validator/agent.py`, update both the import block and `local_tools` atomically.
**Warning signs:** `NameError: name 'list_library_classes' is not defined` or flake8/mypy unused-import warnings.

### Pitfall 5: Prompt references to old tools not updated
**What goes wrong:** Prompt files still mention `list_library_classes` or `get_class_details` after the tool list change, causing the agent to attempt tool calls that no longer exist.
**Why it happens:** Three edit locations: `local_tools` in `agent.py`, prompt workflow steps, and the "Available skills and tools" section in the validator's prompt.
**How to avoid:** The validator's `prompt.md` has an explicit "Available skills and tools" section (lines 31–42) that lists tools by name. The generator's prompt references `list_library_classes` + `get_class_details` in the Libraries and Workflow sections. Both need to be updated when the tool list changes.
**Warning signs:** Agent responds with "I called list_library_classes" or produces a tool-not-found error in ADK logs.

### Pitfall 6: LESSONS.md-first check tied to absolute path in SKILL.md
**What goes wrong:** If the SKILL.md instruction tells the agent to look for LESSONS.md at a hardcoded path that doesn't resolve correctly, the agent fails to find it even when it exists.
**Why it happens:** Skills are loaded via `load_skill_from_dir` (see `tool.py:629`), which reads SKILL.md from a directory. The agent reading the skill doesn't have an OS concept of the skill directory.
**How to avoid:** The SKILL.md instruction should reference LESSONS.md by its location relative to SKILL.md (e.g., "in this skill's directory" or "at the same level as SKILL.md"). The agent uses `read_skill_content` or equivalent ADK skill tooling, which resolves relative to the skill dir. Do not hardcode an absolute path in the markdown instruction.
**Warning signs:** Agent always falls back to raw asset walking despite LESSONS.md existing.

---

## Code Examples

### Exact import block change in ontology_generator/agent.py
```python
# BEFORE (lines 42-48):
from sub_agents._223p.tool import (
    list_library_classes,
    get_class_details,
    scan_python_files,
    write_ontology,
    skills_toolset,
)

# AFTER:
from sub_agents._223p.tool import (
    scan_python_files_filtered,
    search_class_mapping,
    write_ontology,
    skills_toolset,
)
```

### Exact local_tools change in ontology_generator/agent.py
```python
# BEFORE (lines 120-128):
local_tools: list[Any] = [
    skills_toolset,
    list_library_classes,
    get_class_details,
    scan_python_files,
    write_ontology,
    exit_generator_success,
    exit_generator_failure,
]

# AFTER:
local_tools: list[Any] = [
    skills_toolset,
    scan_python_files_filtered,
    search_class_mapping,
    write_ontology,
    exit_generator_success,
    exit_generator_failure,
]
```

### Exact import block change in ontology_validator/agent.py
```python
# BEFORE (lines 49-58):
from sub_agents._223p.tool import (
    execute_ontology,
    get_class_details,
    list_library_classes,
    read_ontology,
    read_prompt,
    scan_python_files,
    write_ontology,
    skills_toolset,
)

# AFTER:
from sub_agents._223p.tool import (
    execute_ontology,
    read_ontology,
    read_prompt,
    scan_python_files_filtered,
    search_class_mapping,
    write_ontology,
    skills_toolset,
)
```

### Exact local_tools change in ontology_validator/agent.py
```python
# BEFORE (lines 137-149):
local_tools: list[Any] = [
    skills_toolset,
    execute_ontology,
    read_ontology,
    write_ontology,
    list_library_classes,
    get_class_details,
    scan_python_files,
    read_prompt,
    checkpoint_code,
    exit_validator_success,
    exit_validator_failure,
]

# AFTER:
local_tools: list[Any] = [
    skills_toolset,
    execute_ontology,
    read_ontology,
    write_ontology,
    scan_python_files_filtered,
    search_class_mapping,
    read_prompt,
    checkpoint_code,
    exit_validator_success,
    exit_validator_failure,
]
```

### Generator prompt workflow section (new steps 2-3, replaces old steps 2-3)
```markdown
## Workflow

1. **Grid** — Call `read_grid` to get all components and coordinates. Extract equipment class names from the result (e.g. "Fan", "Coil", "Damper").
2. **Class lookup** — Call `search_class_mapping(keywords=[<class names from step 1>])` to find which library file each class lives in. Note the `path` field for each match.
3. **Library source** — Call `scan_python_files_filtered` with the path returned by `search_class_mapping` to read the actual class source. No full catalog dump needed.
4. **Samples** — Call `scan_python_files_filtered` on `../223p/ref/code` with the same class name keywords to find relevant reference implementations.
5. **Plan** — Outline entities, connections, and spatial hierarchy.
6. **Generate** — Write the Python ontology code.
7. **Validate** — Confirm output is valid, executable Python using `bob`/`scratch`.
8. **Write** — Call `write_ontology` to save the file.
9. **Exit** — Call `exit_loop_generator_success(summary="...")` immediately after writing.
```

### Validator prompt "Available skills and tools" section (replaces lines 31-42)
```markdown
## Available skills and tools
- `skill-read-code` skill to acquire error-resolution lessons. Keep result in cache.
- `search_class_mapping` tool to find which file a class lives in. Pass class names from errors as keywords.
- `scan_python_files_filtered` tool to read the source of a specific class file (use `path` from `search_class_mapping` result). Also use for `../223p/ref/code` when looking for reference patterns.
- `read_prompt` tool for original generation guidelines. Keep result in cache.
- `read_ontology` tool to read the full source code of the current `ontology.py`.
- `execute_ontology` tool to run the current `ontology.py` and capture stdout, stderr, and return code.
- `write_ontology` tool to write the full corrected source code after each fix iteration.
- `checkpoint_code` tool to save a version snapshot after each fix iteration (mandatory after every write_ontology).
- `exit_validator_success` tool to signal successful validation and terminate the loop.
- `exit_validator_failure` tool to signal validation failure and terminate the loop.
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `list_library_classes` → full class catalog dump | `search_class_mapping` → targeted JSONL lookup | Phase 11 | Eliminates 751-entry catalog from context per call |
| `scan_python_files` unconditional | `scan_python_files_filtered` with keywords | Phase 11 | Returns only relevant files instead of entire directory tree |
| `skill-read-code` walks all dated folders | LESSONS.md-first, falls back to folder walk | Phase 11 | Eliminates multi-file asset walk once distillation done |

**Redundant files after Phase 11:**
- `full_bob.jsonl`: 751 lines — superseded by `classes_bob.jsonl` (752 entries with path field). Delete.
- `full_scratch.jsonl`: 98 lines — superseded by `classes_scratch.jsonl` (99 entries with path field). Delete.

---

## Open Questions

1. **`_MAPPINGS_DIR` path in tool.py**
   - What we know: `_PROJECT_ROOT` is defined at line 393 as three levels up from `_HERE` (i.e., the repo root above the `agent/` folder).
   - What's unclear: Whether `_PROJECT_ROOT` points to `si-mapper/` (repo root) or one level above. Confirmed from code: `_HERE` = `.../agent/sub_agents/_223p/`, three `..` levels = `si-mapper/`. So mappings path = `os.path.join(_PROJECT_ROOT, "agent", "skills", "skill-read-code", "assets", "mappings")`.
   - Recommendation: Use `_PROJECT_ROOT` anchor, construct absolute path. Verify with a smoke test.

2. **Keyword derivation instruction in generator prompt**
   - What we know: The agent gets equipment class names from `read_grid` output (equipment labels/types).
   - What's unclear: The exact `read_grid` response schema and how class names appear in it (field name, whether they're already Python class names or raw labels).
   - Recommendation: The prompt instruction can say "extract the equipment type names as they appear in the grid (e.g. 'Fan', 'Coil', 'Damper') and pass them as keywords". The agent has enough context from its role to adapt.

3. **LESSONS.md content at creation time**
   - What we know: The user wants an "empty skeleton with category headers" bootstrapped now.
   - What's unclear: Whether the skeleton should have any pre-populated content from the existing assets, or truly be empty headers only.
   - Recommendation: Per CONTEXT.md §Specifics, "initially empty skeleton with the category headers — gets populated on first explicit distillation run." Create with headers only, no content.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=9.0.2 |
| Config file | `agent/pyproject.toml` (implicit — no `pytest.ini` found) |
| Quick run command | `cd /home/juan/codes/si-mapper/agent && uv run pytest tests/ -x -q` |
| Full suite command | `cd /home/juan/codes/si-mapper/agent && uv run pytest tests/ -q` |

### Phase Requirements → Test Map

No formal requirement IDs are mapped to this phase. The testable behaviors are:

| Behavior | Test Type | Automated Command | File Exists? |
|----------|-----------|-------------------|-------------|
| `scan_python_files_filtered` returns only files matching keywords | unit | `uv run pytest tests/test_223p_tools.py -x -q` | Wave 0 |
| `scan_python_files_filtered` is case-insensitive | unit | same | Wave 0 |
| `scan_python_files_filtered` returns empty files dict when no keyword matches | unit | same | Wave 0 |
| `search_class_mapping` finds entries in bob and scratch by keyword | unit | same | Wave 0 |
| `search_class_mapping` adds `library` field to results | unit | same | Wave 0 |
| `search_class_mapping` returns empty list for no matches | unit | same | Wave 0 |
| Generator agent `local_tools` contains `scan_python_files_filtered` and `search_class_mapping` | unit | `uv run pytest tests/test_ontology_generator_agent.py -x -q` | Extend existing |
| Generator agent `local_tools` does not contain `list_library_classes` or `get_class_details` | unit | same | Extend existing |
| Validator agent `local_tools` contains both new tools | unit | `uv run pytest tests/test_ontology_validator_agent.py -x -q` | Extend existing |
| Validator agent `local_tools` does not contain old tools | unit | same | Extend existing |

### Sampling Rate
- **Per task commit:** `cd /home/juan/codes/si-mapper/agent && uv run pytest tests/ -x -q`
- **Per wave merge:** `cd /home/juan/codes/si-mapper/agent && uv run pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `agent/tests/test_223p_tools.py` — unit tests for `scan_python_files_filtered` and `search_class_mapping` (mock filesystem and JSONL files)
- [ ] Extend `agent/tests/test_ontology_generator_agent.py` — add assertions that new tools are present and old tools are absent
- [ ] Extend `agent/tests/test_ontology_validator_agent.py` — same

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `agent/sub_agents/_223p/tool.py` — full source of all existing tool functions, schemas, caching pattern, `_PROJECT_ROOT` anchor
- Direct code inspection: `agent/sub_agents/ontology_generator/agent.py` — exact `local_tools` list (lines 120-128), import block (lines 42-48)
- Direct code inspection: `agent/sub_agents/ontology_validator/agent.py` — exact `local_tools` list (lines 137-149), import block (lines 49-58)
- Direct code inspection: `agent/sub_agents/ontology_generator/prompt.md` — current workflow steps and tool references
- Direct code inspection: `agent/sub_agents/ontology_validator/prompt.md` — current "Available skills and tools" section
- Direct code inspection: `agent/skills/skill-read-code/SKILL.md` — existing Reading Protocol (Section 3) and diff categories (Section 4)
- Direct inspection: JSONL mapping files — confirmed structure `{class_name, path, types}` per line; counts 752/99/751/98

### Secondary (MEDIUM confidence)
- `agent/tests/test_ontology_generator_exit_tools.py` — `_make_tool_context` MockToolContext pattern; confirms test approach for new tool functions
- `agent/pyproject.toml` — confirmed pytest >=9.0.2 and no new dependencies needed

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all tools use stdlib; no new dependencies needed (confirmed from pyproject.toml)
- Architecture: HIGH — all patterns derived directly from existing code in `tool.py`; no external research required
- Pitfalls: HIGH — each pitfall derived from concrete code structure observed (explicit `__all__`, deduplication logic, dual edit locations in agent.py)
- Test patterns: HIGH — confirmed from existing test files using identical mock patterns

**Research date:** 2026-03-22
**Valid until:** 2026-04-22 (stable codebase, no external dependencies to drift)
