# Plan: Phase 1 - Sequential Topological Reconstruction

**Goal:** Implement an autonomous, sequential multi-agent pipeline to reconstruct HVAC drawings into a grid-aware digital twin with engineering equivalency.

## Wave 1: Foundation & Tools Verification
**Trigger:** Start of Phase 1
**Focus:** Ensure agents can perceive the digital state and coordinate their actions.

- [x] **[TASK-1.1.1] Verify Grid Awareness Tools** ✅
    - Fixed: Streamable HTTP requires `Accept: application/json, text/event-stream` headers.
    - Verified: `read_grid` retrieves current state; `DuctManager` and `CustomManager` correctly sync on the same grid.
- **[TASK-1.1.2] Setup Sequential Orchestrator** (Removed: New simplified architecture)

## Wave 2: Horizontal Duct Extraction (Primary Trunks)
**Trigger:** Wave 1 Complete
**Focus:** Anchor the floor plan with stabilized, normalized horizontal trunks.

- [x] **[TASK-1.2.1] Refine Horizontal Duct Prompt** ✅
- [x] **[TASK-1.2.2] Implement Horizontal Duct Loop** ✅

## Wave 3: Vertical Duct & Connection Extraction
**Trigger:** Wave 2 Complete
**Focus:** Connect the trunks via mixing zones and branches.

- [x] **[TASK-1.3.1] Implement Vertical Duct Agent Prompt** ✅
- [x] **[TASK-1.3.2] Implement Vertical Duct Loop** ✅

## Wave 4: Equipment Placement & Alignment (Current Step)
**Trigger:** Wave 3 Complete
**Focus:** Functional equipment placement with mandatory center-line alignment.

- **[TASK-1.4.1] Implement Equipment Alignment Prompt** (Part of Wave 4)
    - Enforce "Y-Coordinate Sync" with parent ducts.
    - Logic: "Find Fan SF-1, identify parent Duct-X, sync Fan.Y with Duct.Y".
- **[TASK-1.4.2] Implement Equipment Placement Loop** (Part of Wave 4)
    - Handle conflict resolution (don't overlap coils and fans).
    - Support unique naming based on text recognition.
    - **Verification:** Equipment appears exactly centered within its parent duct on the frontend.

## Wave 5: Verification (Human-in-the-Loop)
**Trigger:** Wave 4 Complete
**Focus:** Engineering validation and final polishing.

- **[TASK-1.5.1] Human Verification**
    - Master Agent requests user confirmation instead of automated Review Agent.

## Must-Haves (DoD)
- [ ] Agents execute in order: Horizontal -> Vertical -> Equipment.
- [ ] All horizontal components share a single Y-coordinate with their parent duct.
- [ ] Zero overlapping components on the grid.
- [ ] Review agent successfully runs and fixes at least one connectivity error.
