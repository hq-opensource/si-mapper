from typing import Any, Callable
from google.adk.agents import LoopAgent
from pydantic import PrivateAttr

class LoopWrapper(LoopAgent):
    """
    A wrapper that turns a standard Agent into a LoopAgent with a custom termination condition.
    Use this to give an agent "retry" or "refinement" capabilities until it signals completion.
    """
    _termination_fn_override: Callable[[dict[str, Any]], bool] | None = PrivateAttr(default=None)

    def __init__(
        self,
        name: str,
        agent: Any,
        termination_fn: Callable[[dict[str, Any]], bool] = None,
        max_iterations: int = 10,
        description: str = ""
    ):
        super().__init__(
            name=name,
            sub_agents=[agent],
            max_iterations=max_iterations,
            description=description
        )
        self._termination_fn_override = termination_fn

    def _default_termination(self, state: dict[str, Any]) -> bool:
        """
        Default termination: Stop if the agent signaled explicit exit via tool.
        """
        if state.get("EXIT_LEVEL_4"):
            # We do NOT reset the flag immediately if we want to preserve state for inspection,
            # but for a reusable wrapper, resetting is safer.
            state["EXIT_LEVEL_4"] = False 
            return True
        return False

    def is_loop_finished(self, state: dict[str, Any]) -> bool:
        if self.iterations >= self.max_iterations:
             return True
             
        if self._termination_fn_override:
            return self._termination_fn_override(state)
        return self._default_termination(state)
