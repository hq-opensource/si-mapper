# Phase 25: Translate Report to French - Research

**Researched:** 2026-04-04
**Domain:** LaTeX document translation, French typographic conventions, pdflatex/babel
**Confidence:** HIGH

## Summary

Phase 25 translates the existing LaTeX research report in `report/` into French and places the output in a new `report_french/` folder. The task is purely textual and structural — no code, agents, or tests are involved. The source report is a 1,279-line, 5-section LaTeX article with one `main.tex`, five section `.tex` files, one `references.bib`, pre-rendered PNG figures (no TikZ source text), and 16 `\todo{}` markers that remain pending.

The primary technical concerns are: (1) enabling French language support in the LaTeX preamble via the `babel` package so that typographic rules (spacing before `:`, `«»` guillemets, section names like "Table des matières") are applied automatically; (2) correctly translating all English body text, captions, section headings, table column headers, and bibliography field values while preserving every LaTeX command and cross-reference unchanged; (3) copying the entire folder structure so the French document compiles identically to the English one using the established Docker `texlive/texlive:latest` compilation pipeline; and (4) deciding how to handle `\todo{}` markers and technical terms (BACnet, ASHRAE 223P, HVAC) that are typically left in English even in French technical documents.

**Primary recommendation:** Copy `report/` to `report_french/`, add `\usepackage[french]{babel}` to the preamble (after `inputenc`), translate all natural-language text file-by-file, leave technical acronyms and proper names in English, and verify compilation with the Docker pdflatex command established in Phase 14.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TBD-01 | Create `report_french/` replicating exact LaTeX structure from `report/` | Folder copy approach documented; `report/` structure fully inventoried |
| TBD-02 | Translate all .tex source files to French | All 5 section files read and scoped; translation guidance provided |
| TBD-03 | Translate `references.bib` entry titles/abstracts | Bib file read; scope and field-by-field guidance provided |
| TBD-04 | Translate any TikZ/diagram LaTeX source text | Confirmed: NO TikZ source exists; all figures are pre-rendered PNGs |
| TBD-05 | Keep same LaTeX preamble structure, packages, and compilation setup | Preamble analyzed; only `babel[french]` addition needed |
| TBD-06 | `report/` folder must not be modified | Enforced by copy-first approach |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| babel (french) | bundled with TeX Live 2026 | French typographic rules, localized headings | The standard LaTeX i18n package; handles French spacing rules automatically |
| pdflatex | TeX Live 2026 (via Docker) | Compilation | Already established in Phase 14; Docker image available |
| texlive/texlive:latest | Docker image | Full TeX Live distribution | Established project pattern — no local pdflatex on WSL2 |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| csquotes | bundled | Context-sensitive quotation marks | Optional; `babel[french]` handles guillemets via `\og`/`\fg` or `"<">"` shortcuts |
| isodate | bundled | Localized date formatting | Only if the `\date` field needs French month name output |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| babel[french] | polyglossia | polyglossia is for XeLaTeX/LuaLaTeX; current preamble uses pdflatex with T1/inputenc — stick with babel |
| Manual guillemets | csquotes | csquotes is cleaner but adds a dependency; babel[french] alone is sufficient for this report |

**Installation:**

No new package installation needed. `texlive/texlive:latest` includes babel and all required language files.

**Compilation command (established in Phase 14):**

```bash
docker run --rm \
  -v /home/juan/codes/si-mapper/report_french:/report \
  -w /report \
  texlive/texlive:latest \
  pdflatex -interaction=nonstopmode main.tex
```

Run twice (first pass builds TOC/cross-references, second pass resolves them). For bibliography:

```bash
docker run --rm -v /home/juan/codes/si-mapper/report_french:/report -w /report texlive/texlive:latest pdflatex -interaction=nonstopmode main.tex
docker run --rm -v /home/juan/codes/si-mapper/report_french:/report -w /report texlive/texlive:latest bibtex main
docker run --rm -v /home/juan/codes/si-mapper/report_french:/report -w /report texlive/texlive:latest pdflatex -interaction=nonstopmode main.tex
docker run --rm -v /home/juan/codes/si-mapper/report_french:/report -w /report texlive/texlive:latest pdflatex -interaction=nonstopmode main.tex
```

## Architecture Patterns

### Report Folder Structure to Replicate

