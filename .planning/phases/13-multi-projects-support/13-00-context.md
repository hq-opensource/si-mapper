The goal of this phase is to support multiple projects and systems across all modules.

This will affect the following modules:
- `mapper` (the frontend): Ability to create, delete, modify, and visualize multiple projects and systems
- `generator` (the agentic backend): Ability to work scoped to a specific system within a project

---

# Core Concepts

## Project
A **project** represents a real-world building or facility.

In Graphivac terms, a project maps to a **Graphivac Project**.

A project contains one or more **systems**.

## System
A **system** represents a specific mechanical or HVAC system within a project (e.g. "Chilled Water Plant", "AHU Zone 1", "Exhaust Network").

In Graphivac terms, a system maps to a **Graphivac Grid**.

Each system has:
- Its own subfolder on disk for uploaded files (drawings, BACnet exports, etc.)
- Its own Graphivac grid
- Its own AI model configuration

The system is the primary unit of work: files belong to a system, the agent operates on a system, and Graphivac displays one system at a time.

## Graphivac Organisation
The Graphivac organisation is **fixed for an entire deployment** and will never change. It is configured exclusively as the `GRAPHIVAC_ORG_ID` environment variable and is **never persisted** in any project or system record on disk.

---

# Mapper
The ability to handle multiple projects and systems requires at least the following:

- Storing a **project record** with its name and the ID of its corresponding Graphivac Project.
- Storing one or more **system records** per project, each with its own Graphivac grid ID, file folder, and model name.
- The UI displaying **one system at a time**, with two selectors in the navbar:
  1. Active project selector
  2. Active system selector (scoped to the chosen project)
- Graphivac embedded in the UI reflects the **active system's grid**.
- The file manager shows only files belonging to the **active system's folder**.
- Creating a new project:
  - Creates a folder in `PROJECTS_FOLDER`.
  - Creates a new Graphivac Project via the Graphivac API.
- Creating a new system under a project:
  - Creates a subfolder inside the project folder.
  - Creates a new Graphivac Grid inside the project's Graphivac Project via the Graphivac API.
- Deleting a system removes its subfolder and Graphivac Grid.
- Deleting a project removes all its systems (folders + grids) and the Graphivac Project itself.

Storage of configuration is done via JSON files on disk: one `project.json` per project, one `system.json` per system.

---

# Generator
The agentic backend works within the scope of a single **active system** (which implies a single active project):

- File access is limited to the active system's folder on disk.
- Graphivac operations target the active system's Graphivac grid.
- The agent receives both the active project context (for project-level metadata) and the active system context (for grid ID, folder path, model) from the frontend via CopilotKit state.
- Future expansion to work across all systems in a project is deferred.
