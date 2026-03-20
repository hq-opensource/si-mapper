from __future__ import annotations
import time
from typing import Optional, List, Any, Dict
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
import logging
from .string_utils import format_agent_name
from .grid_sync_agent_to_graphivac import _run_sync_out

logger = logging.getLogger(__name__)

# ── Per-call timing: keyed by agent_name ─────────────────────────────────────
# Set by shared_before_model_callback, consumed by shared_model_callback.
_call_start_times: Dict[str, float] = {}

# Global store to bridge real-time updates from any agent (Master or Sub-agent)
GLOBAL_SESSION_STORE = {}


def _log_artifact_visibility(agent_name: str, llm_request: Any) -> None:
    """
    Scans llm_request.contents for artifact data (inline_data blobs in tool
    responses) and logs a clear summary so we can confirm whether the model
    is actually receiving image/artifact bytes on this LLM call.
    """
    SEP = "─" * 68
    contents = getattr(llm_request, "contents", None)
    if not contents:
        return

    artifact_summary: list[str] = []
    tool_response_blobs: list[str] = []

    for turn_idx, content in enumerate(contents):
        role = getattr(content, "role", "?")
        parts = getattr(content, "parts", []) or []
        for part_idx, part in enumerate(parts):
            # inline_data on any part (e.g. from a load_artifacts tool response)
            inline = getattr(part, "inline_data", None)
            if inline:
                mime = getattr(inline, "mime_type", "?")
                data = getattr(inline, "data", b"") or b""
                size_kb = len(data) / 1024
                artifact_summary.append(
                    f"  turn[{turn_idx}] part[{part_idx}] role={role} "
                    f"→ BLOB mime={mime} size={size_kb:.1f}KB"
                )
            # function_response that carries parts (ADK wraps tool output)
            fn_resp = getattr(part, "function_response", None)
            if fn_resp:
                fn_name = getattr(fn_resp, "name", "?")
                resp_val = getattr(fn_resp, "response", None)
                # ADK may nest parts inside the function response value
                nested_parts = None
                if isinstance(resp_val, dict):
                    nested_parts = resp_val.get("parts") or resp_val.get("content")
                if nested_parts:
                    for np_idx, np in enumerate(nested_parts if isinstance(nested_parts, list) else [nested_parts]):
                        np_inline = getattr(np, "inline_data", None) if not isinstance(np, dict) else None
                        if np_inline:
                            mime = getattr(np_inline, "mime_type", "?")
                            data = getattr(np_inline, "data", b"") or b""
                            size_kb = len(data) / 1024
                            tool_response_blobs.append(
                                f"  turn[{turn_idx}] part[{part_idx}] fn={fn_name} nested[{np_idx}] "
                                f"→ BLOB mime={mime} size={size_kb:.1f}KB"
                            )

    if artifact_summary or tool_response_blobs:
        print(f"\n{SEP}")
        print(f"  🖼️  ARTIFACT VISIBILITY CHECK — {agent_name}")
        print(SEP)
        print(f"  Total turns in context: {len(contents)}")
        if artifact_summary:
            print("  Inline blobs visible to model:")
            for line in artifact_summary:
                print(line)
        if tool_response_blobs:
            print("  Blobs inside tool responses:")
            for line in tool_response_blobs:
                print(line)
        print(f"  ✅ Model WILL see {len(artifact_summary) + len(tool_response_blobs)} artifact blob(s) this call.")
        print(f"{SEP}\n")
    else:
        # Only log this if load_artifacts was recently called (check last tool call in request)
        last_tool_call = None
        for content in reversed(contents):
            parts = getattr(content, "parts", []) or []
            for part in reversed(parts):
                fn_call = getattr(part, "function_call", None)
                if fn_call:
                    last_tool_call = getattr(fn_call, "name", None)
                    break
            if last_tool_call:
                break
        if last_tool_call == "load_artifacts":
            print(f"\n{SEP}")
            print(f"  ⚠️  ARTIFACT VISIBILITY CHECK — {agent_name}")
            print(SEP)
            print(f"  last tool call was 'load_artifacts' BUT no inline blobs found in request.")
            print(f"  ❌ Model will NOT see any artifact content this call — artifacts may have been dropped.")
            print(f"{SEP}\n")


def shared_before_model_callback(
    callback_context: CallbackContext,
    llm_request: Any,  # google.adk.models.llm_request.LlmRequest
) -> Optional[LlmResponse]:
    """
    Records the wall-clock start time of every LLM call so that
    shared_model_callback can compute the exact round-trip duration.
    Also logs artifact visibility so we can confirm the model actually
    receives image/blob data when load_artifacts is called.
    Returning None means "do not intercept — proceed normally".
    """
    _call_start_times[callback_context.agent_name] = time.perf_counter()
    _log_artifact_visibility(callback_context.agent_name, llm_request)
    return None


