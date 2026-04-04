---
name: skill-hvac-equipments
description: Specialized instructions for identifying and drawing equipments for HVAC systems.
---

# Equipment Placement Agent

Place HVAC equipment on the established duct system.

---


# Execution Flow

1. **Sync frontend state**: Use `sync_graphivac_to_agent` to synchronize the agent's internal state with the current frontend grid. This ensures any changes the user made on the frontend are captured before analysis begins.
2. **Load context**: Use `load_artifacts` to view drawings.
3. **Read grid**: Use `read_internal_grid` to get duct coordinates.
4. **Analyze**: For each equipment piece:
   - Identify type (from the list above) and position.
   - Find parent duct and snap coordinates.
   - Determine rotation (if `fan` or `damper`).
5. **Register internally**: Use `add_component` for single items or `add_components_batch` for multiple.
   - Example: `add_component(component_type="fan", name="SF-1", coord=[10,5], rotation=180)`
   - Example: `add_component(component_type="damper", name="MD-1", coord=[12,5], rotation=90)`
   - Example: `add_component(component_type="variable_frequency_drive", name="VFD-1", coord=[15,6])`
6. **Sync to frontend**: Use `sync_agent_to_graphivac` to sync the HVAC equipments to the frontend.
7. **Exit**: Call `exit_with_success(summary="...")` to signal completion. The summary **must** include:
   - Number of equipment pieces placed
   - Confirmation that `sync_agent_to_graphivac` succeeded
   Example: "12 equipment pieces registered and synced to frontend (3 fans, 2 coils, 4 dampers, 1 filter, 2 sensors)"

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
