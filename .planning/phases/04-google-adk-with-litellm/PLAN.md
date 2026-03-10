# Plan: Phase 4 - Google ADK with LiteLLM

## Overview
Decouple ADK agents from a single model provider by integrating the **LiteLLM Python SDK**. This enables multi-model support (OpenAI, Anthropic, Google Gemini) for existing and future agents within the `si-mapper` ecosystem.

**Goal:** Agents should be able to use any provider supported by LiteLLM via a single configuration.

## Wave 1: Infrastructure & Core Support
**Plan 4.1: Env Readiness & Dependencies (Completed)
1. [x] Install `litellm` and `google-adk` (verify versions).
2. [x] Define `SHARED_ADK_MODEL` in `.env`.
3. [x] Update `agent/main.py` to use `SHARED_ADK_MODEL` as the source of truth for all agents.

**Plan 4.2: ADK Agent Integration (Completed)
1. [x] Update `agent/sub_agents/bacnet/agent.py` (and others) to wrap model names in `LiteLlm(...)` if the model implies a non-native Gemini provider.
2. [x] Implement a unified model loader in `agent/utils/models.py` that handles the mapping.

## Wave 2: Verification & Parity
**Plan 4.3: Provider Verification Loop (Completed)
1. [x] Create a `tests/verify_litellm_providers.py` script.
2. [x] Test **Gemini 3.1 Pro** compatibility (Native ADK).
3. [x] Test **Claude 4.5/4.6** connectivity via LiteLLM.
4. [x] Test **GPT-5.3/5.4** connectivity via LiteLLM.
5. [x] Verify that tools (MCP metadata tools) are correctly called across all providers.

## Definition of Done (DoD)
- [x] Agents can be initialized with `SHARED_ADK_MODEL`.
- [x] Swapping the model in `.env` (e.g., from `gemini-3.0-flash` to `claude-sonnet-4-6`) works without code changes.
- [x] No regressions in tool calling or task processing.
- [x] Explicit failures occur if the model provider or API key is missing.
