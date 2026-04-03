# Phase 22: enhance-bacnet-parsing - Research

**Researched:** 2026-04-03
**Domain:** BACnet metadata enrichment — URI formatting, ref_type classification, ontology skill updates
**Confidence:** HIGH

---

## Summary

Phase 22 enriches the per-point BACnet metadata dictionary written by the BACnet agent. Currently each `bacnet_N` entry holds `{address, name, unit}` where `address` is a raw BACnet address like `"2500.AI13"`. The phase adds two pre-computed fields — `code` (raw address preserved) and `address` (fully-formed BACnet URI) — plus a `ref_type` field that classifies each point as `"sensor"`, `"property"`, or `"skip"`. Skip-type points (PG, CO, TL) get `address: null`.

The work splits cleanly into two layers: (1) a Python helper function change in `agent/utils/bacnet_helpers.py` and its inlined copy in `mcp_server/graphivac/metadata_manager.py`, and (2) three SKILL.md prose updates telling the ontology agents to consume the pre-computed fields instead of parsing addresses manually.

Both copies of the helper must stay in sync (the MCP server and agent are separate packages). The ontology lessons skill already documents the address-parsing rules and BACnet suffix map — Phase 22 makes those agent-computed facts pre-baked into the stored dictionary so the ontology agents never need to reparse.

**Primary recommendation:** Extend `enrich_bacnet_point()` as a new pure function inside `bacnet_helpers.py`, call it from `explode_bacnet_points()`, and mirror the change in the MCP server inlined copy. Then update the three SKILL.md files to reference the new fields.

---

## Architecture Patterns

### Current Data Flow

```
BACnet agent reads CSV
  → builds {address: "2500.AI13", name: "...", unit: "..."}
  → calls update_component_metadata_batch({...})
  → explode_bacnet_points() produces bacnet_N flat entries
  → stored in component custom_fields as bacnet_N keys
  → ontology agent reads via read_internal_grid
  → ontology agent parses "2500.AI13" manually (per skill-ontology-lessons rules)
  → creates BACnetExternalReference("bacnet://2500/analog-input,13/present-value")
```

### Target Data Flow

```
BACnet agent reads CSV
  → builds {address: "2500.AI13", name: "...", unit: "..."}
  → calls update_component_metadata_batch({...})
  → explode_bacnet_points() → enrich_bacnet_point() per entry
  → stored as {code: "2500.AI13", address: "bacnet://2500/analog-input,13/present-value",
               name: "...", unit: "...", ref_type: "sensor"|"property"|"skip"}
  → ontology agent reads via read_internal_grid
  → ontology agent uses pre-computed address directly
  → no manual parsing needed
```

### Pattern 1: enrich_bacnet_point() pure function

**What:** Takes a raw `bacnet_N` dict and component type string; returns enriched dict.
**When to use:** Called from inside `explode_bacnet_points()` after each point is assembled.

```python
# In agent/utils/bacnet_helpers.py

BACNET_TYPE_MAP = {
    "AI": "analog-input",
    "AO": "analog-output",
    "AV": "analog-value",
    "BI": "binary-input",
    "BO": "binary-output",
    "BV": "binary-value",
    "SCH": "schedule",
}
SKIP_TYPES = {"PG", "CO", "TL"}

SENSOR_COMPONENT_TYPES = {
    "duct_sensor_enthalpy", "duct_sensor_temperature",
    "duct_sensor_differential_pressure", "duct_sensor_humidity",
    "duct_sensor_flow", "duct_sensor_low_limit", "duct_sensor_static_pressure",
    "pipe_sensor_temperature",
}

def enrich_bacnet_point(point: dict, component_type: str = "") -> dict:
    """
    Adds code, rewrites address to BACnet URI, and adds ref_type.
    point must already have 'address' key with raw address like '2500.AI13'.
    Returns a new dict (does not mutate input).
    """
    raw = point.get("address", "")
    enriched = dict(point)
    enriched["code"] = raw

    # Parse device and object type from raw address e.g. "2500.AI13"
    uri, ref_type = _parse_bacnet_address(raw, component_type)
    enriched["address"] = uri
    enriched["ref_type"] = ref_type
    return enriched


def _parse_bacnet_address(raw: str, component_type: str) -> tuple[str | None, str]:
    """
    Returns (uri, ref_type).
    uri is None for skip types. ref_type is 'sensor', 'property', or 'skip'.
    """
    if not raw or "." not in raw:
        return None, "skip"

    device, obj = raw.split(".", 1)
    # Extract alphabetic prefix from obj, e.g. "AI13" -> "AI", "13"
    import re
    m = re.match(r"([A-Za-z]+)(\d+)", obj)
    if not m:
        return None, "skip"

    type_code = m.group(1).upper()
    instance = m.group(2)

    if type_code in SKIP_TYPES:
        return None, "skip"

    obj_type = BACNET_TYPE_MAP.get(type_code)
    if not obj_type:
        return None, "skip"

    uri = f"bacnet://{device}/{obj_type},{instance}/present-value"
    ref_type = "sensor" if component_type in SENSOR_COMPONENT_TYPES else "property"
    return uri, ref_type
```

