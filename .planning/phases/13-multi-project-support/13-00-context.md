The goal of this phase is to support multiple projects across all modules.

This will affect the following modules:
- `mapper` (the frontend): Ability to create, delete, modify, visualize multiple projects
- `generator` (the agentic backend): Ability to work with project context awareness

# Mapper
The ability to handle multiple projects requires at least the following:
- Having the ability to store a set of elements and a name for each project.  Elements to store are:
  - File system path to a project folder
  - Graphivac grid id
  - Name
  - AI model name
- Files and folders are organized in a project-specific way
- The project can be selected and displayed in the UI
- Graphivac embedded in the UI should be aware of the current project and display the correct grid
- The ability to create, delete, and modify projects.
- Creating a new project should create:
  - A new folder in the projects folder
  - A new grid in Graphivac, using its api
- Deleting a project should delete the corresponding folder and grid

Storage of a project's configurations could simply be a JSON file in the projects' folder.

# Generator
The ability to work with multiple projects requires at least the following:
- Ability to limit the scope of agents to only the current project's folder
- Only access the current project's Graphivac grid through the Graphivac api
- 