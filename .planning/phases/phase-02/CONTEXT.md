# Context: Phase 2 - Raw Information Extraction & Mapping

## Domain Boundary
Enrich physical HVAC topology with raw technical metadata from BACnet, Control, and Electricity sources. This phase focuses on **multimodal extraction** (CSV, PDF, Images) and **frontend visualization** (HITL) rather than final semantic graph generation.

## Implementation Decisions

### A. Multimodal Data Analysis
Sub-agents must be prompted to handle diverse file formats within their domain folders:
- **Bacnet Sub-Agent**: Must be proficient in parsing CSV point lists and correlating them with visual identifiers in controller screenshots.
- **Control Sub-Agent**: Must extract logic and setpoints from narrative PDF sequences and system diagrams (images).
- **Electricity Sub-Agent**: Must parse high-density technical PDFs (Panel schedules, one-line diagrams) to map power specs to equipment.

### B. MCP Server Expansion
- **Metadata Management**: A new manager `MetadataManager` will manage the merging of arbitrary metadata into component dictionaries in the EDN grid.
- **`add_metadata` Tool**: Exposes `add_metadata(equipment_name: str, metadata: dict)`. It must support nested dictionaries to organize metadata by source (e.g., `{ "bacnet": {...}, "control": {...} }`).

### C. Agent State & Progress (Multi-Agent Verification)
- **Task-Based Tracking**: Every piece of equipment identified via `read_grid` is enqueued as a separate `Task`.
- **Three-Agent Completion**: A task is only considered "Complete" (ready for verification) once it has been processed by:
    1. **Bacnet Sub-Agent** (Sets `bacnet_treated: true`, Tags: `treated-by-bacnet`)
    2. **Control Sub-Agent** (Sets `control_treated: true`, Tags: `treated-by-control`)
    3. **Electricity Sub-Agent** (Sets `electricity_treated: true`, Tags: `treated-by-electricity`)
- **Persistence**: These flags persist in the session state within the task objects, preventing redundant work if the process is interrupted.

## Claude's Discretion
- **Tag Normalization**: Agents have discretion to normalize tag names (e.g., "Temp Alim" to "Supply Temperature") for better human readability on the frontend, while preserving the raw value.
- **Fuzzy Identification**: If a piece of equipment in a file is labeled "AHU-01" but "AHU-1" on the grid, the agent should assume a match but flag it in the metadata for human confirmation.

## Specific Ideas
- Metadata should be stored under source-specific keys (`bacnet`, `control`, `electric`) to keep the data organized for the human reviewer.
- Use the `read_grid` tool early in each sub-agent's prompt to ensure they are looking for specific targets.

## Deferred/Obsolete
- Formal Semantic Graph Generation (Phase 3).
- Automated Ontology Enforcement (Phase 3).
