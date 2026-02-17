
import unittest
from unittest.mock import MagicMock
import os
import sys

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp_server.graphivac.metadata_manager import MetadataManager
from edn_format import Keyword

class TestMetadataBatch(unittest.TestCase):
    def setUp(self):
        # Mock dependencies
        self.mock_api = MagicMock()
        self.manager = MetadataManager("org", "proj", "grid", "title", {}, "url")
        self.manager.api = self.mock_api  # Replace real API with mock

    def test_write_metadata_batch_structure(self):
        # 1. Setup Mock Grid Data (EDN structure simulation)
        # Structure: { :comps { [:obj "AHU-1"] { :custom-fields {} } } }
        
        k_comps = Keyword("comps")
        k_obj = Keyword("obj")
        k_custom = Keyword("custom-fields")
        
        # We use a mutable dict for the mock return to simulate the EDN -> Mutable conversion result
        # Note: In the real code, get_grid_info_edn returns immutable, then we convert.
        # Here we mock the result of `get_grid_info_edn` effectively.
        
        mock_grid_data = {
            k_comps: {
                (k_obj, "AHU-1"): {k_custom: {}},
                (k_obj, "VAV-2"): {k_custom: {"existing": "val"}}
            }
        }
        
        # When get_grid_info_edn is called, return this structure
        self.mock_api.get_grid_info_edn.return_value = mock_grid_data
        
        # 2. Define Inputs (The structure we want to verify)
        updates = {
            "AHU-1": {"bacnet": "ID:1001", "type": "AHU"},
            "VAV-2": {"bacnet": "ID:2002"}
        }
        
        print(f"Testing with input structure: {updates}")
        
        # 3. Execution
        result = self.manager.write_metadata_batch(updates)
        
        # 4. Verify API call arguments (what was sent back)
        args, _ = self.mock_api.update_grid_edn.call_args
        updated_grid = args[0]
        
        comps = updated_grid[k_comps]
        
        # Check AHU-1
        ahu_data = comps[(k_obj, "AHU-1")][k_custom]
        print(f"AHU-1 Result: {ahu_data}")
        self.assertEqual(ahu_data["bacnet"], "ID:1001")
        self.assertEqual(ahu_data["type"], "AHU")
        
        # Check VAV-2
        vav_data = comps[(k_obj, "VAV-2")][k_custom]
        print(f"VAV-2 Result: {vav_data}")
        self.assertEqual(vav_data["bacnet"], "ID:2002")
        self.assertEqual(vav_data["existing"], "val") # Should preserve existing
        
        print("[SUCCESS] Batch structure {Name: MetadataDict} correctly mapped to :custom-fields")

if __name__ == '__main__':
    unittest.main()
