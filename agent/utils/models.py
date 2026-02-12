from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
import uuid

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
