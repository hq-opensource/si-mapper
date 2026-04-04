---
name: skill-ductwork
description: Specialized instructions for identifying and drawing the ductwork for HVAC systems.
---

# Ductwork skill

Identify and replicate all **horizontal and vertical ducts** in HVAC drawings as authoritative spatial anchors.


# Execution Flow

## 1. Ingest Context
- Use `ingest_category_files(category='hvac')`. **Note the artifact names returned** — you will need them in the verification step.
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

### JSON Structure
Use "duct" as the type for all entries
Ensure start_coord and end_coord reflect true airflow direction as explained in the "Duct Continuity Rules" section.

```json
[
  {
    "type": "duct",
    "name": "HD-1",
    "start_coord": [5, 5],
    "end_coord": [15, 5]
  },
  {
    "type": "duct",
    "name": "VD-1",
    "start_coord": [15, 5],
    "end_coord": [15, 10]
  }
]
```

## 4. Send ductwork to the frontend

Call the tool `sync_agent_to_graphivac` to send the ductwork to the frontend.

## 5. Verify the ductwork
After calling the tool `sync_agent_to_graphivac`, perform a **Duct Verification Checkpoint**:
- Call `capture_frontend_state()` to take the screenshot.
- Then call `load_artifacts` passing **both** the snapshot and the original reference drawing artifact name(s) in a single call — for example: `load_artifacts(artifact_names=["verification/latest_snapshot.png", "hvac/<reference_drawing_filename>"])`. Use the artifact names you noted in Step 1.
- Compare the snapshot against the reference image side-by-side. Verify that all horizontal and vertical ducts are present, correctly positioned, and flow directions are correct.
- If discrepancies are found, correct them by calling the tool `add_components_batch` or `delete_components_batch`.
- After all corrections are finished, call `sync_agent_to_graphivac` again and repeat the checkpoint instructions until the ducts match the reference.

## 6. Exit
Call `exit_with_success(summary="...")` to signal completion. The summary **must** include:
- Number of ducts registered (horizontal and vertical counts)
- Number of corrections made during verification
- Final verification result (pass/fail)

**Failure path:** If verification cannot be resolved after 3 correction cycles, call `exit_with_failure(reason="...")` explaining the unresolvable discrepancies.


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
