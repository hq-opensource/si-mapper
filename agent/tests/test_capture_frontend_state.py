import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import os

# Set env vars BEFORE importing the tool
os.environ.setdefault("GRAPHIVAC_BASE_URL", "https://graphivac.hvac.io/api/v1")
os.environ.setdefault("GRAPHIVAC_ORG_ID", "test-org")
os.environ.setdefault("GRAPHIVAC_PROJECT_ID", "test-project")
os.environ.setdefault("GRAPHIVAC_GRID_ID", "test-grid")

from tools.capture_frontend_state_tool import (
    CaptureFrontendStateTool,
    capture_frontend_state_tool,
)


def _make_playwright_context(page):
    """Build a properly nested async context manager chain for async_playwright()."""
    browser = MagicMock()
    browser.new_page = AsyncMock(return_value=page)
    browser.close = AsyncMock()

    p = MagicMock()
    p.chromium.launch = AsyncMock(return_value=browser)

    # async_playwright() is an async context manager
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=p)
    cm.__aexit__ = AsyncMock(return_value=False)

    return cm, p, browser


def test_get_declaration():
    """Tool declaration must expose name='capture_frontend_state'."""
    tool = CaptureFrontendStateTool()
    decl = tool._get_declaration()
    assert decl.name == "capture_frontend_state"


@pytest.mark.asyncio
async def test_run_async_success():
    """Success path: returns correct dict and calls save_artifact."""
    tool = CaptureFrontendStateTool()

    mock_tc = MagicMock()
    mock_tc.save_artifact = AsyncMock(return_value=1)

    page = MagicMock()
    page.goto = AsyncMock()
    page.screenshot = AsyncMock(return_value=b"fake_png_bytes")

    cm, p, browser = _make_playwright_context(page)

    with patch("playwright.async_api.async_playwright", return_value=cm):
        result = await tool.run_async(args={}, tool_context=mock_tc)

    assert result["status"] == "success"
    assert result["artifact"] == "verification/latest_snapshot.png"
    assert "Snapshot saved" in result["message"]
    assert mock_tc.save_artifact.called


@pytest.mark.asyncio
async def test_url_construction():
    """Verify page.goto is called with the correctly constructed URL."""
    tool = CaptureFrontendStateTool()

    mock_tc = MagicMock()
    mock_tc.save_artifact = AsyncMock(return_value=1)

    page = MagicMock()
    page.goto = AsyncMock()
    page.screenshot = AsyncMock(return_value=b"fake_png_bytes")

    cm, p, browser = _make_playwright_context(page)

    with patch("playwright.async_api.async_playwright", return_value=cm):
        await tool.run_async(args={}, tool_context=mock_tc)

    expected_url = (
        "https://graphivac.hvac.io/o/test-org/p/test-project/g/test-grid"
        "?iframe=t&init-zoom=t"
    )
    page.goto.assert_called_once_with(expected_url, wait_until="networkidle")


@pytest.mark.asyncio
async def test_run_async_error():
    """Error path: when Playwright raises, returns status='error' dict."""
    tool = CaptureFrontendStateTool()

    mock_tc = MagicMock()
    mock_tc.save_artifact = AsyncMock(return_value=1)

    # Make async_playwright raise immediately
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(side_effect=Exception("Browser crashed"))
    cm.__aexit__ = AsyncMock(return_value=False)

    with patch("playwright.async_api.async_playwright", return_value=cm):
        result = await tool.run_async(args={}, tool_context=mock_tc)

    assert result["status"] == "error"
    assert "Could not capture canvas snapshot" in result["message"]
    assert "Browser crashed" in result["message"]
