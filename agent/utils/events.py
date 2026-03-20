from enum import Enum
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field
import time
import uuid

class EventType(str, Enum):
    BRAINSTORM = "BRAINSTORM"         # Internal thoughts
    DELEGATION = "DELEGATION"         # Handing off to sub-agent
    ACTION_TRIGGER = "ACTION_TRIGGER" # Tool about to be called
    ACTION_RESULT = "ACTION_RESULT"   # Tool output (cleaned)
    STATE_MUTATION = "STATE_MUTATION" # UI state updates (tasks, plans)
    TEXT_RESPONSE = "TEXT_RESPONSE"   # Final text to user
    ARTIFACT = "ARTIFACT"             # Artifact loading/visibility logs

class AgentEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    agent_name: str
    event_type: EventType
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # helper for frontend merging
    trace_id: Optional[str] = None 
