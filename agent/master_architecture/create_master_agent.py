
import pathlib
from typing import List
from google.adk.agents import LoopAgent
from master_architecture.level_2_master_main_loop import MasterMainLoopAgent
from master_architecture.level_3_master_main_llm import MasterLlmAgent
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.skills import load_skill_from_dir
from google.adk.tools import skill_toolset
from utils.logging_config import configure_logging
from tools.state_tools import save_agent_state, get_agent_state
from tools.internal_grid_tools import (
    add_component, add_components_batch, delete_component,
    delete_components_batch, read_internal_grid
)
from tools.metadata_tools import write_metadata, write_metadata_batch
from master_architecture.tools.capture_frontend_state_tool import capture_frontend_state_tool
from sub_agents.ontology_generator.agent import OntologyGeneratorAgent
from sub_agents.ontology_validator.agent import OntologyValidatorAgent

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


def create_master_agent(session_id: str, model_name: str, subagents: List[LoopAgent] = None) -> LlmAgent:
    """Creates the Master orchestrator agent hierarchy."""
    logger.debug(f"Creating Master Orchestrator for session {session_id}")

    # --- 1. Load Skills from agent/skills ---
    skills_root = pathlib.Path(__file__).parent.parent / "skills"
    loaded_skills = []
    
    if skills_root.exists():
        for skill_dir in skills_root.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                try:
                    skill = load_skill_from_dir(skill_dir)
                    loaded_skills.append(skill)
                    logger.debug(f"Loaded skill: {skill_dir.name}")
                except Exception as e:
                    logger.error(f"Failed to load skill from {skill_dir}: {e}")
    
    # --- 2. Create the SkillToolset ---
    skill_tools = skill_toolset.SkillToolset(skills=loaded_skills)

    task_tools = [
        save_agent_state,
        get_agent_state,
        # Internal grid tools
        add_component,
        add_components_batch,
        delete_component,
        delete_components_batch,
        read_internal_grid,
        # Metadata tools (write BACnet/control data to GraphyVAC custom-fields)
        write_metadata,
        write_metadata_batch,
        capture_frontend_state_tool,
    ]
    
    # --- Ontology sub-agents (flat, master sequences them) ---
    ontology_subagents = [
        OntologyGeneratorAgent(model_name=model_name),
        OntologyValidatorAgent(model_name=model_name),
    ]
    all_subagents = (subagents or []) + ontology_subagents

    master_agent = MasterLlmAgent(
        model_name=model_name,
        subagents=all_subagents,
        tools=[skill_tools] + task_tools,
        session_id=session_id
    )

    # 2. Create the Hierarchy
    master_main_loop = create_inner_master_agent(
        master_agent=master_agent,
        session_id=session_id
    )

    return master_main_loop

