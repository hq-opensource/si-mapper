"""
Unit tests for agent/utils/grid_edn_translator.py

Tests cover:
- Roundtrip correctness for duct, pipe, and all equipment/sensor types
- Rotation bug fix: reads/writes Keyword("rot"), NOT Keyword("rotation")
- Pipe vs duct distinction (distinct EDN keys)
- Unknown EDN symbol handling (silently dropped with warning)
- All 25 component types (2 line + 15 equipment + 8 sensor)

Run with:
    cd /home/juan/codes/si-mapper
    python -m pytest tests/test_grid_edn_translator.py -v
"""

import logging
import sys
import os
import types

# Ensure project root on path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ---------------------------------------------------------------------------
# Stub heavy external dependencies before importing translator
# ---------------------------------------------------------------------------

def _ensure_stub(module_name, **attrs):
    if module_name not in sys.modules:
        mod = types.ModuleType(module_name)
        for k, v in attrs.items():
            setattr(mod, k, v)
        sys.modules[module_name] = mod
    return sys.modules[module_name]


# Stub google.adk hierarchy (needed by internal_grid_tools)
_google_stub = _ensure_stub("google")
_adk_stub = _ensure_stub("google.adk")
_adk_tools_stub = _ensure_stub("google.adk.tools")


class _FakeToolContext:
    pass


_adk_tools_stub.ToolContext = _FakeToolContext

# Stub utils.logging_config (needed by internal_grid_tools)
_utils_stub = _ensure_stub("utils")
_logging_config_stub = _ensure_stub("utils.logging_config")
_logging_config_stub.configure_logging = lambda: logging.getLogger("test")

# Stub tools.internal_grid_tools using real values from the actual module
# (imported via agent. prefix which doesn't require the 'tools' stub)
_tools_stub = _ensure_stub("tools")
_tools_igt_stub = _ensure_stub("tools.internal_grid_tools")

_LINE_TYPES = {"duct", "pipe"}
_EQUIPMENT_TYPES = {
    "cooling_coil", "heating_coil", "fan", "filter", "damper",
    "thermal_wheel", "humidifier", "boiler", "heat_pump", "pump",
    "valve_three_way", "valve_two_way", "variable_frequency_drive",
    "room_baseboard", "pipe_chiller",
}
_SENSOR_TYPES = {
    "duct_sensor_enthalpy", "duct_sensor_temperature",
    "duct_sensor_differential_pressure", "duct_sensor_humidity",
    "duct_sensor_flow", "duct_sensor_low_limit", "duct_sensor_static_pressure",
    "pipe_sensor_temperature",
}
_COORD_TYPES = _EQUIPMENT_TYPES | _SENSOR_TYPES
_ROTATION_TYPES = {"fan", "damper"}

_tools_igt_stub.LINE_TYPES = _LINE_TYPES
_tools_igt_stub.EQUIPMENT_TYPES = _EQUIPMENT_TYPES
_tools_igt_stub.SENSOR_TYPES = _SENSOR_TYPES
_tools_igt_stub.COORD_TYPES = _COORD_TYPES
_tools_igt_stub.ROTATION_TYPES = _ROTATION_TYPES

# ---------------------------------------------------------------------------
# Now safe to import the translator
# ---------------------------------------------------------------------------

import pytest
from edn_format import Keyword

from agent.utils.grid_edn_translator import (
    edn_comps_to_internal_grid,
    internal_grid_to_edn_comps,
    SYMBOL_TO_AGENT,
    AGENT_TO_SYMBOL,
)


# ---------------------------------------------------------------------------
# Helper: build a minimal line-type EDN comp entry
# ---------------------------------------------------------------------------

def _make_line_edn(key_word: str, name: str, pos1, pos2) -> dict:
    return {
        (Keyword(key_word), name): {
            Keyword("n1"): {Keyword("pos"): pos1},
            Keyword("n2"): {Keyword("pos"): pos2},
        }
    }


