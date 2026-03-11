
from google.adk.agents import LlmAgent
from google.adk.tools import McpToolset, AgentTool
from google.adk.planners import BuiltInPlanner
from google.genai import types
from google.adk.tools import load_artifacts

from master_architecture.tools.loop_exit_tools import exit_loop_level_2
from master_architecture.tools.ingest_category_tool import ingest_category_files_tool
from tools.progress_tool import update_step, update_status, update_plan, sync_tasks
from master_architecture.tools.callbacks import model_callback
from utils.prompt_utils import load_prompt_instruction
from utils.models import get_adk_model
from typing import Any

class MasterLlmAgent(LlmAgent):
    """
    Level 3: Master LLM Agent.
    Specialized LlmAgent that evaluates tasks and decides to delegate or not.
    """

    def __init__(self, model_name: str, tools: list[Any] = None, instruction: str = None, session_id: str = None, subagents: list[Any] = None):
        # Configure native Gemini 3 thinking via Planner
        planner = None
        if "thinking" in model_name.lower() or "gemini-3" in model_name.lower():
             thinking_config = types.ThinkingConfig(include_thoughts=True)
             planner = BuiltInPlanner(thinking_config=thinking_config)
        
        # Load instruction from markdown file only if no custom instruction is provided
        if not instruction:
            instruction = load_prompt_instruction("master_architecture/prompts/master_instruction.md")


        default_tools = [ingest_category_files_tool, load_artifacts, update_step, update_status, update_plan, sync_tasks, exit_loop_level_2]
        agent_tools = [AgentTool(agent=sa) for sa in (subagents or [])]
        final_tools = default_tools + (tools or []) + agent_tools

        model_config = types.GenerateContentConfig(temperature=1.0)

        super().__init__(
            name="MasterAgent",
            model=get_adk_model(model_name),
            instruction=instruction,
            tools=final_tools,
            after_model_callback=model_callback,
            planner=planner,
            generate_content_config=model_config,
        )
