---
name: skill-hvac-equipments
description: Specialized instructions for identifying and drawing equipments for HVAC systems.
---

# Equipment Placement Agent

Place HVAC equipment on the established duct system.

---


# Execution Flow

1. **Load context**: Use `load_artifacts` to view drawings. **Note the artifact names of the reference drawings** — you will need them in the verification step.
2. **Read grid**: Use `read_internal_grid` to get duct coordinates.
3. **Analyze**: For each equipment piece:
   - Identify type (from the list above) and position.
   - Find parent duct and snap coordinates.
   - Determine rotation (if `fan` or `damper`).
4. **Register internally**: Use `add_component` for single items or `add_components_batch` for multiple.
   - Example: `add_component(component_type="fan", name="SF-1", coord=[10,5], rotation=180)`
   - Example: `add_component(component_type="damper", name="MD-1", coord=[12,5], rotation=90)`
   - Example: `add_component(component_type="variable_frequency_drive", name="VFD-1", coord=[15,6])`
5. **Sync to frontend**: Use `sync_agent_to_graphivac` to sync the HVAC equipments to the frontend.
6. **Verify**: After calling the tool `sync_agent_to_graphivac`, perform a **Equipment Verification Checkpoint**:
   - Call `capture_frontend_state()` to take the screenshot.
   - Then call `load_artifacts` passing **both** the snapshot and the original reference drawing artifact name(s) in a single call — for example: `load_artifacts(artifact_names=["verification/latest_snapshot.png", "hvac/<reference_drawing_filename>"])`. Use the artifact names you noted in Step 1.
   - Compare the snapshot against the reference image side-by-side. Verify that all equipment components are present, correctly positioned, and correctly attached to the ducts.
   - If discrepancies are found, correct them and repeat the workflow until the equipment matches the reference.
   - Only mark the task as finished after visual confirmation passes.
7. **Exit**: Call `exit_with_success(summary="...")` to signal completion. The summary **must** include:
   - Number of equipment pieces placed
   - Number of corrections made during verification
   - Final verification result (pass/fail)

   **Failure path:** If verification cannot be resolved after 3 correction cycles, call `exit_with_failure(reason="...")` explaining the unresolvable discrepancies.

# Rules

## Placement Requirements
- **Read the grid first**: Always use the tool `read_internal_grid` to see existing ducts
- **Snap to ducts**: Equipment must be placed exactly on its parent duct's line
  - Horizontal duct at Y1 → equipment at `[X, Y1]`
  - Vertical duct at X1 → equipment at `[X1, Y]`
- **No overlaps**: Components cannot share the same coordinates
- **Unique names**: Every component needs a unique identifier

## Equipment Types
Use these exact type strings from `internal_grid_tools.py`:
- **Coils**: `cooling_coil`, `heating_coil`, `boiler`, `heat_pump`
- **Air Handling**: `fan`, `filter`, `damper`, `thermal_wheel`, `humidifier`
- **Piping**: `pump`, `valve_three_way`, `valve_two_way`, `pipe_chiller`
- **Room**: `room_baseboard`
- **Sensors**: 
    - Duct: `duct_sensor_enthalpy`, `duct_sensor_temperature`, `duct_sensor_differential_pressure`, `duct_sensor_humidity`, `duct_sensor_flow`, `duct_sensor_low_limit`, `duct_sensor_static_pressure`
    - Pipe: `pipe_sensor_temperature`
- **Electric**: `variable_frequency_drive`

## Rotation Rules
Only `fan` and `damper` types use the `rotation` parameter.

### Dampers
- Horizontal duct: `rotation: 0`
- Vertical duct: `rotation: 90`

### Fans (based on airflow direction)
- Left → Right: `rotation: 0`
- Right → Left: `rotation: 180`
- Top → Bottom: `rotation: 90`
- Bottom → Top: `rotation: 270`

### All Other Equipment
- Ignore rotation or set to `0`.

## Off-Duct Equipment

Some equipment sits outside the duct (below its parent component):

### Differential Pressure Sensor (`duct_sensor_differential_pressure`)
- Associated with: `filter`
- Placement: Same X-coordinate, Y + 1 unit down
- Example: Filter at `[10, 5]` → Sensor at `[10, 6]`

### Variable Frequency Drive (`variable_frequency_drive`)
- Associated with: `fan`
- Placement: Same X-coordinate, Y + 1 unit down
- Example: Fan at `[15, 5]` → VFD at `[15, 6]`

## Naming convention
Name the equipmens as they are named in the original multimodal data. If the equipment is not named, then create a name for it following the format: `TYPE-ID` where TYPE is the type of the equipment and ID is a unique identifier.






---
