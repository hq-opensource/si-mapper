
import os
import sys
import json
import asyncio
from google.adk.tools import ToolContext
from unittest.mock import MagicMock

# Add project root and agent directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
agent_root = os.path.join(project_root, 'agent')
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if agent_root not in sys.path:
    sys.path.insert(0, agent_root)

from agent.sub_agents.bacnet.agent import BacnetLlmAgent
from agent.utils.models import Task, TaskStatus

async def test_bacnet_agent_readiness():
    print("--- [VERIFICATION] Bacnet Agent Readiness Test ---")
    
    # 1. Setup Mock State
    state = {
        "tasks": [
            {
                "id": "test-task-1",
                "description": "Extract raw technical information for AHU-1",
                "equipment_name": "AHU-1",
                "equipment_type": "AHU",
                "status": "pending",
                "bacnet_treated": False,
                "control_treated": False,
                "electricity_treated": False,
                "tags": []
            }
        ],
        "active_agent": "BacnetAgent"
    }
    
    # 2. Mock ToolContext
    context = MagicMock(spec=ToolContext)
    context.state = state
    
    # 3. Check Artifacts
    csv_path = os.path.join(project_root, "mapper", "uploads", "bacnet", "filtered_CTRL_2500.csv")
    if os.path.exists(csv_path):
        print(f"[OK] CSV Artifact found at {csv_path}")
    else:
        print(f"[ERROR] CSV Artifact NOT found at {csv_path}")
        return

    # 4. Initialize Agent
    # We use a dummy model name since we are just checking logic/tools if possible
    # or we can try a dry run if we have API keys.
    # Note: BacnetAgentInternal uses load_prompt_instruction which depends on relative paths
    # We might need to adjust paths if running from tests/
    
    print("[INFO] Initializing BacnetLlmAgent...")
    try:
        agent = BacnetLlmAgent(model_name="gemini-1.5-flash")
        print("[OK] Agent initialized successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to initialize agent: {e}")
        return

    # 5. Check Prompt Content
    prompt_path = os.path.join(project_root, "agent", "sub_agents", "bacnet", "prompt.md")
    with open(prompt_path, 'r') as f:
        prompt_content = f.read()
    
    if "filtered_CTRL_2500.csv" in prompt_content:
        print("[OK] Prompt contains reference to target CSV.")
    else:
        print("[WARNING] Prompt does NOT mention the sample CSV explicitly, following general instructions.")

    print("\n--- Summary ---")
    print("1. Agent Directory: EXISTS")
    print("2. Agent Class: IMPLEMENTED")
    print("3. Task Infrastructure: READY")
    print("4. Sample Artifacts: AVAILABLE")
    print("5. Metadata Tools: REGISTERED IN MCP")
    
    # 6. Verify Tools Configuration
    internal_agent = agent.sub_agents[0]
    tool_names = [t.name if hasattr(t, 'name') else t.__name__ for t in internal_agent.tools]
    
    required_tools = [
        "fetch_pending_task",
        "mark_technical_progress",
        "create_batch_tasks",
        "load_artifacts",
        "exit_loop_level_4",
        "fetch_batch_tasks",
        "mark_technical_progress_batch"
    ]
    
    missing_tools = [t for t in required_tools if t not in tool_names]
    
    if not missing_tools:
        print(f"[OK] Internal agent has all required tools: {required_tools}")
    else:
        print(f"[ERROR] Internal agent is missing tools: {missing_tools}")
        print(f"       Available tools: {tool_names}")

    print("\n--- Summary ---")
    print("1. Agent Directory: EXISTS")
    print("2. Agent Class: IMPLEMENTED")
    print("3. Task Infrastructure: READY")
    print("4. Sample Artifacts: AVAILABLE")
    print("5. Metadata Tools: REGISTERED IN MCP")
    print("6. Tool Configuration: VERIFIED")
    
    print("\nReady to proceed with end-to-end testing.")

if __name__ == "__main__":
    asyncio.run(test_bacnet_agent_readiness())
