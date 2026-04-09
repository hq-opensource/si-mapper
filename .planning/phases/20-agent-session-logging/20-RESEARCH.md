# Phase 20: Agent Session Logging - Research

**Researched:** 2026-04-03
**Domain:** Python file I/O, JSONL persistence, ADK callback hooks
**Confidence:** HIGH

## Summary

Phase 20 adds disk persistence for every `AgentEvent` that passes through `shared_model_callback()`. The entire event pipeline already exists and produces fully-structured `AgentEvent` Pydantic objects — the only missing piece is a file-write step that appends each event to a per-session JSONL file immediately after it is added to `state["events"]`.

The insertion point is unambiguous: lines 404-408 of `agent/utils/callback_utils.py`, after the `for ne in new_events` loop appends events to `events_history`. Events are created by `EventProcessor.process_parts()` and returned as `List[AgentEvent]`. `AgentEvent` is a Pydantic `BaseModel`, so it exposes `.model_dump()` which returns a JSON-serializable dict. The session ID is extracted at line 311-313 of `callback_utils.py` via `callback_context.session.id`, and is available every time the callback fires.

The recommended implementation creates a single new module `agent/utils/session_logger.py` that owns the log directory, file path computation, and the write operation. The write is synchronous append (`"a"` mode on a JSONL file), which is the correct choice for this use case: callbacks are not on a hot async I/O path, each write is a single line, and synchronous append is atomic enough on Linux for a single-process server. No buffering, no background thread, no log rotation is required in this phase.

**Primary recommendation:** Create `agent/utils/session_logger.py` with `log_events(session_id, events)` that appends JSONL lines to `agent/logs/sessions/{session_id}_{date}.jsonl`, then call it from `shared_model_callback()` after the `state["events"]` update block.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| P20-01 | Per-session JSONL log file created on first event | `session_logger.py` creates dir + file lazily on first write |
| P20-02 | Every AgentEvent written as one JSON line | `.model_dump()` + `json.dumps()` + `\n` appended in "a" mode |
| P20-03 | Log file named `{session_id}_{date}.jsonl` under `agent/logs/sessions/` | Path computed from session_id + `datetime.now().strftime("%Y%m%d")` |
| P20-04 | Full AgentEvent payload (timestamp, agent_name, event_type, content, metadata) persisted | `AgentEvent.model_dump()` serializes all Pydantic fields including nested metadata dict |
| P20-05 | Log survives agent restarts without data loss | Append mode ("a") never truncates; new session = new file; old files preserved |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pathlib.Path` | stdlib | Directory creation and path construction | Already used in `ontology_tools.py` — project standard |
| `json` | stdlib | Serialize `model_dump()` dict to string | Already used throughout codebase |
| `logging` | stdlib | Error logging on write failure | Already used in every module |
| `datetime` | stdlib | Date suffix for log filename | Already used in `ontology_tools.py` |

### No New Dependencies
This phase requires zero new pip packages. All required functionality is in the Python 3.13 stdlib.

**Installation:**
```bash
# No new packages needed
```

## Architecture Patterns

### Recommended Project Structure
```
agent/
├── utils/
│   ├── session_logger.py   # NEW: owns JSONL log writes
│   ├── callback_utils.py   # MODIFIED: call session_logger after events update
│   └── ...
├── logs/
│   └── sessions/           # NEW: created by session_logger at runtime
│       └── {session_id}_{date}.jsonl
└── tests/
    └── test_session_logger.py  # NEW: unit tests
```

### Pattern 1: Lazy Directory Creation with Append Mode
**What:** On first write for a session, `os.makedirs(dir, exist_ok=True)` then open in `"a"` mode for every subsequent write. File handle is NOT cached — open/close per write batch.
**When to use:** Low-frequency writes (one batch per LLM callback), correctness over performance.
**Example:**
```python
# Source: mirrors agent/tools/ontology_tools.py write pattern (lines 531-534)
import json
import os
from datetime import datetime
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
_AGENT_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
_LOGS_DIR = os.path.join(_AGENT_ROOT, "logs", "sessions")


