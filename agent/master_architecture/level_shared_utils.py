
from typing import Any, Callable
import logging
import psycopg
from pydantic import PrivateAttr
from google.adk.agents import LoopAgent, LlmAgent

logger = logging.getLogger(__name__)

# Constants
PAR_SESSION_ID = "par_session_id"
# DB Connection String (Ideally loaded from env/config)
DB_CONN_STR = "postgresql://toolbox_user:my-password@127.0.0.1:5432/toolbox_db"

def check_pending_tasks_exist(session_id: str) -> bool:
    """Returns True if there are pending tasks for the session."""
    try:
        with psycopg.connect(DB_CONN_STR) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM agent_tasks WHERE session_id = %s AND status = 'pending' LIMIT 1",
                    (session_id,)
                )
                return cur.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking pending tasks: {e}")
        return False

def check_verification_tasks_exist(session_id: str) -> bool:
    """Returns True if there are tasks ready for verification."""
    try:
        with psycopg.connect(DB_CONN_STR) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM agent_tasks WHERE session_id = %s AND status = 'verification_ready' LIMIT 1",
                    (session_id,)
                )
                return cur.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking verification tasks: {e}")
        return False

def check_all_tasks_verified(session_id: str) -> bool:
    """Returns True if at least one task exists and ALL are verified."""
    try:
        with psycopg.connect(DB_CONN_STR) as conn:
            with conn.cursor() as cur:
                # Check if we have any tasks at all
                cur.execute("SELECT 1 FROM agent_tasks WHERE session_id = %s LIMIT 1", (session_id,))
                if not cur.fetchone():
                    return False # No tasks created yet? Or maybe success? Assuming we need tasks.
                
                # Check if any non-verified task exists
                cur.execute(
                    "SELECT 1 FROM agent_tasks WHERE session_id = %s AND status != 'verified' LIMIT 1",
                    (session_id,)
                )
                has_unverified = cur.fetchone() is not None
                return not has_unverified
    except Exception as e:
        logger.error(f"Error checking verified status: {e}")
        return False

class GenericLoopAgent(LoopAgent):
    """
    A LoopAgent that terminates based on a provided termination function.
    """
    _termination_fn_override: Callable[[dict[str, Any]], bool] | None = PrivateAttr(default=None)

    def __init__(
        self,
        name: str,
        sub_agent: LlmAgent,
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
        self._termination_fn_override = termination_fn

    def is_loop_finished(self, state: dict[str, Any]) -> bool:
        """Checks termination condition."""
        # Check standard max iterations first (handled by super usually, but explicit here for safety)
        if self.iterations >= self.max_iterations:
             logger.warning(f"{self.name} reached max iterations ({self.max_iterations}).")
             return True
             
        # Check injected termination function
        if not self._termination_fn_override:
            return False

        should_stop = self._termination_fn_override(state)
        
        # Log if we are stopping due to explicit exit tool
        if should_stop:
            if state.get("EXIT_LEVEL_4") or state.get("EXIT_LEVEL_2"):
                logger.debug(f"LoopAgent {self.name} stopping due to EXPLICIT EXIT TOOL signal.")
            else:
                logger.debug(f"LoopAgent {self.name} termination condition met.")
                
        return should_stop
