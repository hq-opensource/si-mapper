# Agent Tools Reference

All tools available to the master agent, grouped by responsibility.
Source: `agent/tools/`

---

## Grid — Sync with Graphivac

### `sync_graphivac_to_agent`
**File:** `sync_graphivac_to_agent_tool.py`

Fetches the live grid from Graphivac via REST GET and loads it into the agent's internal state (`internal_grid`). Overwrites any in-memory grid state with the live version and resets the pending-changes flag.

**Call before:** any task that reads or modifies grid components, to ensure you work with the latest data.

**Returns:** confirmation string with component count, or an error message.

---

### `sync_agent_to_graphivac`
**File:** `sync_graphivac_tool.py`

Pushes the agent's current `internal_grid` to Graphivac via REST PUT. Only runs if there are pending changes (`_updated_grid` flag is set). Converts internal grid to EDN format before sending. Retries once on failure.

**Call after:** finishing a batch of grid modifications to persist them.

**Returns:** confirmation string with component count, or a `SYNC-OUT FAILED` error message.

---

## Grid — Internal State (CRUD)

The agent maintains a local copy of the grid (`internal_grid`) in session state. These tools modify that copy. Changes are not sent to Graphivac until `sync_agent_to_graphivac` is called.

### Component types

| Category | Types |
|----------|-------|
| **Line** (use `start_coord` + `end_coord`) | `duct`, `pipe` |
| **Equipment** (use `coord`) | `cooling_coil`, `heating_coil`, `fan`, `filter`, `damper`, `thermal_wheel`, `humidifier`, `boiler`, `heat_pump`, `pump`, `valve_three_way`, `valve_two_way`, `variable_frequency_drive`, `room_baseboard`, `pipe_chiller` |
| **Sensor** (use `coord`) | `duct_sensor_enthalpy`, `duct_sensor_temperature`, `duct_sensor_differential_pressure`, `duct_sensor_humidity`, `duct_sensor_flow`, `duct_sensor_low_limit`, `duct_sensor_static_pressure`, `pipe_sensor_temperature` |

`fan` and `damper` additionally accept an optional `rotation` parameter (integer, default `0`).

---

### `add_component`
**File:** `internal_grid_tools.py`

Adds a single component to the internal grid.

| Parameter | Type | Description |
|-----------|------|-------------|
| `component_type` | string | Must be one of the valid types above |
| `name` | string | Unique name (e.g. `"SF-1"`) |
| `coord` | `[x, y]` | Required for equipment/sensor types |
| `start_coord` | `[x, y]` | Required for line types |
| `end_coord` | `[x, y]` | Required for line types |
| `rotation` | int | Optional, only for `fan`/`damper` |

**Returns:** confirmation with component ID and total count, or an error string.

---

### `add_components_batch`
**File:** `internal_grid_tools.py`

Adds multiple components in a single call. More efficient than repeated `add_component` calls.

| Parameter | Type | Description |
|-----------|------|-------------|
| `components_json` | string | JSON-encoded array of component dicts. Each dict uses the same fields as `add_component`. |

**Example:**
```json
[
  {"type": "fan", "name": "SF-1", "coord": [5, 5]},
  {"type": "duct", "name": "D-1", "start_coord": [0, 0], "end_coord": [10, 0]}
]
```

**Returns:** summary of added/skipped counts and any per-item errors.

---

### `delete_component`
**File:** `internal_grid_tools.py`

Deletes a single component from the internal grid by name.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Name of the component to remove |

---

### `delete_components_batch`
**File:** `internal_grid_tools.py`

Deletes multiple components by name in one call.

| Parameter | Type | Description |
|-----------|------|-------------|
| `names` | list of strings | Names of components to remove |

---

### `read_internal_grid`
**File:** `internal_grid_tools.py`

Returns the current internal grid as a JSON string. Optionally filter by component type.

| Parameter | Type | Description |
|-----------|------|-------------|
| `component_type` | string (optional) | If provided, returns only components of that type |

---

## Metadata

### `write_metadata`
**File:** `metadata_tools.py`

Writes BACnet/control metadata to a single equipment component on the Graphivac canvas. Reads the live grid, patches the target component's `:custom-fields`, and PUTs it back in one transaction. No intermediate sync needed.

| Parameter | Type | Description |
|-----------|------|-------------|
| `equipment_name` | string | Unique name of the component on the grid (e.g. `"AHU-1"`) |
| `metadata` | dict | Key-value pairs to store in custom-fields |

