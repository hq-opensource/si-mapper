# Phase 4: Google ADK with LiteLLM

## Implementation Notes
Based on the documentation provided:

### Goal
Integrate Google ADK with LiteLLM Python SDK to allow agents to switch between any provider (OpenAI, Anthropic, Gemini) using a shared environment variable.

### References
- [LiteLLM Google ADK Tutorial](https://docs.litellm.ai/docs/tutorials/google_adk)

### Key Components
1. **Model Support:**
   - OpenAI: `gpt-5.4-2026-03-05`
   - Anthropic: `claude-sonnet-4-6`
   - Google Gemini: `gemini-3.1-pro-preview`, `gemini-3.1-pro-preview-customtools`
2. **Infrastructure:**
   - Direct integration via `LiteLlm` wrapper in `google.adk`.
   - **LiteLLM Proxy is deferred** (for future phases).

### Code Example Snippet
```python
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm or str  # depending on model provider
import os

# Model name from shared env
shared_model = os.getenv("SHARED_ADK_MODEL", "gemini-3.0-flash")

# Model initialization logic
model = LiteLlm(model=shared_model) if "gemini" not in shared_model else shared_model

# Agent creation
agent = Agent(
    name="hvac_agent",
    model=model,
    description="Multi-model agent for HVAC mapping.",
    tools=[get_weather] # or HVAC tools
)
```

### Dependencies
- `google-adk`
- `litellm`
