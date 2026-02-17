import os
import sys
import json
from dotenv import load_dotenv

# Add the project root to the Python path
# Fixed path since this is now in tests/ folder
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import GridManager
from mcp_server.graphivac.grid_manager import GridManager

def test_read_grid():
    # Load localized project config
    env_path = os.path.join(project_root, 'mcp_server', 'server', 'mcp.env')
    load_dotenv(env_path)

    # Load Environment Variables
    ORG_ID = os.getenv("GRAPHIVAC_ORG_ID")
    PROJECT_ID = os.getenv("GRAPHIVAC_PROJECT_ID")
    GRID_ID = os.getenv("GRAPHIVAC_GRID_ID")
    GRID_TITLE = os.getenv("GRAPHIVAC_GRID_TITLE")
    BASE_URL = os.getenv("GRAPHIVAC_BASE_URL")
    FONT_CONFIGS = {"family": "Serif", "style": "Oblique", "size": 20, "weight": "Lighter", "color": "string"}

    print(f"Connecting to: {BASE_URL}")
    print(f"Org: {ORG_ID}, Project: {PROJECT_ID}, Grid: {GRID_ID}")

    if not all([ORG_ID, PROJECT_ID, GRID_ID]):
        print("Error: Missing required environment variables.")
        return

    # Initialize manager
    grid_manager = GridManager(ORG_ID, PROJECT_ID, GRID_ID, GRID_TITLE, FONT_CONFIGS, BASE_URL)

    try:
        print("Reading grids and looking for components...")
        from mcp_server.graphivac.graphivac_api import GraphivacAPI
        from edn_format import Keyword
        api = GraphivacAPI(ORG_ID, PROJECT_ID, GRID_ID, GRID_TITLE, FONT_CONFIGS, BASE_URL)
        
        print(f"Checking all grids for Project: {PROJECT_ID}...")
        all_grids = api.get_all_grids()
        print(f"DEBUG: all_grids response: {json.dumps(all_grids, indent=2)}")
        
        for g in all_grids:
            g_id = g.get('grid-id') or g.get('id')
            g_title = g.get('title')
            print(f"\nChecking Grid ID: {g_id}, Title: {g_title}")
            
            try:
                temp_api = GraphivacAPI(ORG_ID, PROJECT_ID, g_id, g_title, FONT_CONFIGS, BASE_URL)
                raw_grid = temp_api.get_grid_info_edn()
                comps = raw_grid.get(Keyword("comps"), {})
                print(f"  Raw comps count: {len(comps)}")
                
                if len(comps) > 0:
                    print(f"  FOUND DATA in grid: {g_id}")
                    # Try reading with manager
                    temp_manager = GridManager(ORG_ID, PROJECT_ID, g_id, g_title, FONT_CONFIGS, BASE_URL)
                    components = temp_manager.read_grid()
                    print(f"  Manager read {len(components)} components.")
                    
                    if components:
                        print(f"  First component sample: {json.dumps(components[0], indent=2)}")
                        # Save result for inspection in the tests folder
                        output_path = os.path.join(os.path.dirname(__file__), "grid_output.json")
                        with open(output_path, "w") as f:
                            json.dump(components, f, indent=2)
                        print(f"  Results saved to {output_path}")
            except Exception as e:
                print(f"  Error reading grid {g_id}: {e}")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_read_grid()
