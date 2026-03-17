# Phase 5: Agent-Frontend Interface & Performance Metrics - CONTEXT

## Domain Boundary
This phase focuses on the "Observation & Telemetry" layer of the HVAC Reconstruction system. It establishes how the reasoning agents (Master and Sub-agents) communicate their internal states (thoughts, plans, tasks, and tool calls) to the Next.js frontend and provides a performance monitoring dashboard.

## Implementation Decisions

### 1. Communication Architecture
- **Dual-Link State Sync:**
    - **Primary (Streaming):** Via CopilotKit's `useCoAgent` hook, which synchronizes the `callback_context.state` from the Python backend to the frontend.
    - **Secondary (Polling):** A fallback mechanism using a custom FastAPI `/session_state` endpoint. This endpoint polls the `GLOBAL_SESSION_STORE` every 2 seconds to ensure UI consistency even if streaming chunks are missed.
- **Event Interception:** 
    - Information is intercepted using Google ADK's `before_model_callback` and `after_model_callback` hooks.
    - `shared_model_callback` in `agent/utils/callback_utils.py` acts as the central hub for processing every agent-LLM interaction.

### 2. Information Extraction (Event Processor)
- **Categorization:** Every model response part is classified into an `AgentEvent`:
    - `BRAINSTORM`: Internal reasoning (extracted from part.thought).
    - `DELEGATION`: Logic involving hand-offs to sub-agents.
    - `ACTION_TRIGGER`: Imminent tool calls.
    - `STATE_MUTATION`: Changes to plans or tasks.
    - `TEXT_RESPONSE`: Final natural language output.
- **Markers:** Thoughts and tools are wrapped in UI markers (`:::thought`, `:::tool_call`) on the backend to allow the frontend Markdown renderer to apply specialized styling.

### 3. Google ADK Alignment
- **State Management:** Fully utilizes ADK's native `SessionState` for persistence.
- **Best Practices:** 
    - Uses `InvocationContext` and `CallbackContext` as intended.
    - Implements a global concurrency controller via `adk_patch.py` to manage API rate limits across multiple parallel sub-agents.
- **Opportunity for Optimization:** Currently, processing happens on the aggregated response. Moving to a chunk-based processing model would allow "streaming thoughts" rather than "batches of thoughts."

### 4. Developer Discretion
- **Performance HUD:** I will design the dashboard to show:
    - LLM Round-trip latency (computed in `shared_model_callback`).
    - Token usage per iteration.
    - Tool success/error frequency.
- **Interaction Model:** The HUD is **Observation-Only**. No "Intercept/Pause" logic will be implemented in this phase to maintain the system's autonomous engineering logic.

## Specific Ideas / References
- Use the `ThinkingBox` and `ThinkingMessage` components in the frontend for unified rendering.
- Reference `agent/utils/callback_utils.py` as the primary integration point.

## Deferred Ideas
- **HITL Interruption:** Allowing a user to "STOP" an agent mid-thought or "EDIT" a plan via the HUD is deferred to a future "Control Integration" phase.