```
report_french/
├── main.tex            # Translated preamble + \input calls (unchanged structure)
├── references.bib      # Translated title fields; other fields mostly unchanged
├── sections/
│   ├── 01-introduction.tex   # 189 lines — translate all body text
│   ├── 02-problem.tex        # 318 lines — translate all body text
│   ├── 03-solution.tex       # 363 lines — translate all body text
│   ├── 04-experiment.tex     # 266 lines — translate all body text
│   └── 05-conclusions.tex    # 143 lines — translate all body text
├── figures/            # COPY UNCHANGED — all pre-rendered PNGs
│   ├── pipeline.png
│   ├── architecture.png
│   ├── experiment-progression.png
│   ├── system_one_original.png
│   ├── system_one_ia_replicated.jpg
│   ├── system_one_graph_full.jpg
│   ├── system_one_graph_detail.jpg
│   ├── system_three.png
│   ├── system_three_ia_replicated.jpg
│   ├── system_three_graph_full.jpg
│   └── system_three_graph_detail.jpg
└── diagrams/           # COPY UNCHANGED — .mmd source files (no text in scope)
    ├── pipeline.mmd
    ├── architecture.mmd
    └── experiment-progression.mmd
```

**Key rule:** `figures/` and `diagrams/` directories contain only pre-rendered images and Mermaid diagram sources. There is NO TikZ or LaTeX-embedded diagram text to translate. Copy these directories verbatim.

### Pattern 1: Preamble French Localization

**What:** Add `\usepackage[french]{babel}` to `main.tex` preamble. This automatically:
- Translates "Table of Contents" → "Table des matières"
- Translates "References" → "Références"
- Applies French spacing (thin non-breaking space before `:`, `;`, `!`, `?`)
- Enables `\og` (ouvrez guillemet «) and `\fg` (fermez guillemet ») macros

**When to use:** Always — add immediately after `\usepackage[utf8]{inputenc}` in `main.tex`.

**Example:**
```latex
% Before (English)
\usepackage[utf8]{inputenc}
\usepackage{lmodern}

% After (French preamble)
\usepackage[utf8]{inputenc}
\usepackage[french]{babel}
\usepackage{lmodern}
```

Also update the `\date` field:
```latex
% English
\date{March 2026}

% French
\date{Mars 2026}
```

### Pattern 2: File-by-File Translation Scope

**What to translate (natural language text only):**
- Section headings (`\section{...}`, `\subsection{...}`, `\subsubsection{...}`)
- Body paragraphs and all prose
- Table column headers (`\textbf{Cost Item}` → `\textbf{Poste de coût}`)
- Figure captions (`\caption{...}`)
- Sub-figure labels (`\caption*{(a) Original engineering drawing}`)
- `\todo{...}` marker text (translate the placeholder description)
- Abstract text

**What NOT to translate:**
- LaTeX commands (`\begin`, `\end`, `\label`, `\ref`, `\cite`, `\input`)
- Cross-reference labels (`\label{sec:introduction}`, `\ref{fig:system1-graph}`)
- Technical acronyms used as proper names: BACnet, ASHRAE 223P, HVAC, AHU, BAS, BMS, VPP, TTL, RDF, OWL, SPARQL, Cypher, OpenADR, DTDL
- Software/tool proper names: SI-Mapper, Graphivac, Neo4j, TeX Live, Gemini, Claude
- Ontology proper names: Brick Schema, Project Haystack, RealEstateCore, BuildingMOTIF, BrickLLM, SkySpark, Willow, Open223
- Code strings, filenames, and BACnet point labels used as examples (e.g., `\texttt{2500.AI11}`, `\texttt{RTU-3/SA-T}`, `\texttt{AHU-1.SA-T}`)
- Company and institution names: NREL, LBNL, PNNL, NIST, DOE, ASHRAE, SMACNA, RMI, SEPA, EPRI
- Citation keys (`\cite{Wang2017}`)
- Numeric values, units, monetary amounts

### Pattern 3: Bibliography Translation Scope

**Translate in `references.bib`:**
- `title` field of each entry (English title → French equivalent)
- `note` field if it contains explanatory English prose

**Do NOT translate in `references.bib`:**
- `author` fields (proper names)
- `institution`, `journal`, `howpublished` values that are proper names
- `url` fields
- `year`, `month`, `volume`, `pages`, `doi`, `number` fields
- `key` identifiers (e.g., `@techreport{Trenbath2022,`)
- Annotation/comment lines (these can be translated optionally as comments)

### Anti-Patterns to Avoid

