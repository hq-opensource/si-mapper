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

#### Configuration
1. Set up your Google API key in a `.env` file (see `.example.env`):
```bash
GOOGLE_API_KEY="your-google-api-key-here"
```