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
from tools.state_tools import save_agent_state, get_agent_state, get_active_project, get_active_system
from tools.internal_grid_tools import (
    add_component, add_components_batch, delete_component,
    delete_components_batch, read_internal_grid,
    update_component_metadata, update_component_metadata_batch
)
from tools.load_ttl_to_neo4j_tool import load_ttl_to_neo4j_tool
from tools.neo4j_query_tools import (
    execute_cypher_tool,
    execute_cypher_batch_tool,
    get_graph_schema_tool,
    search_graph_entities_tool,
)
from tools.ontology_tools import (
    read_python_files,
    scan_python_folder,
    search_class_mapping,
    write_ontology,
    execute_ontology,
    extract_lessons,
)

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
        get_active_project,
        get_active_system,
        # Internal grid tools
        add_component,
        add_components_batch,
        delete_component,
        delete_components_batch,
        read_internal_grid,
        update_component_metadata,
        update_component_metadata_batch,
        load_ttl_to_neo4j_tool,
        # Neo4j query tools
        execute_cypher_tool,
        execute_cypher_batch_tool,
        get_graph_schema_tool,
        search_graph_entities_tool,
        # Ontology tools
        read_python_files,
        scan_python_folder,
        search_class_mapping,
        write_ontology,
        execute_ontology,
        extract_lessons,
    ]

    all_subagents = subagents or []

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

