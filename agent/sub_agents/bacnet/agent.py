from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner
from google.genai import types
from google.adk.tools import load_artifacts
from sub_agents.loop_agents.loop_wrapper import LoopWrapper
from sub_agents.tools.loop_exit_tools import exit_loop_level_4
from sub_agents.tools.ingest_category_tool import ingest_category_files_tool
from tools.progress_tool import update_step, update_status, update_state
from utils.callback_utils import shared_model_callback as model_callback, shared_before_model_callback as before_model_callback
from utils.prompt_utils import load_composed_prompt
from utils.models import get_adk_model
from typing import Any

class BacnetLlmAgent(LoopWrapper):
    """
    Public Interface: Loop-wrapped Bacnet Agent.
    """
    def __init__(self, model_name: str, tools: list[Any] = None, session_id: str = None):
        internal_agent = BacnetAgentInternal(
            model_name=model_name,
            tools=tools,
            session_id=session_id
        )
        super().__init__(
            name="BacnetAgent",
            agent=internal_agent,
            description="Extracts BACnet technical metadata.",
            max_iterations=20
        )

class BacnetAgentInternal(LlmAgent):
    def __init__(self, model_name: str, tools: list[Any] = None, session_id: str = None):
        planner = None
        if "thinking" in model_name.lower() or "gemini-3" in model_name.lower():
             thinking_config = types.ThinkingConfig(
                 include_thoughts=True,
                 thinking_level="high"
             )
             planner = BuiltInPlanner(thinking_config=thinking_config)

        instruction = load_composed_prompt(
            "sub_agents/bacnet/prompt.md",
            ["skills/skill-parse-csv/SKILL.md"]
        )

        default_tools = [
            ingest_category_files_tool,
            load_artifacts,
            update_step,
            update_status,
            update_state,
            exit_loop_level_4
        ]

        all_tools = default_tools + (tools or [])
        unique_tools = list({t.__name__ if hasattr(t, '__name__') else str(t): t for t in all_tools}.values())

        super().__init__(
            name="BacnetAgentInternal",
            model=get_adk_model(model_name),
            instruction=instruction,
            tools=unique_tools,
            after_model_callback=model_callback,
            before_model_callback=before_model_callback,
            planner=planner,
            generate_content_config=types.GenerateContentConfig(temperature=0.0),
        )
