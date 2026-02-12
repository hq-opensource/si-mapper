from __future__ import annotations
import time
from typing import Optional, List, Any, Dict
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
import logging
from .string_utils import format_agent_name

logger = logging.getLogger(__name__)

# Global store to bridge real-time updates from any agent (Master or Sub-agent)
GLOBAL_SESSION_STORE = {}

def shared_model_callback(
    callback_context: CallbackContext, 
    llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """
    Unified callback to process LLM responses, transform content for frontend,
    and persist thoughts/tool calls to the session state for polling.
    """
    agent_name = callback_context.agent_name
    state = callback_context.state
    
    # Update active agent in state
    state["active_agent"] = agent_name
    
    # Extract session ID if possible
    session_id = getattr(callback_context, "session_id", "default-session")
    if not session_id or session_id == "Unknown":
        session_id = "default-session"
    
    # Process all agents that have this callback registered
    pass

    if not llm_response.content or not llm_response.content.parts:
        return llm_response

    # 1. NEW: Process structured events
    from .event_processor import EventProcessor
    from .events import EventType
    
    # Generate fresh events for this chunk (Enables appending behavior in frontend)
    new_events = EventProcessor.process_parts(agent_name, llm_response)
    
    # 2. Update local state history
    events_history = state.get("events", [])
    for ne in new_events:
        # Every chunk from a stream is treated as a new unique event to ensure history is preserved
        events_history.append(ne.model_dump())
    
    state["events"] = events_history[-200:] # Keep more history for complex loops

    # ... (Step 3: backward compatibility fields simplified for length)
    thoughts_list = []
    tools_list = []
    for e in state["events"]:
        if e["event_type"] in [EventType.BRAINSTORM, EventType.DELEGATION]:
            thoughts_list.append({"id": e["id"], "content": e["content"], "agentName": e["agent_name"], "timestamp": e["timestamp"]})
        elif e["event_type"] in [EventType.ACTION_TRIGGER, EventType.STATE_MUTATION]:
            tools_list.append({"id": e["id"], "content": e["content"], "agentName": e["agent_name"], "timestamp": e["timestamp"]})
    state["thoughts"] = thoughts_list[-100:]
    state["tool_calls"] = tools_list[-100:]

    # 4. Transform parts for frontend chat display
    new_parts = []
    for i, part in enumerate(llm_response.content.parts):
        is_thought = getattr(part, "thought", False)
        fn_call = getattr(part, "function_call", None)
        text = part.text or ""
        
        # If native thought summary
        if is_thought:
            clean_text = text.replace(":::thought\n", "").replace(":::thought", "").replace("\n:::\n", "").replace("\n:::", "").replace(":::", "").strip()
            # Wrap in markers for UI highlighting
            part.text = f":::thought\n{clean_text}\n:::\n"
        elif fn_call:
            ui_marker = f"Calling tool: **{fn_call.name}**"
            ui_text = f":::tool_call\n{ui_marker}\nArguments: `{fn_call.args}`\n:::\n"
            try:
                ui_part = type(part)(text=ui_text)
                new_parts.append(ui_part)
            except: pass
        else:
            pass
        new_parts.append(part)

    # 5. --- GLOBAL STORE UPDATE (Deduplicated Merging) ---
    try:
        current_state_dict = state.to_dict() if hasattr(state, "to_dict") else dict(state)
        
        if session_id not in GLOBAL_SESSION_STORE:
            GLOBAL_SESSION_STORE[session_id] = {}
        
        target_store = GLOBAL_SESSION_STORE[session_id]
        
        # Lists that need careful merging/deduplication
        list_keys = ["events", "thoughts", "tool_calls", "tasks"]
        
        for key, value in current_state_dict.items():
            if key in list_keys and isinstance(value, list):
                existing_list = target_store.get(key, [])
                
                # Deduplicate based on 'id' or 'trace_id'
                new_list = list(existing_list)
                for item in value:
                    item_id = item.get("id") or item.get("trace_id")
                    
                    found_idx = -1
                    for i, existing_item in enumerate(new_list):
                        if (existing_item.get("id") == item_id and item_id) or \
                           (existing_item.get("trace_id") == item_id and item_id):
                            found_idx = i
                            break
                    
                    if found_idx >= 0:
                        new_list[found_idx] = item
                    else:
                        new_list.append(item)
                
                target_store[key] = new_list[-100:] # Maintain buffer
            else:
                # Direct update for status, active_agent, plan, etc.
                target_store[key] = value
                
        GLOBAL_SESSION_STORE["latest"] = GLOBAL_SESSION_STORE[session_id]
    except Exception as e:
        logger.warning(f"Failed to update GLOBAL_SESSION_STORE: {e}")

    # --- VERBOSE LOGGING FOR DEBUGGING---
    # print(f"\n{'='*20} ADK AGENT UPDATE ({format_agent_name(agent_name)}) {'='*20}")
    # print(f"  - Session: {session_id}")
    
    # Calculate Metrics
    text_len = sum(len(p.text) for p in llm_response.content.parts if p.text)
    blob_count = sum(1 for p in llm_response.content.parts if p.inline_data)
    tool_calls = [p.function_call.name for p in llm_response.content.parts if p.function_call]
    
    # print(f"  - Response Size: {len(llm_response.content.parts)} parts ({text_len} chars, {blob_count} blobs)")
    if tool_calls:
        # print(f"  - Tool Calls: {', '.join(tool_calls)}")
        pass

    try:
        for key in ["status", "current_step", "active_agent"]:
            val = current_state_dict.get(key)
            if val:
                # print(f"  - {key.upper()}: {val}")
                pass
        
        # Log counts of complex objects
        for key in ["events", "tasks", "thoughts"]:
            val = current_state_dict.get(key)
            if isinstance(val, list):
                # print(f"  - {key.upper()} Count: {len(val)}")
                pass
    except Exception as e:
        # print(f"  - Logging Error: {e}")
        pass
    # print(f"{'='*60}\n")

    # Replace parts
    llm_response.content.parts = new_parts

    # Invocation Control
    has_action = any(getattr(p, "function_call", None) for p in llm_response.content.parts)
    has_real_text = any((p.text and p.text.strip() and not getattr(p, "thought", False) and ":::tool_call" not in p.text) for p in llm_response.content.parts)

    if llm_response.content.role == 'model' and (has_action or has_real_text):
        callback_context._invocation_context.end_invocation = True
                
    return llm_response
