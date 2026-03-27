from __future__ import annotations

import asyncio
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from typing_extensions import override

from google.adk.tools import BaseTool, ToolContext
from google.genai import types

logger = logging.getLogger(__name__)


class CaptureFrontendStateTool(BaseTool):
    """
    A tool that launches headless Chromium via Playwright, navigates to the
    Graphivac view-only URL, takes a PNG screenshot, saves it as a session
    artifact, and returns a status dict.

    NOTE: Run `playwright install chromium` once after installing dependencies.
    """

    def __init__(self):
        super().__init__(
            name='capture_frontend_state',
            description=(
                "Takes a screenshot of the live Graphivac canvas and saves it as a session artifact. "
                "After calling this, use load_artifacts(artifact_names=[\"verification/latest_snapshot.png\"]) "
                "to inspect the image."
            ),
        )

    def _get_declaration(self) -> types.FunctionDeclaration | None:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
            ),
        )

    @override
    async def run_async(
        self, *, args: dict[str, Any], tool_context: ToolContext
    ) -> dict[str, Any]:
        # Build view URL — state-first for project_id and grid_id (13-09)
        base_url = os.getenv("GRAPHIVAC_BASE_URL", "")
        org_id   = os.getenv("GRAPHIVAC_ORG_ID", "")
        active_project = tool_context.state.get("active_project") or {}
        active_system  = tool_context.state.get("active_system") or {}
        project_id = active_project.get("graphivac_project_id") or os.getenv("GRAPHIVAC_PROJECT_ID", "")
        grid_id    = active_system.get("graphivac_grid_id")     or os.getenv("GRAPHIVAC_GRID_ID", "")

        site_url = base_url.replace("/api/v1", "")
        view_url = f"{site_url}/o/{org_id}/p/{project_id}/g/{grid_id}?iframe=t&init-zoom=t"

        logger.debug(f"Capturing frontend state from: {view_url}")

        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()
                await page.goto(view_url, wait_until="load")
                await asyncio.sleep(3)
                png_bytes = await page.screenshot(full_page=True)
                await browser.close()
        except Exception as e:
            return {"status": "error", "message": f"Could not capture canvas snapshot: {e}"}

        # Save to project+system-scoped snapshots dir; fall back to mapper/uploads/snapshots/
        projects_root = os.getenv("PROJECTS_FOLDER", "")
        proj_folder   = active_project.get("folder_path", "")
        sys_folder    = active_system.get("folder_path", "")
        if projects_root and proj_folder and sys_folder:
            snapshots_dir = Path(projects_root) / proj_folder / sys_folder / "snapshots"
        else:
            snapshots_dir = Path(__file__).resolve().parents[3] / "mapper" / "uploads" / "snapshots"
        snapshots_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_filename = f"snapshot_{timestamp}.png"
        snapshot_path = snapshots_dir / snapshot_filename
        snapshot_path.write_bytes(png_bytes)
        (snapshots_dir / "latest_snapshot.png").write_bytes(png_bytes)
        logger.debug(f"Snapshot saved to: {snapshot_path}")

        part = types.Part(inline_data=types.Blob(mime_type="image/png", data=png_bytes))
        await tool_context.save_artifact(filename="verification/latest_snapshot.png", artifact=part)

        return {
            "status": "success",
            "artifact": "verification/latest_snapshot.png",
            "local_path": str(snapshot_path),
            "message": f"Snapshot saved to {snapshot_path}. Call load_artifacts(artifact_names=['verification/latest_snapshot.png']) to inspect it.",
        }


capture_frontend_state_tool = CaptureFrontendStateTool()
