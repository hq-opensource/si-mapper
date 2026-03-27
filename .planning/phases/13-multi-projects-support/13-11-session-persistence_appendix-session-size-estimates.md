# 13-11 Appendix — Session Size Estimates

**Type:** Reference / Analysis
**Parent step:** `13-11-session-persistence.md`
**Updated:** 2026-03-27

Use this document to predict storage requirements before implementing and to set monitoring thresholds after deployment.

---

## Two Independent Data Stores

A persisted ADK session is split across two storage locations that grow at different rates and must be sized separately.

| Store | Location | Grows | Bounded? |
|---|---|---|---|
| `Session.events` | SQLite rows (one row per event) | After every LLM turn | No — unbounded |
| `Session.state` | SQLite JSON blob (upserted per turn) | After every state mutation | Partially — list fields are capped |

---

## Store 1 — `Session.events` (the dominant factor)

Each ADK event is stored as one JSON row. The types that occur in this system and their typical sizes:

| Event type | Typical size | What drives it |
|---|---|---|
| User message | 200–500 B | Length of the user's prompt |
| Thought block | 500–4,000 B | LLM reasoning text; **3–10× larger** with thinking-mode models (Gemini 3 thinking, Claude extended thinking) |
| Tool call | 200–500 B | Function name + arguments (usually small) |
| Tool response — state tools | 500–2,000 B | `update_step`, `update_status`, `update_state` |
| Tool response — `read_internal_grid` | **5–30 KB** | Returns full grid JSON; the largest routine event |
| Tool response — `execute_ontology` | **5–50 KB** | Error traces + Python execution output; the largest possible event |
| Final text response | 300–2,000 B | Length of the agent's answer to the user |

### Events per LLM turn

Derived from `callback_utils.py` and `event_processor.py`:

```
1 user message
+ 1–3 thought events  (brainstorming / planning)
+ 2–5 tool call events
+ 2–5 tool response events
+ 1 final text event
= ~8 ADK events per turn on average
```

### Weighted average bytes per event

Most events are small, but tool responses (especially grid reads and ontology execution) dominate storage. Realistic weighted averages:

| Session character | Avg bytes/event |
|---|---|
| Light (no grid reads, no ontology) | ~1,000 B |
| Typical mixed mapping session | ~3,000 B |
| Heavy ontology session (many `execute_ontology` calls) | ~8,000 B |

---

## Store 2 — `Session.state` (bounded by hard caps)

The state blob is a single JSON object upserted to SQLite after each state-mutating turn. Key fields and their sizes:

| Key | Typical size | Cap in `callback_utils.py` |
|---|---|---|
| `events[]` (UI mirror) | ~400 B × 200 entries = **80 KB** | Hard cap at **200** entries |
| `thoughts[]` | ~200 B × 100 entries = **20 KB** | Hard cap at **100** entries |
| `tool_calls[]` | ~200 B × 100 entries = **20 KB** | Hard cap at **100** entries |
| `tasks[]` | ~250 B × N tasks | **No cap** |
| `detailed_equipment_dict` | ~500 B × N equipment | **No cap** |
| `python_code_snapshots[]` | 5–20 KB each, 1–5 kept | **No cap** |
| `ttl_code_snapshots[]` | 5–20 KB each | **No cap** |
| Scalar fields (`active_agent`, `status`, etc.) | < 1 KB total | — |

For a fully-mapped building (50 equipment, 3 code snapshots):
- **Raw state blob: ~200–400 KB**
- **Compressed (zlib level 9): ~7–14 KB** — measured 3.4% ratio on realistic data

The list-field caps mean state size is largely independent of session length after the first ~20 turns. The uncapped fields (`equipment_dict`, snapshots) are the only ones that grow with the scope of the mapping job, not with the number of turns.

---

## Predicted Total Session Sizes

| Scenario | LLM turns | ADK events | Raw event log | State blob (raw) | **Total SQLite** |
|---|---|---|---|---|---|
| Quick question (3 turns) | 3 | ~25 | ~30 KB | ~50 KB | **~100 KB** |
| Light mapping task (10 turns) | 10 | ~80 | ~150 KB | ~150 KB | **~350 KB** |
| Full equipment mapping (30 turns) | 30 | ~240 | ~700 KB | ~300 KB | **~1 MB** |
| Ontology session with execution (50 turns) | 50 | ~450 | ~2 MB | ~400 KB | **~2.5 MB** |
| Long multi-agent session (100 turns) | 100 | ~900 | ~5 MB | ~400 KB | **~6 MB** |