- **Translating LaTeX command names:** never write `\section` as something else; commands are language-independent.
- **Breaking cross-references:** `\label{sec:introduction}` and `\ref{sec:introduction}` must be identical strings in both files — do not translate label identifiers.
- **Changing `\cite` keys:** `\cite{Wang2017}` must match the `@article{Wang2017,` key in `references.bib` exactly.
- **Using polyglossia:** The preamble uses `pdflatex` + `T1` + `inputenc` — polyglossia requires XeLaTeX/LuaLaTeX. Do not switch engines.
- **Translating figure file paths:** `\includegraphics[width=\textwidth]{system_one_original.png}` paths must remain unchanged because `figures/` is copied verbatim.
- **Omitting the double pdflatex pass:** TOC and cross-references require two pdflatex passes to resolve correctly.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| French headings (Table des matières, etc.) | Manually override `\contentsname` | `\usepackage[french]{babel}` | babel handles all heading names automatically |
| French quotation marks | Type `«` and `»` as literal Unicode | `\og`, `\fg` macros from babel | Portable, correct spacing, works on all TeX backends |
| French date | Manually write "Mars 2026" everywhere | Update `\date{Mars 2026}` once in main.tex | Single source of truth |

**Key insight:** babel[french] eliminates nearly all typographic customization — do not implement manual overrides for things babel handles automatically.

## Common Pitfalls

### Pitfall 1: Breaking `\label`/`\ref` Pairs

**What goes wrong:** Translator renders `\label{sec:introduction}` as `\label{sec:introduction-fr}` or similar. Compilation produces `undefined references` warnings and `??` placeholders in the PDF.

**Why it happens:** Label strings look like translatable identifiers.

**How to avoid:** Treat every `\label{...}` and `\ref{...}` string as opaque — copy verbatim, never modify.

**Warning signs:** PDF contains `??` in place of section numbers or figure references.

### Pitfall 2: Breaking `\cite` / `.bib` Key Consistency

**What goes wrong:** `references.bib` entry key changed during translation (e.g., `Trenbath2022` → `Trenbath2022fr`). bibtex produces "undefined citation" warnings.

**Why it happens:** Entry keys look like they could be language-tagged.

**How to avoid:** Never modify the `@type{key,` identifier line of any bib entry.

**Warning signs:** `[?]` appears in citations in the PDF; bibtex log shows "Warning--I didn't find a database entry".

### Pitfall 3: `\todo{}` Markers Lost or Not Translated

**What goes wrong:** `\todo{}` placeholders in `04-experiment.tex` (15 occurrences) and `02-problem.tex` (1 occurrence) are deleted instead of translated.

**Why it happens:** They look like scaffolding to remove.

**How to avoid:** Translate the text inside `\todo{Fill after human trial}` → `\todo{À compléter après l'essai humain}`. The `\todo` command itself must be kept — it is defined in `main.tex` as `\newcommand{\todo}[1]{\textcolor{red}{\textbf{[TODO: #1]}}}`.

**Warning signs:** `\todo` command undefined error if the `\newcommand` is removed; missing red placeholder text in the French PDF.

### Pitfall 4: Encoding Issues with French Accented Characters

**What goes wrong:** French accented characters (é, è, à, ç, î, œ, etc.) typed directly into `.tex` files appear garbled in the PDF or produce compilation errors.

**Why it happens:** The preamble already has `\usepackage[utf8]{inputenc}` — UTF-8 direct input is fully supported. The risk is if files are accidentally saved in a different encoding.

**How to avoid:** Ensure all `.tex` files are saved as UTF-8. Type accented characters directly (é, à, etc.) — do not use legacy TeX escapes like `\'e` or `\`{a}`. The `T1` font encoding (`\usepackage[T1]{fontenc}`) ensures correct hyphenation of accented words.

**Warning signs:** Garbled characters in PDF; compilation error "Package inputenc Error: Invalid UTF-8 byte".

### Pitfall 5: Compilation Without Bibliography Pass

**What goes wrong:** Running only one `pdflatex` pass produces a PDF with `[?]` in all citation positions.

**Why it happens:** bibtex must be run between pdflatex passes to generate the `.bbl` file.

**How to avoid:** Use the four-command sequence: pdflatex → bibtex → pdflatex → pdflatex. The existing `report/main.bbl` is English — do not copy it to `report_french/`; regenerate it via bibtex on the French `.bib`.

**Warning signs:** All `\cite{}` references show as `[?]` in the output PDF.

