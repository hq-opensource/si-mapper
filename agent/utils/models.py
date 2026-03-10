from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Union, Any
import uuid
import os

# New import for LiteLLM support
try:
    from google.adk.models.lite_llm import LiteLlm
except ImportError:
    LiteLlm = None

def get_adk_model(model_name: str) -> Union[str, Any]:
    """
    Returns the appropriate ADK model object or string.
    If 'gemini' is in the name, returns the string (native Gemini).
    Otherwise, returns a LiteLlm instance (for multi-provider support).
    Automatically adds 'anthropic/' or 'openai/' prefixes if missing.
    """
    if not model_name:
        raise ValueError("Model name must be provided via SHARED_ADK_MODEL.")
    
    if "gemini" in model_name.lower():
        # Native ADK Gemini support
        return model_name
    
    # Auto-prefix for LiteLLM if not already present
    full_model_name = model_name
    if "/" not in model_name:
        if "claude" in model_name.lower():
            full_model_name = f"anthropic/{model_name}"
        elif "gpt" in model_name.lower():
            full_model_name = f"openai/{model_name}"
    
    if LiteLlm:
        return LiteLlm(model=full_model_name)
    
    return full_model_name

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    WORKING = "working"
    VERIFICATION_READY = "verification_ready"
    VERIFIED = "verified"
    FAILED = "failed"

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    status: TaskStatus = TaskStatus.PENDING
    agent_name: Optional[str] = None
    retry_count: int = 0
    
    # Structured context for design reconstruction
    equipment_name: Optional[str] = None
    equipment_type: Optional[str] = None
    location_description: Optional[str] = None

    # Multi-agent technical mapping flags (Independent Statuses)
    bacnet_status: TaskStatus = TaskStatus.PENDING
    control_status: TaskStatus = TaskStatus.PENDING
    electricity_status: TaskStatus = TaskStatus.PENDING
    
    tags: list[str] = []
