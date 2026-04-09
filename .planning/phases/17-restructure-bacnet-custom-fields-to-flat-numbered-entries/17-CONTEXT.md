# Phase 17: Restructure BACnet Custom Fields to Flat Numbered Entries - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning
**Source:** Conversation context capture

<domain>
## Phase Boundary

Replace the current `{"bacnet": {"ADDR": {...}}}` custom_fields structure with a flat, numbered format where each BACnet point gets its own top-level key (`bacnet_1`, `bacnet_2`, ...) containing `{"address": "...", "unit": "...", "name": "..."}`.

This affects every layer that reads or writes BACnet metadata: internal grid tools, MCP metadata manager, ADK metadata tools, the EDN translator, and the BACnet skill documentation.

</domain>

<decisions>
## Implementation Decisions

### New Data Structure

**Old format:**
```json
{
  "custom_fields": {
    "bacnet": {
      "2500.BV1": {"unit": "On/Off", "name": "STATUT DIG 1E"},
      "2500.BO11": {"unit": "On/Off", "name": "CMD DIG 1E"}
    }
  }
}
```

**New format:**
```json
{
  "custom_fields": {
    "bacnet_1": {"address": "2500.BV1", "unit": "On/Off", "name": "STATUT DIG 1E"},
    "bacnet_2": {"address": "2500.BO11", "unit": "On/Off", "name": "CMD DIG 1E"}
  }
}
```

### No Backward Compatibility
- No migration layer. No backward-compatible reading of old `"bacnet"` key.
- If old data is encountered, the code should break — this is intentional.
- After this change, the BACnet skill must be re-run to rewrite existing grid data.

### Explosion Logic Location
- A shared `explode_bacnet_points(metadata: dict) -> dict` helper converts `{"bacnet": {...}}` → `{"bacnet_1": {...}, "bacnet_2": {...}, ...}` at write time.
- This helper must be called at both write paths (ADK direct path and MCP path) to avoid duplication.

### Numbering Convention
- Keys are `bacnet_1`, `bacnet_2`, ... (1-indexed, no zero padding).
- Order follows dict insertion order (Python 3.7+ guarantee).

### Address Field
- BACnet address (e.g. `"2500.BV1"`) moves from being the dict key to a field named `"address"` inside each entry.

### Files to Change
Two parallel write paths, both must be updated:

**Path 1 — Internal Grid → Sync:**
- `agent/tools/internal_grid_tools.py` — `update_component_metadata()` and `update_component_metadata_batch()`: apply explosion before storing in `component["custom_fields"]`
- `agent/utils/grid_edn_translator.py` — `edn_comps_to_internal_grid()` (deserialization) and `internal_grid_to_edn_comps()` (serialization): handle flat `bacnet_N` keys, no special `"bacnet"` key logic

**Path 2 — Direct MCP write:**
- `agent/tools/metadata_tools.py` — `_apply_metadata()`: explode before merging into `:custom-fields`
- `mcp_server/graphivac/metadata_manager.py` — `write_metadata()` and `write_metadata_batch()`: explode before JSON-stringify and store

**Skill docs (read by AI agents — must reflect new format):**
- `agent/skills/skill-bacnet-points/SKILL.md` — update example structures, input format, and `update_component_metadata_batch()` call signature

**Tests:**
- `agent/tests/test_write_metadata_batch_live.py` — update `SAMPLE_BACNET_POINTS` and verification logic to use new flat structure

### Claude's Discretion
- Where to define the `explode_bacnet_points` helper (suggested: a shared utility in `agent/utils/` or inline in `_apply_metadata` if simpler)
- Whether to add a matching `collect_bacnet_points()` inverse helper for read paths (only if needed for a clean round-trip)
- Exact test assertion patterns for the new structure

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Write paths
- `agent/tools/internal_grid_tools.py` — internal grid metadata write (update_component_metadata, update_component_metadata_batch)
- `agent/tools/metadata_tools.py` — ADK direct write path (_apply_metadata, write_metadata, write_metadata_batch)
- `mcp_server/graphivac/metadata_manager.py` — MCP server write path (write_metadata, write_metadata_batch)

### Translator (serialization layer)
- `agent/utils/grid_edn_translator.py` — bidirectional EDN↔internal grid conversion, handles custom_fields

### Skill documentation (consumed by AI coding agents)
- `agent/skills/skill-bacnet-points/SKILL.md` — BACnet extraction and mapping workflow

### Tests
- `agent/tests/test_write_metadata_batch_live.py` — live integration test for metadata writes

</canonical_refs>

<specifics>
## Specific Ideas

The `explode_bacnet_points` helper signature:
```python
def explode_bacnet_points(metadata: dict) -> dict:
    """
    Converts {"bacnet": {"ADDR": {"name": ..., "unit": ...}}}
    into     {"bacnet_1": {"address": "ADDR", "name": ..., "unit": ...}, ...}
    All other keys in metadata pass through unchanged.
    """
    if "bacnet" not in metadata:
        return metadata
    result = {k: v for k, v in metadata.items() if k != "bacnet"}
    for i, (address, point) in enumerate(metadata["bacnet"].items(), start=1):
        result[f"bacnet_{i}"] = {"address": address, **point}
    return result
```

The skill-bacnet-points example batch call changes from:
```json
{
  "AHU-1": {
    "bacnet": {
      "2500.AI11": {"name": "VITESSE RET. No.1A", "unit": "Amperes"}
    }
  }
}
```
to:
```json
{
  "AHU-1": {
    "bacnet_1": {"address": "2500.AI11", "name": "VITESSE RET. No.1A", "unit": "Amperes"}
  }
}
```

</specifics>

<deferred>
## Deferred Ideas

- A `collect_bacnet_points()` inverse (reads `bacnet_N` keys back into a single dict) — defer unless a read path actually needs it
- Renaming existing GraphyVAC grid data in place — out of scope; re-run skill after this change

</deferred>

---

*Phase: 17-restructure-bacnet-custom-fields-to-flat-numbered-entries*
*Context gathered: 2026-04-03 from conversation*
