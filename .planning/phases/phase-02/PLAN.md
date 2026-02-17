# Plan: Phase 2 - Raw Information Extraction & Mapping

**Goal:** Integrate raw technical metadata from BACnet, Control, and Electricity sources with the physical HVAC topology. The extracted data is saved to the frontend (GraphyBack) for easy Human-in-the-Loop (HITL) verification.

## Wave 1: Extraction Infrastructure & Tools
**Trigger:** Start of Phase 2
**Focus:** Build the tools necessary for state persistence and frontend integration.

- [x] **[TASK-2.1.1] Implement Metadata MCP Tool** 
    - Created `mcp_server/graphivac/metadata_manager.py`.
    - Created `mcp_server/graphivac/metadata_tools.py`.
    - Registered `write_metadata`, `read_metadata`, and `delete_metadata` using native EDN maps in `:custom-fields`.
- [x] **[TASK-2.1.2] Verify `read_grid` Integration**
    - Successfully verified with real grid data (15 components retrieved: sensors, fans, VFDs).
- [x] **[TASK-2.1.3] Implement Multi-Agent Task Persistence**
    - Enhanced `Task` model in `agent/utils/models.py` with technical mapping flags (`bacnet_treated`, `control_treated`, `electricity_treated`).
    - Implemented `enqueue_grid_tasks` and `mark_technical_progress` in `agent/tools/task_tools.py`.
    - Logic: Tasks are marked as `VERIFICATION_READY` only when all three specialized agents have processed the equipment.

## Wave 2: Specialized Raw Data Sub-Agents (Multimodal)
**Trigger:** Wave 1 Complete
**Focus:** Create specialized "readers" capable of processing CSV, PDF, and Image data.

- [ ] **[TASK-2.2.1] Create Raw Bacnet Agent**
    - [x] **[TASK-2.2.1.1] Setup Agent Directory**: Create `agent/sub_agents/bacnet/`.
    - [x] **[TASK-2.2.1.2] Design Multimodal Prompt**: Create `prompt.md` with instructions for CSV point-list parsing (BACnet) and screenshot tag identification.
    - [x] **[TASK-2.2.1.3] Implement Agent Class**: Create `agent.py` using `LoopWrapper` for iterative task processing.
    - [x] **[TASK-2.2.1.4] Tool Integration**: Ensure agent has access to `fetch_pending_task`, `mark_technical_progress`, `write_metadata`, and `load_artifacts`.
    - [ ] **[TASK-2.2.1.5] Verification**: Test agent logic with a sample CSV and physical equipment ID from the grid.
- [ ] **[TASK-2.2.2] Create Raw Control Agent**
    - [ ] **[TASK-2.2.2.1] Setup Agent Directory**: Create `agent/sub_agents/control/`.
    - [ ] **[TASK-2.2.2.2] Design Multimodal Prompt**: Create `prompt.md` with instructions for PDF sequence/diagram parsing.
    - [ ] **[TASK-2.2.2.3] Implement Agent Class**: Create `agent.py` using `LoopWrapper`.
    - [ ] **[TASK-2.2.2.4] Tool Integration**: Ensure access to necessary task and metadata tools.
- [ ] **[TASK-2.2.3] Create Raw Electricity Agent**
    - [ ] **[TASK-2.2.3.1] Setup Agent Directory**: Create `agent/sub_agents/electricity/`.
    - [ ] **[TASK-2.2.3.2] Design Multimodal Prompt**: Create `prompt.md` with instructions for Panel Schedule/Single Line Diagram parsing.
    - [ ] **[TASK-2.2.3.3] Implement Agent Class**: Create `agent.py` using `LoopWrapper`.
    - [ ] **[TASK-2.2.3.4] Tool Integration**: Ensure access to necessary task and metadata tools.

## Wave 3: Iterative Raw Mapping Loop
**Trigger:** Wave 2 Complete
**Focus:** Orchestrate the agents to process every piece of equipment on the grid.

- [ ] **[TASK-2.3.1] Setup Raw Mapping Loop Orchestrator**
    - Wrap the specialized agents in a Loop level (Master -> Loop -> Sub-Agents).
- [ ] **[TASK-2.3.2] Implement Mapping Logic**
    - Agents use `read_grid` to get an equipment list.
    - For each equipment, agents iterate through their specific folders to find matching IDs/Tags.
    - Components are matched by name patterns (e.g., `AHU-1` in grid to `1A` or `System 1` in metadata).

## Wave 4: Frontend Persistence & HITL Verification
**Trigger:** Wave 3 Complete
**Focus:** Human validation of the raw extracted data.

- [ ] **[TASK-2.4.1] Batch Sync to Frontend**
    - Use `add_metadata` to push all extracted data to the frontend grid components.
- [ ] **[TASK-2.4.2] Human-in-the-Loop (HITL) Review**
    - User verifies the raw extraction results on the frontend.

## Must-Haves (DoD)
- [ ] Agents successfully process CSV, PDF, and Image sources.
- [ ] `add_metadata` tool correctly updates the component EDN on the frontend.
- [ ] Technical points are correctly linked to physical IDs and visible on the frontend.
