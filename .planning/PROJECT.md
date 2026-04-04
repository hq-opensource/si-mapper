# Project: Automated HVAC Topological Reconstruction & ASHRAE 223P Mapping

**Vision:**  
Transform static HVAC multi-modal data into an engineering-equivalent digital twin. The system will autonomously reconstruct the topology of HVAC systems in a specialized frontend tool and map all operational data (BACnet, control points) to the correct physical components, ultimately exporting a standardized ASHRAE 223P graph.

**Core Value:**  
Engineers can upload a drawing and related technical files (Excel, BACnet, PDFs) and receive a verified, interactive, and functionally accurate digital representation of the system, reducing manual mapping time by 90% and ensuring data consistency.

## Requirements (Hypotheses)
- **[REQ-1] Multi-modal Context Ingestion**: The system must ingest and synchronize data from images (drawings), PDFs, Excel schedules, and BACnet configuration files.
- **[REQ-2] Sequential Topological Extraction**: Agents must execute in a specific order: 
    1. **Horizontal Ducts** (Primary trunks)
    2. **Vertical Ducts** (Mixing zones and connections)
    3. **Equipment** (Fans, Coils, Humidifiers, etc., placed relative to ducts).
- **[REQ-3] Grid-Aware State Synchronization**: Before acting, agents must read the current "Frontend Grid State" to ensure new components are placed accurately relative to existing ones and to avoid overlaps.
- **[REQ-4] Engineering Equivalency Logic**: The reconstruction must prioritize functional connectivity (e.g., "Fan must be upstream of Coils") over exact visual pixel replication.
- **[REQ-5] Data-to-Component Mapping**: Operational data (BACnet points, control logic) must be tagged to the specific component instance identified in the drawing (e.g., SF-1 Fan Speed mapped to the physical SF-1 Fan).
- **[REQ-6] ASHRAE 223P Graph Export**: The final state must be exportable as a valid ASHRAE 223P semantic graph.

## Key Decisions
- **Hierarchical Agent Orchestration**: Use a Master Agent to coordinate a sequence of specialized Level 4 agents (Ducts, Equipment, Review).
- **Frontend-First Validation**: The frontend grid serves as the "Source of Truth" for human verification and agent context.
- **Standardized Mapping**: Use ASHRAE 223P as the final semantic target to ensure industry compatibility.

## Constraints
- **Multi-modal Complexity**: Data sources may be contradictory or incomplete; the agent must handle "best-guess" engineering logic.
- **Alignment Accuracy**: Components must stay within the bounds of their parent ducts (Y-coordinate alignment).
- **No Stack Changes**: Maintain the current Python (FastAPI/GenAI) and TypeScript (Next.js) stack.

## Current State

Phase 23 complete (2026-04-04) — Master agent now has 4 Cypher query tools for live Neo4j exploration: `execute_cypher`, `execute_cypher_batch` (parallel via ThreadPoolExecutor), `get_graph_schema`, `search_graph_entities`. 15 unit tests pass. Neo4j Query Protocol added to master_instruction.md with write-gate safety rule.

**Last updated:** 2026-04-04
