"""
Unit tests for agent/tools/internal_grid_tools.py

Uses a MockToolContext (simple object with a .state dict) so these tests
have no dependency on the Google ADK runtime.

Run with:
    cd /home/juan/codes/si-mapper
    python -m pytest tests/test_internal_grid_tools.py -v
"""

import json
import sys
import os
import unittest

# Ensure project root on path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ---------------------------------------------------------------------------
# Mock ToolContext — no ADK runtime needed
# ---------------------------------------------------------------------------

class MockToolContext:
    def __init__(self):
        self.state = {}


# ---------------------------------------------------------------------------
# Import functions under test
# We mock google.adk.tools so the import doesn't require the ADK package
# to expose ToolContext at module load time.
# ---------------------------------------------------------------------------

# Patch the import before loading the module
import types
_adk_stub = types.ModuleType("google")
_adk_stub.adk = types.ModuleType("google.adk")
_adk_stub.adk.tools = types.ModuleType("google.adk.tools")

class _FakeToolContext:
    pass

_adk_stub.adk.tools.ToolContext = _FakeToolContext

import importlib
sys.modules.setdefault("google", _adk_stub)
sys.modules.setdefault("google.adk", _adk_stub.adk)
sys.modules.setdefault("google.adk.tools", _adk_stub.adk.tools)

# Also stub utils.logging_config
_logging_stub = types.ModuleType("utils")
_logging_config_stub = types.ModuleType("utils.logging_config")
import logging as _logging
_logging_config_stub.configure_logging = lambda: _logging.getLogger("test")
sys.modules.setdefault("utils", _logging_stub)
sys.modules.setdefault("utils.logging_config", _logging_config_stub)

from agent.tools.internal_grid_tools import (
    initialize_internal_grid,
    add_component,
    add_components_batch,
    delete_component,
    delete_components_batch,
    read_internal_grid,
)


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestInitializeInternalGrid(unittest.TestCase):

    def test_initialize_internal_grid(self):
        """Calling initialize creates empty internal_grid in state."""
        ctx = MockToolContext()
        result = initialize_internal_grid(ctx)
        self.assertIn("internal_grid", ctx.state)
        self.assertEqual(ctx.state["internal_grid"], {"components": []})
        self.assertIn("initialized", result.lower())

    def test_initialize_idempotent(self):
        """Calling initialize twice does not reset existing state."""
        ctx = MockToolContext()
        initialize_internal_grid(ctx)
        # Add a component manually so we can check it survives the second call
        ctx.state["internal_grid"]["components"].append(
            {"id": "abc", "type": "fan", "name": "existing-fan", "coord": [1, 1], "rotation": 0}
        )
        result = initialize_internal_grid(ctx)
        # State should still have the component
        self.assertEqual(len(ctx.state["internal_grid"]["components"]), 1)
        self.assertIn("already initialized", result)


class TestAddComponent(unittest.TestCase):

    def test_add_duct(self):
        """add_component with type='duct' stores start/end coords."""
        ctx = MockToolContext()
        initialize_internal_grid(ctx)
        result = add_component(ctx, "duct", "duct-1", start_coord=[0, 0], end_coord=[5, 0])
        components = ctx.state["internal_grid"]["components"]
        self.assertEqual(len(components), 1)
        comp = components[0]
        self.assertEqual(comp["type"], "duct")
        self.assertEqual(comp["name"], "duct-1")
        self.assertEqual(comp["start"], [0, 0])
        self.assertEqual(comp["end"], [5, 0])
        self.assertNotIn("coord", comp)

    def test_add_fan(self):
        """add_component with type='fan' stores coord and rotation."""
        ctx = MockToolContext()
        initialize_internal_grid(ctx)
        result = add_component(ctx, "fan", "fan-1", coord=[3, 4], rotation=90)
        components = ctx.state["internal_grid"]["components"]
        self.assertEqual(len(components), 1)
        comp = components[0]
        self.assertEqual(comp["type"], "fan")
        self.assertEqual(comp["name"], "fan-1")
        self.assertEqual(comp["coord"], [3, 4])
        self.assertEqual(comp["rotation"], 90)

    def test_add_equipment_no_rotation(self):
        """add_component with type='cooling_coil' stores coord without rotation."""
        ctx = MockToolContext()
        initialize_internal_grid(ctx)
        add_component(ctx, "cooling_coil", "coil-1", coord=[2, 2])
        comp = ctx.state["internal_grid"]["components"][0]
        self.assertEqual(comp["type"], "cooling_coil")
        self.assertEqual(comp["coord"], [2, 2])
        self.assertNotIn("rotation", comp)

    def test_add_sensor(self):
        """add_component with type='duct_sensor_temperature' stores coord."""
        ctx = MockToolContext()
        initialize_internal_grid(ctx)
        add_component(ctx, "duct_sensor_temperature", "sensor-1", coord=[7, 3])
        comp = ctx.state["internal_grid"]["components"][0]
        self.assertEqual(comp["type"], "duct_sensor_temperature")
        self.assertEqual(comp["coord"], [7, 3])

    def test_add_duplicate_name(self):
        """Adding same name twice returns error string."""
        ctx = MockToolContext()
        initialize_internal_grid(ctx)
        add_component(ctx, "fan", "fan-dup", coord=[1, 1])
        result = add_component(ctx, "fan", "fan-dup", coord=[2, 2])
        self.assertIn("Error", result)
        self.assertIn("fan-dup", result)
        # Only one component should be stored
        self.assertEqual(len(ctx.state["internal_grid"]["components"]), 1)

    def test_add_invalid_type(self):
        """add_component with type='bogus' returns error string."""
        ctx = MockToolContext()
        initialize_internal_grid(ctx)
        result = add_component(ctx, "bogus", "thing-1", coord=[0, 0])
        self.assertIn("Error", result)
        self.assertIn("bogus", result)
        self.assertEqual(len(ctx.state["internal_grid"]["components"]), 0)

    def test_add_duct_missing_coords(self):
        """add_component type='duct' without start/end returns error."""
        ctx = MockToolContext()
        initialize_internal_grid(ctx)
        result = add_component(ctx, "duct", "duct-bad")
        self.assertIn("Error", result)
        self.assertEqual(len(ctx.state["internal_grid"]["components"]), 0)

    def test_add_fan_missing_coord(self):
        """add_component type='fan' without coord returns error."""
        ctx = MockToolContext()
        initialize_internal_grid(ctx)
        result = add_component(ctx, "fan", "fan-bad")
        self.assertIn("Error", result)
        self.assertEqual(len(ctx.state["internal_grid"]["components"]), 0)

    def test_auto_initialize(self):
        """add_component auto-initializes internal_grid if it is missing from state."""
        ctx = MockToolContext()
        # Do NOT call initialize_internal_grid — rely on auto-init
        self.assertNotIn("internal_grid", ctx.state)
        add_component(ctx, "fan", "auto-fan", coord=[0, 0])
        self.assertIn("internal_grid", ctx.state)
        self.assertEqual(len(ctx.state["internal_grid"]["components"]), 1)