def _make_obj_edn(name: str, symbol: str, pos, rotation=None, custom_fields=None) -> dict:
    value = {
        Keyword("symbol"): symbol,
        Keyword("name"): name,
        Keyword("pos"): pos,
    }
    if rotation is not None:
        value[Keyword("rot")] = rotation
    if custom_fields is not None:
        value[Keyword("custom-fields")] = custom_fields
    return {(Keyword("obj"), name): value}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRoundtripDuct:
    """Test 1: duct line roundtrip"""

    def test_roundtrip_duct(self):
        edn = _make_line_edn("duct", "D-1", [0, 0], [10, 0])
        result = edn_comps_to_internal_grid(edn)
        components = result["components"]
        assert len(components) == 1
        comp = components[0]
        assert comp["type"] == "duct"
        assert comp["name"] == "D-1"
        assert comp["start"] == [0, 0]
        assert comp["end"] == [10, 0]

        # Rebuild to EDN
        rebuilt = internal_grid_to_edn_comps(result)
        assert len(rebuilt) == 1
        key = list(rebuilt.keys())[0]
        assert key[0] == Keyword("duct")
        assert key[1] == "D-1"
        value = rebuilt[key]
        assert value[Keyword("n1")][Keyword("pos")] == [0, 0]
        assert value[Keyword("n2")][Keyword("pos")] == [10, 0]


class TestRoundtripPipe:
    """Test 2: pipe line roundtrip — must use Keyword("pipe"), not Keyword("duct")"""

    def test_roundtrip_pipe(self):
        edn = _make_line_edn("pipe", "P-1", [-3, 3], [1, 3])
        result = edn_comps_to_internal_grid(edn)
        components = result["components"]
        assert len(components) == 1
        comp = components[0]
        # Must be type "pipe", NOT "duct"
        assert comp["type"] == "pipe"
        assert comp["name"] == "P-1"
        assert comp["start"] == [-3, 3]
        assert comp["end"] == [1, 3]

        # Rebuild to EDN — key must use Keyword("pipe")
        rebuilt = internal_grid_to_edn_comps(result)
        key = list(rebuilt.keys())[0]
        assert key[0] == Keyword("pipe")
        assert key[1] == "P-1"


class TestRoundtripFanWithRotation:
    """Test 3: fan with rotation roundtrip"""

    def test_roundtrip_fan_with_rotation(self):
        edn = _make_obj_edn("SF-1", "duct.fan", [5, 5], rotation=90)
        result = edn_comps_to_internal_grid(edn)
        components = result["components"]
        assert len(components) == 1
        comp = components[0]
        assert comp["type"] == "fan"
        assert comp["name"] == "SF-1"
        assert comp["coord"] == [5, 5]
        assert comp["rotation"] == 90

        # Rebuild to EDN — must write Keyword("rot")
        rebuilt = internal_grid_to_edn_comps(result)
        key = list(rebuilt.keys())[0]
        value = rebuilt[key]
        assert value[Keyword("rot")] == 90


class TestRotationBugFix:
    """Test 4: rotation must be read from Keyword("rot"), not Keyword("rotation")"""

    def test_rotation_bug_fix(self):
        # EDN uses Keyword("rot") — the correct key
        edn = {
            (Keyword("obj"), "FAN-BUG"): {
                Keyword("symbol"): "duct.fan",
                Keyword("name"): "FAN-BUG",
                Keyword("pos"): [1, 2],
                Keyword("rot"): 180,
                # Deliberately NOT adding Keyword("rotation") — the wrong key
            }
        }
        result = edn_comps_to_internal_grid(edn)
        comp = result["components"][0]
        # Must be 180, not 0 (if reading wrong key, would be 0)
        assert comp["rotation"] == 180, (
            "Rotation must be read from Keyword('rot'), not Keyword('rotation')"
        )

    def test_rotation_wrong_key_gives_zero(self):
        """Confirms that Keyword('rotation') is not recognized (bug scenario)."""
        edn = {
            (Keyword("obj"), "FAN-WRONG"): {
                Keyword("symbol"): "duct.fan",
                Keyword("name"): "FAN-WRONG",
                Keyword("pos"): [1, 2],
                # Using wrong key — should result in rotation=0
                Keyword("rotation"): 270,
            }
        }
        result = edn_comps_to_internal_grid(edn)
        comp = result["components"][0]
        # Translator reads Keyword("rot") — Keyword("rotation") is ignored
        assert comp["rotation"] == 0