### Pattern 2: explode_bacnet_points() extended

The existing function signature stays identical. It now calls `enrich_bacnet_point()` on each assembled point. The `component_type` is threaded through so `ref_type` can be computed:

```python
def explode_bacnet_points(metadata: dict, component_type: str = "") -> dict:
    if "bacnet" not in metadata:
        return metadata
    result = {k: v for k, v in metadata.items() if k != "bacnet"}
    for i, (address, point) in enumerate(metadata["bacnet"].items(), start=1):
        raw_point = {"address": address, **point}
        result[f"bacnet_{i}"] = enrich_bacnet_point(raw_point, component_type)
    return result
```

**When bacnet_N entries are passed directly** (already flat, as is the case in the BACnet skill workflow since Phase 17), `explode_bacnet_points()` returns them unchanged. To enrich pre-flat entries, a second enrichment pass is needed at the write sites — OR the call site passes enriched dicts. See "Decisions" section below.

### Pattern 3: Write-site enrichment for flat bacnet_N input

Since Phase 17, the BACnet agent writes `bacnet_N` keys directly (no wrapping `bacnet` key). The `explode_bacnet_points()` no-op path is taken for already-flat entries. Therefore enrichment must also happen at the write sites inside `_apply_metadata()` and `update_component_metadata()`:

```python
# In metadata_tools.py _apply_metadata:
def _apply_metadata(value, metadata, k_cf):
    metadata = explode_bacnet_points(metadata)          # handles old nested format
    metadata = enrich_flat_bacnet_points(metadata)      # enriches already-flat bacnet_N entries
    ...

# New helper:
def enrich_flat_bacnet_points(metadata: dict, component_type: str = "") -> dict:
    """Enrich any bacnet_N entries that have 'address' but no 'code' field yet."""
    result = {}
    for key, val in metadata.items():
        if key.startswith("bacnet_") and isinstance(val, dict) and "address" in val and "code" not in val:
            result[key] = enrich_bacnet_point(val, component_type)
        else:
            result[key] = val
    return result
```

**Note:** The `component_type` is not stored in the top-level metadata dict at the write-path level (it is a property of the component in the internal grid). The caller knows the component type. For the ADK write path, `component_type` can be looked up from `tool_context.state["internal_grid"]` by component name before calling `_apply_metadata`. For the MCP server path, the same lookup is available from `mutable_grid` via the component's type field.

**Simpler alternative:** Have the BACnet agent pass pre-enriched dicts (call `enrich_bacnet_point()` in SKILL.md step 3 before calling `update_component_metadata_batch`). But this couples enrichment to the agent prompt, not the code — fragile. Keep enrichment in the Python layer.

### Pattern 4: SKILL.md updates

Three skills need updates:

1. **skill-ontology-generation/SKILL.md** — In "BACnet External References" section, add: use `bacnet_N.address` (pre-formed URI) and `bacnet_N.ref_type` directly; no address parsing needed. Keep the `BACnetExternalReference` pattern but feed it the pre-formed URI.

2. **skill-ontology-validation/SKILL.md** — In "BACnet External References" section, update to the same: if address field starts with `bacnet://`, use it directly; do not re-parse.

