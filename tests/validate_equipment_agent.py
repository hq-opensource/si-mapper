
import asyncio
import os
import sys
from validation_base import AgentValidator, print_validation_report, ValidationResult
from agent.sub_agents.equipment.agent import EquipmentLlmAgent

async def validate_equipment(model_name: str):
    print(f"\n>>> Validating EquipmentAgent with {model_name}...")
    
    initial_state = {
        "active_agent": "EquipmentAgent"
    }

    try:
        agent = EquipmentLlmAgent(model_name=model_name)
        validator = AgentValidator(model_name=model_name)
        
        task_desc = "Place HVAC equipment identified in the project documentation. Use ingest_category_files_tool to look for equipment lists, then call exit_loop_level_4."
        
        result = await validator.run_validation(agent, task_desc, initial_state=initial_state)
        return result
    except Exception as e:
        res = ValidationResult(model_name, "EquipmentAgent")
        res.error = str(e)
        return res

async def main():
    models = sys.argv[1:] if len(sys.argv) > 1 else [
        "gemini-3.1-pro-preview-customtools",
        "claude-sonnet-4-6",
        "gpt-5.4-2026-03-05"
    ]
    
    results = []
    for model in models:
        results.append(await validate_equipment(model))
    
    print_validation_report(results)

if __name__ == "__main__":
    asyncio.run(main())
