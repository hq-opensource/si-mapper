# Testing Patterns

**Analysis Date:** 2026-02-09

## Test Framework
- **Runner:** `pytest`
- **Assertion Library:** Standard Python `assert`
- **Run Commands:** 
  - `pytest` for running all tests.
  - `pytest -v` for verbose output.
  - `pytest tests/test_integration_flow.py` for specific integration tests.

## Test File Organization
- Tests are located in the root `tests/` directory.
- Naming convention: `test_[description].py`.

## Test Structure
- **Integration Tests:** Focus on end-to-end flows like agent integration and tool execution.
- **Connection Tests:** Specific tests for verifying external connectivity (e.g., `test_toolbox_connection.py`).
- **Tool Tests:** Testing individual agent tools (e.g., `test_standard_tools.py`).

## Mocking
- **Framework:** `unittest.mock` or `pytest-mock` (inferred).
- **Patterns:** Mocking AI API responses to enable deterministic testing of loop logic without incurring costs or instability.

## Fixtures and Factories
- Use `pytest fixtures` for setting up shared state like database connections or agent configurations.

## Coverage
- Coverage tracking is not explicitly configured in root, but can be added via `pytest-cov`.

## Test Types
- **Integration:** Testing the interaction between agents and MCP tools.
- **Unit:** (Less prevalent but present in utility tests) testing small pure functions.
- **Smoke Tests:** Included as connection tests to ensure the environment is ready.
