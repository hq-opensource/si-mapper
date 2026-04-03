"""Per-session compact JSONL event logger for offline analysis.

Each line written is {"t": "<type>", "c": "<content>"}.
TEXT_RESPONSE (streaming output chunks) are dropped entirely.
Consecutive identical BRAINSTORM entries are deduplicated.
Markdown formatting is stripped from content.
"""
import json
import logging
import os
import re
from datetime import datetime

logger = logging.getLogger(__name__)

_HERE = os.path.dirname(os.path.abspath(__file__))
_AGENT_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
_LOGS_DIR = os.path.join(_AGENT_ROOT, "logs", "sessions")

# Streaming output chunks — not useful for analysis
_SKIP_TYPES = {"TEXT_RESPONSE"}

# Rename verbose ADK type names to readable labels
_TYPE_LABELS = {
    "BRAINSTORM": "BRAINSTORM",
    "DELEGATION": "DELEGATION",
    "ACTION_TRIGGER": "TOOL_CALL",
    "ACTION_RESULT": "TOOL_RESULT",
    "STATE_MUTATION": "STATE",
    "ARTIFACT": "ARTIFACT",
}

# Dedup: last BRAINSTORM content seen per session (in-process memory)
_last_brainstorm: dict[str, str] = {}


def _clean(text: str) -> str:
    """Strip markdown formatting and normalize whitespace for AI readability."""
    if not text:
        return ""
    # Remove triple-backtick code fences (keep inner text)
    text = re.sub(r"```[a-z]*\n?(.*?)```", r"\1", text, flags=re.DOTALL)
    # Remove bold/italic markers (**x**, *x*, ***x***)
    text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text, flags=re.DOTALL)
    # Remove inline backticks
    text = re.sub(r"`([^`]*)`", r"\1", text)
    # Remove :::tool_call / :::tool_result markers and similar
    text = re.sub(r":::[\w_]+", "", text)
    # Collapse all whitespace (newlines, tabs, multiple spaces) to single space
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _format_tool_call(event: dict) -> str:
    """Render ACTION_TRIGGER as tool_name(k=v, ...) from metadata."""
    meta = event.get("metadata") or {}
    tool_name = meta.get("tool_name", "unknown")
    args = meta.get("arguments") or {}
    if not args:
        return f"{tool_name}()"
    arg_str = ", ".join(
        f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in args.items()
    )
    return f"{tool_name}({arg_str})"


def _format_event(event: dict, session_id: str) -> dict | None:
    """Return a compact {"t": ..., "c": ...} dict, or None to skip."""
    etype = event.get("event_type", "")

    if etype in _SKIP_TYPES:
        return None

    label = _TYPE_LABELS.get(etype, etype)

    if etype == "ACTION_TRIGGER":
        content = _format_tool_call(event)
    else:
        content = _clean(event.get("content") or "")

    if not content:
        return None

    # Deduplicate consecutive identical BRAINSTORM entries (re-emission artifact)
    if etype == "BRAINSTORM":
        if _last_brainstorm.get(session_id) == content:
            return None
        _last_brainstorm[session_id] = content

    return {"t": label, "c": content}


def log_events(session_id: str, events: list[dict]) -> None:
    """Append compact JSONL entries to the session log file.

    Args:
        session_id: The ADK session ID (e.g., "session-a1b2c3d4").
        events: List of dicts from AgentEvent.model_dump(mode="json").
    """
    if not events:
        return

    formatted = [_format_event(e, session_id) for e in events]
    formatted = [f for f in formatted if f is not None]

    if not formatted:
        return

    date_str = datetime.now().strftime("%Y%m%d")
    log_path = os.path.join(_LOGS_DIR, f"{session_id}_{date_str}.jsonl")
    os.makedirs(_LOGS_DIR, exist_ok=True)
    try:
        with open(log_path, "a", encoding="utf-8") as fh:
            for entry in formatted:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        logger.warning("session_logger: write failed: %s", exc)
