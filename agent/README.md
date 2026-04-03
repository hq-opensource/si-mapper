### Agent
The `agent` directory contains the core LLM orchestration service built with Fastmcp and Google ADK.

> **💡 Recommended Setup:** For the easiest setup, run `pnpm install` in the **mapper directory**. This will automatically handle the Python environment for you. See the [Mapper README](../mapper/README.md) for details.

#### Prerequisites
- [uv](https://github.com/astral-sh/uv) (recommended) or Python 3.10+

#### Setup & Running

**Using uv (Recommended)**
The simplest way to set up and run the agent is using `uv`, which handles environment creation and dependency management automatically:

```bash
cd agent
uv sync
uv run main.py
```

**Using standard Python**
If you prefer standard virtual environments:

1. Create and activate a virtual environment:
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Unix/macOS:
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install .
```

3. Run the agent:
```bash
python main.py
```

#### Configuration & Multi-Model Support

The system supports multiple LLM providers through a unified interface. It uses **Google ADK** natively for Gemini models and **LiteLLM** for integration with Anthropic and OpenAI.

##### Supported Models

###### Native ADK (Google Gemini)

These models are handled directly by the Google ADK without any additional adapter. Set `SHARED_ADK_MODEL` to any of the following:

| Model ID | Notes |
| :--- | :--- |
| `gemini-3.1-pro-preview-customtools` | **Recommended for agents** — strictly prioritizes custom tools over internal bash; ideal for production |
| `gemini-3.1-pro-preview` | Standard reasoning flagship; may occasionally prefer its own bash sandbox for logic tasks |
| `gemini-3-flash-preview` | Optimized for low-latency and real-time interaction (Gemini Live API) — Pro intelligence at Flash speed |
| `gemini-3.1-flash-lite-preview` | Most cost-efficient option for high-frequency, simple agent tasks |
| `gemini-2.5-pro` | GA model — complex reasoning with 1M context window, stable for production |
| `gemini-2.5-flash` | Balanced speed/cost for standard automation and data parsing |
| `gemini-2.0-flash` | Previous-gen Flash — well-tested in production |
| `gemini-1.5-pro` | Stable long-context Pro — broad tool support |
| `gemini-1.5-flash` | Stable Flash — high throughput |
| `gemini-1.5-flash-8b` | Smallest 1.5 variant — minimal resource use |

> More recent models may be available. For the full up-to-date list see the **[official Google Gemini model catalogue](https://ai.google.dev/gemini-api/docs/models)**.

###### External Providers (via LiteLLM)

Any model supported by [LiteLLM](https://models.litellm.ai/) can be used by setting the corresponding API key. The agent automatically routes non-Gemini model IDs through LiteLLM.

| Model ID | Provider | Required key |
| :--- | :--- | :--- |
| `github_copilot/claude-sonnet-4-5` | GitHub Copilot | `GITHUB_COPILOT_TOKEN` |
| `github_copilot/gpt-4o` | GitHub Copilot | `GITHUB_COPILOT_TOKEN` |
| `claude-sonnet-4-6` | Anthropic | `ANTHROPIC_API_KEY` |
| `gpt-5.4-2026-03-05` | OpenAI | `OPENAI_API_KEY` |
| `mistral/mistral-large-latest` | Mistral AI | `MISTRAL_API_KEY` |

> For the full catalogue of LiteLLM-compatible models see **[models.litellm.ai](https://models.litellm.ai/)**.

##### Selecting a Model

To select a model, update the `SHARED_ADK_MODEL` variable in your environment file:
- **Local dev:** `agent/.env`
- **Docker:** `agent/docker.env`

1.  **Set the model name:**
    ```bash
    SHARED_ADK_MODEL=claude-sonnet-4-6
    ```

2.  **Ensure all required keys are set:**
    Depending on your model selection, make sure the relevant keys are present:
    ```bash
    # LLM provider — set the one that matches your SHARED_ADK_MODEL
    GOOGLE_API_KEY="your-key-here"
    ANTHROPIC_API_KEY="your-key-here"
    OPENAI_API_KEY="your-key-here"

    # GitHub — required by the read-code skill to fetch repositories
    GITHUB_TOKEN="your-token-here"
    ```

##### How it works
The `agent/utils/models.py` utility handles the model selection:
- **Native Gemini**: If the model name contains "gemini", it uses ADK's native implementation.
- **Provider Abstraction**: For "claude" or "gpt", the system automatically prefixes the provider (e.g., `anthropic/` or `openai/`) and initializes the model via LiteLLM.
- **Compatibility**: The integration is configured with `drop_params=True` to normalize differences between provider APIs ensuring stable tool-calling behavior.

---

#### Environment Variables

All variables below are read from `agent/.env` (local dev) or `agent/docker.env` (Docker). Copy the relevant example file and fill in your values — both files cover the same set of variables.

| Variable | Required | Default | Description |
| :--- | :---: | :--- | :--- |
| `SHARED_ADK_MODEL` | ✅ | `gemini-3.1-pro` | LLM model ID. See [Supported Models](#supported-models) above. |
| `GOOGLE_API_KEY` | ✅ (Gemini) | — | Google AI API key — required when `SHARED_ADK_MODEL` is a Gemini model. |
| `ANTHROPIC_API_KEY` | ✅ (Claude) | — | Anthropic API key — required when `SHARED_ADK_MODEL` is a Claude model. |
| `OPENAI_API_KEY` | ✅ (GPT) | — | OpenAI API key — required when `SHARED_ADK_MODEL` is a GPT model. |
| `GITHUB_TOKEN` | optional | — | GitHub personal access token — required by the `read-code` skill to fetch private repositories. |
| `GRAPHIVAC_BASE_URL` | ✅ | `http://graphivac:3000` | Internal (server-to-server) Graphivac API base URL (no trailing slash). |
| `GRAPHIVAC_ORG_ID` | ✅ | `public` | Graphivac organisation ID. |
| `GRAPHIVAC_PROJECT_ID` | ✅ | — | Graphivac project ID (format: `P-XXXXXXXX`). |
| `GRAPHIVAC_GRID_ID` | ✅ | — | Graphivac grid ID (format: `G-XXXXXXXX`). |
| `PROJECTS_FOLDER` | ✅ | `/app/uploads` | Absolute path to the shared project-files root. Must match the Docker volume mount target. |
| `NEO4J_BOLT_URI` | optional | `bolt://neo4j:7687` | Neo4j Bolt connection URI. |
| `NEO4J_USER` | optional | `neo4j` | Neo4j username. |
| `NEO4J_PASSWORD` | optional | `neo4j_password` | Neo4j password. |
| `DEBUG_LEVEL` | optional | `INFO` | Log verbosity level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `PORT` | optional | `8001` | HTTP port the FastAPI service listens on. |
| `SESSIONS_DB_PATH` | optional | `/app/data/sessions.db` | Path to the SQLite sessions database. Use a named Docker volume path for persistence. |

---

#### Docker Deployment

The agent ships as a self-contained Docker image (`si-mapper-agent`) and is included in the root `docker-compose.yml` under the `deploy` and `build` profiles.

> **Note:** The Docker build context must be the **project root** (not `agent/`), because `pyproject.toml` references `../223p/bin/` for local binary packages. Always run Docker Compose commands from the project root.

##### 1. Configure

Copy the example env file and fill in your credentials:

```bash
# from the project root
cp agent/docker.env.example agent/docker.env
```

> See [Environment Variables](#environment-variables) above for the full list of variables and their defaults. `agent/docker.env` is gitignored — never commit it.

##### 2. Build

```bash
# from the project root
docker compose build si-mapper-agent
```

The image uses a two-stage build:
- **Stage 1 (builder):** installs all Python dependencies via `uv sync --frozen --no-dev` into a virtual environment.
- **Stage 2 (runner):** copies the venv, installs Playwright/Chromium system binaries, then copies the application source. Test files are stripped out.

Final image size: ~811 MB (includes Chromium for the `capture_frontend_state` tool).

##### 3. Run

```bash
# alongside all other services
docker compose --profile deploy up

# agent only
docker compose --profile deploy up si-mapper-agent

# in the background
docker compose --profile deploy up -d si-mapper-agent
```

The agent API is available at **http://localhost:8001**.

##### 4. Verify

```bash
# health check
curl http://localhost:8001/health
# → {"status": "ok"}

# session info
curl http://localhost:8001/session_info
# → {"session_id": "...", "app_name": "si_mapper", "user_id": "demo_user"}
```

##### Shared uploads volume

The agent container mounts `./mapper/uploads` at `/app/uploads` — the same bind-mount used by the frontend container. This ensures project files written by one service are immediately visible to the other. `PROJECTS_FOLDER` must be set to `/app/uploads` in `agent/docker.env` to match.

##### Useful commands

```bash
# tail agent logs
docker compose logs -f si-mapper-agent

# rebuild after a source change
docker compose build si-mapper-agent && docker compose --profile deploy up si-mapper-agent

# open a shell inside the running container
docker exec -it si-mapper-agent bash

# check the uploads volume mount
docker exec -it si-mapper-agent ls /app/uploads
```

