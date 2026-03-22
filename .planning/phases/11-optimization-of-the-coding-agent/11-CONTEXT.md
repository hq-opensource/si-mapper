# Phase 11: Optimization of the Coding Agent - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Reduce context window consumption in the Ontology Generator and Validator agents by replacing three expensive, unconditional operations with cheaper, targeted alternatives. Scope:

1. Replace `skill-read-code` raw file walking with a compact `LESSONS.md` (human-triggered distillation)
2. Replace unconditional `scan_python_files` with a grid-aware filtered version
3. Replace `list_library_classes` + `get_class_details` with a grep-like JSONL lookup tool

All changes apply to **both** `ontology_generator` and `ontology_validator`. New tools go into the shared `_223p/tool.py`. `_223p/` source code is NOT modified — only new functions are added. Prompts in `ontology_generator/prompt.md` and `ontology_validator/prompt.md` are updated to use the new flow.

**Out of scope:**
- Changes to the master agent or any other sub-agent
- Changes to exit tools or state management
- Any new agent capabilities

</domain>

<decisions>
## Implementation Decisions

### Lessons distillation (skill-read-code)
- `LESSONS.md` lives at `agent/skills/skill-read-code/LESSONS.md` — next to `SKILL.md` and the `assets/` archive.
- Raw iteration files in `assets/` are **kept as permanent archive** — never deleted or moved.
- **Trigger:** explicit human instruction to the master agent (e.g. "update lessons"). Master uses the LLM to walk the raw asset files, identify deltas, and rewrite `LESSONS.md` with structured error-to-fix categories. Same HITL pattern as ontology generation.
- **Distillation is LLM-powered:** the master agent reads raw files using `skill-read-code`, synthesizes lessons, and writes `LESSONS.md`.
- **SKILL.md update:** if `LESSONS.md` exists → read it only, stop there. If it doesn't exist → walk `assets/` as today. **No fallback once LESSONS.md is created** — the user chose "LESSONS.md only, no fallback".
- Applies to both generator and validator (both call the same skill).

### Reference code filtering (scan_python_files)
- Add `scan_python_files_filtered(path, keywords: list[str])` to `agent/sub_agents/_223p/tool.py`.
- Returns only `.py` files whose **content** contains at least one keyword (case-insensitive substring match).
- **Applied to ALL `scan_python_files` calls** in both agent prompts — not just the `223p/ref/code` path.
- Workflow in prompt: agent extracts equipment class names from `read_grid` output → passes them as `keywords` to `scan_python_files_filtered`. Only files mentioning those classes are returned.
- Both `ontology_generator/prompt.md` and `ontology_validator/prompt.md` updated to use `scan_python_files_filtered`.

### Scope: both agents
- Every optimization (lessons, filtering, class mapping) applies to **both** `ontology_generator` and `ontology_validator`.
- New tools added to shared `_223p/tool.py` so both agents import from the same location.
- Prompt changes made independently to each agent's `prompt.md` (they are separate files but get the same structural updates).

### Static class mapping (replaces list_library_classes + get_class_details)
- **Mapping files** at `agent/skills/skill-read-code/assets/mappings/`:
  - Keep: `classes_bob.jsonl` (752 entries: `class_name`, `path`, `types`)
  - Keep: `classes_scratch.jsonl` (99 entries: same structure)
  - **Remove:** `full_bob.jsonl` and `full_scratch.jsonl` — redundant since the agent reads the Python source directly via `path`.
- **New tool:** `search_class_mapping(keywords: list[str])` — grep-like search across both `classes_*.jsonl` files. Returns all matching lines as a list of dicts `{class_name, path, types, library}`. Match is case-insensitive substring on `class_name`.
- **Replaces `list_library_classes` entirely.** Replaces most `get_class_details` calls: agent uses `path` from mapping results to read the actual Python source file directly (via `scan_python_files_filtered`), getting full class details without a catalog dump.
- `list_library_classes` and `get_class_details` remain in `tool.py` but are removed from the agent tool lists and prompts.
- Tool added to `_223p/tool.py`, imported into both `ontology_generator/agent.py` and `ontology_validator/agent.py`.