class TestRotationZeroOmitted:
    """Test 5: rotation=0 must NOT appear in rebuilt EDN"""

    def test_rotation_zero_omitted(self):
        internal_grid = {
            "components": [
                {"type": "fan", "name": "FAN-ZERO", "coord": [3, 3], "rotation": 0}
            ]
        }
        rebuilt = internal_grid_to_edn_comps(internal_grid)
        key = list(rebuilt.keys())[0]
        value = rebuilt[key]
        assert Keyword("rot") not in value, (
            "Keyword('rot') should NOT appear in EDN output when rotation is 0"
        )


class TestUnknownSymbolDropped:
    """Test 6: unknown EDN symbol must be dropped with a warning log"""

    def test_unknown_symbol_dropped(self, caplog):
        edn = {
            (Keyword("obj"), "UNKNOWN-1"): {
                Keyword("symbol"): "some.unknown.thing",
                Keyword("name"): "UNKNOWN-1",
                Keyword("pos"): [0, 0],
            }
        }
        with caplog.at_level(logging.WARNING, logger="agent.utils.grid_edn_translator"):
            result = edn_comps_to_internal_grid(edn)

        # Component must NOT be in result
        assert len(result["components"]) == 0

        # Warning must have been logged
        assert any("unknown" in record.message.lower() or "Unknown" in record.message
                   for record in caplog.records), (
            "Expected a warning log for unknown symbol"
        )


class TestAllEquipmentTypes:
    """Test 7: all 15 equipment types parse to correct agent types"""

    def test_all_equipment_types(self):
        equipment_symbols = {
            "duct.fan": "fan",
            "duct.damper": "damper",
            "duct.coil.cooling": "cooling_coil",
            "duct.coil.heating": "heating_coil",
            "duct.filter": "filter",
            "duct.thermal-wheel": "thermal_wheel",
            "duct.humidifier": "humidifier",
            "pipe.boiler": "boiler",
            "pipe.heat-pump": "heat_pump",
            "pipe.pump": "pump",
            "pipe.valve.three-way": "valve_three_way",
            "pipe.valve.two-way": "valve_two_way",
            "electric.vfd": "variable_frequency_drive",
            "user.room.baseboard": "room_baseboard",
            "user.pipe.chiller": "pipe_chiller",
        }
        assert len(equipment_symbols) == 15, "Expected 15 equipment types"

        for symbol, expected_type in equipment_symbols.items():
            name = f"EQ-{symbol.replace('.', '-')}"
            edn = _make_obj_edn(name, symbol, [1, 1])
            result = edn_comps_to_internal_grid(edn)
            assert len(result["components"]) == 1, (
                f"Expected 1 component for symbol '{symbol}', got {len(result['components'])}"
            )
            comp = result["components"][0]
            assert comp["type"] == expected_type, (
                f"Symbol '{symbol}': expected type '{expected_type}', got '{comp['type']}'"
            )


class TestAllSensorTypes:
    """Test 8: all 8 sensor types parse to correct agent types"""

    def test_all_sensor_types(self):
        sensor_symbols = {
            "duct.sensor.enthalpy": "duct_sensor_enthalpy",
            "duct.sensor.temperature": "duct_sensor_temperature",
            "duct.sensor.pressure": "duct_sensor_differential_pressure",
            "duct.sensor.humidity": "duct_sensor_humidity",
            "duct.sensor.flow": "duct_sensor_flow",
            "duct.sensor.low-limit": "duct_sensor_low_limit",
            "duct.sensor.static-pressure": "duct_sensor_static_pressure",
            "pipe.sensor.temperature": "pipe_sensor_temperature",
        }
        assert len(sensor_symbols) == 8, "Expected 8 sensor types"

        for symbol, expected_type in sensor_symbols.items():
            name = f"SN-{symbol.replace('.', '-')}"
            edn = _make_obj_edn(name, symbol, [2, 2])
            result = edn_comps_to_internal_grid(edn)
            assert len(result["components"]) == 1, (
                f"Expected 1 component for symbol '{symbol}', got {len(result['components'])}"
            )
            comp = result["components"][0]
            assert comp["type"] == expected_type, (
                f"Symbol '{symbol}': expected type '{expected_type}', got '{comp['type']}'"
            )


