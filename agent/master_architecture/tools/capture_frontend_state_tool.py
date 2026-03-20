from __future__ import annotations

import os
import logging
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
        # Build view URL from env vars
        base_url = os.getenv("GRAPHIVAC_BASE_URL", "")
        org_id = os.getenv("GRAPHIVAC_ORG_ID", "")
        project_id = os.getenv("GRAPHIVAC_PROJECT_ID", "")
        grid_id = os.getenv("GRAPHIVAC_GRID_ID", "")

        site_url = base_url.replace("/api/v1", "")
        view_url = f"{site_url}/o/{org_id}/p/{project_id}/g/{grid_id}?iframe=t&init-zoom=t"

        logger.debug(f"Capturing frontend state from: {view_url}")

        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(view_url, wait_until="networkidle")
                png_bytes = await page.screenshot(full_page=True)
                await browser.close()
        except Exception as e:
            return {"status": "error", "message": f"Could not capture canvas snapshot: {e}"}

        part = types.Part(inline_data=types.Blob(mime_type="image/png", data=png_bytes))
        await tool_context.save_artifact(filename="verification/latest_snapshot.png", artifact=part)

        return {
            "status": "success",
            "artifact": "verification/latest_snapshot.png",
            "message": "Snapshot saved. Call load_artifacts(artifact_names=['verification/latest_snapshot.png']) to inspect it.",
        }


capture_frontend_state_tool = CaptureFrontendStateTool()
