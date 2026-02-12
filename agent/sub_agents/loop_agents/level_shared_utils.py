
from typing import Any, Callable
import logging
import psycopg
from pydantic import PrivateAttr
from google.adk.agents import LoopAgent, LlmAgent, Agent

logger = logging.getLogger(__name__)

# Constants
PAR_SESSION_ID = "par_session_id"
# DB Connection String (Ideally loaded from env/config)
DB_CONN_STR = "postgresql://toolbox_user:my-password@127.0.0.1:5432/toolbox_db"

def check_pending_tasks_exist(state: dict[str, Any]) -> bool:
    """Returns True if there are pending tasks for the session in the state."""
    tasks = state.get("tasks", [])
    return any(t.get("status") == "pending" for t in tasks)

def check_verification_tasks_exist(state: dict[str, Any]) -> bool:
    """Returns True if there are tasks ready for verification in the state."""
    tasks = state.get("tasks", [])
    return any(t.get("status") == "verification_ready" for t in tasks)

def check_all_tasks_verified(state: dict[str, Any]) -> bool:
    """Returns True if at least one task exists and ALL are verified in the state."""
    tasks = state.get("tasks", [])
    if not tasks:
        return False
    return all(t.get("status") == "verified" for t in tasks)

class GenericLoopAgent(LoopAgent):
    """
    A LoopAgent that terminates based on a provided termination function.
    """
    _termination_fn: Callable[[dict[str, Any]], bool] = PrivateAttr()

    def __init__(
        self,
        name: str,
        sub_agent: Agent,
        termination_fn: Callable[[dict[str, Any]], bool],
        max_iterations: int = 20,
        description: str = ""
    ):
        super().__init__(
            name=name,
            sub_agents=[sub_agent],
            max_iterations=max_iterations,
            description=description
        )
        self._termination_fn = termination_fn

    def is_loop_finished(self, state: dict[str, Any]) -> bool:
        """Checks termination condition."""
        # Check standard max iterations first (handled by super usually, but explicit here for safety)
        if self.iterations >= self.max_iterations:
             logger.warning(f"{self.name} reached max iterations ({self.max_iterations}).")
             return True
             
        # Check injected termination function
        should_stop = self._termination_fn(state)
        
        # Log if we are stopping due to explicit exit tool
        if should_stop:
            if state.get("EXIT_LEVEL_4"):
                logger.info(f"LoopAgent {self.name} stopping due to EXPLICIT EXIT TOOL signal (EXIT_LEVEL_4).")
                # Reset the flag so that the NEXT loop in a sequence doesn't immediately terminate.
                state["EXIT_LEVEL_4"] = False
            
            # Reset the completed sub-agents list if it exists
            if "completed_sub_agents" in state:
                logger.info(f"LoopAgent {self.name} clearing completed_sub_agents for next run.")
                state["completed_sub_agents"] = []

            elif state.get("EXIT_LEVEL_2"):
                logger.info(f"LoopAgent {self.name} stopping due to EXPLICIT EXIT TOOL signal (EXIT_LEVEL_2).")
                # We do NOT reset EXIT_LEVEL_2 here, as it's intended for the Level 2 loop.
            else:
                logger.info(f"LoopAgent {self.name} termination condition met.")
                
        return should_stop
