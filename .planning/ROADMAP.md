# Roadmap: HVAC Reconstruction & Mapping

## Phase 1: Sequential Topological Reconstruction (Completed)
**Goal:** Build the foundation by extracting and placing geometry in the frontend.

- **Phase 1.1: Horizontal Duct Extraction**
    - [x] Create/Refine specialized agent for primary horizontal trunk identification.
    - [x] Implement "Grid Reading" tool for agents to understand current frontend state.
- **Phase 1.2: Vertical Duct & Connection Extraction**
    - [x] Create agent for mixing zones and vertical branches.
    - [x] Implement placement logic relative to horizontal trunks.
- **Phase 1.3: Equipment Placement & Alignment**
    - [x] Extract Fans, Coils, Humidifiers.
    - [x] Enforce grid alignment (Y-coordinate matching with parent ducts).
- **Phase 1.4: Engineering Review & Verification**
    - [x] Implement Review Agent to check connectivity (e.g., flow direction, sequence).
    - [x] Human-in-the-loop (HITL) verification pattern for final topology approval.

## Phase 2: Raw Information Extraction & Mapping (Current Focus)
**Goal:** Extract technical data from source files and map them as raw components to the frontend for human verification.

- **Phase 2.1: Infrastructure & MCP Tools**
    - [x] Implement `write_metadata` tool in `mcp_server/graphivac/metadata_tools.py`.
    - [x] Create `MetadataManager` in `mcp_server/graphivac/metadata_manager.py`.
    - [x] Verify `read_grid` integration with multimodal sub-agents.
    - [x] Implement `save_agent_state` in `agent/tools/state_tools.py` using `ToolContext.state`.
- **Phase 2.2: Specialized Raw Data Agents (Multimodal)**
    - [x] Create Bacnet Sub-Agent.
    - [x] Create Control Sub-Agent.
    - [x] Create Electricity Sub-Agent.
- **Phase 2.3: Iterative Technical Mapping Loop**
    - [ ] Implement the loop to process all grid equipment and attach raw technical metadata.
- **Phase 2.4: Human Verification (HITL)**
    - [ ] Human review of extracted raw data on the frontend before semantic processing.

## Phase 3: Semantic Graph Generation
**Goal:** Transform verified raw data into standardized ontologies (ASHRAE 223P, Haystack).

- **Phase 3.1: Ontology Mapping & Graph Construction**
- **Phase 3.2: Export Logic & Validation**

## Phase 4: Google ADK with LiteLLM (Completed)
**Goal:** Integrate Google ADK with LiteLLM to allow agents to use multiple LLM providers (OpenAI, Anthropic, Gemini) and LiteLLM Proxy for centralized model management.
**Depends on:** None
**Plans:** 3 plans

## Phase 5: Full System Multi-Model Validation (Current Focus)
**Goal:** Validate the entire HVAC reconstruction and mapping system (all agents, tools, MCP integration) using optimized models from Anthropic, OpenAI, and Google through the LiteLLM architecture.
**Depends on:** Phase 4
**Plans:**
- [x] Plan 5.1: Core Validation Scripts
- [ ] Plan 5.2: Multi-Model Execution Loop

---

# Requirements Mapping
| Req ID | Phase | Plan Status |
| :--- | :--- | :--- |
| REQ-1 | Phase 2.1 | Completed |
| REQ-2 | Phase 1.1, 1.2, 1.3 | Completed |
| REQ-3 | Phase 1.1 | Completed |
| REQ-4 | Phase 1.4 | Completed |
| REQ-5 | Phase 2.3 | Pending |
| REQ-6 | Phase 3.1 | Pending |
| REQ-7 | Phase 4 | Completed |
| REQ-8 | Phase 5 | In Progress |
| REQ-9 | Phase 6 | Pending |

## Phase 6: Next.js 16 Upgrade (Current Focus)
**Goal:** Upgrade the frontend (mapper) to Next.js 16, utilizing Turbopack, Cache Components, and the new `proxy.ts` system while ensuring compatibility with Python 3.13/3.14 and CopilotKit.

- **Phase 6.1: Environment & Dependency Preparation**
    - [x] Verify Node.js 20.9+ and TypeScript 5.1+ requirements.
    - [x] Research CopilotKit compatibility with Next.js 16.
    - [x] Create a migration branch.
- **Phase 6.2: Automated & Manual Upgrade**
    - [x] Execute `npx @next/codemod@canary upgrade latest`.
    - [x] Update `next`, `react`, and `react-dom` to latest versions.
- **Phase 6.3: Breaking Changes & Cleanup**
    - [x] Migrate middleware to the new `proxy.ts` system (N/A).
    - [x] Update Asynchronous Request APIs (Params/SearchParams to Promises).
    - [x] Ensure Turbopack compatibility (Fixed `rmdir`).
- **Phase 6.4: Validation & Testing**
    - [x] Run production build and fix any TypeScript or hydration errors.
    - [ ] Verify multi-model agent integration and HUD functionality.
