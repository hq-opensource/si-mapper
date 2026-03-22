---
phase: 11-optimization-of-the-coding-agent
plan: "03"
subsystem: agent
tags: [ontology-generator, ontology-validator, tool-swap, prompt, testing]

# Dependency graph
requires:
  - phase: 11-01
    provides: scan_python_files_filtered tool in _223p/tool.py
  - phase: 11-02
    provides: search_class_mapping tool in _223p/tool.py
provides:
  - Both ontology agents wired to scan_python_files_filtered and search_class_mapping
  - Both prompt.md files updated to use targeted tool workflow
  - Agent tests verify new tools present and old tools absent
  - full_bob.jsonl and full_scratch.jsonl deleted
affects: [ontology-generator, ontology-validator, 223p-agent]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Tool swap: replace list_library_classes+get_class_details two-call pattern with single search_class_mapping+scan_python_files_filtered call"
    - "Agent tests use agent.sub_agents[0].tools to verify tool list composition"

key-files:
  created: []
  modified:
    - agent/sub_agents/ontology_generator/agent.py
    - agent/sub_agents/ontology_validator/agent.py
    - agent/sub_agents/ontology_generator/prompt.md
    - agent/sub_agents/ontology_validator/prompt.md
    - agent/tests/test_ontology_generator_agent.py
    - agent/tests/test_ontology_validator_agent.py
  deleted:
    - agent/skills/skill-read-code/assets/mappings/full_bob.jsonl
    - agent/skills/skill-read-code/assets/mappings/full_scratch.jsonl

key-decisions:
  - "Tool swap complete: both agents now import/use scan_python_files_filtered and search_class_mapping exclusively — old list_library_classes, get_class_details, scan_python_files removed from both agents"
  - "full_bob.jsonl and full_scratch.jsonl deleted — superseded by classes_*.jsonl + path field returned by search_class_mapping"
  - "Generator workflow updated to 9-step sequence: Grid -> Class lookup (search_class_mapping) -> Library source (scan_python_files_filtered) -> Samples -> Plan -> Generate -> Validate -> Write -> Exit"

patterns-established:
  - "Tool list tests: access internal agent via agent.sub_agents[0].tools, extract names via t.__name__ if hasattr(t, '__name__') else str(t)"

requirements-completed:
  - P11-01
  - P11-02
  - P11-04

# Metrics
duration: 3min
completed: 2026-03-22
---

# Phase 11 Plan 03: Wire New Tools into Both Ontology Agents Summary

**Tool swap in both ontology agents: list_library_classes+get_class_details replaced by search_class_mapping+scan_python_files_filtered, prompts rewritten with targeted 9-step workflow, full_*.jsonl deleted**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-22T18:26:30Z
- **Completed:** 2026-03-22T18:29:40Z
- **Tasks:** 2
- **Files modified:** 6 modified, 2 deleted

## Accomplishments
- Swapped tool imports and local_tools in both ontology_generator/agent.py and ontology_validator/agent.py — removed list_library_classes, get_class_details, scan_python_files; added scan_python_files_filtered and search_class_mapping
- Rewrote generator prompt.md with a new 9-step workflow using search_class_mapping for class lookup then scan_python_files_filtered for source reading; updated validator prompt.md Available skills section
- Extended agent tests with 4 new test functions (has_new_tools + no_old_tools for each agent); 12 tests pass
- Deleted full_bob.jsonl and full_scratch.jsonl (867 lines removed); mappings directory now contains only classes_bob.jsonl and classes_scratch.jsonl

## Task Commits

Each task was committed atomically:

1. **Task 1: Swap tool imports and local_tools in both agent.py files** - `c847420` (feat)
2. **Task 2: Rewrite both prompt.md files + extend agent tests + delete redundant JSONL** - `bdea288` (feat)

## Files Created/Modified
- `agent/sub_agents/ontology_generator/agent.py` - Import block and local_tools list updated to new tools
- `agent/sub_agents/ontology_validator/agent.py` - Import block and local_tools list updated to new tools
- `agent/sub_agents/ontology_generator/prompt.md` - Libraries, Code Samples, and Workflow sections rewritten for new tool workflow
- `agent/sub_agents/ontology_validator/prompt.md` - Available skills section and Stop Conditions updated
- `agent/tests/test_ontology_generator_agent.py` - Added test_generator_has_new_tools and test_generator_no_old_tools
- `agent/tests/test_ontology_validator_agent.py` - Added test_validator_has_new_tools and test_validator_no_old_tools
- `agent/skills/skill-read-code/assets/mappings/full_bob.jsonl` - DELETED (superseded)
- `agent/skills/skill-read-code/assets/mappings/full_scratch.jsonl` - DELETED (superseded)

## Decisions Made
- Tool swap complete in both agents — list_library_classes, get_class_details, and unfiltered scan_python_files removed from all import blocks and local_tools lists
- full_bob.jsonl and full_scratch.jsonl deleted; classes_*.jsonl + the path field returned by search_class_mapping is the canonical lookup path
- Generator workflow now explicitly guides class lookup first via search_class_mapping then source reading via scan_python_files_filtered using the returned path

## Deviations from Plan

None - plan executed exactly as written.

Note: `test_capture_frontend_state.py::test_url_construction` was pre-existing broken (confirmed by git stash check); logged to deferred-items.md in phase directory. The plan's full suite pass criterion is met for all tests except this pre-existing failure.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Both ontology agents are fully wired to the cheaper targeted tools
- Agent tests provide regression coverage for tool list composition
- Phase 11 plans 11-01, 11-02, 11-04 (prerequisites) and 11-03 all complete

---
*Phase: 11-optimization-of-the-coding-agent*
*Completed: 2026-03-22*