### Claude's Discretion
- Whether `search_class_mapping` searches both JSONL files in a single call or takes a `library` parameter — implementation detail.
- Exact keyword matching strategy (class name only vs. also matching on `types` field).
- How the prompt instructs the agent to derive keywords from `read_grid` output (inferred from equipment labels/types).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Shared tool file (where new tools are added)
- `agent/sub_agents/_223p/tool.py` — existing tool functions; new tools `scan_python_files_filtered` and `search_class_mapping` go here

### Agent files to update
- `agent/sub_agents/ontology_generator/agent.py` — tool list: add new tools, remove `list_library_classes` and `get_class_details`
- `agent/sub_agents/ontology_validator/agent.py` — same tool list changes
- `agent/sub_agents/ontology_generator/prompt.md` — workflow steps updated to use new tools
- `agent/sub_agents/ontology_validator/prompt.md` — same workflow updates

### Skill to update
- `agent/skills/skill-read-code/SKILL.md` — add LESSONS.md-first reading logic
- `agent/skills/skill-read-code/LESSONS.md` — new file to create (initially empty or bootstrapped from existing assets)

### Mapping files
- `agent/skills/skill-read-code/assets/mappings/classes_bob.jsonl` — JSONL: `{class_name, path, types}` per class in bob
- `agent/skills/skill-read-code/assets/mappings/classes_scratch.jsonl` — same for scratch
- `agent/skills/skill-read-code/assets/mappings/full_bob.jsonl` — TO DELETE
- `agent/skills/skill-read-code/assets/mappings/full_scratch.jsonl` — TO DELETE

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scan_python_files` in `_223p/tool.py:315` — basis for the new `scan_python_files_filtered`; same directory walk, add content keyword filter before including each file.
- `_library_cache` in `_223p/tool.py:144` — existing module-level cache; `search_class_mapping` can use a similar cache keyed on the JSONL file path.
- `skills_toolset` and `skill_toolset.SkillToolset` in `_223p/tool.py:629` — existing pattern for wiring `skill-read-code` into both agents.

### Established Patterns
- All shared tools live in `_223p/tool.py` and are imported identically by both `ontology_generator/agent.py` and `ontology_validator/agent.py`.
- Tool deduplication by name already handled in both `OntologyGeneratorInternal` and `OntologyValidatorInternal` constructors.
- Both prompts follow the same structure: Libraries → Data Source → Workflow steps. New tools slot into the Workflow section.

### Integration Points
- `ontology_generator/agent.py:120–131` — `local_tools` list; add `scan_python_files_filtered`, `search_class_mapping`; remove `list_library_classes`, `get_class_details`.
- `ontology_validator/agent.py` — same local_tools change.
- `skill-read-code/SKILL.md` — the "Reading Protocol" section (Step 1–5) is where the LESSONS.md-first logic is inserted.

</code_context>

<specifics>
## Specific Ideas

- `search_class_mapping` should feel like `grep -i <keyword> classes_bob.jsonl classes_scratch.jsonl` — return the matching lines, include which library (`bob`/`scratch`) each match came from.
- The `path` field in the JSONL (e.g. `"bob/equipment/hvac/fan.py"`) gives the agent a direct path to read the Python source — no discovery step needed.
- LESSONS.md format should mirror the diff categories in `SKILL.md §4` (Imports, Instantiation pattern, Connection wiring, Sensor API, Serialization, Structural approach) so it's structured, not a wall of text.
- When LESSONS.md is first created (bootstrapped), it can be an empty skeleton with the category headers — gets populated on first explicit distillation run.

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope.

</deferred>

---

*Phase: 11-optimization-of-the-coding-agent*
*Context gathered: 2026-03-22*
