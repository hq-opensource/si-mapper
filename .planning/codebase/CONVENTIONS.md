# Coding Conventions

**Analysis Date:** 2026-02-09

## Naming Patterns
**Files:** 
- Agents: `level_[X]_[name].py` (e.g., `level_4_act_loop.py`).
- Utilities: `snake_case.py`.
- Frontend: `PascalCase.tsx` for components.
**Functions:** `snake_case()` for Python, `camelCase()` for TypeScript.
**Variables:** `snake_case` for Python, `camelCase` for TypeScript.
**Types:** `PascalCase` for both Pydantic models (Python) and TypeScript interfaces/types.

## Code Style
**Formatting:** 
- Python: Uses `black` / standard PEP8 (implied).
- TypeScript: Uses Prettier (implied by Node.js project).
**Linting:** 
- Python: Likely `ruff` or `flake8` (inferred from development environment).
- TypeScript: `ESLint` (config found in `mapper/eslint.config.mjs`).

## Import Organization
**Order (Python):**
1. Standard library imports.
2. Third-party packages (e.g., `fastapi`, `google-genai`).
3. Internal project modules (e.g., `agent.utils`).
4. Relative imports.

## Error Handling
**Patterns:** 
- Use of `try-except` blocks to catch specific AI/API failures.
- Errors are often wrapped in a response object that includes status and message to be processed by the higher-level agent loops.
- Avoid "silent failures"; always log and optionally drift errors up.

## Logging
**Framework:** Standard Python `logging` module.
**Patterns:** 
- Log informational steps to `app_run.log`.
- Log critical errors with stack traces.
- Structured logging where possible for easier parsing.

## Comments
**When to Comment:** 
- Document complex logic in agent loops.
- Explain "Why" rather than "What" for AI-specific prompts and transformations.
- Docstrings are preferred for public-facing utilities.

## Function Design
- Keep level-based agent functions focused on their specific role (Plan, Act, or Review).
- Pass state explicitly through loops rather than relying on global state.
- Use type hints for all Python functions.

## Module Design
- Use `__init__.py` to expose clean internal APIs.
- Group related agent levels into sub-directories (e.g., `drawing_architecture`).
