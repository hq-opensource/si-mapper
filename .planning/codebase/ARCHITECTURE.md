# Architecture

**Analysis Date:** 2026-02-09

## Pattern Overview
**Overall:** Multi-Agent Hierarchical Network with Decentralized Tooling (MCP).

**Key Characteristics:**
- **Hierarchical Agents:** Logic is split into levels (1-5) ranging from low-level act loops to high-level LLM reasoning.
- **MCP-First Tooling:** Tools are not hardcoded into agents but exposed via the Model Context Protocol, allowing for easy expansion and decoupling.
- **Async-First:** Heavy use of asynchronous Python (FastAPI, asyncio) for parallel agent execution.

## Layers
**Agent Layer:**
- Purpose: High-level reasoning and orchestration of HVAC mapping tasks.
- Contains: `drawing_architecture`, `master_architecture`, `equipment_architecture_optimized`.
- Depends on: Google Gemini API, MCP Server tools.
- Used by: Orchestrator scripts (`main.py`).

**Interface Layer (MCP):**
- Purpose: Bridges the agents with system tools and external data.
- Contains: `mcp_server`.
- Depends on: Database, Graphivac service.
- Used by: Agent Layer.

**Data Layer:**
- Purpose: Persistent storage for tasks and graph representations.
- Contains: Postgres Database, Graphivac public graph.
- Depends on: None.
- Used by: MCP Server.

**UI Layer:**
- Purpose: Visualization and manual correction of mapping results.
- Contains: `mapper/` (Next.js application).
- Depends on: Agent/MCP APIs.
- Used by: Human users.

## Data Flow
**HVAC Mapping Flow:**
1. **Input:** User provides an HVAC drawing image.
2. **Processing:** The Master Agent (Level 5) analyzes the request and delegates to specific Drawing or Equipment agents (Level 4).
3. **Execution:** Level 4 agents use MCP tools to query the database, identify components, and register findings.
4. **Verification:** A review loop (Level 4/5) validates the findings against the original drawing.
5. **Output:** The final graph model is updated in the database/Graphivac.

**State Management:**
- Agent state is managed through a `State` object passed through loops, often synchronized with a persistent task database via MCP.

## Key Abstractions
**Agent Loop (Level 4):**
- Purpose: Manages a specific phase of a task (Plan, Act, Review).
- Examples: `level_4_plan_loop.py`, `level_4_act_loop.py`.
- Pattern: Strategy/State machine.

**MCP Tool:**
- Purpose: Encapsulates a specific capability (e.g., "Find equipment coordinate").
- Pattern: Command/Remote Procedure Call via MCP.

## Entry Points
**Master Orchestrator:**
- Location: `agent/main_master_architecture.py`
- Triggers: CLI or API request.
- Responsibilities: Initializes the master agent and starts the top-level orchestration.

**MCP Server:**
- Location: `mcp_server/server/`
- Triggers: HTTP/SSE connection.
- Responsibilities: Serves as a gateway for tools.

## Error Handling
**Strategy:** Distributed error handling. Level-based agents are designed to catch and report errors at their respective levels. Retry logic is implemented in loops, and final failures are drifted up to the master agent.

## Cross-Cutting Concerns
**Logging:** Structured logging to `app_run.log` using standard Python `logging`.
**Validation:** Pydantic is used for strict schema validation across agent levels and API boundaries.
**Authentication:** Managed via environment variables (API keys) and Docker secrets where applicable.