> SQLite adds ~10–20% B-tree page overhead on top of raw JSON totals.

---

## Deployment Scale

Assumptions for a typical deployment:

| Variable | Value |
|---|---|
| Systems per deployment | 5 |
| Active sessions kept per system | 3–5 |
| Average session size | 1–2.5 MB |

| Scope | Estimated size |
|---|---|
| Per system (3–5 sessions) | 3–12 MB |
| All systems (5 × above) | **15–60 MB** |
| `sessions.db` file total | **15–60 MB** |

SQLite operates comfortably at 10–100 GB. 60 MB is negligible and requires no special infrastructure.

---

## The Wildcard — `execute_ontology` Repeated Failures

The `OntologyValidatorAgent` is configured with up to **100 iterations**. If execution fails on each iteration and produces a 20 KB error trace:

```
100 iterations × 1 tool call + 1 tool response
= 200 extra events × ~20 KB avg
= ~4 MB from validator events alone in one session
```

A pathological validator run could push a **single session to 10–20 MB**. This is not a problem for SQLite, but it is the scenario to watch in production monitoring.

**Mitigation already in place:** the validator exits on success early. The 100-iteration limit is a ceiling, not a typical run length.

---

## Effect of Thinking-Mode Models

When `MasterLlmAgent` uses a thinking-mode model (Gemini 3 with `thinking_level="high"`, or Claude extended thinking), thought blocks are significantly larger:

| Model type | Thought block size | Impact on session size |
|---|---|---|
| Standard model (GPT-4o, Claude Sonnet standard) | 200–800 B | Baseline |
| Thinking-mode model | 1,000–8,000 B | **3–10× larger event log** |

For a 30-turn session with a thinking model, the event log could reach **3–5 MB** instead of the typical ~700 KB. Factor this in when selecting `ai_model_name` per system.

---

## Size Prediction Formula

```
session_bytes ≈ (turns × 8 × avg_bytes_per_event) + state_blob_bytes

Where:
  avg_bytes_per_event:
    ~1,000 B   — light sessions (no grid reads, no ontology execution)
    ~3,000 B   — typical mixed sessions
    ~8,000 B   — heavy ontology sessions (many execute_ontology calls)
    ×3–10      — if using a thinking-mode model

  state_blob_bytes:
    ≈ 120,000                        (capped list fields at max)
    + (equipment_count × 500)
    + (snapshot_count × 10,000)
```

### Quick reference for planning

| Session type | 10 turns | 30 turns | 100 turns |
|---|---|---|---|
| Light (standard model) | 100 KB | 290 KB | 920 KB |
| Typical (standard model) | 240 KB | 700 KB | 2.7 MB |
| Heavy ontology (standard model) | 560 KB | 1.8 MB | 6.5 MB |
| Typical (thinking model, ×5) | 1.2 MB | 3.5 MB | 13 MB |

---

## Compression Impact

Compression (`zlib` level 9) achieves ~3.4% of original size on the `Session.state` blob. Applied to the **event log rows**, compression is not recommended — it prevents SQLite from scanning rows and negates its own page compression.

Practical effect of compressing state only (Milestone 4):

| Session type | Uncompressed total | With state compression | Saving |
|---|---|---|---|
| Light (350 KB) | 350 KB | ~300 KB | ~14% |
| Typical (1 MB) | 1 MB | ~870 KB | ~13% |
| Long ontology (2.5 MB) | 2.5 MB | ~2.2 MB | ~12% |

The saving is modest (~12–15%) because the event log (uncompressed rows) is the dominant term, not the state blob. Compression helps debugging readability more than it helps storage at this scale.

**Conclusion:** compression is a nice-to-have, not a requirement. At 15–60 MB total database size, storage cost is not a driver.

---

## Monitoring Thresholds (post-deployment)

| Metric | Warning | Critical |
|---|---|---|
| Single session size | > 10 MB | > 20 MB |
| `sessions.db` total size | > 500 MB | > 2 GB |
| Sessions per system | > 20 | > 50 |
| Validator iterations in one session | > 50 | > 80 |

Add a `GET /sessions/stats` endpoint in Milestone 2 that returns these metrics for operational visibility.

