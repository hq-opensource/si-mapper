---
phase: 25
slug: translate-report-to-french
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-04
---

# Phase 25 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | manual + bash checks (no test framework — LaTeX output validation) |
| **Config file** | none |
| **Quick run command** | `ls report_french/sections/*.tex report_french/references.bib report_french/main.tex` |
| **Full suite command** | `docker run --rm -v $(pwd)/report_french:/report -w /report texlive/texlive:latest pdflatex -interaction=nonstopmode main.tex 2>&1 | tail -5` |
| **Estimated runtime** | ~60 seconds (Docker LaTeX compile) |

---

## Sampling Rate

- **After every task commit:** Run `ls report_french/sections/*.tex report_french/references.bib report_french/main.tex`
- **After every plan wave:** Run Docker pdflatex compilation
- **Before `/gsd:verify-work`:** Full Docker compile must produce PDF with 0 errors
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 25-01-01 | 01 | 1 | Structure | file-exists | `ls report_french/main.tex report_french/references.bib` | ❌ W0 | ⬜ pending |
| 25-01-02 | 01 | 1 | Preamble | grep | `grep 'french.*babel\|babel.*french' report_french/main.tex` | ❌ W0 | ⬜ pending |
| 25-01-03 | 01 | 2 | Sections | file-exists | `ls report_french/sections/` | ❌ W0 | ⬜ pending |
| 25-01-04 | 01 | 2 | Bib | file-exists | `ls report_french/references.bib` | ❌ W0 | ⬜ pending |
| 25-01-05 | 01 | 3 | Labels intact | grep | `grep -c '\\label{' report_french/sections/*.tex` | ❌ W0 | ⬜ pending |
| 25-01-06 | 01 | 3 | Compile | docker | `docker run ... pdflatex main.tex` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `report_french/` directory created with structure mirroring `report/`
- [ ] `report_french/main.tex` copied and modified with babel[french]
- [ ] All figure/image files symlinked or copied from `report/figures/`

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Translation quality | All body text in French | LLM translation quality not grep-verifiable | Open each .tex file, spot-check paragraphs for French language |
| References.bib titles in French | Bib entries translated | Content quality check | Open references.bib, verify @article title= fields are in French |
| PDF renders correctly | Layout preserved | Visual check | Open report_french/main.pdf, verify no layout regressions vs report/main.pdf |
| \label/\ref consistency | Cross-refs intact | Grep checks label count but not correctness | Check PDF has no "??" reference placeholders |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
