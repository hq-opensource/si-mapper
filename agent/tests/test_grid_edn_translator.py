"""
Unit tests for agent/utils/grid_edn_translator.py.

Covers bidirectional EDN <-> internal_grid translation,
including round-trip verification of flat bacnet_N custom_fields.
"""

import sys
from pathlib import Path

import pytest

# Allow imports from agent/
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.grid_edn_translator import (
    edn_comps_to_internal_grid,
    internal_grid_to_edn_comps,
    SYMBOL_TO_AGENT,
    AGENT_TO_SYMBOL,
)


# ---------------------------------------------------------------------------
# Basic round-trip tests
# ---------------------------------------------------------------------------

def test_agent_to_symbol_is_inverse_of_symbol_to_agent():
    """AGENT_TO_SYMBOL is exact inverse of SYMBOL_TO_AGENT."""
    for symbol, agent in SYMBOL_TO_AGENT.items():
        assert AGENT_TO_SYMBOL[agent] == symbol


def test_empty_grid_round_trip():
    """An empty components list survives a round-trip."""
    grid = {"components": []}
    edn = internal_grid_to_edn_comps(grid)
    restored = edn_comps_to_internal_grid(edn)
    assert restored == {"components": []}


def test_fan_component_round_trip():
    """A basic fan component (no custom_fields) survives a round-trip."""
    grid = {"components": [{
        "type": "fan",
        "name": "SF-1",
        "coord": [5, 5],
    }]}
    edn = internal_grid_to_edn_comps(grid)
    restored = edn_comps_to_internal_grid(edn)
    comp = restored["components"][0]
    assert comp["type"] == "fan"
    assert comp["name"] == "SF-1"
    assert comp["coord"] == [5, 5]


def test_duct_line_round_trip():
    """A duct line component survives a round-trip."""
    grid = {"components": [{
        "type": "duct",
        "name": "D-1",
        "start": [0, 0],
        "end": [10, 10],
    }]}
    edn = internal_grid_to_edn_comps(grid)
    restored = edn_comps_to_internal_grid(edn)
    comp = restored["components"][0]
    assert comp["type"] == "duct"
    assert comp["start"] == [0, 0]
    assert comp["end"] == [10, 10]


# ---------------------------------------------------------------------------
# flat bacnet_N custom_fields round-trip
# ---------------------------------------------------------------------------

def test_bacnet_flat_keys_round_trip():
    """Flat bacnet_N keys survive EDN round-trip."""
    grid = {"components": [{
        "type": "fan",
        "name": "SF-1",
        "coord": [5, 5],
        "custom_fields": {
            "bacnet_1": {"address": "2500.AI11", "name": "VITESSE RET.", "unit": "Amperes"},
            "bacnet_2": {"address": "2500.BI3", "name": "STATUT", "unit": ""},
        }
    }]}
    edn = internal_grid_to_edn_comps(grid)
    restored = edn_comps_to_internal_grid(edn)
    comp = restored["components"][0]
    assert "bacnet_1" in comp["custom_fields"]
    assert comp["custom_fields"]["bacnet_1"]["address"] == "2500.AI11"
    assert comp["custom_fields"]["bacnet_1"]["name"] == "VITESSE RET."
    assert comp["custom_fields"]["bacnet_1"]["unit"] == "Amperes"
    assert "bacnet_2" in comp["custom_fields"]
    assert comp["custom_fields"]["bacnet_2"]["address"] == "2500.BI3"
    assert comp["custom_fields"]["bacnet_2"]["name"] == "STATUT"
    assert comp["custom_fields"]["bacnet_2"]["unit"] == ""


def test_bacnet_five_points_round_trip():
    """Five flat bacnet_N keys all survive a round-trip intact."""
    grid = {"components": [{
        "type": "fan",
        "name": "AHU-1",
        "coord": [3, 7],
        "custom_fields": {
            "bacnet_1": {"address": "2500.AI11", "name": "VITESSE RET. No.1A", "unit": "Amperes"},
            "bacnet_2": {"address": "2500.AI13", "name": "TEMP. ALIM. No.1A", "unit": "Celsius"},
            "bacnet_3": {"address": "2500.BI3",  "name": "STATUT DIG. 1A", "unit": ""},
            "bacnet_4": {"address": "2500.BO1",  "name": "A/D VENT. 1A", "unit": ""},
            "bacnet_5": {"address": "2500.AO5",  "name": "MOD. VFD 1A", "unit": "%"},
        }
    }]}
    edn = internal_grid_to_edn_comps(grid)
    restored = edn_comps_to_internal_grid(edn)
    comp = restored["components"][0]
    cf = comp["custom_fields"]
    for i in range(1, 6):
        assert f"bacnet_{i}" in cf, f"bacnet_{i} missing after round-trip"
    assert cf["bacnet_3"]["address"] == "2500.BI3"
    assert cf["bacnet_5"]["unit"] == "%"


def test_no_bacnet_special_casing_in_translator():
    """The translator must NOT contain any hard-coded 'bacnet' string."""
    import agent.utils.grid_edn_translator as mod
    import inspect
    source = inspect.getsource(mod)
    # Allow the string to appear only in comments/docstrings, not as a dict key or variable
    # The simplest check: no literal '"bacnet"' (double-quoted) in source
    assert '"bacnet"' not in source, (
        "Translator contains hard-coded '\"bacnet\"' — remove special-case logic"
    )
