---
name: skill-horizontal-ducts
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

## Execution Flow

### 1. Ingest Context & Initialization
- You will be provided with drawing artifacts. Use the available tool `load_artifacts` to view them if they are not already in context.
- Use the `initialize_internal_grid` tool to ensure the internal state is ready.

### 2. Analyze
- Count chevron starts for exact duct count
- Check legends for duct symbols and flow arrows
- Identify vertical track ordering (top to bottom)
- Map horizontal spans: (x1, y1) to (x2, y1) where y1 indicates the vertical position of the duct
- Verify the airflow direction of each duct using the chevron-tail style mark 'Σ', and the arrow style marks '<' and '>' symbols. 'Σ>' for left-to-right flow, '<Σ' for right-to-left flow.

### 3. Register Findings
Register all your findings using the `add_components_batch` tool. The `components_json` argument must be a JSON array of objects with the following structure:

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
    "name": "HD-2",
    "start_coord": [20, 10],
    "end_coord": [5, 10]
  }
]
```

You MUST call the `add_components_batch` tool with all your findings at once. Use "duct" as the `type` for all horizontal ducts.

---

## Common Errors to Avoid
- ❌ Segmenting at junctions or inline equipment
- ❌ Treating stacked parallel tracks as one duct
- ❌ Including vertical segments
- ❌ Registering pre/post equipment spans separately
- ❌ Describing span order inconsistently with flow direction