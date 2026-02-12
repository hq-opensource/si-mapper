# Roadmap: HVAC Reconstruction & Mapping

## Phase 1: Sequential Topological Reconstruction (Current Focus)
**Goal:** Build the foundation by extracting and placing geometry in the frontend.

- **Phase 1.1: Horizontal Duct Extraction**
    - [ ] Create/Refine specialized agent for primary horizontal trunk identification.
    - [ ] Implement "Grid Reading" tool for agents to understand current frontend state.
- **Phase 1.2: Vertical Duct & Connection Extraction**
    - [ ] Create agent for mixing zones and vertical branches.
    - [ ] Implement placement logic relative to horizontal trunks.
- **Phase 1.3: Equipment Placement & Alignment**
    - [ ] Extract Fans, Coils, Humidifiers.
    - [ ] Enforce grid alignment (Y-coordinate matching with parent ducts).
- **Phase 1.4: Engineering Review & Verification**
    - [ ] Implement Review Agent to check connectivity (e.g., flow direction, sequence).
    - [ ] Human-in-the-loop (HITL) verification pattern for final topology approval.

## Phase 2: Information Extraction & Semantic Tagging
**Goal:** Map technical data to the physical components.

- **Phase 2.1: Multi-modal Data Aggregation** (Excel, BACnet, Control Files)
- **Phase 2.2: Nameplate & Tag Recognition**
- **Phase 2.3: Semantic Point Mapping** (Mapping BACnet objects to components)

## Phase 3: Semantic Graph Generation
**Goal:** Final export to industry standards.

- **Phase 3.1: ASHRAE 223P Ontology Mapping**
- **Phase 3.2: Export Logic & Validation**

---

# Requirements Mapping
| Req ID | Phase | Plan Status |
| :--- | :--- | :--- |
| REQ-1 | Phase 2.1 | Pending |
| REQ-2 | Phase 1.1, 1.2, 1.3 | Pending |
| REQ-3 | Phase 1.1 | Pending |
| REQ-4 | Phase 1.4 | Pending |
| REQ-5 | Phase 2.3 | Pending |
| REQ-6 | Phase 3.1 | Pending |
