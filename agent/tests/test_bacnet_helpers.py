"""
Unit tests for agent/utils/bacnet_helpers.py — explode_bacnet_points helper.
"""
import pytest
from utils.bacnet_helpers import (
    explode_bacnet_points,
    enrich_bacnet_point,
    enrich_flat_bacnet_points,
    BACNET_TYPE_MAP,
    SKIP_TYPES,
)


# ── Test 1: Two-point bacnet dict produces bacnet_1 and bacnet_2 ───────────────

def test_two_points_produces_bacnet_1_and_bacnet_2():
    metadata = {
        "bacnet": {
            "2500.BV1": {"unit": "On/Off", "name": "STATUT DIG 1E"},
            "2500.BO11": {"unit": "On/Off", "name": "CMD DIG 1E"},
        }
    }
    result = explode_bacnet_points(metadata)
    assert "bacnet_1" in result
    assert "bacnet_2" in result
    assert "bacnet" not in result
    # explode_bacnet_points now enriches: address→URI, raw address preserved as code
    assert result["bacnet_1"]["code"] == "2500.BV1"
    assert result["bacnet_1"]["address"] == "bacnet://2500/binary-value,1/present-value"
    assert result["bacnet_1"]["unit"] == "On/Off"
    assert result["bacnet_1"]["name"] == "STATUT DIG 1E"
    assert result["bacnet_2"]["code"] == "2500.BO11"
    assert result["bacnet_2"]["address"] == "bacnet://2500/binary-output,11/present-value"


# ── Test 2: No "bacnet" key returns metadata unchanged ─────────────────────────

def test_no_bacnet_key_returns_unchanged():
    metadata = {"control": "value", "other": 42}
    result = explode_bacnet_points(metadata)
    assert result == {"control": "value", "other": 42}
    assert result is metadata  # same object, no copy needed


# ── Test 3: Mixed keys — bacnet key and other keys preserved ───────────────────

def test_other_keys_preserved_alongside_bacnet():
    metadata = {
        "control": "on",
        "bacnet": {
            "2500.AI11": {"unit": "Amperes", "name": "VITESSE RET."},
        },
        "notes": "test",
    }
    result = explode_bacnet_points(metadata)
    assert "bacnet" not in result
    assert result["control"] == "on"
    assert result["notes"] == "test"
    assert "bacnet_1" in result
    # explode_bacnet_points now enriches: raw address preserved as code
    assert result["bacnet_1"]["code"] == "2500.AI11"
    assert result["bacnet_1"]["address"] == "bacnet://2500/analog-input,11/present-value"


# ── Test 4: Empty "bacnet" dict removes the key, no bacnet_N keys added ────────

def test_empty_bacnet_dict_removes_key():
    metadata = {"bacnet": {}}
    result = explode_bacnet_points(metadata)
    assert "bacnet" not in result
    assert not any(k.startswith("bacnet_") for k in result)


# ── Test 5: Single-point bacnet dict produces only bacnet_1 ───────────────────

def test_single_point_produces_only_bacnet_1():
    metadata = {
        "bacnet": {
            "2500.AI11": {"unit": "Amperes", "name": "VITESSE RET. No.1A"},
        }
    }
    result = explode_bacnet_points(metadata)
    assert list(k for k in result if k.startswith("bacnet_")) == ["bacnet_1"]
    # explode_bacnet_points now enriches: raw address preserved as code
    assert result["bacnet_1"]["code"] == "2500.AI11"
    assert result["bacnet_1"]["address"] == "bacnet://2500/analog-input,11/present-value"
    assert result["bacnet_1"]["unit"] == "Amperes"
    assert result["bacnet_1"]["name"] == "VITESSE RET. No.1A"


# ── Test 6: address field matches the original dict key ───────────────────────

def test_address_field_matches_original_key():
    addr_a = "2500.BV1"
    addr_b = "2500.BO11"
    metadata = {
        "bacnet": {
            addr_a: {"unit": "On/Off", "name": "STATUT"},
            addr_b: {"unit": "On/Off", "name": "CMD"},
        }
    }
    result = explode_bacnet_points(metadata)
    # explode_bacnet_points now enriches: raw address preserved as code
    assert result["bacnet_1"]["code"] == addr_a
    assert result["bacnet_2"]["code"] == addr_b


# ── New enrichment tests ──────────────────────────────────────────────────────

def test_enrich_sensor_point():
    """Sensor component type produces ref_type='sensor' and correct URI."""
    result = enrich_bacnet_point(
        {"address": "2500.AI13", "name": "TEMP", "unit": "Celsius"},
        "duct_sensor_temperature",
    )
    assert result == {
        "code": "2500.AI13",
        "address": "bacnet://2500/analog-input,13/present-value",
        "name": "TEMP",
        "unit": "Celsius",
        "ref_type": "sensor",
    }


def test_enrich_property_point():
    """Non-sensor component type produces ref_type='property'."""
    result = enrich_bacnet_point(
        {"address": "2500.AO6", "name": "MOD", "unit": "Percent"},
        "fan",
    )
    assert result["ref_type"] == "property"
    assert result["address"] == "bacnet://2500/analog-output,6/present-value"
    assert result["code"] == "2500.AO6"


