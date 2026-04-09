---
name: skill-ductwork
description: Specialized instructions for identifying and drawing the ductwork for HVAC systems.
---

# Ductwork skill

Identify and replicate all **horizontal and vertical ducts** in HVAC drawings as authoritative spatial anchors.


# Execution Flow

## 1. Ingest Context
- Use `sync_graphivac_to_agent` to synchronize the agent's internal state with the current frontend grid. This ensures any changes the user made on the frontend are captured before analysis begins.
- Use `ingest_category_files(category='hvac')`.
- Use `load_artifacts` to access drawing artifacts. **Remember which artifact names contain the reference drawings.**
- Use `read_internal_grid` to retrieve existing components

## 2. Analyze

### Horizontal Ducts
- Count chevron starts for exact duct count
- Check legends for duct symbols and flow arrows
- Identify vertical ordering (top to bottom)
- Map horizontal spans: (x1, y) → (x2, y)
- Determine airflow direction:
  - 'Σ>' → left-to-right
  - '<Σ' → right-to-left

### Vertical Ducts
- Identify vertical spans: (x, y1) → (x, y2)
- Ensure both endpoints connect to horizontal ducts
- Confirm alignment at same x-coordinate
- Vertical ducts are rare → validate carefully


## 3. Register findings internally

Register ALL ducts (horizontal and vertical) in a **single call** to `add_components_batch`.

### Naming Convention
- Horizontal ducts: `HD-1`, `HD-2`, ..., numbered from top to bottom.
- Vertical ducts: `VD-1`, `VD-2`, ..., numbered from left to right.

### How to call `add_components_batch`

Even though the parameter is named `components_json`, **write the value as a plain JSON array in your tool call — do not manually escape or stringify it**. The framework handles serialization automatically.

Correct tool call:
```json
{
  "components_json": [
    {"type": "duct", "name": "HD-1", "start_coord": [5, 5], "end_coord": [15, 5]},
    {"type": "duct", "name": "VD-1", "start_coord": [15, 5], "end_coord": [15, 10]}
  ]
}
```

❌ Wrong — do NOT manually escape it into a string:
```json
{
  "components_json": "[{\"type\": \"duct\", \"name\": \"HD-1\", ...}]"
}
```

Use "duct" as the type for all entries. Ensure `start_coord` and `end_coord` reflect true airflow direction as explained in the "Duct Continuity Rules" section.

## 4. Send ductwork to the frontend

Call the tool `sync_agent_to_graphivac` to send the ductwork to the frontend.

## 5. Exit
Call `exit_with_success(summary="...")` to signal completion. The summary **must** include:
- Number of ducts registered (horizontal and vertical counts)
- Confirmation that `sync_agent_to_graphivac` succeeded
Example: "5 ducts registered and synced to frontend (4 horizontal, 1 vertical)"


# Rules

## What to Identify

### Horizontal Ducts
- Only horizontal duct segments
- Each distinct horizontal track = separate duct
- Ducts continue through inline equipment (filters, coils, fans, mixing boxes)

### Vertical Ducts
- Only vertical duct segments that connect two horizontal ducts
- Vertical ducts must start in a horizontal duct and end in a horizontal duct
- Vertical ducts occur at a constant x-coordinate

## Duct Continuity Rules

### What Ends a Horizontal Duct
- Arrow mark '>' (left-to-right flow endpoint)
- Arrow mark '<' (right-to-left flow endpoint)
- 90-degree turn into a vertical duct

### What Does NOT End a Horizontal Duct
- Inline equipment
- Vertical branches
- Mixing sections
- Junction boxes


# Common Errors to Avoid
General
❌ Treating multiple parallel tracks as one duct
❌ Misaligning coordinates with drawing geometry
❌ Inconsistent span direction vs airflow

Horizontal-Specific
❌ Including vertical segments
❌ Segmenting at inline equipment or junctions
❌ Breaking ducts at vertical branches

Vertical-Specific
❌ Including horizontal segments
❌ Creating vertical ducts not connected to horizontal ducts
❌ Misplacing x-coordinate alignment
❌ Over-detecting (vertical ducts are rare)
