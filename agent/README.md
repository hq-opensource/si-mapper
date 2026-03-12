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

To select a model, update the `SHARED_ADK_MODEL` variable in your `agent/.env` file.

1.  **Set the model name:**
    ```bash
    SHARED_ADK_MODEL=claude-sonnet-4-6
    ```

2.  **Ensure required API Keys are set:**
    Depending on your selection, make sure the relevant key is present:
    ```bash
    GOOGLE_API_KEY="your-key-here"
    ANTHROPIC_API_KEY="your-key-here"
    OPENAI_API_KEY="your-key-here"
    ```

##### How it works
The `agent/utils/models.py` utility handles the model selection:
- **Native Gemini**: If the model name contains "gemini", it uses ADK's native implementation.
- **Provider Abstraction**: For "claude" or "gpt", the system automatically prefixes the provider (e.g., `anthropic/` or `openai/`) and initializes the model via LiteLLM.
- **Compatibility**: The integration is configured with `drop_params=True` to normalize differences between provider APIs ensuring stable tool-calling behavior.