### Pitfall 6: `report/` Modified Accidentally

**What goes wrong:** Files in `report/` are edited instead of their `report_french/` copies.

**Why it happens:** Both folders exist in the same parent; editor tab confusion.

**How to avoid:** Perform the copy first (`cp -r report/ report_french/`), then edit exclusively in `report_french/`. Verify with `git status` that no files under `report/` appear modified.

## Code Examples

### Preamble Change (main.tex)

```latex
% Source: babel package documentation, https://ctan.org/pkg/babel
% Add after \usepackage[utf8]{inputenc}:
\usepackage[french]{babel}

% Updated date line:
\date{Mars 2026}

% Updated title (example — translate the English title):
\title{SI-Mapper : Intelligence artificielle agentique pour la modélisation sémantique automatisée des systèmes CVC\\[0.5em]
\large Des données BACnet et des plans d'ingénierie aux ontologies ASHRAE 223P}

% Updated author line (keep name, update affiliation placeholder):
\author{Juan [Nom de famille] \\ \textit{[Affiliation]}}
```

### Section Heading Translation Examples

```latex
% English
\section{Introduction and Context}
\subsection{Building Ontologies: A Standardized Language for Buildings}

% French equivalents
\section{Introduction et contexte}
\subsection{Les ontologies de bâtiments : un langage standardisé pour les bâtiments}
```

### Table Column Header Translation Examples

```latex
% English (from 01-introduction.tex)
\textbf{Ontology} & \textbf{Governed By} & \textbf{Approach} & \textbf{Focus} & \textbf{Maturity}

% French equivalents
\textbf{Ontologie} & \textbf{Gouverné par} & \textbf{Approche} & \textbf{Domaine} & \textbf{Maturité}
```

### Figure Caption Translation Examples

```latex
% English
\caption{System 1 --- original HVAC schematic (left) and the agent's replication on the
Graphivac grid (right), produced as an intermediate step before ASHRAE 223P generation.}

% French
\caption{Système 1 --- schéma HVAC original (à gauche) et la réplication de l'agent sur
la grille Graphivac (à droite), produite en étape intermédiaire avant la génération ASHRAE 223P.}
```

### `\todo{}` Translation Example

```latex
% English
\todo{Fill after human trial}

% French
\todo{À compléter après l'essai humain}
```

### Abstract Translation (main.tex)

```latex
% The abstract block in main.tex must be translated:
\begin{abstract}
Ce rapport présente SI-Mapper, un système d'IA agentique qui automatise la création de
modèles sémantiques de bâtiments conformes à ASHRAE 223P à partir de plans d'ingénierie
CVC et de données de points BACnet. [... continue full translation ...]
\end{abstract}
```

### Folder Copy Command

```bash
cp -r /home/juan/codes/si-mapper/report /home/juan/codes/si-mapper/report_french
```

After copying, edit only files in `report_french/`. The `figures/` and `diagrams/` subdirectories require no changes.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `\usepackage[latin1]{inputenc}` + `\'e` escapes | `\usepackage[utf8]{inputenc}` + direct Unicode | ~2010 | Type accents directly; no escape sequences needed |
| polyglossia for French | babel[french] for pdflatex | Long-standing | polyglossia requires LuaLaTeX/XeLaTeX; babel works with pdflatex |
| Manual `\contentsname` override | `\usepackage[french]{babel}` | N/A | babel handles all localized heading strings automatically |

**Deprecated/outdated:**
- `\usepackage[latin1]{inputenc}`: obsolete; current preamble already uses utf8.
- TeX escape sequences for accents (`\'e`, `\`{a}`): redundant with utf8 inputenc; avoid.

## Open Questions

1. **Should `report.md` be translated?**
   - What we know: `report.md` exists in `report/` and contains an earlier informal narrative (not used in LaTeX compilation).
   - What's unclear: Whether it is in scope for this phase.
   - Recommendation: The phase description says "LaTeX source files (.tex)" and "references.bib". `report.md` is not referenced by `main.tex`. Treat it as out of scope unless explicitly requested.

2. **Should `.mmd` diagram source files be translated?**
   - What we know: The three `.mmd` files contain English labels (node names like "HVAC Drawing", "BACnet CSV", "ASHRAE 223P TTL"). These are Mermaid source files, not LaTeX source. The corresponding PNGs are already rendered and used in the document.
   - What's unclear: Whether re-rendering translated diagrams is required.
   - Recommendation: The phase description says "diagram/figure text that is in LaTeX source (TikZ, etc.)". Mermaid `.mmd` files are not LaTeX source. The PNGs are copied verbatim. Treat `.mmd` translation as out of scope unless the planner explicitly includes it as a task.

