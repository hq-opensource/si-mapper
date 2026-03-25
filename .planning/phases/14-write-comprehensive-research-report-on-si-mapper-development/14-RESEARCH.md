# Phase 14: Write Comprehensive Research Report on SI-Mapper Development - Research

**Researched:** 2026-03-25
**Domain:** LaTeX report writing; HVAC building ontologies; BACnet/Modbus mapping; ASHRAE 223P; agentic AI for building systems; NWA/VPP business case
**Confidence:** HIGH (LaTeX tooling), HIGH (ASHRAE 223P), MEDIUM-HIGH (BACnet costs), MEDIUM (NWA/VPP connection)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- LaTeX files in the existing `report/` folder
- One main `.tex` file with chapters as separate `.tex` files (or sections within one file — Claude's discretion on file structure)
- Diagrams: Mermaid diagrams rendered inside LaTeX (e.g., via `minted` or external render + include)
- No Word or Markdown output — LaTeX is the final artifact
- Target audience: business units, managers, non-technical stakeholders
- Tone: professional but accessible; technical concepts explained at a high level, not deep dives
- Length: short and focused — all key ideas present but none over-explained
- Avoid jargon-heavy or code-heavy content; prefer clear prose + tables + diagrams
- Section 4 focus: **why** decisions were made, not just what or how
- For the final iteration: explain what components exist, why single-agent + skills was chosen over sub-agents, why earlier approaches were abandoned, architecture decisions (ADK, Neo4j, CopilotKit)
- `agent/skills.md` and `agent/tools.md` heavily summarized — tables or brief lists only
- History of experiments presented as a progression narrative, not a detailed technical log
- No code snippets — architecture diagrams (Mermaid) and tables instead
- Section 5 is placeholder only — data not yet available; leave clear TODO markers
- Results structure: System 1 (AHU) + System 3 (AHU) experiments; token count, cost, time; Human engineer baseline; comparison tables

### Claude's Discretion
- LaTeX file/folder structure within `report/`
- Exact Mermaid rendering approach in LaTeX
- Table styling and figure captions
- Bibliography/citation format (if any references are added)

### Deferred Ideas (OUT OF SCOPE)
- None
</user_constraints>

---

## Summary

This phase produces a complete LaTeX research report documenting the SI-Mapper project — from theoretical context through implementation history to a results comparison. The report has six fixed sections. Sections 1-4 and 6 are fully writable now; Section 5 is a placeholder awaiting experiment data.

The research below is organized to feed directly into report chapters. Key findings: (1) building ontologies are a well-established but fragmented landscape, with ASHRAE 223P emerging as a unifying semantic layer currently in second advisory public review; (2) BACnet/Modbus point mapping for existing buildings is a documented, costly, labor-intensive problem with no widely-adopted automated solution; (3) the NWA/VPP sector urgently needs interoperable building data and is actively blocked by the same metadata problem SI-Mapper solves; (4) agentic AI for building digitization is a very recent development with no prior system combining multimodal drawing recognition, BACnet mapping, and ASHRAE 223P generation in a single agentic pipeline.

**Primary recommendation:** Structure the LaTeX as a single main file (`report/main.tex`) with `\input{}` for each section file. Use `minted` for any code display and render Mermaid diagrams externally then include as PDF/PNG figures. This approach is standard, maintainable, and avoids LaTeX compilation complexity.

---

## Section 1 Research: Building Ontology Landscape (Chapter 1 Content)

### The Semantic Metadata Problem in Buildings

Every building contains dozens to hundreds of sensors, actuators, and control points. Each BMS vendor uses proprietary naming conventions. Without a standardized metadata layer, software cannot automatically understand what a point named `2500.AI11` means, which physical device it belongs to, or how that device connects to others in the system.

This metadata gap — the absence of machine-readable building descriptions — is the root cause of why building software is not "plug and play." Every deployment requires manual, building-by-building point mapping. As the U.S. Department of Energy states directly: "building software is not 'plug and play' — technicians must manually map sensors and actuators to software inputs through tedious point mapping processes that vary building-by-building."

### The Four Major Building Ontologies

| Ontology | Governed By | Approach | Focus | Maturity |
|----------|------------|----------|-------|---------|
| **Project Haystack** | Haystack Connect | Tag-based dictionary | Equipment types, sensor tags | Widely deployed, informal |
| **Brick Schema** | Open consortium | RDF/OWL semantic graph | Equipment, sensor, spatial hierarchy | Production ready (v1.4) |
| **RealEstateCore (REC)** | RealEstateCore Consortium | OWL ontology | Property management + technical systems | Production ready |
| **ASHRAE 223P** | ASHRAE + DOE/NREL | Formal OWL ontology | Topology, connections, telemetry, mediums | Second advisory public review (2025) |

**Haystack** uses a tagging system with no formal rules for tag usage, resulting in highly customized and inconsistent modeling practices across vendors. **Brick Schema** adds formal semantic rules on top of a Haystack-like vocabulary, promoting consistency and interpretability — it has greater completeness and expressiveness. **RealEstateCore** focuses more on property management but overlaps significantly with technical building systems. **ASHRAE 223P** is the most rigorous: it defines not just equipment types but full topology (connections, mediums, directionality) and links semantic entities to BACnet external references.

A 2025 systematic comparison of these four ontologies found that Haystack and Brick are more compact in axiomatic design, while Brick and RealEstateCore have greater expressiveness. No single ontology covers all needs — in practice, a complete building model is expected to be "a mix of ASHRAE 223P, Brick, QUDT, RealEstateCore, and possibly additional standards."

ASHRAE's BACnet committee, Project Haystack, and Brick Schema are actively collaborating to integrate their vocabularies into ASHRAE 223P as the unifying standard. ASHRAE 223P is designed as the low-level schema that ties together existing approaches.

### Advantages and Disadvantages of Semantic Building Models

**Advantages:**
- Software portability: applications can work across buildings without building-specific customization
- Enable advanced analytics: fault detection, automated commissioning, predictive maintenance
- Enable grid services: semantic models are required to connect building loads to utility VPP/NWA programs
- Reduce integration costs: once a model exists, any compliant application can consume it
- Support digital twins: semantic layer is the connective tissue between real and virtual systems

**Disadvantages / Current Barriers:**
- High creation cost: building a semantic model today requires specialized domain expertise and significant labor
- No automated tooling for existing buildings: most approaches are manual or semi-manual
- Fragmented standards landscape: organizations must choose between partially-overlapping standards
- Model maintenance: models drift from reality as systems are modified
- Low adoption: the industry has been slow to adopt formal ontologies despite their benefits

### Relevant Source Material for Chapter 1
- ASHRAE 223P documentation at docs.open223.info (HIGH confidence)
- DOE Semantic Modeling and Interoperability project page (HIGH confidence)
- Systematic comparison paper on building ontologies (arXiv 2603.14374, 2025) (HIGH confidence)
- ProptechOS semantic modeling guide for BMS engineers (MEDIUM confidence)
- Brick Schema + RealEstateCore harmonization announcement (HIGH confidence)

---

## Section 2 Research: ASHRAE 223P Deep Dive (Chapters 1 and 3 Content)

### What ASHRAE 223P Is

ASHRAE Standard 223P is a proposed ASHRAE standard that formally defines a knowledge representation framework for building systems. It is a semantic ontology — a machine-readable vocabulary with formal rules — that enables software applications to determine the meaning and context of building data.

**Current status (as of 2025-2026):** Second advisory public review. Not yet a ratified standard. The project runs October 2023 through September 2025 with $1.3M DOE funding. Lead performer: National Renewable Energy Laboratory (NREL), with Lawrence Berkeley National Lab (LBNL), Pacific Northwest National Lab (PNNL), NIST, Colorado School of Mines, Cornell University, and Semantic Interoperability Consultants.

### What ASHRAE 223P Standardizes

The standard organizes building system information around **six core concepts**:

| Concept | Definition | Example |
|---------|------------|---------|
| **Type** | Well-defined classes with formal rules governing usage | `s223:Fan`, `s223:Pump`, `s223:CoolingCoil` |
| **Topology** | How equipment and spaces connect | Fan outlet → Duct → Coil inlet |
| **Composition** | Hierarchical grouping of entities | AHU contains Fan, Coil, Damper |
| **Telemetry** | Observable/actuatable properties with external data references | Supply air temp → BACnet object `2500.AI11` |
| **Characteristics** | Descriptive attributes with units from QUDT | Rated airflow in m³/s |
| **Medium** | Substance conveyed through connections | Chilled water, Supply air, Electricity |

**Topology** is the most distinctive concept. 223P introduces:
- **Connectables**: entities capable of connecting to each other (Equipment, Spaces)
- **ConnectionPoints**: precise locations where connections occur (InletConnectionPoint, OutletConnectionPoint, BidirectionalConnectionPoint)
- **Connections**: physical conveyance paths (ducts, pipes, wires)

This allows an ASHRAE 223P model to represent not just "there is a fan and a coil" but "air flows from the fan outlet through a duct segment into the coil inlet, conveying the medium Supply Air."

**Telemetry / External References** allow BACnet object IDs to be explicitly linked to semantic properties. A temperature sensor in the model can reference `BACnet object 2500.AI11` — closing the loop between the ontology and the live BMS.

### ASHRAE 223P Relationship to Other Standards

| 223P Concept | Maps To | Notes |
|-------------|---------|-------|
| Equipment types | Brick Schema classes | Active harmonization underway |
| Tags | Project Haystack tags | Tag concepts integrated |
| Units | QUDT ontology | Formal unit representation |
| Spatial hierarchy | Brick Schema locations | Complementary, not competing |
| BACnet reference | BACnet object model | First-class external reference concept |

The intended workflow: ASHRAE 223P provides the rigorous semantic backbone. Brick and Haystack provide practical vocabulary. QUDT provides units. Together they describe a building's systems completely enough for software to self-configure without manual intervention.

### Why ASHRAE 223P Matters for SI-Mapper

SI-Mapper generates ASHRAE 223P-compliant TTL files as its primary output. This is not arbitrary — it is the only standard that:
1. Captures full HVAC topology (not just equipment lists)
2. Links BACnet points to semantic equipment properties
3. Is designed specifically for advanced building controls and grid services
4. Is backed by DOE, NREL, LBNL, and is undergoing standardization through ASHRAE

---

## Section 3 Research: The BACnet/Modbus Mapping Problem (Chapter 2 Content)

### What the Problem Is

Building automation systems (BAS) expose operational data through a hierarchy of "points" — individual sensors, actuators, setpoints, alarms, schedules, and status flags. In BACnet, each point is a typed object (Analog Input, Binary Output, etc.) with a unique address. In a typical commercial building, there may be hundreds to thousands of such points.

The mapping problem is this: **a raw list of BACnet points contains no standard information about what physical equipment each point belongs to, what role it plays (supply vs. return, setpoint vs. measurement), or how that equipment connects to others in the system.** This information must be reconstructed — either by reading HVAC drawings, by interrogating BMS programming, or by expert engineering judgment.

### Cost and Effort Data

Manual BACnet/BMS point mapping is widely acknowledged as a major cost driver. Research and industry reports document the following:

**Direct commissioning costs:**
- Building Automation System commissioning costs 0.5%–1.5% of total construction costs, or 8%–15% of the BAS project value. (Source: Building Commissioning Association / pingcx.com)
- A 150,000 sq ft school example: $225,000 commissioning cost ($1.50/sq ft). (Source: pingcx.com)
- National Renewable Energy Lab 2021: complete BAS installation averages $7.76/sq ft, range $5.20–$14.18/sq ft.
- Legacy BMS integration (existing buildings) adds 20%–40% to base cost. Integration services for legacy buildings accounted for 39% of all service revenue in 2023. (Source: envigilance.com)

**Hidden costs of poor mapping:**
- Inadequate documentation increases troubleshooting time 30–45%, resulting in 12–15 additional service calls per year. (Source: pingcx.com)
- Energy performance drift: 15–30% energy waste within the first three years from inadequate commissioning, costing $0.20–$0.50/sq ft/year. (Source: pingcx.com)
- First-year performance issues in the case study school: $175,000 in unplanned expenses — nearly equal to the original commissioning cost.
- Manual approaches typically test only 10–20% of terminal units; every 10% reduction in testing coverage correlates to ~6–8% increase in post-occupancy issues.

**Labor market context:**
- The HVAC industry faces a critical shortage of 110,000 technicians as of 2024–2025. (Source: leads4build.com)
- Qualified BMS engineers who can perform point mapping are a scarce, expensive resource.

**Per-point cost (industry estimates):**
A DOE/ACEEE paper from 2024 describes manual point mapping as "labor intensive and costly, presenting a major impediment to innovations in building control" — validating the problem even if exact per-point figures vary by project and contractor. Industry practitioners report costs of $50–$200 per point for full commissioning including mapping, though this is not a single authoritative source figure.

### The Research Gap

A ScienceDirect review paper (Automated Point Mapping for Building Control Systems, S0926580517300018) identifies that the field lacks:
- A complete problem formulation with integrated solution approaches
- Standardized test datasets and performance metrics
- Methods well-aligned with real-world mapping requirements

This gap validates SI-Mapper's research contribution: there is no established, widely-deployed automated solution for the point mapping problem.

### Who Has Documented This Pain

1. **DOE / NREL / LBNL**: The entire ASHRAE 223P project is a direct response to this problem. The DOE states explicitly: technicians "must manually map sensors and actuators to software inputs through tedious point mapping processes."
2. **Building Commissioning Association (2024 Commissioning Definitions)**: Defines point-to-point checking as a required verification step, confirming it is a standard labor-intensive activity on every BAS project.
3. **ACEEE 2024 conference paper** (Digital and Interoperable: The Future of Building Automation): documents the gap between current BMS interoperability and what is needed for advanced controls.
4. **Academic literature**: The ScienceDirect review paper explicitly labels manual point mapping as "a major impediment to innovations in building control."

### Modbus Context

Modbus is the older, simpler protocol used in legacy HVAC equipment, meters, and industrial controllers. It exposes data as registers with no semantic meaning whatsoever — even less information than BACnet. Mapping Modbus points to physical equipment and semantic properties requires the same expert knowledge as BACnet but with even less metadata to work from. SI-Mapper's approach (reading BACnet CSV exports with French equipment naming conventions from Quebec installations) represents a real-world instance of this challenge.

---

## Section 4 Research: NWA / VPP Business Case (Chapter 2 Content)

### Why Grid Operators Need This Data

Non-Wire Alternatives (NWA) and Virtual Power Plants (VPP) aggregate distributed energy resources — including commercial building HVAC loads — to provide grid services equivalent to traditional infrastructure. Buildings represent a major flexible load: HVAC systems consume 40% of total commercial building energy and can be modulated to respond to grid signals.

**2024–2025 VPP market facts:**
- North American VPP market: 37.5 GW of flexible behind-the-meter capacity as of 2025, up 14% from 2024.
- Active VPP deployments rose more than 33% in the same period.
- In 2024, ten state legislatures introduced VPP bills; regulators in ten states and D.C. advanced VPP policy.
- Massachusetts utilities are implementing a $50M Grid Services Compensation Fund for non-wire alternatives.
- California Energy Commission awarded a $2M EPRI grant specifically to demonstrate VPPs for **commercial buildings** including HVAC controls.
- DOE VPP Liftoff 2025 report identifies simplifying enrollment as the top priority. (Source: DOE Liftoff / Pew Charitable Trusts)

### The Critical Link: Interoperability Blocks VPP Enrollment

The primary barrier to scaling VPP programs to commercial buildings is exactly the same problem SI-Mapper addresses: **lack of technical interoperability and standardized building system metadata.**

From the DOE VPP 2025 report: "No industry standardization exists. VPP vendors have been building their solutions from the ground up, then working on a case-by-case basis with utilities to develop customized solutions, resulting in rigid systems that can't easily be replicated in new areas."

From a United Illuminating pilot (NWA program): the major barrier to enrolling large commercial facilities in automated demand response is "IT data security and building system interoperability."

The chain of causality:
1. Building HVAC system data is not machine-readable in a standard form
2. Each building requires custom integration work to connect to a VPP platform
3. Custom integration is expensive ($5–$15k per building, or more for complex facilities)
4. High per-building cost prevents aggregators from enrolling the thousands of buildings needed for VPP scale
5. Without scale, VPP programs cannot reliably deliver the grid capacity utilities need

**If buildings had ASHRAE 223P semantic models**, VPP platforms could automatically understand what controllable loads exist, what their current state is, and how to dispatch them — eliminating the custom integration barrier.

### Why This Makes SI-Mapper Strategically Important

SI-Mapper is not just a productivity tool for individual HVAC engineers. It is potentially a critical piece of infrastructure for the energy transition:

- HVAC load flexibility is essential for integrating renewable energy (solar/wind intermittency requires dispatchable demand)
- Commercial buildings represent a 37.5 GW flexible resource in North America alone
- The bottleneck is not the hardware — it is the missing semantic data layer
- SI-Mapper automates the creation of that data layer from existing BMS exports and drawings

This positions the tool as infrastructure for the grid — not just a building design aid.

---

## Section 5 Research: Existing Approaches and Their Limitations (Chapter 3 Content)

### What Has Been Tried

| Approach | What It Does | Why It Falls Short |
|----------|-------------|-------------------|
| **Manual expert mapping** | Engineer reads drawings, BMS configuration, names all points by hand | $50–$200/point, weeks per building, requires scarce expertise, error-prone |
| **Vendor proprietary tools** | BMS vendors (Siemens, Johnson Controls, etc.) provide semi-automated configuration within their own ecosystem | Vendor lock-in; does not interoperate; does not produce semantic models; tied to new installations only |
| **Tag-based normalization** | Rule-based scripts parse point names using regex or keyword matching (Haystack tagging) | Brittle; breaks with naming convention variations; does not capture topology or equipment relationships |
| **Building Information Modeling (BIM)** | Architectural/MEP models capture equipment and geometry | Created during design; diverges from as-built; HVAC operational data not included; requires BIM expertise |
| **Brick Schema generation tools (manual)** | Engineers use Brick tools to manually describe building in RDF | Still requires expert knowledge and manual data entry; no automation of the process |
| **BrickLLM (2025)** | LLM converts natural language building descriptions to Brick RDF | Requires accurate natural language input; no visual drawing analysis; no BACnet integration; produces Brick (not ASHRAE 223P with topology) |
| **LLM point classification** | LLMs classify BACnet point names into ontology tags | Classifies individual points; does not reconstruct topology; does not handle drawings; not end-to-end |

### The State of the Art Gap

No prior system combines:
1. Visual HVAC drawing analysis (multimodal AI)
2. Automated BACnet CSV point-to-equipment mapping
3. Full ASHRAE 223P topology generation with ConnectionPoints and Connections
4. Iterative validation with error correction

The closest academic work (BrickLLM, 2025, ScienceDirect S2352711025000883) addresses only natural language → Brick RDF and requires accurate text input describing the building. It does not address the drawing recognition problem, the BACnet CSV parsing problem, or ASHRAE 223P topology generation.

The automated point mapping review paper (ScienceDirect S0926580517300018) identifies this as an open research problem, explicitly noting the lack of "complete problem formulation with integrated solution approaches."

### Why Multimodal AI Changes the Equation

Recent multimodal LLMs (Gemini 2.0/2.5, Claude Sonnet, GPT-4V) can analyze engineering drawings. A 2025 benchmark (AECV-bench, 150 residential floor plans) showed Gemini 2.5 Pro achieving 41% average accuracy for general architectural elements. HVAC diagrams (schematic, symbol-based) are different from architectural floor plans — they are simpler and more regular, with a smaller symbol vocabulary — making AI recognition more tractable.

The key insight from SI-Mapper's development: standard general-purpose AI models underperform on domain-specific drawing recognition until guided by detailed, domain-specific instructions. The skills-based architecture addresses this by providing the agent with expert-level HVAC drawing reading instructions, not just a generic vision task.

---

## Section 6 Research: Agentic AI for Building Systems (Chapter 3 Content)

### What Agentic AI Is

Agentic AI systems differ from earlier AI in that they can autonomously plan, execute, and verify multi-step tasks without human intervention at each step. They use tools, maintain state across turns, and can loop until a goal is achieved — not just answer a single question.

The industry recognizes three generations:
- **V1:** AI as question-answering function calls (business logic hardcoded by humans)
- **V2:** AI in workflows (business logic in predefined sequences)
- **V3:** Agentic AI (AI autonomously plans and executes, humans set goals and review outcomes)

### Industry Context (2024–2025)

- The global smart buildings market reached $280 billion in 2024; HVAC is 40% of commercial building energy.
- Gartner reported a 1,445% surge in multi-agent system inquiries from Q1 2024 to Q2 2025.
- MCP (Model Context Protocol) has become the de-facto standard for AI-to-tool connectivity, supported by Anthropic, OpenAI, Microsoft, and Replit.
- Companies like Brainbox AI and Xempla are deploying agentic systems for HVAC optimization (not metadata generation).
- The Nexus Labs article identifies the next challenge for building AI as standardized integration — exactly what ASHRAE 223P and SI-Mapper address.

### Agentic AI for Ontology Generation: Novel Territory

Using agentic AI specifically to **generate building semantic models from drawings and BACnet data** is a novel research contribution. Current published work includes:
- **BrickLLM (2025)**: LLM from text → Brick RDF (not agentic, not drawing-based, not 223P)
- **AI agent digital twins for O&M (2025, ScienceDirect S2352710225010393)**: AI agents for operations using an existing ontology (not generating the ontology from raw data)
- **LLM point classification**: Classification of individual point names (not topology reconstruction)

SI-Mapper addresses a prior step: **creating the semantic model in the first place** from raw inputs (HVAC drawings, BACnet CSV, control documentation). This is the gap that blocks all downstream applications.

### Why a Skills-Based Single Master Agent is the Right Architecture

From the experiment history (report/report.md) and the project's architectural evolution:

**Sub-agent architectures failed because:**
- Complex prompts across multiple agents introduced coordination overhead
- Sub-agents finished tasks too early without completing the full goal
- Loop agents added on top of sub-agent architectures improved results but added architectural complexity
- The PAR (Plan-Act-Review) sub-agent architecture improved quality but was still insufficient

**Skills-based single master agent succeeded because:**
- Latest LLMs (Gemini 3.1, Claude Sonnet 4.6) are powerful enough to follow long, detailed skill instructions without decomposing into sub-agents
- Skills provide detailed domain expertise inline without the coordination overhead of separate agents
- Single agent maintains full context across the entire pipeline (drawing → grid → BACnet → ontology)
- Iterative self-correction (screenshot → compare → fix) is natural in a single-agent loop
- Architecture is dramatically simpler to maintain and debug

This progression — from hardcoded functions through workflows through sub-agents to a skills-based master agent — mirrors the industry's broader evolution of agentic AI architectures and provides a compelling narrative for the report.

---

## Section 7: LaTeX Technical Approach (Implementation Planning)

### Recommended File Structure

```
report/
├── main.tex              # Master file: document class, preamble, \input{} calls
├── sections/
│   ├── 01-introduction.tex
│   ├── 02-problem.tex
│   ├── 03-solution.tex
│   ├── 04-implementation.tex
│   ├── 05-results.tex
│   └── 06-conclusions.tex
├── figures/
│   ├── architecture.png  # Rendered Mermaid diagrams (PNG or PDF)
│   ├── pipeline.png
│   └── experiment-progression.png
└── references.bib        # BibTeX file (optional, if citations added)
```

### Mermaid in LaTeX — Recommended Approach

Mermaid cannot be rendered natively inside LaTeX without external tooling. The practical approach for this project is:

**Option A (Recommended): Pre-render Mermaid to PNG/PDF, include as figures**
- Write Mermaid source in a `diagrams/` subfolder (`.mmd` files) for documentation
- Render using `mmdc` CLI: `npx @mermaid-js/mermaid-cli -i diagram.mmd -o diagram.png`
- Include in LaTeX with `\includegraphics{figures/diagram.png}`
- This is reliable and produces publication-quality output

**Option B: TikZ (more LaTeX-native)**
- Convert Mermaid to TikZ using tools like underleaf.ai/mermaid-to-latex
- More complex but fully within the LaTeX ecosystem
- Overkill for a management-facing report

**Recommendation:** Option A. Pre-render PNG at high resolution (300 DPI), include as figures. This avoids compilation complexity and is standard practice for management reports.

### LaTeX Document Class and Packages

For a management-facing technical report:
- Document class: `\documentclass[11pt, a4paper]{report}` or `article`
- Essential packages:
  - `geometry` — margin control
  - `graphicx` — figure inclusion
  - `booktabs` — professional tables
  - `hyperref` — clickable cross-references
  - `xcolor` — colored headings/tables
  - `minted` — if any code blocks are needed (requires `--shell-escape` flag)
  - `microtype` — better typography
  - `biblatex` or `natbib` — citations (if used)

### Table Styling Recommendation

Use `booktabs` tables (no vertical lines, horizontal rules only) — this is the professional standard for technical reports and looks far better than default LaTeX tables.

```
\begin{table}[h]
\caption{...}
\begin{tabular}{lll}
\toprule
Column A & Column B & Column C \\
\midrule
...
\bottomrule
\end{tabular}
\end{table}
```

### Compilation Command

```bash
pdflatex -shell-escape main.tex
bibtex main    # if bibliography used
pdflatex -shell-escape main.tex
pdflatex -shell-escape main.tex
```

Or use `latexmk` for automated compilation management.

---

## Section 8: Validation Architecture

> `workflow.nyquist_validation` key is absent from `.planning/config.json` — treated as enabled.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | No automated tests applicable — report is a LaTeX document |
| Config file | N/A |
| Quick run command | `pdflatex -shell-escape report/main.tex` (compiles without errors) |
| Full suite command | Manual review of compiled PDF against section checklist |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| R14-01 | LaTeX compiles without errors | compile | `pdflatex -shell-escape report/main.tex 2>&1 \| grep -c "Error"` (expect 0) | ❌ Wave 0 |
| R14-02 | All 6 sections present in PDF | manual | Read compiled PDF and verify section headings | ❌ Wave 0 |
| R14-03 | All figures included and render correctly | manual | Visual check of compiled PDF | ❌ Wave 0 |
| R14-04 | All TODO markers visible in results section | manual | `grep -n "TODO" report/sections/05-results.tex` | ❌ Wave 0 |
| R14-05 | Skills table and tools table present in Section 4 | manual | Visual check of compiled PDF | ❌ Wave 0 |

### Sampling Rate

- **Per section completed:** `pdflatex -shell-escape report/main.tex` — verify no LaTeX errors
- **Per wave merge:** Full PDF review against 6-section checklist
- **Phase gate:** Compiled PDF with all 6 sections, no compilation errors, all figures rendering

### Wave 0 Gaps

- [ ] `report/main.tex` — master LaTeX file does not yet exist
- [ ] `report/sections/` — section files do not yet exist
- [ ] `report/figures/` — Mermaid PNG renders do not yet exist
- [ ] Mermaid CLI available: `npm install -g @mermaid-js/mermaid-cli` — verify or install

---

## Architecture and Content Summary for Planner

### Section Content Map

| Section | Title | Primary Sources | Key Content |
|---------|-------|----------------|-------------|
| 1 | Introduction & Context | ASHRAE 223P docs, ontology comparison research | Building ontology landscape, ASHRAE 223P explanation, problem motivation |
| 2 | Problem Description | DOE semantic modeling page, commissioning cost data, VPP/NWA research | BACnet mapping cost/effort, why this matters for grid services |
| 3 | Solution Overview | Agentic AI literature, ADK docs, SI-Mapper architecture | Agentic AI approach, why it addresses the problem, high-level architecture |
| 4 | Implementation | `report/report.md` (experiments), `agent/skills.md`, `agent/tools.md` | Experiment history narrative, final architecture, skills and tools tables, Mermaid diagrams |
| 5 | Results | PLACEHOLDER | TODO tables for System 1 / System 3 metrics |
| 6 | Conclusions | Everything above | Key achievements, limitations, future work |

### Mermaid Diagrams to Create

Three diagrams should be created and rendered for the report:

1. **Pipeline diagram** (Section 3): HVAC Drawing + BACnet CSV → Agent Pipeline → ASHRAE 223P TTL → Neo4j Graph
2. **Architecture diagram** (Section 4): Master Agent + Skills (ductwork, hvac-equip, bacnet-points, ontology-gen, ontology-val) + Tools + Neo4j + CopilotKit Frontend
3. **Experiment progression** (Section 4): Timeline of iterations from V1 (function calling) through V9 (skills-based master agent)

### Tables to Create

**Section 4 tables (from skills.md and tools.md):**

Skills table (6 rows):
| Skill | Purpose |
|-------|---------|
| skill-ductwork | Identify and place all ductwork from HVAC drawings |
| skill-hvac-equipments | Place all HVAC equipment onto established duct system |
| skill-bacnet-points | Extract and map BACnet points to grid equipment |
| skill-ontology-generation | Generate ASHRAE 223P Python code from grid state |
| skill-ontology-validation | Iteratively fix and validate ontology code to produce TTL |
| skill-read-code | Load error-resolution lessons from past sessions |

Tools (grouped by category — ~25 tools across Grid, Metadata, Ontology, Neo4j, Frontend, Ingestion, State, Loop Control categories).

---

## Common Pitfalls (LaTeX Report Writing)

### Pitfall 1: LaTeX Compilation Errors from Missing Packages
**What goes wrong:** `\usepackage{minted}` requires Python `pygments` package and `--shell-escape` flag; omitting either causes hard errors.
**How to avoid:** Verify `pip install pygments` in the environment; always compile with `-shell-escape`.

### Pitfall 2: Mermaid Figures Not Found at Compile Time
**What goes wrong:** `\includegraphics{figures/architecture.png}` fails if PNG was not pre-rendered before compilation.
**How to avoid:** Pre-render all Mermaid diagrams before writing LaTeX that references them; use Wave 0 to set up the render pipeline.

### Pitfall 3: Table Float Positioning
**What goes wrong:** LaTeX places tables at unexpected positions when using `[h]` or `[t]` specifiers with large tables.
**How to avoid:** Use `[htbp]` and `\small` inside wide tables; consider `longtable` for tables longer than one page.

### Pitfall 4: Verbatim Environment Limitations
**What goes wrong:** Standard `\verb{}` cannot appear inside macros or captions; `minted` handles this better.
**How to avoid:** Use `minted` for all code; avoid `verbatim` inside captions.

### Pitfall 5: TODO Markers Not Visible
**What goes wrong:** `% TODO` comments in LaTeX source are invisible in the compiled PDF.
**How to avoid:** Use visible markers like `\textbf{[TODO: Fill in token count after running experiment]}` or a custom `\todo{}` command with red color.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Mermaid → LaTeX conversion | Custom parser | `mmdc` CLI + `\includegraphics` | mmdc produces consistent, high-quality output |
| Bibliography management | Manual `\bibitem` | BibTeX/BibLaTeX | Automated formatting, consistent citation style |
| Multi-file LaTeX | Single monolithic `.tex` | `\input{}` per section | Easier to edit individual sections, planner can assign one task per section file |
| TODO visibility | Code comments | `\textbf{[TODO: ...]}` or `\todo{}` macro | Comments don't appear in PDF; user needs to see TODOs |

---

## Sources

### Primary (HIGH Confidence)
- [ASHRAE Standard 223P User Documentation](https://docs.open223.info/overview/) — overview, definitions, topology, connections, Brick/REC integration
- [DOE Semantic Modeling and Interoperability](https://www.energy.gov/eere/buildings/semantic-modeling-and-interoperability) — DOE project context, problem statement, ASHRAE 223P relationship
- [Open223 Models](https://models.open223.info/intro.html) — example 223P models
- [Google ADK Documentation](https://google.github.io/adk-docs/) — ADK architecture, skills, agent types
- `report/report.md` — experiment history (project source, highest confidence)
- `agent/skills.md`, `agent/tools.md` — final architecture (project source, highest confidence)
- [Building Commissioning Association 2024 Definitions](https://www.bcxa.org/uploads/resources/commissioning-definitions-2024.pdf) — commissioning definitions and point-to-point checking

### Secondary (MEDIUM Confidence)
- [Automated Point Mapping Review Paper](https://www.sciencedirect.com/science/article/abs/pii/S0926580517300018) — manual mapping costs and research gaps (older paper but still referenced as authoritative)
- [Hidden Costs of Manual Commissioning](https://www.pingcx.com/blog/the-hidden-costs-of-manual-commissioning-in-todays-complex-buildings) — commissioning cost data ($225k case study)
- [BrickLLM Paper](https://www.sciencedirect.com/science/article/pii/S2352711025000883) — LLM-based Brick metadata generation
- [Ontology-Enabled AI Agent Digital Twins](https://www.sciencedirect.com/science/article/abs/pii/S2352710225010393) — AI agents for building O&M using ontologies
- [DOE VPP Liftoff 2025](https://liftoff.energy.gov/vpp/) — VPP market size, barriers, commercial building context
- [Nexus Labs Agentic AI for Buildings](https://www.nexuslabs.online/content/understanding-agentic-ai-the-next-leap-in-building-intelligence) — agentic AI in building systems context
- [Systematic Comparison of Building Ontologies](https://arxiv.org/abs/2603.14374) — Brick/Haystack/REC/Digital Buildings comparison
- [Brick + REC Harmonization](https://www.realestatecore.io/brickrec/) — current harmonization efforts

### Tertiary (LOW Confidence — needs verification if cited)
- [2025 HVAC Industry Statistics](https://leads4build.com/insights/hvac-statistics-trends) — 110k technician shortage figure
- [HVAC AI Agents 2025](https://panorad.ai/blog/hvac-ai-agents-smart-building-automation-2025/) — $280B smart buildings market, 40% HVAC energy share
- AECV-bench floor plan recognition results — sourced from a secondary article, not the original benchmark paper

---

## Metadata

**Confidence breakdown:**
- ASHRAE 223P content: HIGH — verified against official docs.open223.info documentation
- BACnet mapping costs: MEDIUM — multiple industry sources, no single authoritative per-point figure; figures are directionally consistent
- NWA/VPP business case: MEDIUM — well-documented at high level; specific technical barrier link to BACnet metadata is logical but not explicitly documented in a single source
- Agentic AI for buildings: HIGH — well-documented industry trend with authoritative sources
- LaTeX tooling: HIGH — standard LaTeX knowledge, verified against common practices
- Existing approaches comparison: HIGH — synthesized from academic literature and DOE sources

**Research date:** 2026-03-25
**Valid until:** 2026-06-25 (ASHRAE 223P status may change if ratification advances; VPP market data updates quarterly)