class TestPipeVsDuctNotConflated:
    """Test 9: duct and pipe must use distinct EDN keys and not be conflated"""

    def test_pipe_vs_duct_not_conflated(self):
        edn = {}
        edn.update(_make_line_edn("duct", "DUCT-1", [0, 0], [5, 0]))
        edn.update(_make_line_edn("pipe", "PIPE-1", [0, 1], [5, 1]))

        result = edn_comps_to_internal_grid(edn)
        components = result["components"]
        assert len(components) == 2

        types_found = {c["type"] for c in components}
        assert "duct" in types_found
        assert "pipe" in types_found

        # Rebuild and check keys
        rebuilt = internal_grid_to_edn_comps(result)
        assert len(rebuilt) == 2
        keywords = {key[0] for key in rebuilt.keys()}
        assert Keyword("duct") in keywords
        assert Keyword("pipe") in keywords


class TestFullRoundtripAllTypes:
    """Test 10: full roundtrip covering all 25 component types"""

    def test_full_roundtrip_all_types(self):
        # Build internal_grid with one component of each of the 25 types
        components = []

        # 2 line types
        components.append({
            "type": "duct", "name": "ALL-DUCT", "start": [0, 0], "end": [1, 0]
        })
        components.append({
            "type": "pipe", "name": "ALL-PIPE", "start": [0, 1], "end": [1, 1]
        })

        # 15 equipment types
        for eq_type in _EQUIPMENT_TYPES:
            comp: dict = {"type": eq_type, "name": f"ALL-{eq_type}", "coord": [2, 2]}
            if eq_type in _ROTATION_TYPES:
                comp["rotation"] = 0
            components.append(comp)

        # 8 sensor types
        for sensor_type in _SENSOR_TYPES:
            components.append({
                "type": sensor_type, "name": f"ALL-{sensor_type}", "coord": [3, 3]
            })

        assert len(components) == 25, f"Expected 25 components, got {len(components)}"

        internal_grid = {"components": components}

        # Translate to EDN
        edn_comps = internal_grid_to_edn_comps(internal_grid)
        assert len(edn_comps) == 25, (
            f"Expected 25 EDN entries, got {len(edn_comps)}"
        )

        # Translate back
        restored = edn_comps_to_internal_grid(edn_comps)
        restored_components = restored["components"]
        assert len(restored_components) == 25, (
            f"Expected 25 restored components, got {len(restored_components)}"
        )

        # Verify all types present
        restored_types = {c["type"] for c in restored_components}
        all_expected_types = _LINE_TYPES | _EQUIPMENT_TYPES | _SENSOR_TYPES
        assert restored_types == all_expected_types, (
            f"Missing types: {all_expected_types - restored_types}"
        )

        # Verify all names present
        restored_names = {c["name"] for c in restored_components}
        expected_names = {c["name"] for c in components}
        assert restored_names == expected_names

        # Verify line type coords preserved
        for comp in restored_components:
            if comp["type"] == "duct":
                assert comp["name"] == "ALL-DUCT"
                assert comp["start"] == [0, 0]
                assert comp["end"] == [1, 0]
            elif comp["type"] == "pipe":
                assert comp["name"] == "ALL-PIPE"
                assert comp["start"] == [0, 1]
                assert comp["end"] == [1, 1]
            else:
                # Equipment/sensor: verify coord
                if comp["type"] in _EQUIPMENT_TYPES:
                    assert comp["coord"] == [2, 2], (
                        f"Equipment {comp['type']} coord mismatch"
                    )
                else:
                    assert comp["coord"] == [3, 3], (
                        f"Sensor {comp['type']} coord mismatch"
                    )


class TestMappingTableCompleteness:
    """Additional tests to verify mapping table completeness"""

    def test_symbol_to_agent_count(self):
        assert len(SYMBOL_TO_AGENT) == 23, (
            f"SYMBOL_TO_AGENT should have 23 entries, has {len(SYMBOL_TO_AGENT)}"
        )

    def test_agent_to_symbol_count(self):
        assert len(AGENT_TO_SYMBOL) == 23, (
            f"AGENT_TO_SYMBOL should have 23 entries, has {len(AGENT_TO_SYMBOL)}"
        )

    def test_agent_to_symbol_is_reverse_of_symbol_to_agent(self):
        """Verify AGENT_TO_SYMBOL is exactly the inverse of SYMBOL_TO_AGENT."""
        for symbol, agent_type in SYMBOL_TO_AGENT.items():
            assert AGENT_TO_SYMBOL[agent_type] == symbol, (
                f"AGENT_TO_SYMBOL['{agent_type}'] = '{AGENT_TO_SYMBOL.get(agent_type)}', "
                f"expected '{symbol}'"
            )

    def test_all_coord_types_have_symbol(self):
        """Every type in COORD_TYPES must have a mapping in AGENT_TO_SYMBOL."""
        missing = _COORD_TYPES - set(AGENT_TO_SYMBOL.keys())
        assert not missing, (
            f"These COORD_TYPES have no AGENT_TO_SYMBOL entry: {missing}"
        )


