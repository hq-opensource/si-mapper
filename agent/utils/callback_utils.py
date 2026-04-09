from __future__ import annotations
import time
from typing import Optional, List, Any, Dict
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from google.genai import types as genai_types
import logging
from .string_utils import format_agent_name
from .events import AgentEvent, EventType
from .event_processor import EventProcessor
from .session_logger import log_events

logger = logging.getLogger(__name__)

# ── Per-call timing: keyed by agent_name ─────────────────────────────────────
# Set by shared_before_model_callback, consumed by shared_model_callback.
_call_start_times: Dict[str, float] = {}

# Global store to bridge real-time updates from any agent (Master or Sub-agent)
GLOBAL_SESSION_STORE = {}


def _log_artifact_visibility(callback_context: CallbackContext, llm_request: Any) -> None:
    """
    Scans llm_request.contents for artifact data (inline_data blobs in tool
    responses) and logs a clear summary so we can confirm whether the model
    is actually receiving image/artifact bytes on this LLM call.
    """
    agent_name = callback_context.agent_name
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
        pass

        # Emit event for frontend
        metadata = {
            "visibility_check": True,
            "turns_in_context": len(contents),
            "inline_blobs": artifact_summary,
            "tool_response_blobs": tool_response_blobs,
            "total_blobs": len(artifact_summary) + len(tool_response_blobs)
        }
        event = AgentEvent(
            agent_name=agent_name,
            event_type=EventType.ARTIFACT,
            content=f"🖼️ Artifact Visibility Check: {len(artifact_summary) + len(tool_response_blobs)} blobs visible",
            metadata=metadata
        )
        events_list = callback_context.state.get("events", [])
        events_list.append(event.model_dump())
        callback_context.state["events"] = events_list[-200:]
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
            pass

            # Emit event for frontend
            event = AgentEvent(
                agent_name=agent_name,
                event_type=EventType.ARTIFACT,
                content="⚠️ Artifact Visibility Check: NO blobs visible (possible drop!)",
                metadata={"visibility_check": True, "dropped": True}
            )
            events_list = callback_context.state.get("events", [])
            events_list.append(event.model_dump())
            callback_context.state["events"] = events_list[-200:]


async def _ensure_pending_artifacts_injected(
    callback_context: CallbackContext,
    llm_request: Any,
) -> None:
    """
    Sticky artifact re-injection safety net.

    ADK's load_artifacts tool injects artifact bytes only when the LAST entry
    in llm_request.contents is a load_artifacts function_response (see
    load_artifacts_tool.py _append_artifacts_to_llm_request, line ~212).
    When the model calls load_artifacts alongside other tools in the same
    response, those other tools' function_responses become the last entry,
    and ADK's check fires for the wrong tool — the image is never injected.

    This function detects that situation and manually re-injects the pending
    artifact bytes directly into llm_request.contents (in memory only, never
    written to session history — same as ADK's own approach).

    State lifecycle:
      - Set:   in shared_model_callback when model calls load_artifacts
               (stores requested artifact names in state["temp:_pending_artifacts"])
      - Clear: in shared_model_callback when model produces a non-tool text
               response (meaning it has processed the artifacts)
    """
    state = callback_context.state
    pending = state.get("temp:_pending_artifacts", [])
    if not pending:
        return

    # Check if ADK's own mechanism already fired (last content = load_artifacts response).
    # If so, don't double-inject.
    contents = getattr(llm_request, "contents", None) or []
    last_content_is_load_artifacts = (
        contents
        and getattr(contents[-1], "parts", None)
        and getattr(contents[-1].parts[0], "function_response", None)
        and contents[-1].parts[0].function_response.name == "load_artifacts"
    )
    if last_content_is_load_artifacts:
        return  # ADK handled it

    # Also skip if blobs are already present (e.g., from a prior injection this step).
    has_blobs = any(
        getattr(part, "inline_data", None)
        for content in contents
        for part in (getattr(content, "parts", []) or [])
    )
    if has_blobs:
        return

    # ADK's injection missed — inject manually.
    agent_name = callback_context.agent_name
    pass

    injected = []
    for name in pending:
        artifact = await callback_context.load_artifact(name)
        if artifact is None and not name.startswith("user:"):
            artifact = await callback_context.load_artifact(f"user:{name}")
        if artifact is None:
            logger.warning(f"  ⚠️  Artifact '{name}' not found in artifact service, skipping.")
            continue

        size_info = ""
        if artifact.inline_data and artifact.inline_data.data:
            size_info = f" ({len(artifact.inline_data.data) / 1024:.1f} KB, {artifact.inline_data.mime_type})"

        llm_request.contents.append(
            genai_types.Content(
                role="user",
                parts=[
                    genai_types.Part.from_text(text=f"Artifact {name} is:"),
                    artifact,
                ],
            )
        )
        injected.append(name)
        # Logged to frontend

    pass

    if injected:
        event = AgentEvent(
            agent_name=agent_name,
            event_type=EventType.ARTIFACT,
            content=f"🔄 Sticky Re-injection: {len(injected)} artifacts injected",
            metadata={"reinjection": True, "artifacts": injected}
        )
        events_list = callback_context.state.get("events", [])
        events_list.append(event.model_dump())
        callback_context.state["events"] = events_list[-200:]


