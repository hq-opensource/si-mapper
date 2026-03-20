---
name: skill-vertical-ducts
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


## Execution Flow

### 1. Ingest Context & Grid Awareness
- You will be provided with drawing artifacts. Use the available tool `load_artifacts` to view them if they are not already in context.
- Use the `initialize_internal_grid` tool to ensure the internal state is ready.
- Use the `read_internal_grid` tool to retrieve the current state of the grid. 
    - You will see a list of components. 
    - Horizontal ducts will have `type: "duct"` and provide coordinates via `start` and `end` keys (e.g., `{"start": [x1,y1], "end": [x2,y2]}`). Use the start and end coordinates to identify the direction of the flow: 
        - If x1 < x2, the flow is from left to right
        - If x1 > x2, the flow is from right to left
    - Other components like fans or room baseboards will have their own types (e.g., `type: "fan"`) and a `coord`.

### 2. Analyze
- Match each vertical duct track between the drawing image and the digital twin.
- Identify vertical spans of the ducts: (x, y1) to (x, y2), where y1 and y2 are the y-coordinates of the horizontal ducts that the vertical duct connects to.
- Vertical ducts enter and exit the horizontal ducts at the same x coordinate
- Vertical ducts are rare. Therefore, there is usually only few vertical ducts in each design, so be careful not to misidentify components as vertical ducts.

### 3. Register Findings
Register all your findings using the `add_components_batch` tool. The `components_json` argument must be a JSON array of objects with the following structure:

```json
[
  {
    "type": "duct",
    "name": "VD-1",
    "start_coord": [15, 5],
    "end_coord": [15, 10]
  },
  {
    "type": "duct",
    "name": "VD-2",
    "start_coord": [25, 12],
    "end_coord": [25, 2]
  }
]
```

You MUST call the `add_components_batch` tool with all your findings at once. Use "duct" as the `type` for all vertical ducts.


---

## Common Errors to Avoid
- ❌ Including horizontal segments
- ❌ Treating stacked parallel tracks as one duct
- ❌ Ignoring source/destination connections
- ❌ Describing span order inconsistently with flow direction
