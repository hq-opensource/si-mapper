import re
import json
from typing import List, Optional, Any
from google.adk.models import LlmResponse
from .events import AgentEvent, EventType

class EventProcessor:
    """
    Transforms raw model parts into structured AgentEvents.
    """
    
    @staticmethod
    def process_parts(agent_name: str, llm_response: LlmResponse, metrics: Optional[dict] = None) -> List[AgentEvent]:
        events = []
        import time 
        import uuid
        
        # Unique turn_id for every call (prevents overwriting in frontend streaming)
        turn_id = f"{agent_name}_{str(uuid.uuid4())[:8]}_{int(time.time() * 1000)}"
        
        for i, part in enumerate(llm_response.content.parts):
            is_thought = getattr(part, "thought", False)
            fn_call = getattr(part, "function_call", None)
            text = getattr(part, "text", "") or ""
            trace_id = f"{turn_id}_{i}"
            
            # Extract content: prefer native thought field, fall back to marker detection
            is_marker_thought = ":::thought" in text
            
            if is_thought or is_marker_thought:
                # Clean thought text
                clean_text = text.replace(":::thought\n", "").replace(":::thought", "").replace("\n:::\n", "").replace("\n:::", "").replace(":::", "").strip()
                
                # Detect delegation in thought text (heuristic)
                event_type = EventType.BRAINSTORM
                if "Delegating" in clean_text or "handing off" in clean_text.lower():
                    event_type = EventType.DELEGATION
                
                events.append(AgentEvent(
                    agent_name=agent_name,
                    event_type=event_type,
                    content=clean_text,
                    trace_id=trace_id,
                    metadata=metrics or {}
                ))
                
            elif fn_call:
                # Format arguments nicely
                try:
                    args_str = json.dumps(fn_call.args, indent=2) if isinstance(fn_call.args, dict) else str(fn_call.args)
                except:
                    args_str = str(fn_call.args)
                
                # Check for state mutation tools
                state_tools = ["update_step", "update_status", "update_state", "register_equipment_type"]
                event_type = EventType.STATE_MUTATION if fn_call.name in state_tools else EventType.ACTION_TRIGGER
                
                # Check for delegation tools
                delegation_tools = ["PARMainLoopAgent", "ExtractionAgent", "OntologyAgent"]
                if fn_call.name in delegation_tools:
                    event_type = EventType.DELEGATION

                event_metadata = {
                        "tool_name": fn_call.name,
                        "arguments": fn_call.args,
                        "pretty_args": args_str
                }
                if metrics:
                    event_metadata.update(metrics)

                events.append(AgentEvent(
                    agent_name=agent_name,
                    event_type=event_type,
                    content=f"Calling tool: **{fn_call.name}**",
                    metadata=event_metadata,
                    trace_id=trace_id
                ))
            
            elif text.strip() and ":::tool_call" not in text:
                # Final response text
                events.append(AgentEvent(
                    agent_name=agent_name,
                    event_type=EventType.TEXT_RESPONSE,
                    content=text.strip(),
                    trace_id=trace_id,
                    metadata=metrics or {}
                ))
                
        # If we have metrics but no text response (e.g. only tool calls), 
        # ensure metrics are on at least one event (the last one)
        if metrics and events:
            events[-1].metadata.update(metrics)
            
        return events