class TestCustomFieldsRoundtrip:
    """Test 12: custom_fields must survive the full EDN → internal → EDN roundtrip."""

    def test_single_field_preserved_on_read(self):
        """Reading a component with :custom-fields populates custom_fields on the component."""
        edn = _make_obj_edn(
            "FAN-CF", "duct.fan", [5, 5],
            custom_fields={"bacnet": '{"2500.AO1": {"name": "FAN"}}'},
        )
        result = edn_comps_to_internal_grid(edn)
        comp = result["components"][0]
        assert "custom_fields" in comp
        assert comp["custom_fields"]["bacnet"] == '{"2500.AO1": {"name": "FAN"}}'

    def test_multiple_fields_preserved_on_read(self):
        """All custom field keys are preserved, not just 'bacnet'."""
        edn = _make_obj_edn(
            "SENSOR-CF", "duct.sensor.temperature", [3, 3],
            custom_fields={"bacnet": "bacnet-data", "control": "ctrl-ref"},
        )
        result = edn_comps_to_internal_grid(edn)
        comp = result["components"][0]
        assert comp["custom_fields"] == {"bacnet": "bacnet-data", "control": "ctrl-ref"}

    def test_edn_keyword_keys_normalised_to_strings(self):
        """EDN Keyword keys inside :custom-fields are normalised to plain strings."""
        edn = _make_obj_edn(
            "DAMP-CF", "duct.damper", [2, 2],
            custom_fields={Keyword("bacnet"): "some-value"},
        )
        result = edn_comps_to_internal_grid(edn)
        comp = result["components"][0]
        assert "bacnet" in comp["custom_fields"]
        assert Keyword("bacnet") not in comp["custom_fields"]

    def test_no_custom_fields_key_absent(self):
        """Components without :custom-fields must NOT have custom_fields in internal repr."""
        edn = _make_obj_edn("DAMP-PLAIN", "duct.damper", [1, 1])
        result = edn_comps_to_internal_grid(edn)
        comp = result["components"][0]
        assert "custom_fields" not in comp

    def test_custom_fields_written_to_edn(self):
        """custom_fields in internal grid are written as Keyword('custom-fields') in EDN."""
        internal_grid = {
            "components": [
                {
                    "type": "fan",
                    "name": "FAN-WRITE",
                    "coord": [7, 7],
                    "rotation": 0,
                    "custom_fields": {"bacnet": "data", "control": "ref"},
                }
            ]
        }
        rebuilt = internal_grid_to_edn_comps(internal_grid)
        key = list(rebuilt.keys())[0]
        value = rebuilt[key]
        assert Keyword("custom-fields") in value
        cf = value[Keyword("custom-fields")]
        assert cf["bacnet"] == "data"
        assert cf["control"] == "ref"

    def test_empty_custom_fields_omitted_from_edn(self):
        """An empty custom_fields dict must NOT produce :custom-fields in EDN output."""
        internal_grid = {
            "components": [
                {"type": "fan", "name": "FAN-EMPTY", "coord": [1, 1], "custom_fields": {}}
            ]
        }
        rebuilt = internal_grid_to_edn_comps(internal_grid)
        key = list(rebuilt.keys())[0]
        value = rebuilt[key]
        assert Keyword("custom-fields") not in value

    def test_full_roundtrip_with_custom_fields(self):
        """Full EDN → internal → EDN roundtrip preserves custom_fields exactly."""
        original_cf = {"bacnet": '{"2500.AI14": {"name": "TEMP"}}', "control": "ctrl-1"}
        edn = _make_obj_edn("HUMI-RT", "duct.humidifier", [10, 10], custom_fields=original_cf)

        internal = edn_comps_to_internal_grid(edn)
        rebuilt = internal_grid_to_edn_comps(internal)

        key = list(rebuilt.keys())[0]
        cf_out = rebuilt[key][Keyword("custom-fields")]
        assert cf_out == original_cf


