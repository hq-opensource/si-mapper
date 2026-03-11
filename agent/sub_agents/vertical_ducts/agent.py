from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner
from google.genai import types
from google.adk.tools import load_artifacts
from sub_agents.tools.ingest_category_tool import ingest_category_files_tool
from sub_agents.tools.loop_exit_tools import exit_loop_level_4
from sub_agents.loop_agents.loop_wrapper import LoopWrapper
from tools.progress_tool import update_step, update_status, update_state
from utils.callback_utils import shared_model_callback as model_callback
from utils.prompt_utils import load_prompt_instruction
from utils.models import get_adk_model
from typing import Any

class VerticalDuctLlmAgent(LoopWrapper):
    """
    Public Interface: Loop-wrapped Vertical Duct Agent.
    """
    def __init__(self, model_name: str, tools: list[Any] = None, session_id: str = None):
        # Instantiate the inner LLM agent
        internal_agent = VerticalDuctLlmAgentInternal(
            model_name=model_name, 
            tools=tools, 
            session_id=session_id
        )
        # Wrap it
        super().__init__(
            name="VerticalDuctAgent",
            agent=internal_agent,
            description="Extracts vertical ducts.",
            max_iterations=10
        )

# Internal class definition to keep the file structure clean
class VerticalDuctLlmAgentInternal(LlmAgent):
    def __init__(self, model_name: str, tools: list[Any] = None, session_id: str = None):
        planner = None
        if "thinking" in model_name.lower() or "gemini-3" in model_name.lower():
            thinking_config = types.ThinkingConfig(include_thoughts=True)
            planner = BuiltInPlanner(thinking_config=thinking_config)
        
        instruction = load_prompt_instruction("sub_agents/vertical_ducts/prompt.md")

        default_tools = [ingest_category_files_tool, load_artifacts, update_step, update_status, update_state, exit_loop_level_4]
        all_tools = default_tools + (tools or [])
        unique_tools = list({t.__name__ if hasattr(t, '__name__') else str(t): t for t in all_tools}.values())

        super().__init__(
            name="VerticalDuctAgentInternal",
            model=get_adk_model(model_name),
            instruction=instruction,
            tools=unique_tools,
            after_model_callback=model_callback,
            planner=planner,
            generate_content_config=types.GenerateContentConfig(temperature=0.0),
        )
