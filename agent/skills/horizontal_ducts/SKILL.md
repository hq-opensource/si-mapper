---
name: horizontal_ducts
description: Specialized instructions for identifying and drawing horizontal ducts for HVAC systems.
---

# Horizontal Ducts skill

Identify and list all **horizontal ducts** in HVAC drawings as authoritative spatial anchors.

---

## Rules

### What to Identify
- **Only horizontal duct segments** (ignore vertical portions)
- Each distinct horizontal track = separate duct (even if functionally similar)
- Ducts continue through inline equipment (filters, coils, fans, mixing boxes)

### How a Duct Ends
- The arrow style mark '>' for left-to-right air flow.
- The arrow style mark '<' for right-to-left air flow.
- **90-degree turn to vertical** (horizontal ends, vertical begins)

### What Does NOT End a Duct
- Inline equipment
- Vertical branches tapping off
- Mixing sections (treat as continuation)
- Junction boxes

---

## Coordinate System
- Origin (0,0) = **top-left**
- End (30,15) = **bottom-right**
- X-axis: 0 (left) → 30 (right)
- Y-axis: 0 (top) → 15 (bottom)

## Flow Direction Convention
- Left-to-right flow: Span as ascending x coordinates (e.g., "5 to 15 X-axis")
- Right-to-left flow: Span as descending x coordinates (e.g., "15 to 5 X-axis")
- This convention uses span order to encode flow direction

---

## Execution Flow

### 1. Ingest Context
You will be provided with drawing artifacts. Use the available tool `load_artifacts` to view them if they are not already in context.

### 2. Analyze
- Count chevron starts for exact duct count
- Check legends for duct symbols and flow arrows
- Identify vertical track ordering (top to bottom)
- Map horizontal spans: (x1, y1) to (x2, y1) where y1 indicates the vertical position of the duct
- Verify the airflow direction of each duct using the chevron-tail style mark 'Σ', and the arrow style marks '<' and '>' symbols. 'Σ>' for left-to-right flow, '<Σ' for right-to-left flow.

### 3. Register Findings
Register all your findings using the following json structure:
```json
{
  "horizontal_ducts": {
    "duct_name_1": {"start": [5,5], "end": [15,5]},
    "duct_name_2": {"start": [20,10], "end": [5,10]}
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
Example: `exit_loop_level_4(summary="I identified and registered 12 horizontal ducts flowing left-to-right via batch tool.")`

---

## Common Errors to Avoid
- ❌ Segmenting at junctions or inline equipment
- ❌ Treating stacked parallel tracks as one duct
- ❌ Including vertical segments
- ❌ Registering pre/post equipment spans separately
- ❌ Describing span order inconsistently with flow direction