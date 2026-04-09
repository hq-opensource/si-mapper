---
phase: 23
slug: add-cypher-query-tool-for-neo4j-agent-exploration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-04
---

# Phase 23 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| **Config file** | `agent/pyproject.toml` (existing) |
| **Quick run command** | `python -m pytest agent/tests/test_neo4j_query_tools.py -v` |
| **Full suite command** | `python -m pytest agent/tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest agent/tests/test_neo4j_query_tools.py -v`
- **After every plan wave:** Run `python -m pytest agent/tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 23-01-01 | 01 | 0 | Wave0 | unit | `python -m pytest agent/tests/test_neo4j_query_tools.py -v` | ❌ W0 | ⬜ pending |
| 23-01-02 | 01 | 1 | execute_cypher success | unit | `pytest agent/tests/test_neo4j_query_tools.py::TestExecuteCypherTool::test_successful_query -x` | ❌ W0 | ⬜ pending |
| 23-01-03 | 01 | 1 | execute_cypher error handling | unit | `pytest agent/tests/test_neo4j_query_tools.py::TestExecuteCypherTool::test_cypher_error -x` | ❌ W0 | ⬜ pending |
| 23-01-04 | 01 | 1 | execute_cypher row cap | unit | `pytest agent/tests/test_neo4j_query_tools.py::TestExecuteCypherTool::test_row_cap -x` | ❌ W0 | ⬜ pending |
| 23-01-05 | 01 | 1 | execute_cypher_batch ordered results | unit | `pytest agent/tests/test_neo4j_query_tools.py::TestExecuteCypherBatchTool::test_batch_ordered -x` | ❌ W0 | ⬜ pending |
| 23-01-06 | 01 | 1 | execute_cypher_batch partial failure | unit | `pytest agent/tests/test_neo4j_query_tools.py::TestExecuteCypherBatchTool::test_batch_partial_failure -x` | ❌ W0 | ⬜ pending |
| 23-01-07 | 01 | 1 | get_graph_schema labels/rels/props | unit | `pytest agent/tests/test_neo4j_query_tools.py::TestGetGraphSchemaTool::test_schema_success -x` | ❌ W0 | ⬜ pending |
| 23-01-08 | 01 | 1 | search_graph_entities case-insensitive | unit | `pytest agent/tests/test_neo4j_query_tools.py::TestSearchGraphEntitiesTool::test_keyword_match -x` | ❌ W0 | ⬜ pending |
| 23-01-09 | 01 | 1 | FunctionDeclaration names correct | unit | `pytest agent/tests/test_neo4j_query_tools.py -k "declaration" -x` | ❌ W0 | ⬜ pending |
| 23-01-10 | 01 | 2 | master agent registers all 4 tools | unit | `python -m pytest agent/tests/test_create_master_agent.py -x` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `agent/tests/test_neo4j_query_tools.py` — test stubs for all 4 tools (does not exist yet)

*Existing infrastructure covers all other requirements. This is the only new test file needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Agent can fire 4+ parallel Cypher queries and receive structured results | Parallel exploration | Requires live Neo4j container + loaded ontology | Load TTL, ask agent to run 4 queries simultaneously, verify all return results |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
