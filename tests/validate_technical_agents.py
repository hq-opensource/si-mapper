
import asyncio
import os
import sys
from validation_base import AgentValidator, print_validation_report, ValidationResult
from agent.sub_agents.control.agent import ControlLlmAgent
from agent.sub_agents.electricity.agent import ElectricityLlmAgent

async def validate_technical(model_name: str, agent_type: str):
    print(f"\n>>> Validating {agent_type} Agent with {model_name}...")
    
    initial_state = {
        "tasks": [
            {
                "id": f"task-{agent_type.lower()}-validation",
                "description": f"Extract {agent_type} data for AHU-1",
                "equipment_name": "AHU-1",
                "equipment_type": "AHU",
                "status": "pending",
                "bacnet_status": "verified",
                "control_status": "pending",
                "electricity_status": "pending",
                "tags": []
            }
        ],
        "active_agent": f"{agent_type}Agent"
    }

    try:
        if agent_type == "Control":
            agent = ControlLlmAgent(model_name=model_name)
        else:
            agent = ElectricityLlmAgent(model_name=model_name)
            
        validator = AgentValidator(model_name=model_name)
        
        task_desc = f"Process the pending task for AHU-1. Call fetch_pending_task, use ingest_category_files_tool to look for {agent_type.lower()} data, mark_technical_progress, and finally call exit_loop_level_4."
        
        result = await validator.run_validation(agent, task_desc, initial_state=initial_state)
        return result
    except Exception as e:
        res = ValidationResult(model_name, f"{agent_type}Agent")
        res.error = str(e)
        return res

async def main():
    models = sys.argv[1:] if len(sys.argv) > 1 else [
        "gemini-3.1-pro-preview-customtools",
        "claude-sonnet-4-6",
        "gpt-5.4-2026-03-05"
    ]
    
    all_results = []
    for model in models:
        for agent_type in ["Control", "Electricity"]:
            all_results.append(await validate_technical(model, agent_type))
    
    print_validation_report(all_results)

if __name__ == "__main__":
    asyncio.run(main())