**Example:**
```json
{
  "bacnet": {"2500.AI11": {"name": "SUPPLY AIR TEMP", "unit": "°C"}}
}
```

---

### `write_metadata_batch`
**File:** `metadata_tools.py`

Writes metadata to multiple components in a single transaction. Reads the grid once, applies all updates, writes it back once. More efficient than repeated `write_metadata` calls.

| Parameter | Type | Description |
|-----------|------|-------------|
| `updates` | dict | Keys are equipment names, values are their metadata dicts |

**Example:**
```json
{
  "AHU-1": {"bacnet": {"2500.AI11": {"name": "VITESSE RET.", "unit": "A"}}},
  "VAV-101": {"bacnet": {"2501.BI3": {"name": "STATUT", "unit": ""}}}
}
```

---

## Ontology — ASHRAE 223P

### `search_class_mapping`
**File:** `ontology_tools.py`

Searches the ASHRAE 223P class mapping index (bob and scratch libraries) for classes matching any of the given keywords. Returns class name, library, relative path, absolute venv path, and `scan_dir` — the directory to pass directly to `scan_python_files_filtered`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `keywords` | list of strings | Class name keywords to match (case-insensitive substring) |

**Returns:** list of matches, each with:
- `class_name` — e.g. `"Fan"`
- `library` — `"bob"` or `"scratch"`
- `path` — relative path within the library (e.g. `"bob/equipment/hvac/fan.py"`)
- `abs_path` — absolute path to the file in the venv
- `scan_dir` — parent directory of the file — pass this to `scan_python_files_filtered`

**Typical workflow:** call this first to find where a class lives, then pass `scan_dir` to `scan_python_files_filtered` to read the source.

---

### `scan_python_files_filtered`
**File:** `ontology_tools.py`

Recursively scans a directory and returns the full source of every `.py` file whose content contains at least one of the given keywords. Use `scan_dir` from `search_class_mapping` as the path.

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | string | Absolute or relative directory to scan |
| `keywords` | list of strings | Only files containing at least one keyword are returned |

**Returns:** JSON object `{ "root": "...", "files": { "relative/path.py": "<source>" } }`.

---

### `read_ontology`
**File:** `ontology_tools.py`

Reads the current content of `223p/src/ontology.py`.

**Returns:** `{ "path": "...", "content": "<source code>" }`

---

### `write_ontology`
**File:** `ontology_tools.py`

Overwrites `223p/src/ontology.py` with new Python source code. Automatically creates a numbered backup before writing (e.g. `ontology_1.py`, `ontology_2.py`). Also appends a snapshot to `python_code_snapshots` in session state for the frontend.

| Parameter | Type | Description |
|-----------|------|-------------|
| `content` | string | Complete Python source to write. Must be valid Python. No markdown fences. |

---

### `execute_ontology`
**File:** `ontology_tools.py`

Executes `223p/src/ontology.py` in a subprocess using the venv Python interpreter. Captures stdout/stderr and the generated TTL file path. On success, appends the TTL content to `ttl_code_snapshots` in session state.

**Returns:**
```json
{
  "success": true,
  "returncode": 0,
  "stdout": "...",
  "stderr": "...",
  "ttl_file": "/path/to/ontology.ttl"
}
```

---

### `read_prompt`
**File:** `ontology_tools.py`

Reads the 223P ontology generator `prompt.md` reference file (`agent/sub_agents/_223p/generator/prompt.md`). Documents generation conventions, library usage guidelines, and modeling requirements.

**Returns:** `{ "path": "...", "content": "<text>" }`

---

## Ontology — Exit / Checkpoint Signals

These tools signal the master loop about ontology task outcomes. They set session state flags and call `actions.escalate` to terminate the current skill execution.

### `checkpoint_code`
**File:** `ontology_exit_tools.py`

Saves a fix snapshot to `python_code_snapshots` in session state. **Does NOT escalate** — the validator loop continues. Use this between correction attempts to record intermediate versions visible in the frontend.

| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | string | Current Python source code for the snapshot |

---

### `exit_generator_success`
**File:** `ontology_exit_tools.py`

Signals that ontology generation completed successfully. Saves an "Initial" snapshot, persists the Python file to `mapper/uploads/python/`, sets `ONTOLOGY_GENERATION_SUCCESS = True`, sets `EXIT_LEVEL_2 = True`, and escalates.

| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | string | Final generated Python source |
| `summary` | string | Description of what was built (equipment count, connections, decisions) |

---

### `exit_generator_failure`
**File:** `ontology_exit_tools.py`