3. **skill-ontology-lessons/SKILL.md** — Update the "Address parsing" entry in "BACnet External References": note that starting with Phase 22, `address` in `bacnet_N` is already the fully-formed URI and `code` holds the original. The old parsing rules remain as fallback for legacy data.

### Anti-Patterns to Avoid

- **Double-enriching:** If `enrich_flat_bacnet_points()` checks for `"code" not in val`, it is idempotent. Don't enrich twice.
- **Breaking the inlined MCP copy:** Both `explode_bacnet_points` and `enrich_bacnet_point` must be mirrored in `mcp_server/graphivac/metadata_manager.py`. The comment in that file already warns about the sync requirement.
- **Changing the BACnet skill (skill-bacnet-points):** The BACnet agent just stores raw CSV data. It should continue to store the raw address in `address` for the agent, then the Python layer enriches it at write-time. The skill SKILL.md does NOT need to change.
- **ref_type based on object type suffix:** The phase description says ref_type is determined from the component's grid type (duct_sensor_* → "sensor"), NOT from the BACnet object suffix (AI/AO/etc.). Do not confuse these.

---

## File Map: What to Change

| File | Change | Notes |
|------|--------|-------|
| `agent/utils/bacnet_helpers.py` | Add `BACNET_TYPE_MAP`, `SKIP_TYPES`, `SENSOR_COMPONENT_TYPES` constants; add `_parse_bacnet_address()` and `enrich_bacnet_point()` functions; extend `explode_bacnet_points()` to call enrich; add `enrich_flat_bacnet_points()` | Primary implementation |
| `mcp_server/graphivac/metadata_manager.py` | Mirror all new helper functions as inlined copies; extend `_explode_bacnet_points()` similarly | Separate package boundary — cannot import from agent/ |
| `agent/tools/metadata_tools.py` | Call `enrich_flat_bacnet_points()` in `_apply_metadata()` | Enriches flat bacnet_N input at write time |
| `agent/tools/internal_grid_tools.py` | Pass `component_type` to enrichment at `update_component_metadata` and `update_component_metadata_batch` | Component type available from the component dict |
| `agent/skills/skill-ontology-generation/SKILL.md` | Update "BACnet External References" section | Use pre-formed `address` URI, note `ref_type` |
| `agent/skills/skill-ontology-validation/SKILL.md` | Update "BACnet External References" section | Same |
| `agent/skills/skill-ontology-lessons/SKILL.md` | Update "BACnet External References" address parsing lesson | Note pre-formed URI as of Phase 22 |
| `agent/tests/test_bacnet_helpers.py` | Add tests for `enrich_bacnet_point`, `_parse_bacnet_address`, `enrich_flat_bacnet_points`, and extended `explode_bacnet_points` | TDD — write tests first |

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| BACnet address regex | Custom regex per call site | `_parse_bacnet_address()` centralized | Single source of truth; DRY |
| Type-to-URI mapping | Hardcoded strings scattered | `BACNET_TYPE_MAP` dict constant | Easy to audit and extend |
| ref_type determination | Inline conditionals at each write site | `enrich_bacnet_point()` with `SENSOR_COMPONENT_TYPES` set | Consistent across ADK and MCP paths |

**Key insight:** The full suffix-to-URI logic already exists in `skill-ontology-lessons` as prose. Phase 22 simply moves it into executable Python so agents don't have to implement it.

---

## Common Pitfalls

### Pitfall 1: MCP server inlined copy drift

**What goes wrong:** `bacnet_helpers.py` is updated but `metadata_manager.py` inlined copy is not, causing different enrichment between MCP and ADK write paths.
**Why it happens:** The `NOTE:` comment in `metadata_manager.py` warns about this but it's easy to miss during review.
**How to avoid:** Update both files in the same plan. Add a test that asserts both produce the same output for canonical inputs.
**Warning signs:** Live test passes (ADK path) but MCP-path verification shows old format.

### Pitfall 2: component_type not available at enrichment call site