async def shared_before_model_callback(
    callback_context: CallbackContext,
    llm_request: Any,  # google.adk.models.llm_request.LlmRequest
) -> Optional[LlmResponse]:
    """
    Records the wall-clock start time of every LLM call so that
    shared_model_callback can compute the exact round-trip duration.
    Also:
    - Logs artifact visibility to confirm the model receives image/blob data.
    - Re-injects pending artifacts when ADK's own injection mechanism missed
      them (happens when load_artifacts was called alongside other tools).
    Returning None means "do not intercept — proceed normally".
    """
    _call_start_times[callback_context.agent_name] = time.perf_counter()
    await _ensure_pending_artifacts_injected(callback_context, llm_request)
    _log_artifact_visibility(callback_context, llm_request)

    # Capture the current model name and persist it to session state.
    current_model = getattr(llm_request, "model", None)
    if current_model:
        callback_context.state["llm_model"] = current_model

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

def _extract_metrics(agent_name: str, llm_response: LlmResponse) -> Dict[str, Any]:
    """Pops the per-call start time and returns a timing + token-usage metrics dict."""
    start = _call_start_times.pop(agent_name, None)
    elapsed = (time.perf_counter() - start) if start is not None else None
    usage = getattr(llm_response, "usage_metadata", None)
    return {
        "latency_s": elapsed,
        "prompt_tokens": getattr(usage, "prompt_token_count", 0),
        "completion_tokens": getattr(usage, "candidates_token_count", 0),
        "total_tokens": getattr(usage, "total_token_count", 0),
        "cached_tokens": getattr(usage, "cached_content_token_count", 0),
        "provider": "google",
    }


def _debug_log_parts(agent_name: str, llm_response: LlmResponse) -> None:
    """Logs a structured debug summary of every part in the LLM response."""
    parts_info = []
    for p in llm_response.content.parts:
        info = f"type(p)={type(p)}"
        if hasattr(p, "thought"):
            info += f", thought={p.thought}"
        if hasattr(p, "text"):
            info += f", text_len={len(p.text) if p.text else 0}"
        if hasattr(p, "function_call"):
            info += f", fn={p.function_call.name if p.function_call else 'None'}"
        parts_info.append(info)
    logger.debug(f"[{agent_name}] Response Parts: {parts_info}")


def _manage_artifact_pending_state(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
    fn_calls_in_response: List[str],
) -> None:
    """
    Tracks artifact names requested via load_artifacts so the re-injection
    safety net (_ensure_pending_artifacts_injected) can act on the next call.
    Clears the pending list once the model produces a real text response.
    """
    agent_name = callback_context.agent_name
    state = callback_context.state

    if "load_artifacts" in fn_calls_in_response:
        requested_names: List[str] = []
        for p in llm_response.content.parts:
            fn_call = getattr(p, "function_call", None)
            if fn_call and fn_call.name == "load_artifacts":
                requested_names = (fn_call.args or {}).get("artifact_names", [])
                break
        if requested_names:
            state["temp:_pending_artifacts"] = requested_names

        other_tools = [t for t in fn_calls_in_response if t != "load_artifacts"]
        event = AgentEvent(
            agent_name=agent_name,
            event_type=EventType.ARTIFACT,
            content=f"📥 load_artifacts called for: {requested_names}",
            metadata={
                "load_artifacts": True,
                "requested_names": requested_names,
                "tool_calls": fn_calls_in_response,
                "other_tools": other_tools,
            },
        )
        events_list = state.get("events", [])
        events_list.append(event.model_dump())
        state["events"] = events_list[-200:]

    # Clear pending list once a real text response (not tool-call-only) arrives.
    has_text_response = any(
        p.text and p.text.strip() and not getattr(p, "thought", False)
        for p in llm_response.content.parts
    )
    if has_text_response and "load_artifacts" not in fn_calls_in_response:
        if state.get("temp:_pending_artifacts"):
            logger.debug(f"[{agent_name}] Clearing temp:_pending_artifacts (model produced text response)")
            state["temp:_pending_artifacts"] = []


