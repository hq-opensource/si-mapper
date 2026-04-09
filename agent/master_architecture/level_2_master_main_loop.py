
from typing import Any
from google.adk.agents import LoopAgent
from pydantic import PrivateAttr
from master_architecture.level_shared_utils import check_all_tasks_verified
from master_architecture.level_3_master_main_llm import MasterLlmAgent

class MasterMainLoopAgent(LoopAgent):
    """
    Level 2: Master Main Loop Agent.
    This agent makes a fast execution loop. 
    It decides if the tasks are simple and can be accomplished acting fast, or if the task needs to be delegated to a subagent.
    If it decides to act fast, it performs the actions directly.
    If it decides that more thorough planning and review is needed, then it delegates to the PARSequentialAgent.
    """

    def __init__(self, master_llm: MasterLlmAgent, session_id: str, max_iterations: int = 100):
        super().__init__(
            name="MasterMainLoopAgent",
            sub_agents=[master_llm],
            max_iterations=max_iterations,
            description="Orchestrator Agent. Decides to act directly or to delegate tasks."
        )
        self._session_id = session_id

    def is_loop_finished(self, state: dict[str, Any]) -> bool:
         # Terminates if all tasks are verified, or max iterations reached (handled by parent).
         if self.iterations >= self.max_iterations:
             return True
             
         if state.get("EXIT_LEVEL_2"):
             return True
             
         return check_all_tasks_verified(self._session_id)
