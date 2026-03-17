"""
Unified standalone runner for the ASHRAE 223P agents.

Selects which agent to execute via a positional ``agent`` argument:

- ``generator``  — runs :class:`OntologyLlmAgent` alone (generates ontology.py)
- ``validator``  — runs :class:`OntologyValidatorAgent` alone (fixes ontology.py)
- ``pipeline``   — runs :class:`Ontology223PSequentialAgent` (generator → validator)

Usage
-----
::

    cd agent

    # full pipeline (default)
    python -m sub_agents._223p.run pipeline

    # generator only
    python -m sub_agents._223p.run generator

    # validator only
    python -m sub_agents._223p.run validator

    # override task, model, credentials
    python -m sub_agents._223p.run generator --model github_copilot/gpt-4o "Generate the ontology"
    python -m sub_agents._223p.run pipeline --github-token TOKEN --mcp-server-url http://host/mcp/

Environment variables (used when the matching CLI flag is omitted)
------------------------------------------------------------------
``MCP_SERVER_URL``   URL of the MCP server (default: http://localhost:8080/mcp/).
``GOOGLE_API_KEY``   Google ADK / Gemini API key.
``GITHUB_TOKEN``     GitHub Copilot token forwarded to LiteLLM.
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from typing import Any

# ── Path bootstrap ─────────────────────────────────────────────────────────────
# Resolve agent/ root (three levels up from sub_agents/_223p/run.py)
_agent_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

if not __package__:
    if _agent_root not in sys.path:
        sys.path.insert(0, _agent_root)
# ──────────────────────────────────────────────────────────────────────────────

# ── SSL Verification disabled ──────────────────────────────────────────────────
os.environ["SSL_CERT_FILE"] = ""
# ──────────────────────────────────────────────────────────────────────────────

from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from sub_agents._223p.agent import Ontology223PSequentialAgent
from sub_agents._223p.generator.agent import OntologyLlmAgent
from sub_agents._223p.validator.agent import OntologyValidatorAgent

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

_STANDALONE_DEFAULT_MODEL = "github_copilot/claude-sonnet-4.5"


_PIPELINE_DEFAULT_TASK = (
    "Follow the sequence of sub agents."
    "The result will be the creation a functional python and ttl file."
)

# ──────────────────────────────────────────────────────────────────────────────
# Agent registry
#
# Each entry describes how to build the agent and how to run it.
#   factory          – callable(model_name, tools) → agent instance
#   default_task     – task string used when none is supplied on the CLI
#   app_name         – ADK app_name for session/runner namespacing
#   session_prefix   – prefix for the generated session id
#   max_iterations   – displayed in log messages; None means no limit shown
#   label            – human-readable name used in log messages
#   multi_part_resp  – True → join up to 5 text parts; False → take first part
# ──────────────────────────────────────────────────────────────────────────────

_AGENT_REGISTRY: dict[str, dict[str, Any]] = {
    "generator": {
        "label": "Generator",
        "app_name": "ontology_standalone",
        "session_prefix": "standalone",
        "max_iterations": 50,
        "default_task": "",
        "factory": lambda model_name, tools: OntologyLlmAgent(
            model_name=model_name, tools=tools
        ),
        "multi_part_resp": False,
    },
    "validator": {
        "label": "Validator",
        "app_name": "ontology_validator_standalone",
        "session_prefix": "validator-standalone",
        "max_iterations": 100,
        "default_task": "",
        "factory": lambda model_name, tools: OntologyValidatorAgent(
            model_name=model_name, tools=tools
        ),
        "multi_part_resp": True,
    },
    "pipeline": {
        "label": "Pipeline",
        "app_name": "ontology_pipeline_standalone",
        "session_prefix": "pipeline",
        "max_iterations": None,
        "default_task": _PIPELINE_DEFAULT_TASK,
        "factory": lambda model_name, tools: Ontology223PSequentialAgent(
            model_name=model_name, tools=tools
        ),
        "multi_part_resp": False,
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# Unified runner
# ──────────────────────────────────────────────────────────────────────────────


class Ontology223PRunner:
    """
    Thin harness that runs any of the three ASHRAE 223P agents as a standalone
    process, independently of the main FastAPI service.

    Parameters
    ----------
    mcp_server_url:
        URL of the MCP server.  Falls back to ``MCP_SERVER_URL`` env var, then
        ``http://localhost:8080/mcp/``.
    google_api_key:
        Google ADK / Gemini API key.  Falls back to ``GOOGLE_API_KEY`` env var.
    github_token:
        GitHub Copilot token forwarded to LiteLLM.  Falls back to
        ``GITHUB_TOKEN`` env var.
    model_name:
        Model name passed to the chosen agent.  Defaults to
        ``_STANDALONE_DEFAULT_MODEL``.
    """

    iteration: int = 0

    def __init__(
        self,
        mcp_server_url: str | None = None,
        google_api_key: str | None = None,
        github_token: str | None = None,
        model_name: str = _STANDALONE_DEFAULT_MODEL,
    ) -> None:
        self.mcp_server_url = mcp_server_url or os.getenv(
            "MCP_SERVER_URL", "http://localhost:8080/mcp/"
        )
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.model_name = model_name

    def _inject_credentials(self) -> None:
        """Propagate credentials to environment variables expected by ADK/LiteLLM."""
        if self.google_api_key:
            os.environ.setdefault("GOOGLE_API_KEY", self.google_api_key)
            os.environ.setdefault("GOOGLE_GENAI_API_KEY", self.google_api_key)
        if self.github_token:
            os.environ.setdefault("GITHUB_TOKEN", self.github_token)
            os.environ.setdefault("LITELLM_API_KEY", self.github_token)

    async def run(self, agent_name: str, task: str | None = None) -> str:
        """
        Run the selected agent with *task* as the initial user message.

        Parameters
        ----------
        agent_name:
            One of ``"generator"``, ``"validator"``, or ``"pipeline"``.
        task:
            Task description.  Defaults to the built-in task for the chosen
            agent when *None*.

        Returns
        -------
        str
            The final response text produced by the agent.
        """
        if agent_name not in _AGENT_REGISTRY:
            raise ValueError(
                f"Unknown agent '{agent_name}'. "
                f"Choose from: {', '.join(_AGENT_REGISTRY)}"
            )

        config = _AGENT_REGISTRY[agent_name]
        task = task or config["default_task"]
        if task is None:
            raise ValueError(
                f"A task description is required for the '{agent_name}' agent. "
                f"Pass it as a positional argument."
            )
        label = config["label"]
        max_iter = config["max_iterations"]

        self._inject_credentials()

        from utils.mcp_utils import create_mcp_toolset

        print(f"[{label}Runner] Connecting to MCP server at {self.mcp_server_url} …")
        mcp_toolset = create_mcp_toolset(self.mcp_server_url)

        agent = config["factory"](self.model_name, [mcp_toolset])

        session_service = InMemorySessionService()
        artifact_service = InMemoryArtifactService()
        session_id = f"{config['session_prefix']}-{uuid.uuid4().hex[:8]}"

        await session_service.create_session(
            app_name=config["app_name"],
            user_id="standalone_user",
            session_id=session_id,
        )

        runner = Runner(
            agent=agent,
            app_name=config["app_name"],
            session_service=session_service,
            artifact_service=artifact_service,
        )

        content = types.Content(
            role="user",
            parts=[types.Part(text=task)],
        )

        iter_info = f" (max {max_iter} iterations)" if max_iter else ""
        print(f"[{label}Runner] Starting agent{iter_info} …\n")

        final_response = ""

        async for event in runner.run_async(
            user_id="standalone_user",
            session_id=session_id,
            new_message=content,
        ):
            if event.is_final_response():
                self.iteration += 1
                if event.content and event.content.parts:
                    if config["multi_part_resp"]:
                        final_response = "\n".join(
                            part.text
                            for part in event.content.parts[:5]
                            if getattr(part, "text", None)
                        )
                    else:
                        final_response = event.content.parts[0].text

                iter_str = f" {self.iteration}/{max_iter}" if max_iter else ""
                print(f"\n[{label}Runner{iter_str}] ✓ Agent finished.\n")
                print(final_response)

        return final_response


# ──────────────────────────────────────────────────────────────────────────────
# Entry-point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    from dotenv import load_dotenv
    import argparse

    load_dotenv(os.path.join(_agent_root, ".env"))

    parser = argparse.ArgumentParser(
        description="Unified standalone runner for the ASHRAE 223P agents.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m sub_agents._223p.run pipeline\n"
            "  python -m sub_agents._223p.run generator --model github_copilot/gpt-4o\n"
            "  python -m sub_agents._223p.run validator 'Fix ontology.py'\n"
            "\n"
            "Credentials can also be supplied via environment variables:\n"
            "  GOOGLE_API_KEY  – Google ADK / Gemini API key\n"
            "  GITHUB_TOKEN    – GitHub Copilot token (used by LiteLLM)\n"
            "  MCP_SERVER_URL  – MCP server URL\n"
        ),
    )
    parser.add_argument(
        "agent",
        choices=list(_AGENT_REGISTRY),
        help="Which agent to run: generator, validator, or pipeline.",
    )
    parser.add_argument(
        "task",
        nargs="*",
        help=(
            "Task description passed to the agent as the initial user message. "
            "Defaults to the built-in task for the chosen agent."
        ),
    )
    parser.add_argument(
        "--model",
        metavar="MODEL",
        default=_STANDALONE_DEFAULT_MODEL,
        help="Model name to use (default: %(default)s).",
    )
    parser.add_argument("--google-api-key", metavar="KEY", default=None)
    parser.add_argument("--github-token", metavar="TOKEN", default=None)
    parser.add_argument("--mcp-server-url", metavar="URL", default=None)

    args = parser.parse_args()
    task_arg = " ".join(args.task) if args.task else None

    if task_arg is None and _AGENT_REGISTRY[args.agent]["default_task"] is None:
        parser.error(f"A task description is required for the '{args.agent}' agent.")

    asyncio.run(
        Ontology223PRunner(
            mcp_server_url=args.mcp_server_url,
            google_api_key=args.google_api_key,
            github_token=args.github_token,
            model_name=args.model,
        ).run(agent_name=args.agent, task=task_arg)
    )