def _print_iteration_report(
    agent_name: str,
    llm_response: LlmResponse,
    elapsed: float | None,
) -> None:
    """
    Prints a concise per-LLM-call report to stdout:
      - Wall-clock time for the API round-trip
      - Token usage (prompt / completion / total / cached)
      - Estimated equivalent cost (informational for flat-rate Copilot subscriptions)
      - Tool calls that were triggered
      - Excerpts of the model's thinking (first 300 chars per thought block)
    """
    SEP = "─" * 68

    # ── Token usage ───────────────────────────────────────────────────────────
    usage = getattr(llm_response, "usage_metadata", None)
    prompt_tokens    = getattr(usage, "prompt_token_count",          0) or 0
    candidate_tokens = getattr(usage, "candidates_token_count",      0) or 0
    total_tokens     = getattr(usage, "total_token_count",           0) or 0
    cached_tokens    = getattr(usage, "cached_content_token_count",  0) or 0

    # ── Thought excerpts ──────────────────────────────────────────────────────
    thought_texts: List[str] = []
    tool_calls: List[str] = []
    has_final_text = False

    if llm_response.content and llm_response.content.parts:
        for part in llm_response.content.parts:
            if getattr(part, "thought", False) and part.text:
                raw = part.text.strip()
                excerpt = raw[:300] + ("…" if len(raw) > 300 else "")
                thought_texts.append(excerpt)
            fn = getattr(part, "function_call", None)
            if fn:
                tool_calls.append(fn.name)
            text = part.text or ""
            if text.strip() and not getattr(part, "thought", False) and ":::tool_call" not in text:
                has_final_text = True

    # ── Print ─────────────────────────────────────────────────────────────────
    kind = "FINAL RESPONSE" if has_final_text else ("TOOL CALL" if tool_calls else "THINKING")

    print(f"\n{SEP}")
    print(f"  📊 ITERATION REPORT  [{kind}]  — {agent_name}")
    print(SEP)
    if elapsed is not None:
        print(f"  ⏱  Time          : {elapsed:.2f} s")
    if total_tokens:
        cached_note = f"  ({cached_tokens:,} cached)" if cached_tokens else ""
        print(
            f"  🔢 Tokens        : {prompt_tokens:,} in  │  "
            f"{candidate_tokens:,} out  │  {total_tokens:,} total{cached_note}"
        )
    else:
        print("  🔢 Tokens        : (not reported by provider)")
    if tool_calls:
        print(f"  🔧 Tools called  : {', '.join(tool_calls)}")
    if thought_texts:
        print(f"  🧠 Thinking      :")
        for i, t in enumerate(thought_texts, 1):
            print(f"       [{i}] {t}")
    print(f"{SEP}\n")

async def shared_model_callback(
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
    
    # Extract session ID from invocation context
    try:
        session_id = callback_context.session.id
    except:
        session_id = "default-session"
    
    # Process all agents that have this callback registered
    pass

    if not llm_response.content or not llm_response.content.parts:
        return llm_response

    start = _call_start_times.pop(agent_name, None)
    elapsed = (time.perf_counter() - start) if start is not None else None
    
    # Extract token usage
    usage = getattr(llm_response, "usage_metadata", None)
    metrics = {
        "latency_s": elapsed,
        "prompt_tokens": getattr(usage, "prompt_token_count", 0),
        "completion_tokens": getattr(usage, "candidates_token_count", 0),
        "total_tokens": getattr(usage, "total_token_count", 0),
        "cached_tokens": getattr(usage, "cached_content_token_count", 0),
        "provider": "google",
    }

    # --- DEBUG: Print parts types ---
    parts_info = []
    for p in llm_response.content.parts:
        info = f"type(p)={type(p)}"
        if hasattr(p, 'thought'): info += f", thought={p.thought}"
        if hasattr(p, 'text'): info += f", text_len={len(p.text) if p.text else 0}"
        if hasattr(p, 'function_call'): info += f", fn={p.function_call.name if p.function_call else 'None'}"
        parts_info.append(info)
    logger.debug(f"[{agent_name}] Response Parts: {parts_info}")
    # --------------------------------

    # ── Artifact race-condition detector ──────────────────────────────────────
    # If the model calls load_artifacts AND other tools in the same turn, the
    # artifact content will be injected for the *next* LLM call but the model
    # won't have a chance to process it before more tool calls flush it out.
    fn_calls_in_response = [
        p.function_call.name
        for p in llm_response.content.parts
        if getattr(p, "function_call", None)
    ]
    if "load_artifacts" in fn_calls_in_response:
        other_tools = [t for t in fn_calls_in_response if t != "load_artifacts"]
        SEP = "─" * 68
        print(f"\n{SEP}")
        print(f"  📥 load_artifacts CALLED — {agent_name}")
        print(SEP)
        print(f"  All tool calls in this response: {fn_calls_in_response}")
        if other_tools:
            print(f"  ⚠️  WARNING: load_artifacts called alongside other tools: {other_tools}")
            print(f"  ⚠️  The artifact content will be injected NEXT call but model may not pause to read it!")
        else:
            print(f"  ✅ load_artifacts called alone — model should receive artifact content next call.")
        print(f"{SEP}\n")
    # ─────────────────────────────────────────────────────────────────────────

    # 1. NEW: Process structured events
    from .event_processor import EventProcessor
    from .events import EventType
    
    # Generate fresh events for this chunk (Enables appending behavior in frontend)
    new_events = EventProcessor.process_parts(agent_name, llm_response, metrics=metrics)
    logger.debug(f"[{agent_name}] Extracted {len(new_events)} new events")
    
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

    has_action = any(getattr(p, "function_call", None) for p in llm_response.content.parts)
    has_real_text = any(
        p.text and p.text.strip()
        and not getattr(p, "thought", False)
        and ":::tool_call" not in p.text
        for p in llm_response.content.parts
    )

    # Sync-out: fires only on the final model response (real text, no tool calls).
    # Gating on has_real_text prevents firing on every intermediate thinking/reasoning
    # chunk — without this, a thinking model triggers dozens of unnecessary PUTs
    # per turn (one per thought block). We only want to sync when the agent has
    # finished its reasoning and produced an actual response.
    if not has_action and has_real_text:
        await _run_sync_out(callback_context)

    # _print_iteration_report(agent_name, llm_response, elapsed)
    # ─────────────────────────────────────────────────────────────────────────

    return llm_response
