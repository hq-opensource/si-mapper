---
name: vertical-ducts
description: Specialized instructions for identifying and drawing vertical ducts for HVAC systems.
---

# Vertical Ducts Skill

Identify and list all **vertical ducts** in HVAC drawings that connect two horizontal ducts.

---

## Rules

### What to Identify
- Only vertical duct segments that connect two horizontal tracks
- Vertical ducts start in a horizontal duct 
- Vertical ducts end in a horizontal duct

---

## Coordinate System
- Origin (0,0) = **top-left**
- End (30,15) = **bottom-right**
- X-axis: 0 (left) → 30 (right)
- Y-axis: 0 (top) → 15 (bottom)

---

## Execution Flow

### 1. Ingest Context & Grid Awareness
- You will be provided with drawing artifacts. Use the available tool `load_artifacts` to view them if they are not already in context.
- Use the `read_grid` tool to retrieve the current state of the grid. 
    - You will see a list of components. 
    - Horizontal ducts will have `type: "duct"` and provide coordinates via `start` and `end` keys (e.g., `{"start": [x1,y1], "end": [x2,y2]}`). Use the start and end coordinates to identify the direction of the flow: 
        - If x1 < x2, the flow is from left to right
        - If x1 > x2, the flow is from right to left
    - Other components like fans or room baseboards will have their own types (e.g., `type: "fan"`) and a `position`.

### 2. Analyze
- Match each vertical duct track between the drawing image and the digital twin.
- Identify vertical spans of the ducts: (x, y1) to (x, y2), where y1 and y2 are the y-coordinates of the horizontal ducts that the vertical duct connects to.
- Vertical ducts enter and exit the horizontal ducts at the same x coordinate
- Vertical ducts are rare. Therefore, there is usually only few vertical ducts in each design, so be careful not to misidentify components as vertical ducts.

### 3. Register Findings
Register all your findings using the following json structure:
```json
{
  "vertical_ducts": {
    "duct_name_1": {"start": [15,5], "end": [15,10]},
    "duct_name_2": {"start": [25,12], "end": [25,2]}
  }
}
```
You MUST call the `create_ducts_batch` tool with all your findings at once.

### 4. Output
Return the findings as a JSON object summary. 
If no ducts are found, return `{"horizontal_ducts": {}}`.


### 5. Exit
After calling `create_ducts_batch`, you MUST call the `exit_loop_level_4` tool.
**CRITICAL**: You MUST provide a `summary` argument to `exit_loop_level_4` describing exactly what you did.
Example: `exit_loop_level_4(summary="I identified and registered 8 vertical ducts via batch tool.")`

---

## Common Errors to Avoid
- ❌ Including horizontal segments
- ❌ Treating stacked parallel tracks as one duct
- ❌ Ignoring source/destination connections
- ❌ Describing span order inconsistently with flow direction
