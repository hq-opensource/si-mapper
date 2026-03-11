
import asyncio
import os
import sys
from validation_base import AgentValidator, print_validation_report, ValidationResult
from agent.sub_agents.bacnet.agent import BacnetLlmAgent

async def validate_bacnet(model_name: str):
    print(f"\n>>> Validating BacnetAgent with {model_name}...")
    
    # 1. Setup Initial State
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
        "active_agent": "BacnetAgent"
    }

    try:
        # 2. Initialize Agent
        agent = BacnetLlmAgent(model_name=model_name)
        
        # 3. Initialize Validator
        validator = AgentValidator(model_name=model_name)
        
        # 4. Run Task
        # We give a prompt that triggers the agent's internal loop logic
        task_desc = "Process the pending task for AHU-1. Call fetch_pending_task, then use ingest_category_files_tool to look for point data, mark_technical_progress, and finally call exit_loop_level_4."
        
        result = await validator.run_validation(agent, task_desc, initial_state=initial_state)
        return result
    except Exception as e:
        res = ValidationResult(model_name, "BacnetAgent")
        res.error = str(e)
        return res

async def main():
    # If a model is passed as an argument, only test that one. Otherwise test all.
    models = sys.argv[1:] if len(sys.argv) > 1 else [
        "gemini-3.1-pro-preview-customtools",
        "claude-sonnet-4-6",
        "gpt-5.4-2026-03-05"
    ]
    
    results = []
    for model in models:
        results.append(await validate_bacnet(model))
    
    print_validation_report(results)

if __name__ == "__main__":
    asyncio.run(main())
