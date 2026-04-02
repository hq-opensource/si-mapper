# Agent Skills Reference

All skills available to the master agent. Skills are loaded from `agent/skills/` at startup — each folder containing a `SKILL.md` is registered automatically.

Skills are specialized instruction sets the master agent executes inline. They are not sub-agents; they run inside the master agent's context using the shared tool set defined in `tools.md`.

---

## skill-ductwork

**File:** `skills/skill-ductwork/SKILL.md`
**Purpose:** Identify and draw all ductwork (horizontal and vertical) from HVAC drawings as the foundational spatial layer of the grid.

Ducts are the first thing placed on the grid — all equipment must snap to them. This skill reads the HVAC drawing, counts and maps every duct segment, places them in the internal grid, syncs to the frontend, and visually verifies the result against the original drawing.

### Workflow
1. Ingest HVAC drawing files via `ingest_category_files(category='hvac')`
2. Analyze the drawing — count chevron starts, identify horizontal spans `(x1,y)→(x2,y)` and vertical spans `(x,y1)→(x,y2)`
3. Register all ducts in a single `add_components_batch` call
4. Sync to frontend via `sync_agent_to_graphivac`
5. Take a screenshot with `capture_frontend_state`, compare against the reference drawing, and correct any discrepancies until the visual check passes

### Key rules
- Horizontal ducts: numbered `HD-1`, `HD-2`, ... top to bottom
- Vertical ducts: numbered `VD-1`, `VD-2`, ... left to right
- Inline equipment (filters, fans, coils) does **not** end a duct — the duct continues through them
- Vertical branches do **not** split a horizontal duct
- Vertical ducts are rare — validate carefully before adding them

### Tools used
`ingest_category_files`, `load_artifacts`, `read_internal_grid`, `add_components_batch`, `delete_components_batch`, `sync_agent_to_graphivac`, `capture_frontend_state`

---

## skill-hvac-equipments

**File:** `skills/skill-hvac-equipments/SKILL.md`
**Purpose:** Place all HVAC equipment (fans, coils, dampers, sensors, VFDs, etc.) onto the duct system already established by `skill-ductwork`.

This skill runs after ductwork is complete. It reads the existing grid to get duct coordinates, then places each equipment piece at the correct position snapped to its parent duct.

### Workflow
1. Load drawing artifacts via `load_artifacts`
2. Read existing ducts via `read_internal_grid`
3. For each equipment piece: identify type, find parent duct, compute snapped coordinates, determine rotation (fans and dampers only)
4. Register via `add_component` or `add_components_batch`
5. Sync to frontend via `sync_agent_to_graphivac`
6. Take a screenshot with `capture_frontend_state`, compare against reference, correct until visual check passes

### Placement rules
- Equipment must be placed exactly on the parent duct's line — same Y for horizontal ducts, same X for vertical ducts
- No two components may share coordinates
- `fan` and `damper` use a `rotation` parameter; all other types ignore it

**Rotation values for fans** (based on airflow direction):

| Direction | Rotation |
|-----------|----------|
| Left → Right | `0` |
| Right → Left | `180` |
| Top → Bottom | `90` |
| Bottom → Top | `270` |

**Off-duct placement** (equipment placed below its parent):
- `duct_sensor_differential_pressure` → same X as its `filter`, Y+1
- `variable_frequency_drive` → same X as its `fan`, Y+1

### Equipment types
Coils: `cooling_coil`, `heating_coil`, `boiler`, `heat_pump` · Air: `fan`, `filter`, `damper`, `thermal_wheel`, `humidifier` · Piping: `pump`, `valve_three_way`, `valve_two_way`, `pipe_chiller` · Room: `room_baseboard` · Electric: `variable_frequency_drive` · Sensors: `duct_sensor_temperature`, `duct_sensor_humidity`, `duct_sensor_flow`, `duct_sensor_enthalpy`, `duct_sensor_differential_pressure`, `duct_sensor_low_limit`, `duct_sensor_static_pressure`, `pipe_sensor_temperature`

### Tools used
`load_artifacts`, `read_internal_grid`, `add_component`, `add_components_batch`, `delete_components_batch`, `sync_agent_to_graphivac`, `capture_frontend_state`

---

## skill-bacnet-points

**File:** `skills/skill-bacnet-points/SKILL.md`
**Purpose:** Extract BACnet point metadata from CSV exports and map each point to its corresponding equipment on the grid.

This skill reads BMS CSV files, identifies which points belong to which equipment (using French naming conventions common in Quebec/Canadian installations), builds a structured metadata dict, and writes it to the grid components via `write_metadata_batch`.

### Workflow
1. Ingest BACnet CSV files via `ingest_category_files(category='bacnet')`
2. Parse the CSV — columns are `bacnet` (point ID like `2500.AI11`), `nom` (French name), `valeur` (current value), `unit`
3. Group points by equipment using suffix IDs (e.g. all exhaust fan points end in `1E`)
4. Build nested metadata: `{ "AHU-1": { "bacnet": { "2500.AI11": { "name": "...", "unit": "..." } } } }`
5. Write to grid via `write_metadata_batch`

### BACnet object type suffixes
`.AI` Analog Input · `.AO` Analog Output · `.AV` Analog Value · `.BI` Binary Input · `.BO` Binary Output · `.BV` Binary Value · `.CO` Control Loop · `.PG` Program · `.SCH` Schedule · `.TL` Trend Log

