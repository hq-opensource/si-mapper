# Plan: Phase 4 - Google ADK with LiteLLM

## Overview
Decouple ADK agents from a single model provider by integrating the **LiteLLM Python SDK**. This enables multi-model support (OpenAI, Anthropic, Google Gemini) for existing and future agents within the `si-mapper` ecosystem.

**Goal:** Agents should be able to use any provider supported by LiteLLM via a single configuration.

## Wave 1: Infrastructure & Core Support
**Plan 4.1: Env Readiness & Dependencies**
1. Install `litellm` and `google-adk` (verify versions).
2. Define `SHARED_ADK_MODEL` in `.env`.
3. Update `agent/main.py` to use `SHARED_ADK_MODEL` as the source of truth for all agents.

**Plan 4.2: ADK Agent Integration**
1. Update `agent/sub_agents/bacnet/agent.py` (and others) to wrap model names in `LiteLlm(...)` if the model implies a non-native Gemini provider.
2. Implement a unified model loader in `agent/utils/models.py` that handles the mapping.

## Wave 2: Verification & Parity
**Plan 4.3: Provider Verification Loop**
1. Create a `tests/verify_litellm_providers.py` script.
2. Test **Gemini 3.1 Pro** compatibility (Native ADK).
3. Test **Claude 4.6 Opus** connectivity via LiteLLM.
4. Test **GPT-5.3** connectivity via LiteLLM.
5. Verify that tools (MCP metadata tools) are correctly called across all providers.

## Definition of Done (DoD)
- [ ] Agents can be initialized with `SHARED_ADK_MODEL`.
- [ ] Swapping the model in `.env` (e.g., from `gemini-3.0-flash` to `claude-4.6-sonnet`) works without code changes.
- [ ] No regressions in tool calling or task processing.
- [ ] Explicit failures occur if the model provider or API key is missing.