def log_events(session_id: str, events: list[dict]) -> None:
    """Append serialized AgentEvent dicts to the session JSONL log."""
    if not events:
        return
    date_str = datetime.now().strftime("%Y%m%d")
    log_path = os.path.join(_LOGS_DIR, f"{session_id}_{date_str}.jsonl")
    os.makedirs(_LOGS_DIR, exist_ok=True)
    try:
        with open(log_path, "a", encoding="utf-8") as fh:
            for event in events:
                fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError as exc:
        import logging
        logging.getLogger(__name__).warning("session_logger: write failed: %s", exc)
```

### Pattern 2: Insertion Point in callback_utils.py
**What:** Call `log_events()` immediately after `state["events"]` is updated, passing only the NEW events from this callback invocation.
**When to use:** Always — we want to persist each callback's new events before the function returns.
**Example:**
```python
# Source: agent/utils/callback_utils.py lines 402-408 (existing code context)
# After this existing block:
events_history = state.get("events", [])
for ne in new_events:
    events_history.append(ne.model_dump())
state["events"] = events_history[-200:]

# ADD HERE:
from .session_logger import log_events
log_events(session_id, [ne.model_dump() for ne in new_events])
```

The import should be at the top of `callback_utils.py`, not inline.

### Pattern 3: AgentEvent Serialization
**What:** `AgentEvent` is a Pydantic `BaseModel` (confirmed in `agent/utils/events.py`). Use `.model_dump()` to get a plain dict, then `json.dumps()`.
**Example:**
```python
# Source: agent/utils/callback_utils.py line 89 and 406 — already done in codebase
event_dict = agent_event.model_dump()  # returns dict with id, timestamp, agent_name, etc.
line = json.dumps(event_dict, ensure_ascii=False)
```

`.model_dump()` is the Pydantic v2 API (confirmed: `pydantic>=2.12.5` in pyproject.toml). Do NOT use `.dict()` (deprecated in Pydantic v2).

### Anti-Patterns to Avoid
- **Caching a persistent file handle:** Do not store an open file handle in a module-level dict keyed by session_id. If the process is killed mid-write, unflushed data is lost. Open/close per batch is safer.
- **Writing inside the GLOBAL_SESSION_STORE merge block:** The merge block (lines 445-484) already has try/except. Do not nest file I/O inside it — keep concerns separate.
- **Writing ALL events_history instead of only new_events:** The `events_history` list is truncated to 200 items and contains duplicates from prior callbacks. Only `new_events` (the current callback's fresh events) should be appended to the log.
- **Using async file I/O (aiofiles):** The callback `shared_model_callback` is async but file I/O is fast enough to be synchronous. Adding aiofiles introduces a dependency and complexity for no benefit.
- **Writing in `shared_before_model_callback`:** That callback fires before the LLM response is known. Only `shared_model_callback` has events to log.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSONL serialization | Custom recursive serializer | `json.dumps(event.model_dump())` | Pydantic model_dump() handles all field types including nested dicts and Enum (EventType is `str` Enum, serializes as string automatically) |
| Log rotation | Time-based rotation thread | Date suffix in filename (`{session_id}_{date}.jsonl`) | A new file per calendar day is sufficient; no rotation library needed |
| Thread safety | Locks, queues | Open/close per write on Linux | Linux `write()` syscalls to append mode are atomic for writes under 4096 bytes; a single JSON line easily fits |

**Key insight:** The codebase already does synchronous file I/O in tools (e.g., `ontology_tools.py` writes `latest_ontology.py` and session archives synchronously). The callback is on a background thread managed by the ADK runtime — the same pattern is safe here.

## Common Pitfalls

### Pitfall 1: EventType Enum Serialization
**What goes wrong:** `json.dumps(event.model_dump())` raises `TypeError: Object of type EventType is not JSON serializable` if Pydantic does not serialize the Enum.
**Why it happens:** Pydantic v2 `model_dump()` returns Enum values as their Python Enum object by default, not as strings, when `mode="python"` (the default).
**How to avoid:** Use `model_dump(mode="json")` which forces all values to JSON-compatible types (strings for `str` Enum). Alternatively, since `EventType(str, Enum)` inherits from `str`, `json.dumps` will serialize it as a string without special handling — but `mode="json"` is explicit and safe.
**Warning signs:** `TypeError` on the first write; easy to miss in tests if you only check file existence.

Confirmed: `EventType` is defined as `class EventType(str, Enum)` — it WILL serialize as a string with standard `json.dumps`. This is low risk but worth noting.

### Pitfall 2: session_id Not Available on All Code Paths
**What goes wrong:** The try/except at callback_utils.py line 309-312 falls back to `"default-session"` if `callback_context.session.id` raises. If this happens, all events from different real sessions accumulate in `default-session_{date}.jsonl`.
**Why it happens:** ADK session ID access can fail during agent initialization or in edge cases.
**How to avoid:** The existing fallback `"default-session"` is acceptable. Log a warning when the fallback is used so it is visible in console output.
**Warning signs:** A single large JSONL file named `default-session_{date}.jsonl` instead of per-session files.

### Pitfall 3: Duplicate Events Written
**What goes wrong:** The same event is written to the JSONL file multiple times because `callback_utils.py` deduplicates in the GLOBAL_SESSION_STORE but the log write does not deduplicate.
**Why it happens:** `new_events` from `EventProcessor.process_parts()` are always fresh (each has a new UUID via `default_factory=lambda: str(uuid.uuid4())`). If `shared_model_callback` is called multiple times for the same LLM turn (streaming), each call produces distinct events — there is NO actual duplication risk from the current code.
**How to avoid:** Write only `new_events` (the list returned by `EventProcessor.process_parts()`), not the accumulated `events_history`.
**Warning signs:** Repeated identical content in JSONL but different UUIDs — this is expected streaming behavior, not a bug.

### Pitfall 4: OSError Crashing the Callback
**What goes wrong:** A disk-full or permission error in the log write propagates up and crashes the entire callback, causing the ADK agent to fail.
**Why it happens:** Unhandled exceptions in ADK callbacks break the agent loop.
**How to avoid:** Wrap the file write in try/except OSError and log a warning — never re-raise. Logging to disk is best-effort.
**Warning signs:** Agent stops responding after disk fills up.

### Pitfall 5: Log Directory Not in .gitignore
**What goes wrong:** `agent/logs/sessions/` with potentially large JSONL files gets committed to git.
**Why it happens:** New directory not excluded.
**How to avoid:** Add `agent/logs/` to `.gitignore` before the first run.

## Code Examples

Verified patterns from codebase:

### AgentEvent model_dump (already used in codebase)
```python
# Source: agent/utils/callback_utils.py line 89 and 406
event.model_dump()
# Returns: {"id": "uuid", "timestamp": 1711234567890, "agent_name": "...",
#           "event_type": "BRAINSTORM", "content": "...", "metadata": {...}, "trace_id": null}
```

### Existing file write pattern (project standard)
```python
# Source: agent/tools/ontology_tools.py lines 531-534
os.makedirs(os.path.dirname(ONTOLOGY_FILE), exist_ok=True)
try:
    with open(ONTOLOGY_FILE, "w", encoding="utf-8") as fh:
        fh.write(content)
