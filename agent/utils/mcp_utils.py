from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from utils.logging_config import configure_logging

logger = configure_logging()

def create_mcp_toolset(url: str) -> McpToolset:
    """Initializes the MCP Toolset."""
    logger.info(f"Initializing MCP Toolset with URL: {url}")
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=url,
            timeout=30.0
        )
    )
