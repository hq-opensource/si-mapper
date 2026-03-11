
import asyncio
import os
import sys
from validation_base import AgentValidator, print_validation_report, ValidationResult
from agent.sub_agents.horizontal_ducts.agent import HorizontalDuctLlmAgent
from agent.sub_agents.vertical_ducts.agent import VerticalDuctLlmAgent

async def validate_ducts(model_name: str, duct_type: str):
    print(f"\n>>> Validating {duct_type} Duct Agent with {model_name}...")
    
    initial_state = {
        "active_agent": f"{duct_type}DuctAgent"
    }

    try:
        if duct_type == "Horizontal":
            agent = HorizontalDuctLlmAgent(model_name=model_name)
        else:
            agent = VerticalDuctLlmAgent(model_name=model_name)
            
        validator = AgentValidator(model_name=model_name)
        
        task_desc = f"Extract {duct_type.lower()} ducts from the provided artifacts. Use ingest_category_files_tool to look for duct data, then call exit_loop_level_4."
        
        result = await validator.run_validation(agent, task_desc, initial_state=initial_state)
        return result
    except Exception as e:
        res = ValidationResult(model_name, f"{duct_type}DuctAgent")
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
        for duct_type in ["Horizontal", "Vertical"]:
            all_results.append(await validate_ducts(model, duct_type))
    
    print_validation_report(all_results)

if __name__ == "__main__":
    asyncio.run(main())
