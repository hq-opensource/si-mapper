# Phase 7: EDN-JSON Translator + Direct REST Sync-Out — Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the MCP-based per-component sync-out with a single REST PUT per agent turn. Build a bidirectional EDN↔JSON translator in the agent package. The before_agent_callback saves the raw EDN and parses it to `internal_grid`. The after_agent_callback translates `internal_grid` back to EDN and PUTs the full grid in one call. No diffs. No snapshots. No MCP involvement in the sync lifecycle.

The MCP server itself is NOT removed — subagents still call it during thinking for their own tool calls. Only the two sync callbacks are changed.

</domain>

<decisions>
## Implementation Decisions

### Architecture
- **No diff, no snapshot**: The after_callback does a full comps rebuild from `internal_grid` every turn. Whatever is in `internal_grid` at turn end is the truth.
- **Raw EDN preserved**: The before_callback saves `_raw_edn_grid` (the full mutable EDN dict) — not for diffing, but to carry non-comps metadata (title, font configs, etc.) through to the PUT. Graphivac's PUT is a full replacement; only the `comps` key is replaced.
- **`_initial_grid_snapshot` removed**: No longer needed anywhere in the codebase.

### Unknown symbol handling
- If the translator encounters an EDN symbol it doesn't recognize during sync-in (e.g., a user-created custom component), that component is **silently dropped** — it will not appear in `internal_grid` and will be absent from the next PUT.
- This is acceptable for now. Future symbols can be added to the mapping table when needed.
- Log a warning for each dropped symbol so it's visible in logs.

### Sync-out failure behavior
- On PUT failure: **retry once** with the same request.
- If the retry also fails: **inject a warning Content into the agent's next turn** and log a warning. The agent should treat this as a signal to stop work.
- Rationale: a failed PUT means `internal_grid` and Graphivac are diverged. The next sync-in would read the old Graphivac state and overwrite `internal_grid`, silently losing the agent's turn. Better to stop and warn than to let that happen.
- This failure mode is considered unlikely (would only occur on network issues). Build the warning infrastructure but don't over-engineer recovery logic.
- The `after_agent_callback` returns `Optional[types.Content]` — return a `types.Content` with the error message on unrecoverable failure; return `None` on success.

### Pipe vs duct distinction
- Pipes and ducts are **distinct EDN types** and must not be conflated.
- Pipe line components use `(Keyword("pipe"), name)` as the EDN key — verified in `pipe_manager.py` and confirmed in Graphivac UI (`:comps {[:pipe "D3tBIs0TvG"] {:n1 {:pos [-3 3]}, :n2 {:pos [1 3]}}}`).
- Duct line components use `(Keyword("duct"), name)`.
- The translator must distinguish them on both read (sync-in) and write (sync-out).

### Test scope
- **Unit tests**: Translator module (`agent/utils/grid_edn_translator.py`) tested in isolation — roundtrip correctness, unknown symbol handling, rotation bug fix, pipe vs duct distinction.
- **Integration test**: A dedicated test script that connects to a **real Graphivac grid** using environment variables. It:
  1. Reads the live grid via the before_callback logic
  2. Parses it to `internal_grid`
  3. Adds a known set of test components
  4. Translates back to EDN via the translator
  5. PUTs to the real Graphivac grid
  6. Human verifies the result in the Graphivac UI
- The test must print clear instructions for the human: what was added, what to look for in the UI, and how to clean up.
- The test agent itself is mocked — we're testing the translator and REST pipeline, not the LLM.

### Bug fix: `:rot` vs `:rotation`
- Fan/damper rotation is stored in EDN as `Keyword("rot")` (confirmed in duct_manager).
- The existing before_callback reads it as `Keyword("rotation")` — a bug that causes rotation to always read as 0.
- The new translator must use `Keyword("rot")` for both reading and writing rotation.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Files being replaced/rewritten
- `agent/utils/grid_sync_graphivac_to_agent.py` — Current sync-in logic (to be updated: use translator, save `_raw_edn_grid`, remove snapshot)
- `agent/utils/grid_sync_agent_to_graphivac.py` — Current sync-out logic (to be fully rewritten: drop all MCP code, use translator + single REST PUT)

### EDN key structure — verified source of truth
- `mcp_server/graphivac/duct_manager.py` — Duct and equipment EDN key/value structure (`Keyword("duct")`, `Keyword("obj")`)
- `mcp_server/graphivac/pipe_manager.py` — Pipe line type uses `Keyword("pipe")`, pipe equipment uses `Keyword("obj")`
- `mcp_server/graphivac/electric_manager.py` — VFD uses `Keyword("obj")` + symbol `"electric.vfd"`
- `mcp_server/graphivac/custom_manager.py` — Custom types (`user.room.baseboard`, `user.pipe.chiller`)

### Utilities to reimplement locally
- `mcp_server/graphivac/utils/edn_to_mutable.py` — `edn_to_mutable()` recursively converts ImmutableDict/ImmutableList to standard Python. Must be reimplemented in the agent package (no cross-package imports).
- `mcp_server/graphivac/utils/grid_status.py` — `_to_json_friendly()` Keyword-to-string conversion. Reference only.