3. **Technical terminology conventions in French academic writing**
   - What we know: French academic papers in engineering frequently leave English technical acronyms (BACnet, HVAC, API, CSV, TTL, RDF) untranslated. Terms like "CVC" (Chauffage, Ventilation, Climatisation) is the French equivalent of HVAC, but "HVAC" is also widely used in French technical literature.
   - Recommendation: Use "CVC" in first reference with "(HVAC)" in parentheses; thereafter use "HVAC" or "CVC" consistently throughout the document.

## Validation Architecture

> workflow.nyquist_validation not set to false — section included.

This phase has no automated tests. The validation criterion is: the French PDF compiles with 0 error lines.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Docker pdflatex (not a unit test framework) |
| Config file | none — compilation is the test |
| Quick run command | `docker run --rm -v /home/juan/codes/si-mapper/report_french:/report -w /report texlive/texlive:latest pdflatex -interaction=nonstopmode main.tex 2>&1 \| grep "^!"` |
| Full suite command | 4-pass sequence: pdflatex → bibtex → pdflatex → pdflatex; check exit codes and grep for `^!` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TBD-01 | `report_french/` exists with correct structure | smoke | `ls report_french/sections/*.tex report_french/figures/ report_french/references.bib` | ❌ Wave 0 |
| TBD-02 | All .tex files compile to PDF with 0 errors | compile | `docker run ... pdflatex ... 2>&1 \| grep "^!" \| wc -l` → must be 0 | ❌ Wave 0 |
| TBD-03 | Bibliography compiles without undefined citations | compile | `docker run ... bibtex main 2>&1 \| grep "Warning"` → must be 0 undefined | ❌ Wave 0 |
| TBD-04 | No TikZ to translate | N/A — confirmed no TikZ | manual-only | N/A — confirmed |
| TBD-05 | Preamble unchanged except babel addition | manual | Review `report_french/main.tex` diff | ❌ Wave 0 |
| TBD-06 | `report/` unmodified | smoke | `git diff report/` → must be empty | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `docker run --rm -v /home/juan/codes/si-mapper/report_french:/report -w /report texlive/texlive:latest pdflatex -interaction=nonstopmode main.tex 2>&1 | grep "^!"` — must return 0 lines
- **Per wave merge:** Full 4-pass compilation sequence; open PDF visually to confirm French text renders
- **Phase gate:** Zero `!` error lines in final 4-pass compilation before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `report_french/` — entire directory created by copying `report/`
- [ ] `report_french/main.tex` — babel[french] added, abstract and title translated
- [ ] `report_french/sections/01-introduction.tex` through `05-conclusions.tex` — translated
- [ ] `report_french/references.bib` — titles translated

*(No existing test infrastructure; this phase has no Python/JS code — compilation is the sole verifiable artifact)*

## Sources

### Primary (HIGH confidence)

- Direct inspection of `report/main.tex` — preamble structure, packages used, section file list
- Direct inspection of all 5 section `.tex` files — confirmed no TikZ; confirmed `\todo{}` count
- Direct inspection of `report/references.bib` — confirmed entry structure, translatable fields
- `report/main.log` — confirmed pdflatex via TeX Live 2026, Docker compilation active
- Phase 14 SUMMARY/VERIFICATION files — confirmed Docker command pattern and bibtex requirement

### Secondary (MEDIUM confidence)

- CTAN babel package documentation (https://ctan.org/pkg/babel) — French option behavior, `\og`/`\fg` macros, automatic heading translation
- LaTeX Wikibook French chapter — utf8 + T1 + babel[french] as canonical pdflatex French setup

### Tertiary (LOW confidence)

- French technical writing conventions for HVAC/BACnet acronyms — based on general knowledge of French engineering literature conventions; validate against target audience expectations if needed

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — preamble already established in Phase 14; only babel addition needed; verified via existing `main.log`
- Architecture: HIGH — folder structure fully inventoried; no TikZ confirmed; translation scope clearly defined
- Pitfalls: HIGH — all pitfalls derived from direct inspection of actual source files (label patterns, bib keys, todo markers, encoding)

**Research date:** 2026-04-04
**Valid until:** 2026-05-04 (stable domain — LaTeX/babel conventions do not change rapidly)
