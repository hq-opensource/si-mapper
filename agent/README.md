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

You can choose one of the following validated models:

| Model ID | Provider | Mode |
| :--- | :--- | :--- |
| `gemini-3.1-pro-preview-customtools` | Google | Native ADK |
| `claude-sonnet-4-6` | Anthropic | via LiteLLM |
| `gpt-5.4-2026-03-05` | OpenAI | via LiteLLM |

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

#### Docker Deployment

The agent ships as a self-contained Docker image (`si-mapper-agent`) and is included in the root `docker-compose.yml` under the `deploy` and `build` profiles.

> **Note:** The Docker build context must be the **project root** (not `agent/`), because `pyproject.toml` references `../223p/bin/` for local binary packages. Always run Docker Compose commands from the project root.

##### 1. Configure

Copy the example env file and fill in your credentials:

```bash
# from the project root
cp agent/docker.env.example agent/docker.env
```

Key variables in `agent/docker.env`:

| Variable | Required | Description |
| :--- | :--- | :--- |
| `SHARED_ADK_MODEL` | ✅ | Model ID (e.g. `gemini-3.1-pro`) |
| `GOOGLE_API_KEY` | ✅ (Gemini) | Google AI API key |
| `ANTHROPIC_API_KEY` | ✅ (Claude) | Anthropic API key |
| `OPENAI_API_KEY` | ✅ (GPT) | OpenAI API key |
| `GITHUB_TOKEN` | optional | GitHub personal access token — required by the read-code skill to fetch private repositories |
| `GRAPHIVAC_BASE_URL` | ✅ | Graphivac API base URL |
| `GRAPHIVAC_ORG_ID` | ✅ | Graphivac organisation ID |
| `GRAPHIVAC_PROJECT_ID` | ✅ | Graphivac project ID |
| `GRAPHIVAC_GRID_ID` | ✅ | Graphivac grid ID |
| `PROJECTS_FOLDER` | ✅ | Must be `/app/uploads` to match the volume mount |
| `NEO4J_BOLT_URI` | optional | Neo4j connection URI |
| `PORT` | optional | HTTP port (default `8001`) |

> `agent/docker.env` is gitignored. Never commit it.

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

