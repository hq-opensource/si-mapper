# Context: Phase 5 - Full System Multi-Model Validation

## Domain Boundary
Validate the entire HVAC system (all agents, tools, MCP) using high-tier "Powerhouse" models.

## Implementation Decisions

### Selected Models
- **Anthropic:** `claude-sonnet-4-6`
- **OpenAI:** `gpt-5.4-2026-03-05`
- **Google:** `gemini-3.1-pro-preview-customtools`

### Validation Strategy: Agent-Specific Testing Scripts
Rather than a generic connectivity test, we will create individual Python scripts for each sub-agent. These scripts will:
1. Initialize the specific agent (e.g., `BacnetLlmAgent`).
2. Provide a real-world task related to that agent's domain.
3. Verify the agent can correctly:
   - Access and use MCP tools (e.g., `read_grid`).
   - Follow its `prompt.md` instructions and skills.
   - Return structured, accurate technical data.

### Infrastructure Validation
- Confirm that `SHARED_ADK_MODEL` in `.env` can switch between these models and providers.
- Ensure consistent tool-calling behavior across all three providers.

## Special Instructions
We are using these cheaper models to confirm the robustness of the system's logic independently of the "highest-tier" model capabilities. The system should correctly handle these specific model strings and route them via LiteLLM as established in Phase 4.

## Deferred Ideas
- Dynamic model switching based on task complexity (e.g., use Haiku for extraction, Pro for final Review).
