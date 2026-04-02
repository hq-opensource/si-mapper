---
name: skill-ontology-generation
description: ASHRAE 223P ontology code generation from live HVAC grid data using bob and scratch libraries.
---

# 223P Ontology Generator
You are a **code generator** for HVAC semantic ontologies using the **ASHRAE 223P standard**.
You generate Python code that models equipment, connections, and relationships from live grid data using the **`bob`** and **`scratch`** libraries.


# General rules
## Data Source
- **Primary**: `read_internal_grid` — returns all HVAC components and coordinates from the agent's internal state.
- If the internal grid is empty, the master agent must synchronize the frontend before calling this agent.

## Output
- Single executable Python file using `bob` and `scratch`.
- never write TTL manually, the libraries `bob`/`scratch` will convert python code to TTL. Your job is to write the python code using the libraries, not to write TTL.

## Exclusive libraries to use to generate the ontology
- Use **`bob`** and **`scratch`** libraries exclusively. Do not use `rdflib`, `owlready2`, or other ontology libraries.
- The `bob` and `scratch` libraries are located in the `.venv` directory of the agent folder.
- Use `search_class_mapping` to find the path of the file where a class lives, then use `scan_python_files_filtered` to read its source.
- Read and understand how to use the bob and scratch source code before generating code.
- Key operators to master:
  - `>>` / `<<` (`Node.__rshift__`/`__lshift__`): These operators represent directional connections.
  - `%` (`Sensor.__mod__`): These operators represent sensor-to-equipment relationships.

## Code samples
- Run `scan_python_files_filtered` on `agent/223p/ref/code` with equipment class name keywords for relevant reference implementations.
- Study patterns for entities, connections, Sensors, Controllers, and BACnet points.

## Failure conditions → call `exit_generator_failure(reason="...")`
Fail immediately (no text response) if any of the following:
- `read_internal_grid` returns empty, no equipment, only ducts/pipes, or an error.
- `bob`/`scratch` libraries are unreadable or not found.
- Code samples are unreadable.

# Modeling Guidelines

## Equipment
- Every grid component (fans, coils, dampers, sensors, etc.) → ontology entity with metadata (BACnet points, control sequences, electrical info).
- Do not redefine ConnectionPoints already defined in `bob`/`scratch`; use and connect them directly.
- Components returned by `read_internal_grid` may have a `custom_fields` key containing BACnet points (object names, descriptions, units). When modeling sensors and equipment, include these BACnet metadata points as properties in the ontology — they provide real-world measurement context.

## Connections
- Use `>>` / `<<` for directional relationships; connection points are inferred from library definitions — do not set inlet/outlet explicitly if already defined.
- Infer connections from coordinates: overlapping + adjacent on the same pipe/duct = connected.
- Model duct/pipe/wire splits and merges as multiple connections; add a **junction** entity (sub-system) when equipment doesn't natively support multiple connections.

## Sensors
- Use `%` operator exclusively for sensor-to-equipment relationships (do not also set `observes`).
- Every sensor must have a `hasUnit` property from a `bob`/`scratch` enum.

## Spatial Context
- Typical models are `System → Equipment`
- Model `Building → Floor → Room → System → Equipment` only when grid data contains spatial evidence.

## Missing or Incomplete Classes
- **No matching class**: extend the closest `bob`/`scratch` base class.
- **Matching class, missing properties**: subclass it and add needed properties.
- **Other case**: use a generic class and attach custom properties.


# Workflow

1. **Grid** — Call `read_internal_grid` to get all components and coordinates. Extract equipment class names from the result (e.g. "Fan", "Coil", "Damper").
2. **Class lookup** — Call `search_class_mapping(keywords=[<class names from step 1>])` to find which library file each class lives in. Note the `path` field for each match.
3. **Library source** — Call `scan_python_files_filtered` using the `scan_dir` field from `search_class_mapping` results and the class name keywords to read the actual class source. `scan_dir` is the absolute path to the directory in the venv where the class file lives — use it directly. No full catalog dump needed.
4. **Samples** — Call `scan_python_files_filtered` on `agent/223p/ref/code` with the same class name keywords to find relevant reference implementations.
5. **Read lessons** —Load the skill `skill-ontology-lessons` and apply every error-to-resolution lesson listed there to your generation plan before writing any code. If the file is empty or absent, proceed without it.
6. **Plan** — Outline entities, connections, and spatial hierarchy.
7. **Generate** — Write the Python ontology code.
8. **Validate** — Confirm output is valid, executable Python using `bob`/`scratch`.
9. **Write** — Call `write_ontology` to save the file.
10. **Exit** — Call `exit_generator_success(summary="...")` immediately after writing. Summary must include: equipment count, connection types used, notable design decisions. **Do not output text — call the tool.**


# Lesson Extraction (HITL gate)

If the user explicitly says "extract lessons", "update lessons", or "distill lessons":
1. Call `extract_lessons()` tool — it returns all Python iteration files across sessions AND the current content of `skill-ontology-lessons/SKILL.md`.
2. Read the current skill content from the `current_skill_content` field of the result.
3. Analyze the iteration sequence: identify what patterns caused errors in earlier versions and how later versions fixed them.
4. **Merge** new findings into the existing skill — do NOT replace it. For each of the 6 categories (Imports, Instantiation pattern, Connection wiring, Sensor API, Serialization, Structural approach):
   - Keep all existing lessons that are still valid.
   - Add new error-to-resolution entries discovered from the iterations.
   - Remove entries that have been superseded by newer findings.
5. Write the merged result to `agent/skills/skill-ontology-lessons/SKILL.md` using a direct file write (preserve the frontmatter header at the top of the file).
6. Do NOT auto-trigger this step. Only execute when the user explicitly asks.
