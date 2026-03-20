#!/usr/bin/env python3
"""
Integration test: exercises the full translator + REST pipeline against a real Graphivac grid.

Usage:
    GRAPHIVAC_BASE_URL=https://... GRAPHIVAC_ORG_ID=... GRAPHIVAC_PROJECT_ID=... GRAPHIVAC_GRID_ID=... python tests/test_integration_grid_sync.py

The script will:
1. Read the live grid via REST GET
2. Parse it to internal_grid using the translator
3. Add test components (a duct, a pipe, a fan with rotation, a sensor)
4. Translate back to EDN using the translator
5. PUT to Graphivac
6. Print verification instructions for the human
"""
import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "agent"))

import requests
import edn_format
from edn_format import Keyword

from agent.utils.edn_to_mutable import edn_to_mutable
from agent.utils.grid_edn_translator import edn_comps_to_internal_grid, internal_grid_to_edn_comps


def main():
    # --- Check required env vars ---
    base_url = os.environ.get("GRAPHIVAC_BASE_URL", "")
    org_id = os.environ.get("GRAPHIVAC_ORG_ID", "")
    project_id = os.environ.get("GRAPHIVAC_PROJECT_ID", "")
    grid_id = os.environ.get("GRAPHIVAC_GRID_ID", "")

    missing = [
        name for name, val in [
            ("GRAPHIVAC_BASE_URL", base_url),
            ("GRAPHIVAC_ORG_ID", org_id),
            ("GRAPHIVAC_PROJECT_ID", project_id),
            ("GRAPHIVAC_GRID_ID", grid_id),
        ]
        if not val
    ]

    if missing:
        print("ERROR: The following required environment variables are not set:")
        for var in missing:
            print(f"  - {var}")
        print()
        print("Usage:")
        print(
            "  GRAPHIVAC_BASE_URL=https://... GRAPHIVAC_ORG_ID=... "
            "GRAPHIVAC_PROJECT_ID=... GRAPHIVAC_GRID_ID=... "
            "python tests/test_integration_grid_sync.py"
        )
        sys.exit(1)

    url = f"{base_url}/orgs/{org_id}/projects/{project_id}/grids/{grid_id}"

    # --- Step 1: GET the live grid ---
    print("Step 1: Reading live grid from Graphivac...")
    response = requests.get(url, headers={"Accept": "application/edn"}, timeout=10)
    response.raise_for_status()
    edn_data = edn_format.loads(response.text)
    raw_edn_grid = edn_to_mutable(edn_data)

    existing_comps = raw_edn_grid.get(Keyword("comps"), {})
    n_existing = len(existing_comps)
    print(f"Step 1: Read grid — {n_existing} existing components")

    # --- Step 2: Parse to internal_grid ---
    internal_grid = edn_comps_to_internal_grid(existing_comps)
    n_parsed = len(internal_grid.get("components", []))
    print(f"Step 2: Parsed to internal_grid — {n_parsed} components")

    # --- Step 3: Add test components ---
    test_components = [
        {"id": "test-1", "type": "duct", "name": "TEST-DUCT-1", "start": [0, 15], "end": [10, 15]},
        {"id": "test-2", "type": "pipe", "name": "TEST-PIPE-1", "start": [-3, 17], "end": [1, 17]},
        {"id": "test-3", "type": "fan", "name": "TEST-FAN-1", "coord": [5, 15], "rotation": 90},
        {"id": "test-4", "type": "duct_sensor_temperature", "name": "TEST-SENSOR-1", "coord": [8, 15]},
    ]
    internal_grid["components"].extend(test_components)
    print("Step 3: Added 4 test components (duct, pipe, fan with rot=90, temp sensor)")

    # --- Step 4: Translate back to EDN and PUT ---
    print("Step 4: Translating to EDN and PUTting to Graphivac...")
    new_comps = internal_grid_to_edn_comps(internal_grid)
    raw_edn_grid[Keyword("comps")] = new_comps
    data = edn_format.dumps(raw_edn_grid)
    response = requests.put(url, headers={"Content-Type": "application/edn"}, data=data, timeout=15)
    response.raise_for_status()

    total = len(internal_grid.get("components", []))
    print(f"Step 4: PUT successful — grid updated with {total} components")

    # --- Step 5: Print human verification instructions ---
    print()
    print("=" * 60)
    print("VERIFICATION INSTRUCTIONS")
    print("=" * 60)
    print()
    print("Open the Graphivac UI and check the grid. You should see:")
    print()
    print("  1. TEST-DUCT-1: A duct line from [0,15] to [10,15]")
    print("  2. TEST-PIPE-1: A pipe line from [-3,17] to [1,17]")
    print("  3. TEST-FAN-1:  A fan at [5,15] with 90-degree rotation")
    print("  4. TEST-SENSOR-1: A temperature sensor at [8,15]")
    print()
    print("Verify:")
    print("  - The duct and pipe are DISTINCT line types (not both ducts)")
    print("  - The fan rotation is visible (rotated 90 degrees)")
    print("  - All existing components from before are still present")
    print()
    print("CLEANUP: To remove test components, re-run the agent or")
    print("manually delete TEST-DUCT-1, TEST-PIPE-1, TEST-FAN-1, TEST-SENSOR-1")
    print("from the Graphivac UI.")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.HTTPError as e:
        print(f"\nERROR: HTTP error from Graphivac: {e}")
        print(f"  Response status: {e.response.status_code}")
        print(f"  Response body: {e.response.text[:500]}")
        sys.exit(1)
    except requests.exceptions.ConnectionError as e:
        print(f"\nERROR: Could not connect to Graphivac: {e}")
        print("  Check that GRAPHIVAC_BASE_URL is correct and the server is running.")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("\nERROR: Request to Graphivac timed out.")
        print("  Check that the server is reachable and responding.")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: Unexpected failure: {type(e).__name__}: {e}")
        sys.exit(1)
