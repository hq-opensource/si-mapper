# Phase 5: Agent-Frontend Interface & Performance Metrics - PLAN

Establish a robust communication layer between the reasoning agent and the Next.js frontend, ensuring transparency of thoughts, tool calls, and performance metrics.

## User Review Required

> [!IMPORTANT]
> This plan assumes `http://localhost:8001` is the active backend port for polling.

- [x] **DASHBOARD DESIGN:** Metrics will be placed on a new, standalone Performance Dashboard accessible from the navigation.

---

## Proposed Phases

### 5.1: Communication Audit & Latency Mapping
- **Goal:** Understand exactly where time is spent during a "Thought -> UI" cycle.
- **Tasks:**
    - [x] Insert millisecond-level telemetry in `shared_model_callback` for:
        - LLM response time
        - `EventProcessor` duration
    - [ ] Audit `useAgentPolling` vs `useCoAgent` performance in the frontend.
- **Verification:** Log trace showing the breakdown of a single agent turn.

### 5.2: "True" Streaming Thoughts (Ongoing)
- **Goal:** Ensure thoughts appear in the UI as they are generated, not after the turn finishes.
- **Tasks:**
    - [ ] Verify if `after_model_callback` in ADK supports chunk-level interception for Gemini.
    - [ ] Update `EventProcessor` to handle partial/incremental content if necessary.
- **Verification:** User observes "Thinking Trace" updates incrementally during a long reasoning step.

### 5.3: Performance Metrics Integration
- **Goal:** Expose technical telemetry to the frontend HUD.
- **Tasks:**
    - [x] Update `AgentEvent` to include a `metrics` block (latency, tokens, provider).
    - [x] Update Mapper components (`ThoughtsWindow`, `AgentNavbar`) to render these metrics.
- **Verification:** HUD displays "Latency: 2.3s | Tokens: 450" for recent steps.

### 5.4: Reliability & Synchronization Cleanup
- **Goal:** Eliminate "stale state" issues between polling and streaming.
- **Tasks:**
    - [ ] Implement a `sequence_number` for state updates to prevent out-of-order rendering.
    - [ ] Clean up redundant keys in `GLOBAL_SESSION_STORE`.
- **Verification:** Rapid agent steps no longer cause "flickering" or reversed history in the UI.
