# Phase 5: Full System Multi-Model Validation

## Overview
This phase validates the end-to-end functionality of the HVAC reconstruction and mapping system using the most powerful models available. We will verify that each specialist agent (Horizontal/Vertical Ducts, Equipment, Bacnet, Control, Electricity) operates correctly across all providers, ensuring tool calling, MCP integration, and complex reasoning are robust.

## Powerhouse Models for Validation
- **Anthropic:** `claude-sonnet-4-6`
- **OpenAI:** `gpt-5.4-2026-03-05`
- **Google:** `gemini-3.1-pro-preview-customtools`

## Goals
1. Verify system-wide compatibility with high-tier models.
2. Confirm that all custom tools, MCP integrations, and prompt skills remain functional and performant.
3. Validate each agent individually through dedicated test scripts.
4. Ensure the `SHARED_ADK_MODEL` routing logic correctly handles these specific model identifiers across the entire system.
