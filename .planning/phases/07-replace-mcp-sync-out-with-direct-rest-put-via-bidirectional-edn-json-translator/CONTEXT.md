# Phase 7 Context: Bidirectional EDN-JSON Translator + Direct REST Sync

## Problem Statement

The current sync-out (after_agent_callback) uses the MCP server as a middleman. For every component the agent adds or deletes, it:
1. Opens an MCP connection
2. Calls a tool (e.g., `create_fan`)
3. The MCP manager does a full **GET** of the EDN grid, mutates it, then **PUT**s it back
4. Repeats for each component

For 50 fans: 50 GETs + 50 PUTs. This is serial, slow, and architecturally unnecessary — the MCP server provides no value that direct REST cannot.

The sync-in (before_agent_callback) already uses direct REST. The goal is to make sync-out match: a single REST PUT of the full grid.

---

## Design: No Diffs, No Snapshots — Full Comps Rebuild

The simplest correct approach: if the translator is reliable enough to reconstruct valid EDN from `internal_grid`, then the after_callback just **rebuilds the entire `comps` section from scratch** and PUTs it. No diff. No initial snapshot. Whatever is in `internal_grid` at the end of the turn is the truth.

### Why the raw EDN still needs to be saved

The EDN grid is not just `comps`. It has other top-level keys: grid title, font configs, and any other Graphivac metadata. Graphivac's PUT endpoint is a **full replacement** — this is confirmed by how every manager works (GET full grid → mutate comps → PUT full grid). Sending only `{comps: {...}}` would wipe everything else.

So the raw EDN is saved in the before_callback — not for diffing, but as the **carrier** that preserves non-comps metadata. The after_callback replaces only the `comps` key and PUTs the rest unchanged.

### What becomes unnecessary

- `_initial_grid_snapshot` — no longer needed (no diff to compute)
- All diff logic in the after_callback
- The MCP session, `streamablehttp_client`, `ClientSession` imports

---

## Target Architecture

```
before_agent_callback
  REST GET → raw_edn (full EDN grid)
  state["_raw_edn_grid"]  = edn_to_mutable(raw_edn)   ← for non-comps metadata
  state["internal_grid"]  = edn_to_internal_grid(raw_edn)

[agent thinks, tools mutate internal_grid only]

after_agent_callback
  new_comps = internal_grid_to_edn_comps(internal_grid)
  modified_edn = {**_raw_edn_grid, Keyword("comps"): new_comps}
  REST PUT modified_edn → Graphivac   ← one call, no MCP
```

---

## What Needs to Be Built: The Translator

`agent/utils/grid_edn_translator.py` — a single module with two functions:

### `edn_to_internal_grid(raw_edn: dict) -> dict`
Converts a parsed EDN grid into the agent's `internal_grid` format:
```json
{"components": [
  {"id": "...", "type": "fan",  "name": "SF-1", "coord": [5, 3], "rotation": 0},
  {"id": "...", "type": "duct", "name": "D-1",  "start": [0, 0], "end": [10, 0]}
]}
```
Replaces the inline parsing logic currently in `grid_sync_graphivac_to_agent.py`.

### `internal_grid_to_edn_comps(internal_grid: dict) -> dict`
Converts `internal_grid["components"]` into an EDN `comps` map (keyed by `(Keyword, name)` tuples).
Iterates every component, maps agent type → EDN symbol, and builds the full comps dict from scratch.
Returns a dict ready to be set as `raw_edn[Keyword("comps")]`.

---

## Type Mapping Table (Agent ↔ EDN)

Complete bidirectional contract between agent type names and EDN symbols:

| Agent type (internal_grid) | EDN key prefix | EDN symbol string |
|---|---|---|
| `duct` | `(Keyword("duct"), name)` | *(key type encodes this, no symbol field)* |
| `pipe` | `(Keyword("duct"), name)` | *(treated as duct in EDN)* |
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
| `room_baseboard` | `(Keyword("obj"), name)` | `"user.room.baseboard"` |
| `pipe_chiller` | `(Keyword("obj"), name)` | `"user.pipe.chiller"` |
| `boiler` | `(Keyword("obj"), name)` | `"pipe.boiler"` *(verify in pipe_manager)* |
| `heat_pump` | `(Keyword("obj"), name)` | `"pipe.heat-pump"` *(verify in pipe_manager)* |
| `pump` | `(Keyword("obj"), name)` | `"pipe.pump"` *(verify in pipe_manager)* |
| `valve_three_way` | `(Keyword("obj"), name)` | `"pipe.valve.three-way"` *(verify in pipe_manager)* |
| `valve_two_way` | `(Keyword("obj"), name)` | `"pipe.valve.two-way"` *(verify in pipe_manager)* |
| `variable_frequency_drive` | `(Keyword("obj"), name)` | `"elec.vfd"` *(verify in electric_manager)* |
| `pipe_sensor_temperature` | `(Keyword("obj"), name)` | `"pipe.sensor.temperature"` *(verify in pipe_manager)* |

> Symbols marked "verify" must be confirmed by reading the corresponding manager files before implementing. The pattern is consistent — check the `Keyword("symbol")` value in each manager's `create_*` action.

---

## Known Bug to Fix: `:rot` vs `:rotation`

The duct_manager stores fan/damper rotation in EDN as `Keyword("rot")`:
```python
new_value[Keyword("rot")] = rotation
```

But the current before_callback parser reads it as `Keyword("rotation")`:
```python
rotation = value.get(Keyword("rotation"), 0)  # ← always returns 0, bug!
```

The new translator must use `Keyword("rot")` for both reading and writing rotation.

---

## Files Affected

| File | Change |
|---|---|
| `agent/utils/grid_edn_translator.py` | **New** — bidirectional translator |
| `agent/utils/grid_sync_graphivac_to_agent.py` | Update: use translator, save `_raw_edn_grid`, remove snapshot |
| `agent/utils/grid_sync_agent_to_graphivac.py` | Rewrite: drop all MCP code, use translator + single REST PUT |

The MCP server itself is **not removed** — subagents still use it for their own tool calls during thinking. Only the sync callbacks stop using it.

---

## Existing Utilities to Reference (from MCP server)

- `mcp_server/graphivac/utils/edn_to_mutable.py` — recursively converts ImmutableDict/ImmutableList to standard Python dicts/lists. The translator needs this same logic (reimplemented locally — no cross-package imports).
- `mcp_server/graphivac/utils/grid_status.py` — `_to_json_friendly()` for Keyword-to-string conversion. Reference only.