Signals that ontology generation failed. Sets `ONTOLOGY_GENERATION_SUCCESS = False`, records the failure reason, sets `EXIT_LEVEL_2 = True`, and escalates.

| Parameter | Type | Description |
|-----------|------|-------------|
| `reason` | string | Explanation of why generation failed |

---

### `exit_validator_success`
**File:** `ontology_exit_tools.py`

Signals that ontology validation completed successfully. Saves a "Final/validated" Python snapshot, persists both Python and TTL files to `mapper/uploads/`, sets `ONTOLOGY_VALIDATION_SUCCESS = True`, sets `EXIT_LEVEL_2 = True`, and escalates.

| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | string | Final validated Python source |
| `summary` | string | Validation summary |
| `ttl_content` | string (optional) | TTL file content to persist and snapshot |

---

### `exit_validator_failure`
**File:** `ontology_exit_tools.py`

Signals that ontology validation failed. Sets `ONTOLOGY_VALIDATION_SUCCESS = False`, records the reason, sets `EXIT_LEVEL_2 = True`, and escalates.

| Parameter | Type | Description |
|-----------|------|-------------|
| `reason` | string | Explanation of why validation failed |

---

## Neo4j

### `load_ttl_to_neo4j`
**File:** `load_ttl_to_neo4j_tool.py`

Wipes the Neo4j graph database and reimports the current `mapper/uploads/ttl/latest_ontology.ttl` file using Neosemantics (`n10s.rdf.import.inline`). Each call is a complete wipe-and-reimport — there is no incremental update. The TTL file is the source of truth.

**Trigger phrases:** *"load to neo4j"*, *"import to graph"*, *"populate the graph"*

**Requires:** Neo4j running (`docker compose --profile graph up -d neo4j`) and `latest_ontology.ttl` present (run the ontology validator first).

**Returns:**
```json
{
  "status": "success",
  "triples_loaded": 142,
  "termination_status": "OK",
  "node_count": 87,
  "relationship_count": 55
}
```

---

## Session State

### `save_agent_state`
**File:** `state_tools.py`

Saves the processing status of a specific component to persist state across turns. Used to track which equipment has already been processed.

| Parameter | Type | Description |
|-----------|------|-------------|
| `equipment_id` | string | Component ID (e.g. `"0LJ2gpN3pY"`) |
| `status` | string | Processing status (e.g. `"treated"`, `"error"`, `"pending"`) |

---

### `get_agent_state`
**File:** `state_tools.py`

Retrieves processing status from the persistent `treated` dictionary in session state.

| Parameter | Type | Description |
|-----------|------|-------------|
| `equipment_id` | string (optional) | If provided, returns status for that ID only. If omitted, returns the entire `treated` dict. |

---

## Progress / Observability

### `update_step`
**File:** `progress_tool.py`

Updates the current activity label and appends it to `observed_steps` in session state. Visible in the frontend progress display.

| Parameter | Type | Description |
|-----------|------|-------------|
| `step` | string | Current step description (e.g. `"Analyzing horizontal ducts"`) |

---

### `update_status`
**File:** `progress_tool.py`

Updates the overall agent status label in session state.

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Status string (e.g. `"processing"`, `"working"`, `"completed"`) |

---

## Frontend

### `capture_frontend_state`
**File:** `capture_frontend_state_tool.py`

Takes a screenshot of the live Graphivac canvas using headless Chromium (Playwright), saves the PNG to `mapper/uploads/snapshots/`, and registers it as a session artifact at `verification/latest_snapshot.png`.

**Requires:** `playwright install chromium` run once after installing dependencies.

After calling this, use `load_artifacts(artifact_names=["verification/latest_snapshot.png"])` to inspect the image.

---

## Ingestion

### `ingest_category_files`
**File:** `ingest_category_tool.py`

Reads all supported files (CSV, PDF, PNG/JPG, TXT) from a specific category folder in `mapper/uploads/` and saves them as session artifacts. After calling this, use `load_artifacts` with the returned artifact names to inspect their content.

| Parameter | Type | Description |
|-----------|------|-------------|
| `category` | string | Folder name under `mapper/uploads/` (e.g. `"hvac"`, `"bacnet"`, `"control"`, `"electricity"`) |

**Returns:** list of saved artifact names and any per-file errors.

---

## Loop Control

### `exit_loop_level_2`
**File:** `loop_exit_tools.py`

Signals the Level 2 master loop (`MasterMainLoopAgent`) to terminate, ending the entire agent session. Use only when all tasks across all phases are successfully completed.

Sets `EXIT_LEVEL_2 = True` in session state and calls `actions.escalate`.
