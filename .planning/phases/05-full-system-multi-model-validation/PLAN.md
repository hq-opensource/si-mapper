# Plan: Phase 5 - Full System Multi-Model Validation

## Overview
Validate the entire HVAC reconstruction and mapping system using the most powerful models from Google, Anthropic, and OpenAI. The validation will be performed agent-by-agent using dedicated Python scripts to ensure full tool-calling and reasoning parity.

## Wave 1: Test Infrastructure
**Plan 5.1: Core Validation Scripts**
1. Create a base test utility for initializing agents and capturing results.
2. Create `tests/validate_bacnet_agent.py`.
3. Create `tests/validate_duct_agents.py` (Horizontal & Vertical).
4. Create `tests/validate_equipment_agent.py`.
5. Create `tests/validate_technical_agents.py` (Control & Electricity).

## Wave 2: Execution & Fine-Tuning
**Plan 5.2: Multi-Model Execution Loop**
1. Run each test script with `gemini-3.1-pro-preview-customtools`.
2. Run each test script with `claude-sonnet-4-6`.
3. Run each test script with `gpt-5.4-2026-03-05`.
4. Document any discrepancies in reasoning, tool calls, or output format.
5. Fine-tune `prompt.md` files if any provider-specific adjustments are needed.

## Definition of Done (DoD)
- [ ] Dedicated test scripts exist for all sub-agents.
- [ ] All agents successfully execute their domain tasks with all three providers.
- [ ] All agents can correctly call MCP tools (e.g., `read_grid`, `ingest_category_files`).
- [ ] The `SHARED_ADK_MODEL` logic is verified across the entire system.
- [ ] Results documented in a `VALIDATION_RESULTS.md` file.
