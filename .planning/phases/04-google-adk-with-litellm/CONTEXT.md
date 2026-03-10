# Context: Phase 4 - Google ADK with LiteLLM

## Domain Boundary
Decouple ADK agents from a single model provider by integrating the **LiteLLM Python SDK**. This enables multi-model support (OpenAI, Anthropic, Google Gemini) for existing and future agents within the `si-mapper` ecosystem.

## Implementation Decisions

### Model Routing
- **Global Configuration:** All agents will share a single model name provided via a shared environment variable (e.g., `SHARED_ADK_MODEL`).
- **No Fallback:** If the specified model fails or the environment variable is missing, the system should fail explicitly to aid in direct troubleshooting.
- **Provider Parity:** Use standard environment variables for secret management (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`).

### Supported Models
Implementation will focus on verifying compatibility for the following primary models:
- **Google:** gemini-3.1-pro-preview, gemini-3.1-pro-preview-customtools.
- **Anthropic:** claude-sonnet-4-6.
- **OpenAI:** gpt-5.4-2026-03-05.

### Infrastructure
- **Direct SDK Integration:** Use the `LiteLlm` wrapper from the `google.adk` package directly. 
- **Proxy Status:** LiteLLM Proxy is **not** to be used for this phase; we are prioritizing direct SDK calls.

## Claude's Discretion
- Standardizing the initialization logic for agents to automatically switch between `LiteLlm(...)` and native ADK model strings based on the provider prefix.
- Defining the exact environment variable name (e.g., `ADK_PROVIDER_MODEL`) and ensuring it is propagated across all runners.

## Specific Ideas / References
- Follow the patterns in the [LiteLLM Google ADK Tutorial](https://docs.litellm.ai/docs/tutorials/google_adk).
- Ensure existing tools (like `get_weather` or HVAC extraction tools) remain compatible without modification.

## Deferred Ideas
- **Individual Agent Model Assignment:** Allowing different agents in the same session to use different providers.
- **Proxy-based Metering/Logging:** Centralized management via LiteLLM Proxy.
