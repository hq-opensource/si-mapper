from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from utils.logging_config import configure_logging

logger = configure_logging()

def create_mcp_toolset(url: str) -> McpToolset:
    """Initializes the MCP Toolset."""
    logger.info(f"Initializing MCP Toolset with URL: {url}")
    toolset = McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=url,
            timeout=30.0
        )
    )
    # ag_ui_adk calls model_copy(deep=True) on the entire agent tree for each
    # background execution. McpToolset holds live network streams that cannot be
    # deep-copied. Since it's a stateful connection manager, returning `self`
    # is the correct behaviour — the same connection pool should be reused.
    toolset.__deepcopy__ = lambda memo: toolset  # type: ignore[assignment]
    return toolset
