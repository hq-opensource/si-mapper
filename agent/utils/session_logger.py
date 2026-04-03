"""Per-session JSONL event logger for offline analysis."""
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

_HERE = os.path.dirname(os.path.abspath(__file__))
_AGENT_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
_LOGS_DIR = os.path.join(_AGENT_ROOT, "logs", "sessions")


def log_events(session_id: str, events: list[dict]) -> None:
    """Append serialized AgentEvent dicts as JSONL lines to the session log file.

    Args:
        session_id: The ADK session ID (e.g., "session-a1b2c3d4").
        events: List of dicts from AgentEvent.model_dump(mode="json").
    """
    if not events:
        return
    date_str = datetime.now().strftime("%Y%m%d")
    log_path = os.path.join(_LOGS_DIR, f"{session_id}_{date_str}.jsonl")
    os.makedirs(_LOGS_DIR, exist_ok=True)
    try:
        with open(log_path, "a", encoding="utf-8") as fh:
            for event in events:
                fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError as exc:
        logger.warning("session_logger: write failed: %s", exc)
