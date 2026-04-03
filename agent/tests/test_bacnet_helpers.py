"""
Unit tests for agent/utils/bacnet_helpers.py — explode_bacnet_points helper.
"""
import pytest
from utils.bacnet_helpers import explode_bacnet_points


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
    assert result["bacnet_1"] == {"address": "2500.BV1", "unit": "On/Off", "name": "STATUT DIG 1E"}
    assert result["bacnet_2"] == {"address": "2500.BO11", "unit": "On/Off", "name": "CMD DIG 1E"}


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
    assert result["bacnet_1"]["address"] == "2500.AI11"


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
    assert result["bacnet_1"] == {
        "address": "2500.AI11",
        "unit": "Amperes",
        "name": "VITESSE RET. No.1A",
    }


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
    assert result["bacnet_1"]["address"] == addr_a
    assert result["bacnet_2"]["address"] == addr_b