### Graphivac REST API
- `mcp_server/graphivac/graphivac_api.py` — `get_grid_info_edn()` (GET) and `update_grid_edn()` (PUT) — the exact REST calls the sync callbacks make.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `mcp_server/graphivac/utils/edn_to_mutable.py`: 15-line utility, trivial to copy into agent package
- `mcp_server/graphivac/graphivac_api.py`: REST GET/PUT implementations to mirror in the sync callbacks
- `agent/tools/internal_grid_tools.py`: `LINE_TYPES`, `ROTATION_TYPES`, `EQUIPMENT_TYPES`, `SENSOR_TYPES` constants — import or replicate in the translator

### Established Patterns
- All sync env vars (`GRAPHIVAC_BASE_URL`, `GRAPHIVAC_ORG_ID`, `GRAPHIVAC_PROJECT_ID`, `GRAPHIVAC_GRID_ID`) are already read in the before_callback — same pattern applies to the after_callback
- `asyncio.to_thread()` is used for blocking HTTP calls in the before_callback — same pattern for the PUT in the after_callback
- The `after_agent_callback` return signature is `Optional[types.Content]` — return `None` on success, `types.Content` with error message on unrecoverable PUT failure

### Integration Points
- `level_3_master_main_llm.py`: `before_agent_callback=sync_graphivac_to_agent_callback` and `after_agent_callback=sync_agent_to_graphivac_callback` — no changes needed here, just swap implementations
- `agent/tests/` — existing test pattern uses `MockToolContext`; integration test is a standalone script, not a pytest unit test

</code_context>

<specifics>
## Specific Ideas

- Integration test should be a **standalone runnable script** (not a pytest test) so the human can run it manually, watch the Graphivac UI in real time, and verify the result visually.
- The test should print something like: "Added fan 'TEST-FAN-1' at [5,5] and duct 'TEST-DUCT-1' from [0,0] to [10,0]. Check the Graphivac UI — you should see these two components. Press Enter to clean up..."
- User confirmed pipes are stored as `[:pipe "name"]` in Graphivac EDN (verified in the live UI).
- The failure warning injected into the agent on a failed PUT should be clear enough for the agent to understand it must stop: something like "SYNC ERROR: Failed to write grid to Graphivac after retry. Grid state is diverged. Stop all grid operations."

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope.

</deferred>

---

## Verified Type Mapping Table

Complete, verified bidirectional contract between agent type names and EDN representation:

| Agent type | EDN key | EDN symbol |
|---|---|---|
| `duct` | `(Keyword("duct"), name)` | *(no symbol — key encodes type)* |
| `pipe` | `(Keyword("pipe"), name)` | *(no symbol — key encodes type)* |
| `fan` | `(Keyword("obj"), name)` | `"duct.fan"` |
| `damper` | `(Keyword("obj"), name)` | `"duct.damper"` |
| `cooling_coil` | `(Keyword("obj"), name)` | `"duct.coil.cooling"` |
| `heating_coil` | `(Keyword("obj"), name)` | `"duct.coil.heating"` |
| `filter` | `(Keyword("obj"), name)` | `"duct.filter"` |
| `thermal_wheel` | `(Keyword("obj"), name)` | `"duct.thermal-wheel"` |
| `humidifier` | `(Keyword("obj"), name)` | `"duct.humidifier"` |
| `duct_sensor_enthalpy` | `(Keyword("obj"), name)` | `"duct.sensor.enthalpy"` |
| `duct_sensor_temperature` | `(Keyword("obj"), name)` | `"duct.sensor.temperature"` |
| `duct_sensor_differential_pressure` | `(Keyword("obj"), name)` | `"duct.sensor.pressure"` |
| `duct_sensor_humidity` | `(Keyword("obj"), name)` | `"duct.sensor.humidity"` |
| `duct_sensor_flow` | `(Keyword("obj"), name)` | `"duct.sensor.flow"` |
| `duct_sensor_low_limit` | `(Keyword("obj"), name)` | `"duct.sensor.low-limit"` |
| `duct_sensor_static_pressure` | `(Keyword("obj"), name)` | `"duct.sensor.static-pressure"` |
| `boiler` | `(Keyword("obj"), name)` | `"pipe.boiler"` |
| `heat_pump` | `(Keyword("obj"), name)` | `"pipe.heat-pump"` |
| `pump` | `(Keyword("obj"), name)` | `"pipe.pump"` |
| `valve_three_way` | `(Keyword("obj"), name)` | `"pipe.valve.three-way"` |
| `valve_two_way` | `(Keyword("obj"), name)` | `"pipe.valve.two-way"` |
| `pipe_sensor_temperature` | `(Keyword("obj"), name)` | `"pipe.sensor.temperature"` |
| `variable_frequency_drive` | `(Keyword("obj"), name)` | `"electric.vfd"` |
| `room_baseboard` | `(Keyword("obj"), name)` | `"user.room.baseboard"` |
| `pipe_chiller` | `(Keyword("obj"), name)` | `"user.pipe.chiller"` |

*All symbols verified directly from manager source files.*

---

*Phase: 07-replace-mcp-sync-out-with-direct-rest-put-via-bidirectional-edn-json-translator*
*Context gathered: 2026-03-19*
