# Phase 13 — Multi-Project Support

**Updated:** 2026-03-27

---

## Goal

Support multiple projects and systems across all modules:
- **`mapper`** (frontend): create, delete, modify, and visualize multiple projects and systems.
- **`agent`** (agentic backend): operate scoped to a specific system within a project.

---

## Core Concepts

### Project
Represents a real-world building or facility. Maps to a **Graphivac Project**. Contains one or more systems.

### System
Represents a specific mechanical/HVAC system (e.g. "Chilled Water Plant", "AHU Zone 1"). Maps to a **Graphivac Grid**. Owns its file subfolder, its grid, and its AI model config. The system is the primary unit of work.

### Graphivac Organisation
Fixed per deployment. Configured via `GRAPHIVAC_ORG_ID` env var only — never persisted in project/system records.

---

## Step Summary

| Step  | Title                              | Status        |
|-------|------------------------------------|---------------|
| 13-01 | Externalize Frontend Configs       | ✅ Done        |
| 13-02 | Deployable Frontend (Docker)       | ✅ Done        |
| 13-03 | Deployable Agent (Docker)          | ✅ Done        |
| 13-04 | Project & System Data Model        | ✅ Done        |
| 13-05 | Project & System Management API    | ✅ Done        |
| 13-06 | Graphivac API Integration          | ✅ Done        |
| 13-07 | Project Selector & Scoped UI       | ✅ Done        |
| 13-08 | Project Management UI              | ✅ Done        |
| 13-09 | Agent System Context Awareness     | 🔲 Not started |
| 13-10 | Runtime Model Switching            | 🔲 Not started |
| 13-11 | Session Persistence                | 🔲 Not started |
| 13-12 | Self-Hosted Graphivac              | 🔲 Not started |
| 13-99 | MCP Server System Context          | 🔲 Not started |

---

## What Is Done

- All frontend environment-specific values are externalized via Next.js env vars.
- The frontend and agent each ship as a production Docker image in `docker-compose.yml` under the `deploy` profile.
- `Project` and `System` schemas are defined in TypeScript; records are stored as `project.json` / `system.json` under `PROJECTS_FOLDER` on disk.
- Full CRUD REST API for projects and systems (create, list, get, delete), wired to Graphivac project/grid lifecycle.
- A `WorkspaceContext` provides `activeProject` and `activeSystem` across the frontend via React context + CopilotKit state.
- Navbar selectors (project + system) and a scoped file manager (uploads filtered to the active system folder) are live.
- A Project Management UI (modal/drawer) lets users create, rename, and delete projects and systems from the UI.

## What Remains

- **13-09**: Agent reads `activeProject`/`activeSystem` from CopilotKit state; all file access and Graphivac calls use the system's folder and grid ID.
- **13-10**: Per-system AI model selection is applied at runtime when the agent processes a request.
- **13-11**: CopilotKit conversation state is auto-saved per system and restored on next visit.
- **13-12**: Graphivac can be self-hosted; `docker-compose.yml`, agent, and MCP server all point to the self-hosted instance.
- **13-99**: MCP server reads the active system's grid ID from env/context so its tools always target the correct Graphivac grid.
