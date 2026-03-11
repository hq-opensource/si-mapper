from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner
from google.genai import types
from google.adk.tools import load_artifacts
from sub_agents.loop_agents.loop_wrapper import LoopWrapper
from sub_agents.tools.loop_exit_tools import exit_loop_level_4
from sub_agents.tools.ingest_category_tool import ingest_category_files_tool
from tools.task_tools import fetch_pending_task, mark_technical_progress, create_batch_tasks, fetch_batch_tasks, mark_technical_progress_batch, complete_tasks_batch
from tools.progress_tool import update_step, update_status, update_state
from utils.callback_utils import shared_model_callback as model_callback
from utils.prompt_utils import load_prompt_instruction
from utils.models import get_adk_model
from typing import Any

class ElectricityLlmAgent(LoopWrapper):
    """
    Public Interface: Loop-wrapped Electricity Agent.
    """
    def __init__(self, model_name: str, tools: list[Any] = None, session_id: str = None):
        internal_agent = ElectricityAgentInternal(
            model_name=model_name,
            tools=tools,
            session_id=session_id
        )
        super().__init__(
            name="ElectricityAgent",
            agent=internal_agent,
            description="Extracts electrical distribution and power technical data.",
            max_iterations=20
        )

class ElectricityAgentInternal(LlmAgent):
    def __init__(self, model_name: str, tools: list[Any] = None, session_id: str = None):
        planner = None
        if "thinking" in model_name.lower() or "gemini-3" in model_name.lower():
            thinking_config = types.ThinkingConfig(include_thoughts=True)
            planner = BuiltInPlanner(thinking_config=thinking_config)
        
        instruction = load_prompt_instruction("sub_agents/electricity/prompt.md")

        # Core tools for the Electricity extraction loop
        default_tools = [
            fetch_pending_task, 
            mark_technical_progress,
            fetch_batch_tasks,
            mark_technical_progress_batch,
            create_batch_tasks,
            complete_tasks_batch,
            ingest_category_files_tool,
            load_artifacts, 
            update_step, 
            update_status, 
            update_state, 
            exit_loop_level_4
        ]
        
        # Merge with any passed-in tools (like MCP write_metadata)
        all_tools = default_tools + (tools or [])
        unique_tools = list({t.__name__ if hasattr(t, '__name__') else str(t): t for t in all_tools}.values())

        super().__init__(
            name="ElectricityAgentInternal",
            model=get_adk_model(model_name),
            instruction=instruction,
            tools=unique_tools,
            after_model_callback=model_callback,
            planner=planner,
            generate_content_config=types.GenerateContentConfig(temperature=0.0),
        )
