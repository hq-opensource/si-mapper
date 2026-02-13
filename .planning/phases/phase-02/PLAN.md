# Plan: Phase 2 - Raw Information Extraction & Mapping

**Goal:** Integrate raw technical metadata from BACnet, Control, and Electricity sources with the physical HVAC topology. The extracted data is saved to the frontend (GraphyBack) for easy Human-in-the-Loop (HITL) verification.

## Wave 1: Extraction Infrastructure & Tools
**Trigger:** Start of Phase 2
**Focus:** Build the tools necessary for state persistence and frontend integration.

- [x] **[TASK-2.1.1] Implement Metadata MCP Tool** 
    - Created `mcp_server/graphivac/metadata_manager.py`.
    - Created `mcp_server/graphivac/metadata_tools.py`.
    - Registered `write_metadata`, `read_metadata`, and `delete_metadata` using native EDN maps in `:custom-fields`.
- [ ] **[TASK-2.1.2] Implement Agent State Persistence Tool**
    - Create `agent/tools/state_tools.py`.
    - Logic: Use `ToolContext.state` to save a `treated` dictionary mapping `equipment_id` to status.
- [ ] **[TASK-2.1.3] Verify `read_grid` Integration**
    - Ensure sub-agents can retrieve equipment lists from the grid via the existing `read_grid` tool.

## Wave 2: Specialized Raw Data Sub-Agents (Multimodal)
**Trigger:** Wave 1 Complete
**Focus:** Create specialized "readers" capable of processing CSV, PDF, and Image data.

- [ ] **[TASK-2.2.1] Create Raw Bacnet Agent**
    - Location: `agent/sub_agents/bacnet/`
    - Logic: Parse `.csv` files (e.g., `filtered_CTRL_2500.csv`) for point lists and analyze images of controller screens for visual confirmation of tags.
- [ ] **[TASK-2.2.2] Create Raw Control Agent**
    - Location: `agent/sub_agents/control/`
    - Logic: Read `.pdf` documents (e.g., Sequence of Operations) to extract operational logic, and analyze system diagram images.
- [ ] **[TASK-2.2.3] Create Raw Electricity Agent**
    - Location: `agent/sub_agents/electricity/`
    - Logic: Analyze `.pdf` files (e.g., panel schedules, one-line diagrams) to extract power requirements (Voltage, Amperage, Panel IDs).

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