class TestAddComponentsBatch(unittest.TestCase):

    def test_add_components_batch(self):
        """Batch add of 3 components stores all 3."""
        ctx = MockToolContext()
        initialize_internal_grid(ctx)
        batch = [
            {"type": "fan", "name": "fan-a", "coord": [1, 1]},
            {"type": "duct", "name": "duct-a", "start_coord": [0, 0], "end_coord": [3, 0]},
            {"type": "cooling_coil", "name": "coil-a", "coord": [5, 5]},
        ]
        result = add_components_batch(ctx, batch)
        self.assertEqual(len(ctx.state["internal_grid"]["components"]), 3)
        self.assertIn("3 added", result)


class TestDeleteComponent(unittest.TestCase):

    def test_delete_component(self):
        """Delete by name removes the component."""
        ctx = MockToolContext()
        initialize_internal_grid(ctx)
        add_component(ctx, "fan", "fan-del", coord=[1, 1])
        self.assertEqual(len(ctx.state["internal_grid"]["components"]), 1)
        result = delete_component(ctx, "fan-del")
        self.assertEqual(len(ctx.state["internal_grid"]["components"]), 0)
        self.assertIn("Deleted", result)

    def test_delete_nonexistent(self):
        """Delete unknown name returns error."""
        ctx = MockToolContext()
        initialize_internal_grid(ctx)
        result = delete_component(ctx, "ghost")
        self.assertIn("Error", result)
        self.assertIn("ghost", result)

    def test_delete_batch(self):
        """Batch delete removes multiple components."""
        ctx = MockToolContext()
        initialize_internal_grid(ctx)
        add_component(ctx, "fan", "fan-1", coord=[1, 1])
        add_component(ctx, "fan", "fan-2", coord=[2, 2])
        add_component(ctx, "fan", "fan-3", coord=[3, 3])
        result = delete_components_batch(ctx, ["fan-1", "fan-2"])
        self.assertEqual(len(ctx.state["internal_grid"]["components"]), 1)
        remaining = ctx.state["internal_grid"]["components"][0]
        self.assertEqual(remaining["name"], "fan-3")
        self.assertIn("2 deleted", result)


class TestReadInternalGrid(unittest.TestCase):

    def test_read_internal_grid_all(self):
        """read_internal_grid returns all components as JSON."""
        ctx = MockToolContext()
        initialize_internal_grid(ctx)
        add_component(ctx, "fan", "fan-r1", coord=[1, 1])
        add_component(ctx, "cooling_coil", "coil-r1", coord=[2, 2])
        result = read_internal_grid(ctx)
        # Should contain both names
        self.assertIn("fan-r1", result)
        self.assertIn("coil-r1", result)

    def test_read_internal_grid_filtered(self):
        """read_internal_grid with type filter returns subset."""
        ctx = MockToolContext()
        initialize_internal_grid(ctx)
        add_component(ctx, "fan", "fan-f1", coord=[1, 1])
        add_component(ctx, "cooling_coil", "coil-f1", coord=[2, 2])
        result = read_internal_grid(ctx, component_type="fan")
        self.assertIn("fan-f1", result)
        self.assertNotIn("coil-f1", result)


if __name__ == "__main__":
    unittest.main()
