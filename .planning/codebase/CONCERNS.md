# Codebase Concerns

**Analysis Date:** 2026-02-09

## Tech Debt
- **Large Log Files:** `app_run.log` grows rapidly (currently ~2MB) and is committed to git (based on `list_dir` output). Recommendation: Add to `.gitignore` or implement log rotation.
- **Hierarchical Complexity:** The multi-level agent architecture (Levels 1-5) is powerful but creates high cognitive load for developers. Documentation within specific levels is sparse.

## Known Bugs
- **Integration Stability:** Recent conversation history suggests issues with equipment registration and 500 server errors during parallel execution (likely rate limiting or concurrency issues).

## Security Considerations
- **API Key Management:** `GOOGLE_API_KEY` is central. If leaked, it provides full access to the Gemini account. Recommendation: Use secret management in Docker/Cloud rather than environment variables in `.env` or `launch.json`.

## Performance Bottlenecks
- **LLM Latency:** Multi-level agents make sequential LLM calls, leading to significant end-to-end task duration.
- **Image Processing:** High-resolution HVAC drawings can slow down vision agents or exceed token limits.

## Fragile Areas
- **Agent Loops:** The logic in `level_4_act_loop.py` and similar files is highly dependent on specific prompt formatting. Small changes in prompts can break functional flows.

## Scaling Limits
- **Concurrency:** Parallel agent execution is capped by LLM rate limits and Docker resource allocation (especially for DB connections).

## Dependencies at Risk
- **google-genai:** Rapid updates to the library might break existing logic.
- **Graphivac:** Dependence on a public hosted service for graph data is a risk for production stability/privacy.

## Missing Critical Features
- **Unit Test Coverage:** High reliance on integration tests; fewer unit tests for individual agent transformations.
- **Automated CI:** No obvious CI pipeline found (e.g., GitHub Actions).

## Test Coverage Gaps
- **Edge Case Drawings:** Tests focus on standard flows; lacks stress tests for complex or low-quality HVAC drawings.