**What goes wrong:** `_apply_metadata()` in `metadata_tools.py` doesn't receive `component_type`, so `ref_type` always defaults to `"property"` even for sensors.
**Why it happens:** `_apply_metadata()` is a private helper that only receives `value` (the component dict) and `metadata`. The component type lives in the EDN grid value.
**How to avoid:** Extract `component_type` from the EDN component value before calling `_apply_metadata()`. In the mutable grid dict, the component type is stored under the `:type` Keyword (check how the EDN translator writes it, or use `value.get(Keyword("type"))` or the `k_type` key).
**Warning signs:** All BACnet points in ontology output have `ref_type: "property"` regardless of component type.

### Pitfall 3: Already-enriched bacnet_N entries re-processed

**What goes wrong:** If `enrich_flat_bacnet_points()` is not idempotent, running it twice corrupts `code` (overwriting the URI into `code`).
**Why it happens:** Batch write path may process the same component twice.
**How to avoid:** Guard: `if "code" not in val:` before enriching. Once `code` is set, the entry is already enriched.

### Pitfall 4: SCH suffix ignored in skip list

**What goes wrong:** SCH (schedule) points are not in SKIP_TYPES but `BACNET_TYPE_MAP` maps them. The phase description says SCH is valid. Don't add SCH to SKIP_TYPES.
**Why it happens:** Phase description says "For invalid BACnet object types (PG, CO, TL): set address to null". SCH is explicitly listed in the suffix map as valid.
**How to avoid:** Only PG, CO, TL → skip. SCH → `bacnet://device/schedule,N/present-value`, ref_type based on component type (likely "property" for schedules).

### Pitfall 5: skill-bacnet-points SKILL.md modified unnecessarily

**What goes wrong:** Changing the BACnet agent skill to call enrichment functions breaks the clean separation.
**Why it happens:** Misreading the phase description as requiring skill-bacnet-points to be updated.
**How to avoid:** The phase description says "update the three ontology skills". The BACnet skill stays unchanged — it writes raw data, Python enriches it.

---

## Code Examples

### Suffix map and skip set

```python
# Source: skill-ontology-lessons BACnet External References section + phase description
BACNET_TYPE_MAP = {
    "AI": "analog-input",
    "AO": "analog-output",
    "AV": "analog-value",
    "BI": "binary-input",
    "BO": "binary-output",
    "BV": "binary-value",
    "SCH": "schedule",
}
SKIP_TYPES = {"PG", "CO", "TL"}
```

### Expected output for a sensor component

```python
# Input (from BACnet agent, component type "duct_sensor_temperature"):
{
  "address": "2500.AI13",
  "name": "TEMP. ALIM. No.1A",
  "unit": "Celsius"
}

# After enrich_bacnet_point(point, "duct_sensor_temperature"):
{
  "code": "2500.AI13",
  "address": "bacnet://2500/analog-input,13/present-value",
  "name": "TEMP. ALIM. No.1A",
  "unit": "Celsius",
  "ref_type": "sensor"
}
```

### Expected output for skip type

```python
# Input:
{
  "address": "2500.PG5",
  "name": "PROGRAMME 5",
  "unit": ""
}

# After enrich_bacnet_point(point, "fan"):
{
  "code": "2500.PG5",
  "address": None,
  "name": "PROGRAMME 5",
  "unit": "",
  "ref_type": "skip"
}
```

### Expected output for equipment property

```python
# Input (component type "fan"):
{
  "address": "2500.AO6",
  "name": "MOD. DRIVE ALM No.1A",
  "unit": "Percent"
}

# After enrich_bacnet_point(point, "fan"):
{
  "code": "2500.AO6",
  "address": "bacnet://2500/analog-output,6/present-value",
  "name": "MOD. DRIVE ALM No.1A",
  "unit": "Percent",
  "ref_type": "property"
}
```

### Ontology skill instruction update (generation SKILL.md)

The current text in "BACnet External References":
> See `skill-ontology-lessons` (section "BACnet External References") for the full address-parsing rules, type suffix map, and code patterns.

