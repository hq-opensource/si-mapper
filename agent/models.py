from pydantic import BaseModel
from typing import List, Dict, Any

class AgentState(BaseModel):
    """Shared state for the agent."""
    status: str = "idle"
    current_step: str = ""
    observed_steps: List[str] = []
    active_agent: str = ""
    tasks: List[Dict[str, Any]] = []
    data: Dict[str, Any] = {}
