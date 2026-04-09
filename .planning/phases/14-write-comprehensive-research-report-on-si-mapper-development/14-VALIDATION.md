---
phase: 14
slug: write-comprehensive-research-report-on-si-mapper-development
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | LaTeX compilation check (no automated test suite — report is a document) |
| **Config file** | none — Wave 0 creates report structure |
| **Quick run command** | `pdflatex -shell-escape -interaction=nonstopmode report/main.tex 2>&1 \| grep -c "^!"` (expect 0 errors) |
| **Full suite command** | Manual review of compiled PDF against 6-section checklist |
| **Estimated runtime** | ~10 seconds for compilation check |

---

## Sampling Rate

- **After every section file written:** Run `pdflatex -shell-escape -interaction=nonstopmode report/main.tex` — verify no errors
- **After every plan wave:** Full PDF review against 6-section checklist
- **Before `/gsd:verify-work`:** Full suite must compile cleanly with all 6 sections present
- **Max feedback latency:** 10 seconds (compile check)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| R14-01 | 14-01 | 0 | LaTeX structure created | compile | `pdflatex -shell-escape -interaction=nonstopmode report/main.tex 2>&1 \| grep -c "^!"` expect 0 | ❌ Wave 0 | ⬜ pending |
| R14-02 | 14-01 | 0 | All 6 sections present | file_exists | `ls report/sections/0{1..6}-*.tex` expect 6 files | ❌ Wave 0 | ⬜ pending |
| R14-03 | 14-02 | 1 | Mermaid CLI available | compile | `mmdc --version` exits 0 | ❌ Wave 0 | ⬜ pending |
| R14-04 | 14-02 | 1 | Mermaid diagrams rendered | file_exists | `ls report/figures/*.png` expect ≥3 files | ❌ Wave 0 | ⬜ pending |
| R14-05 | 14-03 | 1 | TODO markers in results | grep | `grep -n "TODO" report/sections/05-results.tex` expect ≥5 matches | ❌ Wave 0 | ⬜ pending |
| R14-06 | 14-03 | 1 | Skills and tools tables present | grep | `grep -c "skill-ductwork\|skill-hvac" report/sections/04-implementation.tex` expect ≥1 | ❌ Wave 0 | ⬜ pending |
| R14-07 | 14-04 | 2 | Full PDF compiles clean | compile | `pdflatex -shell-escape -interaction=nonstopmode report/main.tex 2>&1 \| grep -c "^!"` expect 0 | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `report/main.tex` — master LaTeX file (preamble, \input{} sections, bibliography)
- [ ] `report/sections/01-introduction.tex` — empty section stub
- [ ] `report/sections/02-problem.tex` — empty section stub
- [ ] `report/sections/03-solution.tex` — empty section stub
- [ ] `report/sections/04-implementation.tex` — empty section stub
- [ ] `report/sections/05-results.tex` — empty section stub with TODO markers
- [ ] `report/sections/06-conclusions.tex` — empty section stub
- [ ] `report/figures/` — directory for Mermaid PNG renders
- [ ] Mermaid CLI: `npm install -g @mermaid-js/mermaid-cli` — verify or install

*Wave 0 creates the document skeleton. Content goes in Wave 1+.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Section content accuracy | All 6 chapters | Content quality requires human judgment | Read compiled PDF; verify each section matches CONTEXT.md decisions |
| Mermaid diagram clarity | Architecture diagrams | Visual quality can't be automated | Open rendered PNGs; verify components and arrows are legible |
| Business-appropriate tone | Audience: managers | Register and tone require human assessment | Read intro and problem sections; verify non-technical language |
| TODO placeholders visible | Results section | Must be clear for user to fill data | Scan Section 5 in compiled PDF; all metric fields show "TODO" or equivalent |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (report/ structure)
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