### French abbreviations (common in nom column)
`RET./RETOUR` = Return · `ALIM.` = Supply · `MEL.` = Mixing · `EVAC.` = Exhaust · `TEMP.` = Temperature · `PRES./STAT.` = Pressure · `HUMI.` = Humidity · `VENT.` = Fan · `A/D` = Start/Stop · `FAUTE` = Fault · `P.C.` = Setpoint · `DRIVE` = VFD

### Tools used
`ingest_category_files`, `load_artifacts`, `write_metadata_batch`

---

## skill-control-points

**File:** `skills/skill-control-points/SKILL.md`
**Purpose:** Placeholder — extracts control sequence information and maps control points to grid equipment.

> This skill is currently a placeholder and has not yet been fully defined.

---

## skill-ontology-generation

**File:** `skills/skill-ontology-generation/SKILL.md`
**Purpose:** Generate Python code that models the HVAC system as an ASHRAE 223P semantic ontology using the `bob` and `scratch` libraries.

This skill reads the current grid state, looks up the relevant library classes, reads their source, generates a complete `ontology.py` file, and writes it to disk. It does not execute or validate — that is the job of `skill-ontology-validation`.

### Workflow
1. **Grid** — Call `read_internal_grid` to get all components and coordinates. Extract equipment class names (e.g. "Fan", "Coil", "Damper")
2. **Class lookup** — Call `search_class_mapping(keywords=[<class names>])` to find which library file each class lives in. Note the `scan_dir` field in each result
3. **Library source** — Call `scan_python_files_filtered` using the `scan_dir` field from `search_class_mapping` to read the actual class source
4. **Samples** — Call `scan_python_files_filtered` on `agent/223p/ref/code` with the same keywords to find reference implementations
5. **Plan** — Outline entities, connections, and spatial hierarchy
6. **Generate** — Write the Python ontology code
7. **Validate** — Confirm the output is valid, executable Python
8. **Write** — Call `write_ontology` to save the file
9. **Exit** — Call `exit_generator_success(summary="...")` immediately after writing

### Key modeling rules
- Use `bob` and `scratch` exclusively — never `rdflib`, `owlready2`, or other ontology libraries
- `>>` / `<<` for directional connections between equipment
- `%` operator exclusively for sensor-to-equipment relationships (do not also set `observes`)
- Every sensor must have a `hasUnit` property from a `bob`/`scratch` enum
- Do not redefine ConnectionPoints already defined in the library — use and connect them directly
- Never write TTL manually — let `bob`/`scratch` handle serialization

### Failure conditions (call `exit_generator_failure`)
- `read_internal_grid` returns empty, no equipment, only ducts/pipes, or an error
- `bob`/`scratch` libraries are unreadable or not found
- Code samples are unreadable

### Tools used
`read_internal_grid`, `search_class_mapping`, `scan_python_files_filtered`, `read_prompt`, `write_ontology`, `extract_lessons`, `exit_generator_success`, `exit_generator_failure`

---

## skill-ontology-validation

**File:** `skills/skill-ontology-validation/SKILL.md`
**Purpose:** Validate the generated `ontology.py`, iteratively fix all errors, and produce a clean `.ttl` file. Does not regenerate from scratch — it repairs what exists.

This skill runs after `skill-ontology-generation`. It enters a fix loop: read → execute → analyze errors → fix → write → checkpoint → repeat, until the file runs cleanly and produces a valid TTL.

### Workflow
1. Read `agent/223p/LESSONS.md` for error-resolution lessons from previous sessions (if empty or absent, proceed without it)
2. Read the current `ontology.py` via `read_ontology`
3. Execute via `execute_ontology` — capture stdout, stderr, return code
4. If clean and TTL produced → read the TTL file content, call `exit_validator_success(code=..., ttl_content=..., summary=...)`
5. Otherwise → analyze errors, look up affected classes via `search_class_mapping` + `scan_python_files_filtered`, write corrected file via `write_ontology`, then immediately call `checkpoint_code` to save a version snapshot
6. Go to step 3

### Fixing strategy
- Fix the root cause, not the symptom
- Fix one error at a time; write the full corrected file after each fix
- Never comment out errors to suppress them
- `checkpoint_code` is mandatory after every `write_ontology` call

### Stop conditions (call `exit_validator_failure`)
- `agent/223p/LESSONS.md` is unreadable and no error-resolution context is available — proceed best-effort but log the limitation
- `read_ontology` returns empty or missing file
- `search_class_mapping` returns empty for known class names
- Same error persists after 10 consecutive fix attempts
- Code is fundamentally broken (non-Python, random text)

### Success exit summary must include
- Number of fix iterations performed
- Error categories fixed
- Path of the produced TTL file

### Tools used
`read_ontology`, `execute_ontology`, `write_ontology`, `checkpoint_code`, `search_class_mapping`, `scan_python_files_filtered`, `read_prompt`, `exit_validator_success`, `exit_validator_failure`


---

## Skill execution order

The skills follow a natural dependency chain for a full HVAC-to-ontology pipeline:

```
skill-ductwork
    └─▶ skill-hvac-equipments
            └─▶ skill-bacnet-points
                    └─▶ skill-ontology-generation
                                └─▶ skill-ontology-validation
                                            └─▶ load_ttl_to_neo4j (tool)
```

Each skill assumes the previous one has completed. The master agent is responsible for orchestrating the order and deciding when to invoke each skill based on the current state of the grid and user instructions.
