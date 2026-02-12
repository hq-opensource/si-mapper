# Context: Phase 1 - Sequential Topological Reconstruction (Refactored)

## Domain Boundary
This phase focuses on the autonomous reconstruction of HVAC system topology in the frontend. It involves the sequential extraction and placement of system components (ducts and equipment) onto a grid. 
**Crucial Change:** The architecture is being flattened. The complex, nested "Drawing Architecture" is replaced by a simpler **Master Agent -> Sub-Agents** pattern.

## Implementation Decisions

### A. Architecture: Flat Master-SubAgent Structure
- **Master Agent as Orchestrator**: The Master Agent directly manages the workflow and delegates tasks.
- **Sub-Agents**: Three specific sub-agents will be created in `agent/sub_agents/`, derived from the previous "Level 5" agents:
    1.  **Horizontal Ducts Agent** (`agent/sub_agents/horizontal_ducts/`)
    2.  **Vertical Ducts Agent** (`agent/sub_agents/vertical_ducts/`)
    3.  **Equipment Agent** (`agent/sub_agents/equipment/`)
- **Direct Delegation**: The Master Agent will have specific instructions (prompts) to delegate tasks to these three agents sequentially or as needed, without intermediate "Loop" or "Sequential" agents.

### B. Legacy Removal
- **Delete Drawing Architecture**: The entire `agent/drawing_architecture/` folder (containing nested loops, sequential agents, review agents) is obsolete and will be deleted after the new sub-agents are verified.
- **Review Agent Removed**: The automated "Review Agent" (Phase 1.4) is removed.
- **Human Review**: Verification is now a "Human-in-the-loop" process. The Master Agent will present results, and the human (User) provides the "Review" function.

### C. Behavior: Placement Logic (Preserved)
- **Center-Line Snapping**: Equipment must snap to the center-line (Y-coordinate) of parent horizontal ducts.
- **Rectilinear Normalization**: Ducts must be perfectly horizontal or vertical.
- **Layering**: Ducts first, then Equipment.
- **Grid Awareness**: Agents must use `read_grid` to be aware of existing components.

### D. Sub-Agent Responsibilities
- **Horizontal Ducts**: Extract and place primary horizontal trunks.
- **Vertical Ducts**: Extract and place vertical branches and mixing zones.
- **Equipment**: Extract and place fans, coils, humidifiers, etc., snapping them to the grids.

## Claude's Discretion
- **Tools Adaptation**: The existing tools used by Level 5 agents should be ported/imported for the new sub-agents.
- **Prompt Migration**: The existing prompts for Level 5 agents should be moved and slightly adjusted to fit the new flat structure (removing references to the old hierarchy if any).

## Specific Ideas
- Create a `agent/sub_agents` directory with a flat file structure.
- Update `master_instruction.md` to explicitly list the 3 new sub-agents and their purposes.

## Deferred/Obsolete
- Automated Review Agent (Removed).
- Complex nested agent loops (Removed).
