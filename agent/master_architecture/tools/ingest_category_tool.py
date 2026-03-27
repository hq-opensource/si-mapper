from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Any, List, Dict
from typing_extensions import override

from google.adk.tools import BaseTool, ToolContext
from google.genai import types

# Import content loaders.
# We assume the code is run from the project root or 'agent' module is in path.
from utils import content_loaders

logger = logging.getLogger(__name__)

class IngestCategoryFilesTool(BaseTool):
    """
    A tool that scans a specific category folder in 'mapper/uploads',
    loads all supported files (PDF, CSV, Images), and saves them as artifacts
    into the current ADK session.
    """

    def __init__(self):
        super().__init__(
            name='ingest_category_files',
            description="""Reads all files (CSV, PDF, Images like PNG/JPG, Text) from a specific category folder and saves them as artifacts to the session.
            
            Use this tool to Make information about a topic (like 'hvac', 'bacnet', 'control', etc.) available to the agent.
            After calling this, you must use `load_artifacts` to actually inspect the content of the files.""",
        )

    def _get_declaration(self) -> types.FunctionDeclaration | None:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'category': types.Schema(
                        type=types.Type.STRING,
                        description="The category of information to ingest (e.g., 'hvac', 'bacnet', 'control', 'electricity')."
                    ),
                },
                required=['category']
            ),
        )

    @override
    async def run_async(
        self, *, args: dict[str, Any], tool_context: ToolContext
    ) -> dict[str, Any]:
        category = args.get('category')
        if not category:
            return {'error': 'Category is required.'}

        # Resolve uploads dir — scoped by project + system when both are in state (13-09)
        projects_root = os.getenv("PROJECTS_FOLDER", "")
        active_project = tool_context.state.get("active_project") or {}
        active_system  = tool_context.state.get("active_system") or {}
        proj_folder = active_project.get("folder_path", "")
        sys_folder  = active_system.get("folder_path", "")

        if projects_root and proj_folder and sys_folder:
            uploads_dir = Path(projects_root) / proj_folder / sys_folder
        else:
            # Legacy fallback: repo_root/mapper/uploads
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent.parent
            uploads_dir = project_root / 'mapper' / 'uploads'
        # Try to find the category directory, handling case insensitivity
        found_category_dir = None
        actual_category_name = category

        # 1. Check for exact match first
        if (uploads_dir / category).exists() and (uploads_dir / category).is_dir():
            found_category_dir = uploads_dir / category
        else:
            # 2. Case-insensitive lookup
            if uploads_dir.exists():
                for method in uploads_dir.iterdir():
                    if method.is_dir() and method.name.lower() == category.lower():
                        found_category_dir = method
                        actual_category_name = method.name
                        break
        
        if not found_category_dir:
             # List available categories to be helpful
            available = [p.name for p in uploads_dir.iterdir() if p.is_dir()] if uploads_dir.exists() else []
            return {
                'error': f"Category folder '{category}' not found in {uploads_dir}.",
                'available_categories': available
            }
            
        category_dir = found_category_dir
        # Update category to match filesystem name for consistent artifact naming
        category = actual_category_name

        saved_artifacts = []
        errors = []

        logger.debug(f"Ingesting files from {category_dir}")

        for file_path in category_dir.iterdir():
            if not file_path.is_file():
                continue
            
            # Skip hidden files
            if file_path.name.startswith('.'):
                continue

            try:
                part = None
                # Determine loader based on extension (simple dispatch)
                # We could expose a generic 'load_file' in content_loaders, but we'll map here for now.
                suffix = file_path.suffix.lower()
                
                if suffix == '.csv':
                    part = content_loaders.load_csv_part(str(file_path))
                elif suffix == '.pdf':
                    part = content_loaders.load_pdf_part(str(file_path))
                elif suffix in ['.jpg', '.jpeg', '.png']:
                    part = content_loaders.load_image_part(str(file_path))
                elif suffix == '.txt':
                     # Simple text loader if needed, or use generic
                     with open(file_path, 'r', encoding='utf-8') as f:
                         part = types.Part.from_text(text=f.read())
                else:
                    logger.warning(f"Skipping unsupported file type: {file_path.name}")
                    continue

                if part:
                    # Construct a meaningful artifact name: "category/filename"
                    artifact_name = f"{category}/{file_path.name}"
                    
                    # Save into the session persistence
                    version = await tool_context.save_artifact(
                        filename=artifact_name,
                        artifact=part
                    )
                    saved_artifacts.append(artifact_name)
                    mime = part.inline_data.mime_type if part.inline_data else "unknown"
                    logger.debug(f"Saved artifact: {artifact_name} (v{version}) [Mime: {mime}]")

            except Exception as e:
                msg = f"Failed to ingest {file_path.name}: {str(e)}"
                logger.error(msg)
                errors.append(msg)

        result = {
            'status': 'success',
            'saved_artifacts': saved_artifacts,
            'message': f"Successfully saved {len(saved_artifacts)} artifacts from category '{category}'. Call `load_artifacts` with these names to view their content."
        }
        
        if errors:
            result['errors'] = errors
            
        return result

ingest_category_files_tool = IngestCategoryFilesTool()