def _process_and_update_events(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
    metrics: Dict[str, Any],
) -> None:
    """
    Runs the EventProcessor, appends new events to state history, and
    rebuilds the backward-compatible 'thoughts' / 'tool_calls' lists.
    """
    agent_name = callback_context.agent_name
    state = callback_context.state

    new_events = EventProcessor.process_parts(agent_name, llm_response, metrics=metrics)
    logger.debug(f"[{agent_name}] Extracted {len(new_events)} new events")

    events_history = state.get("events", [])
    # Dedup by (event_type, content) against recent history — ADK occasionally
    # re-emits the same response parts (re-emission artifact), producing
    # identical events with different IDs/trace_ids that bypass ID-based dedup.
    recent_signatures = {
        (e["event_type"], e["content"])
        for e in events_history[-20:]
    }
    for ne in new_events:
        sig = (ne.event_type, ne.content)
        if sig in recent_signatures:
            continue
        events_history.append(ne.model_dump())
        recent_signatures.add(sig)

    state["events"] = events_history[-200:] # Keep more history for complex loops
    # Persist new events to per-session JSONL log (best-effort, non-blocking)
    log_events(callback_context.session.id, [ne.model_dump(mode="json") for ne in new_events])

    thoughts_list: List[Dict] = []
    tools_list: List[Dict] = []
    for e in state["events"]:
        entry = {
            "id": e["id"],
            "content": e["content"],
            "agentName": e["agent_name"],
            "timestamp": e["timestamp"],
        }
        if e["event_type"] in [EventType.BRAINSTORM, EventType.DELEGATION]:
            thoughts_list.append(entry)
        elif e["event_type"] in [EventType.ACTION_TRIGGER, EventType.STATE_MUTATION]:
            tools_list.append(entry)
    state["thoughts"] = thoughts_list[-100:]
    state["tool_calls"] = tools_list[-100:]


def _transform_parts_for_frontend(llm_response: LlmResponse) -> List[Any]:
    """
    Rewrites response parts for the chat UI:
    - Wraps thought text in :::thought … ::: markers.
    - Prepends a human-readable :::tool_call … ::: part for every function call.
    """
    new_parts: List[Any] = []
    for part in llm_response.content.parts:
        is_thought = getattr(part, "thought", False)
        fn_call = getattr(part, "function_call", None)
        text = part.text or ""

        if is_thought:
            clean_text = (
                text.replace(":::thought\n", "")
                    .replace(":::thought", "")
                    .replace("\n:::\n", "")
                    .replace("\n:::", "")
                    .replace(":::", "")
                    .strip()
            )
            part.text = f":::thought\n{clean_text}\n:::\n"
        elif fn_call:
            ui_text = (
                f":::tool_call\nCalling tool: **{fn_call.name}**\n"
                f"Arguments: `{fn_call.args}`\n:::\n"
            )
            try:
                new_parts.append(type(part)(text=ui_text))
            except Exception:
                pass

        new_parts.append(part)
    return new_parts


def _update_global_store(callback_context: CallbackContext, session_id: str) -> None:
    """
    Merges the current session state into GLOBAL_SESSION_STORE, deduplicating
    list entries by their 'id' / 'trace_id' key so the frontend always sees a
    consistent, non-duplicated event stream.
    """
    state = callback_context.state
    try:
        current_state_dict = state.to_dict() if hasattr(state, "to_dict") else dict(state)

        if session_id not in GLOBAL_SESSION_STORE:
            GLOBAL_SESSION_STORE[session_id] = {}

        target_store = GLOBAL_SESSION_STORE[session_id]
        list_keys = ["events", "thoughts", "tool_calls"]
        
        for key, value in current_state_dict.items():
            if key in list_keys and isinstance(value, list):
                existing_list = target_store.get(key, [])
                new_list = list(existing_list)
                for item in value:
                    item_id = item.get("id") or item.get("trace_id")
                    found_idx = next(
                        (
                            i for i, ex in enumerate(new_list)
                            if item_id and (ex.get("id") == item_id or ex.get("trace_id") == item_id)
                        ),
                        -1,
                    )
                    if found_idx >= 0:
                        new_list[found_idx] = item
                    else:
                        new_list.append(item)
                target_store[key] = new_list[-100:]
            else:
                target_store[key] = value

        GLOBAL_SESSION_STORE["latest"] = GLOBAL_SESSION_STORE[session_id]
    except Exception as e:
        logger.warning(f"Failed to update GLOBAL_SESSION_STORE: {e}")


async def shared_model_callback(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> Optional[LlmResponse]:
    """
    Unified callback to process LLM responses, transform content for frontend,
    and persist thoughts/tool calls to the session state for polling.
    """
    agent_name = callback_context.agent_name
    state = callback_context.state

    state["active_agent"] = agent_name

    try:
        session_id = callback_context.session.id
    except Exception:
        session_id = "default-session"

    if not llm_response.content or not llm_response.content.parts:
        return llm_response

    # 1. Timing + token metrics
    metrics = _extract_metrics(agent_name, llm_response)

    # 2. Debug log parts structure
    _debug_log_parts(agent_name, llm_response)

    # 3. Artifact pending-state management
    fn_calls_in_response = [
        p.function_call.name
        for p in llm_response.content.parts
        if getattr(p, "function_call", None)
    ]
    _manage_artifact_pending_state(callback_context, llm_response, fn_calls_in_response)

    # 4. Process structured events + update backward-compat state fields
    _process_and_update_events(callback_context, llm_response, metrics)

    # 5. Rewrite parts for frontend display
    llm_response.content.parts = _transform_parts_for_frontend(llm_response)

    # 6. Sync to global session store
    _update_global_store(callback_context, session_id)

    return llm_response