def test_enrich_skip_PG():
    """PG address type yields address=None and ref_type='skip'."""
    result = enrich_bacnet_point(
        {"address": "2500.PG5", "name": "PROG", "unit": ""},
        "fan",
    )
    assert result["code"] == "2500.PG5"
    assert result["address"] is None
    assert result["ref_type"] == "skip"


def test_enrich_skip_CO():
    """CO address type yields address=None and ref_type='skip'."""
    result = enrich_bacnet_point({"address": "2500.CO3", "name": "X"}, "fan")
    assert result["address"] is None
    assert result["ref_type"] == "skip"


def test_enrich_skip_TL():
    """TL address type yields address=None and ref_type='skip'."""
    result = enrich_bacnet_point({"address": "2500.TL1", "name": "X"}, "fan")
    assert result["address"] is None
    assert result["ref_type"] == "skip"


def test_enrich_empty_address():
    """Empty address yields address=None and ref_type='skip'."""
    result = enrich_bacnet_point({"address": "", "name": "X"}, "")
    assert result["address"] is None
    assert result["ref_type"] == "skip"


def test_enrich_no_dot_address():
    """Address without a dot yields address=None and ref_type='skip'."""
    result = enrich_bacnet_point({"address": "NODOT", "name": "X"}, "")
    assert result["address"] is None
    assert result["ref_type"] == "skip"


def test_enrich_schedule_type():
    """SCH address type produces schedule URI."""
    result = enrich_bacnet_point({"address": "2500.SCH4", "name": "S"}, "fan")
    assert result["address"] == "bacnet://2500/schedule,4/present-value"


def test_enrich_all_suffix_map():
    """BACNET_TYPE_MAP has exactly 7 entries."""
    assert len(BACNET_TYPE_MAP) == 7
    assert set(BACNET_TYPE_MAP.keys()) == {"AI", "AO", "AV", "BI", "BO", "BV", "SCH"}


def test_enrich_BV_binary_value():
    """BV address type produces binary-value URI."""
    result = enrich_bacnet_point({"address": "2500.BV1", "name": "X"}, "fan")
    assert result["address"] == "bacnet://2500/binary-value,1/present-value"


def test_enrich_BI_binary_input():
    """BI address type produces binary-input URI."""
    result = enrich_bacnet_point({"address": "2500.BI3", "name": "X"}, "fan")
    assert result["address"] == "bacnet://2500/binary-input,3/present-value"


def test_enrich_does_not_mutate_input():
    """enrich_bacnet_point does not mutate the original input dict."""
    original = {"address": "2500.AI13", "name": "TEMP", "unit": "Celsius"}
    original_copy = dict(original)
    enrich_bacnet_point(original, "duct_sensor_temperature")
    assert original == original_copy


def test_enrich_flat_bacnet_points_enriches_unenriched():
    """enrich_flat_bacnet_points enriches bacnet_N entries without 'code', passes other keys through."""
    data = {
        "bacnet_1": {"address": "2500.AI13", "name": "T"},
        "control": "on",
    }
    result = enrich_flat_bacnet_points(data)
    assert "code" in result["bacnet_1"]
    assert result["bacnet_1"]["code"] == "2500.AI13"
    assert result["bacnet_1"]["ref_type"] == "property"
    assert result["control"] == "on"


def test_enrich_flat_bacnet_points_idempotent():
    """Entry with 'code' already present is NOT re-enriched."""
    already_enriched = {
        "address": "bacnet://2500/analog-input,13/present-value",
        "code": "2500.AI13",
        "name": "T",
        "ref_type": "sensor",
    }
    data = {"bacnet_1": already_enriched}
    result = enrich_flat_bacnet_points(data)
    # Should be returned as-is (same object or equal value, no re-enrichment)
    assert result["bacnet_1"] is already_enriched


def test_enrich_flat_bacnet_points_skips_non_bacnet_keys():
    """Keys not starting with 'bacnet_' are passed through unchanged."""
    data = {"control": "on", "notes": "test", "bacnet_1": {"address": "2500.AI1", "name": "X"}}
    result = enrich_flat_bacnet_points(data)
    assert result["control"] == "on"
    assert result["notes"] == "test"


def test_explode_bacnet_points_now_enriches():
    """explode_bacnet_points with component_type produces enriched output."""
    metadata = {
        "bacnet": {
            "2500.AI13": {"name": "T", "unit": "C"},
        }
    }
    result = explode_bacnet_points(metadata, component_type="duct_sensor_temperature")
    assert "bacnet_1" in result
    point = result["bacnet_1"]
    assert point["code"] == "2500.AI13"
    assert point["address"] == "bacnet://2500/analog-input,13/present-value"
    assert point["ref_type"] == "sensor"


def test_existing_tests_still_pass():
    """explode_bacnet_points backward-compatible (no component_type arg)."""
    metadata = {
        "bacnet": {
            "2500.BV1": {"unit": "On/Off", "name": "STATUT"},
        }
    }
    result = explode_bacnet_points(metadata)
    assert "bacnet_1" in result
    # Enriched with default component_type="" → ref_type="property"
    assert result["bacnet_1"]["code"] == "2500.BV1"