except OSError as exc:
    logger.warning("Failed to write %s: %s", ONTOLOGY_FILE, exc)
```

### Session ID extraction (already in callback_utils.py)
```python
# Source: agent/utils/callback_utils.py lines 309-312
try:
    session_id = callback_context.session.id
except:
    session_id = "default-session"
```

### session_id in main.py (app startup)
```python
# Source: agent/main.py line 36
session_id = f"session-{uuid.uuid4().hex[:8]}"
# Example: "session-a1b2c3d4"
```

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|-----------------|--------|
| Console-only logging (`logging_config.py`) | Append JSONL on every callback | Enables offline analysis of thinking traces |
| Events truncated to 200 in memory | Events persisted to disk without truncation | Full history preserved across long sessions |

**Not applicable:**
- Log rotation: date suffix per file is sufficient for this project's scale.
- Structured logging frameworks (structlog, loguru): stdlib `json` + append mode is simpler and already fits the codebase pattern.

## Open Questions

1. **Should `agent/logs/` be gitignored project-wide or locally?**
   - What we know: No `.gitignore` entry for `agent/logs/` currently exists.
   - What's unclear: Whether log files should ever be committed (e.g., for debugging sessions).
   - Recommendation: Add `agent/logs/` to the root `.gitignore`. If specific logs need to be shared, they can be copied manually.

2. **Should artifact-path events (ARTIFACT type from `_log_artifact_visibility`) also be persisted?**
   - What we know: Those events are also appended to `state["events"]` and flow through `events_history` — they will be picked up by the same write path automatically.
   - What's unclear: Whether the binary blob sizes in metadata could make lines very large.
   - Recommendation: They will be written automatically since they go through `state["events"]`. The metadata for artifact events contains only string summaries (mime type, size in KB, artifact names) — no binary data. No special handling needed.

3. **Do we need a `session_id` field inside each JSONL line?**
   - What we know: `AgentEvent` does not have a `session_id` field. The session ID is encoded in the filename.
   - What's unclear: Whether offline analysis tools will need per-line session_id for log merging.
   - Recommendation: The planner should decide. Option A: filename is sufficient (simpler). Option B: inject `session_id` into `model_dump()` result before writing (adds one key per line). Both are valid — document as a plan decision.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| Config file | `agent/pyproject.toml` (`[tool.pytest.ini_options]`, `asyncio_mode = "auto"`) |
| Quick run command | `cd agent && python -m pytest tests/test_session_logger.py -x` |
| Full suite command | `cd agent && python -m pytest tests/ -x` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| P20-01 | Directory and file created on first write | unit | `pytest tests/test_session_logger.py::test_creates_log_dir_on_first_write -x` | Wave 0 |
| P20-02 | Each event written as one JSON line, parseable | unit | `pytest tests/test_session_logger.py::test_each_event_is_one_json_line -x` | Wave 0 |
| P20-03 | Log filename matches `{session_id}_{date}.jsonl` pattern | unit | `pytest tests/test_session_logger.py::test_log_filename_format -x` | Wave 0 |
| P20-04 | All AgentEvent fields present in written JSON | unit | `pytest tests/test_session_logger.py::test_agent_event_fields_complete -x` | Wave 0 |
| P20-05 | Second write appends; file not truncated | unit | `pytest tests/test_session_logger.py::test_append_does_not_truncate -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd agent && python -m pytest tests/test_session_logger.py -x`
- **Per wave merge:** `cd agent && python -m pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `agent/tests/test_session_logger.py` — covers P20-01 through P20-05 (all 5 unit tests)
- [ ] `agent/utils/session_logger.py` — the module being tested (must exist before tests can import)

