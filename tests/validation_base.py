
import os
import sys
import asyncio
import uuid
from typing import Any, List, Optional
from dotenv import load_dotenv
from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner

# Setup paths
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
agent_root = os.path.join(project_root, 'agent')
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if agent_root not in sys.path:
    sys.path.insert(0, agent_root)

# Load environment variables
load_dotenv(os.path.join(agent_root, ".env"))

class ValidationResult:
    def __init__(self, model_name: str, agent_name: str):
        self.model_name = model_name
        self.agent_name = agent_name
        self.success = False
        self.error = None
        self.tool_calls = []
        self.response = ""
        self.final_state = {}

class AgentValidator:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.session_service = InMemorySessionService()
        self.artifact_service = InMemoryArtifactService()

    async def run_validation(self, agent_instance: Any, task_description: str, initial_state: Optional[dict] = None) -> ValidationResult:
        result = ValidationResult(self.model_name, agent_instance.name)
        
        # Prepare session
        # Prepare session with initial state
        session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        session = await self.session_service.create_session(
            app_name="validation_app",
            user_id="test_user",
            session_id=session_id,
            state=initial_state or {}
        )
        
        if initial_state:
            print(f"DEBUG: Injected state keys: {list(initial_state.keys())}")
            if "tasks" in initial_state:
                print(f"DEBUG: Tasks count: {len(initial_state['tasks'])}")
        
        runner = Runner(
            agent=agent_instance,
            app_name="validation_app",
            session_service=self.session_service,
            artifact_service=self.artifact_service
        )
        
        content = types.Content(role='user', parts=[types.Part(text=task_description)])
        
        try:
            async for event in runner.run_async(
                user_id="test_user",
                session_id=session_id,
                new_message=content
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        result.response = event.content.parts[0].text
                    result.success = True
                    # Don't break yet, we want to see if more events come (unlikely but safe)
            
            # If we reached here, the agent has finished its execution
            if not result.success and result.error is None:
                result.success = True
            
            # Capture final state for further validation if needed
            final_session = await self.session_service.get_session(
                app_name="validation_app", 
                user_id="test_user", 
                session_id=session_id
            )
            result.final_state = final_session.state if final_session else {}
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            result.error = str(e)
            result.success = False
            
        return result

def print_validation_report(results: List[ValidationResult]):
    print("\n" + "="*60)
    print(f"{'VALIDATION REPORT':^60}")
    print("="*60)
    for res in results:
        status = "PASS" if res.success else "FAIL"
        print(f"[{status}] {res.agent_name:<20} | {res.model_name}")
        if not res.success:
            print(f"      Error: {res.error}")
        else:
            preview = res.response.replace('\n', ' ')[:80]
            print(f"      Response: {preview}...")
    print("="*60 + "\n")
