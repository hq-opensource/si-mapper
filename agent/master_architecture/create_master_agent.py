
from typing import List
from google.adk.agents import LoopAgent
from master_architecture.level_2_master_main_loop import MasterMainLoopAgent
from master_architecture.level_3_master_main_llm import MasterLlmAgent
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.agents import LlmAgent
from google.adk.tools import McpToolset
from utils.logging_config import configure_logging
from tools.task_tools import add_task, set_task_status, enqueue_grid_tasks, mark_technical_progress
from tools.state_tools import save_agent_state, get_agent_state

# --- Configuration ---
load_dotenv()
logger = configure_logging()

def create_inner_master_agent(
    master_agent: MasterLlmAgent, 
    session_id: str
) -> LoopAgent:
    """
    Factory function to build the full Master Architecture hierarchy.
    """
    # Level 2: Main Loop
    main_loop = MasterMainLoopAgent(master_llm=master_agent, session_id=session_id)

    return main_loop


def create_master_agent(session_id: str, subagents:List[LoopAgent], model_name: str, si_mapper_toolset: McpToolset) -> LlmAgent:
    """Creates the Master orchestrator agent hierarchy."""
    logger.debug(f"Creating Master Orchestrator for session {session_id}")

    # 1. Instantiate Level 3 Agents
    task_tools = [
        add_task, 
        set_task_status, 
        save_agent_state, 
        get_agent_state, 
        enqueue_grid_tasks, 
        mark_technical_progress
    ]
    
    master_agent = MasterLlmAgent(
        model_name=model_name,
        subagents=subagents,
        tools=[si_mapper_toolset] + task_tools,
        session_id=session_id
    )

    # 2. Create the Hierarchy
    master_main_loop = create_inner_master_agent(
        master_agent=master_agent,
        session_id=session_id
    )

    return master_main_loop