## Sources

### Primary (HIGH confidence)
- `agent/utils/callback_utils.py` — exact insertion point at lines 402-408; session_id at lines 309-312; GLOBAL_SESSION_STORE merge block lines 445-484
- `agent/utils/events.py` — `AgentEvent(BaseModel)` with `.model_dump()` (Pydantic v2); `EventType(str, Enum)` serializes as string
- `agent/utils/event_processor.py` — events always have id, timestamp, agent_name, event_type, content, metadata; trace_id sometimes null
- `agent/main.py` — session lifecycle: single session per process startup, `session_id = f"session-{uuid.uuid4().hex[:8]}"`, registered in GLOBAL_SESSION_STORE at lines 40-47
- `agent/pyproject.toml` — Python 3.13, pydantic>=2.12.5 (v2 API confirmed)
- `agent/tools/ontology_tools.py` — established file I/O patterns for the project (os.makedirs, open/close, OSError handling, pathlib.Path)

### Secondary (MEDIUM confidence)
- `agent/tests/test_ontology_tools.py` — test structure patterns (sys.path, stub pattern, TDD approach)
- `agent/utils/logging_config.py` — confirms console-only output currently, no existing file handler

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — stdlib only, no new dependencies
- Architecture: HIGH — insertion point precisely identified in source code
- Pitfalls: HIGH — derived from direct code inspection of the existing callback and Pydantic version

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (stable codebase, no fast-moving dependencies)
