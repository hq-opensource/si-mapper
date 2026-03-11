
import os
import sys
from unittest.mock import MagicMock

# Setup paths
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
agent_root = os.path.join(project_root, 'agent')
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if agent_root not in sys.path:
    sys.path.insert(0, agent_root)

from agent.utils.task_service import TaskService
from agent.utils.models import TaskStatus

def test_debug():
    initial_state = {
        "tasks": [
            {
                "id": "task-bacnet-validation",
                "description": "Extract BACnet data for AHU-1",
                "equipment_name": "AHU-1",
                "equipment_type": "AHU",
                "status": "pending",
                "bacnet_status": "pending",
                "control_status": "pending",
                "electricity_status": "pending",
                "tags": []
            }
        ],
        "active_agent": "BacnetAgentInternal"
    }

    mock_context = MagicMock()
    mock_context.state = initial_state

    # Verify Tasks
    tasks = TaskService.get_tasks(mock_context)
    print(f"Loaded {len(tasks)} tasks.")
    for t in tasks:
        print(f"Task ID: {t.id}, bacnet_status: {t.bacnet_status} (type: {type(t.bacnet_status)})")

    # Run fetch
    task = TaskService.fetch_pending_task(mock_context)
    if task:
        print(f"Fetched task: {task.id}")
    else:
        print("Failed to fetch task.")

if __name__ == "__main__":
    test_debug()