Updated text:
> As of Phase 22, each `bacnet_N` entry in `custom_fields` contains pre-computed fields:
> - `code` — the original raw BACnet address (e.g. `"2500.AI13"`)
> - `address` — the fully-formed BACnet URI (e.g. `"bacnet://2500/analog-input,13/present-value"`) or `null` for skip types
> - `ref_type` — `"sensor"`, `"property"`, or `"skip"`
>
> Use `bacnet_N.address` directly when constructing `BACnetExternalReference`. Skip entries where `bacnet_N.ref_type == "skip"` or `bacnet_N.address is null`. No manual address parsing is needed.

---

## Validation Architecture

nyquist_validation key is absent from `.planning/config.json` — treat as enabled.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (agent/.venv/bin/python -m pytest) |
| Config file | none (discovery-based) |
| Quick run command | `cd agent && .venv/bin/python -m pytest tests/test_bacnet_helpers.py -q` |
| Full suite command | `cd agent && .venv/bin/python -m pytest tests/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| P22-01 | `enrich_bacnet_point` adds `code` field with raw address | unit | `pytest tests/test_bacnet_helpers.py -k "enrich"` | ❌ Wave 0 |
| P22-02 | `enrich_bacnet_point` rewrites `address` to BACnet URI | unit | `pytest tests/test_bacnet_helpers.py -k "uri"` | ❌ Wave 0 |
| P22-03 | `enrich_bacnet_point` sets `ref_type="sensor"` for sensor component types | unit | `pytest tests/test_bacnet_helpers.py -k "ref_type"` | ❌ Wave 0 |
| P22-04 | `enrich_bacnet_point` sets `ref_type="property"` for non-sensor types | unit | `pytest tests/test_bacnet_helpers.py -k "ref_type"` | ❌ Wave 0 |
| P22-05 | PG/CO/TL addresses produce `address=None, ref_type="skip"` | unit | `pytest tests/test_bacnet_helpers.py -k "skip"` | ❌ Wave 0 |
| P22-06 | `enrich_flat_bacnet_points` is idempotent (code present → no re-enrich) | unit | `pytest tests/test_bacnet_helpers.py -k "idempotent"` | ❌ Wave 0 |
| P22-07 | Suffix map covers all 7 valid types (AI AO AV BI BO BV SCH) | unit | `pytest tests/test_bacnet_helpers.py -k "suffix_map"` | ❌ Wave 0 |
| P22-08 | SKILL.md files updated (grep check) | manual | manual read/review | n/a |

### Sampling Rate

- **Per task commit:** `cd /home/juan/codes/si-mapper/agent && .venv/bin/python -m pytest tests/test_bacnet_helpers.py -q`
- **Per wave merge:** `cd /home/juan/codes/si-mapper/agent && .venv/bin/python -m pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_bacnet_helpers.py` — extend with enrich tests (file exists, add new test functions)
- [ ] No new test files needed — all helper tests go in existing `test_bacnet_helpers.py`

---

## Sources

### Primary (HIGH confidence)

- Direct code reading of `agent/utils/bacnet_helpers.py` — current helper signature and tests
- Direct code reading of `agent/tools/internal_grid_tools.py` — SENSOR_TYPES, EQUIPMENT_TYPES constants
- Direct code reading of `mcp_server/graphivac/metadata_manager.py` — inlined copy and sync comment
- Direct code reading of `agent/tools/metadata_tools.py` — `_apply_metadata` write path
- `agent/skills/skill-ontology-lessons/SKILL.md` — authoritative BACnet suffix map and skip types
- Phase description — ref_type logic and field specs

### Secondary (MEDIUM confidence)

- `agent/tests/test_bacnet_helpers.py` — TDD patterns to follow (6 existing tests, all passing)
- `agent/skills/skill-ontology-generation/SKILL.md`, `skill-ontology-validation/SKILL.md` — current BACnet reference section wording

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — no new libraries; pure Python string manipulation + existing helpers
- Architecture: HIGH — all write paths, type sets, and inlining constraints directly observed from source
- Pitfalls: HIGH — MCP sync issue documented in source code comment; component_type availability verified by reading both write paths
- SKILL.md changes: HIGH — current wording read directly; target wording follows established Phase 16/18 patterns

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (stable internal codebase, no external dependencies)
