import os
import sys
import logging
import contextlib
from collections.abc import AsyncIterator

import uvicorn
from fastmcp import FastMCP
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp_server.graphivac.custom_manager import CustomManager #noqa
from mcp_server.graphivac.duct_manager import DuctManager #noqa
from mcp_server.graphivac.pipe_manager import PipeManager #noqa
from mcp_server.graphivac.grid_manager import GridManager #noqa
from mcp_server.graphivac.electric_manager import ElectricManager #noqa
from mcp_server.graphivac.metadata_manager import MetadataManager #noqa
from mcp_server.graphivac import custom_tools, duct_tools, pipe_tools, grid_tools, electric_tools, metadata_tools #noqa

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# --- 1. INITIALIZATION & CONFIGURATION ---

# Load localized project config
env_path = os.path.join(os.path.dirname(__file__), 'mcp.env')
load_dotenv(env_path)

# Load root-level secrets (fallback)
load_dotenv()

# Create the MCP Server (FastMCP wrapper)
mcp = FastMCP("Graphivac HVAC Agent")

# Load Environment Variables and Instantiate Managers
ORG_ID = os.getenv("GRAPHIVAC_ORG_ID")
PROJECT_ID = os.getenv("GRAPHIVAC_PROJECT_ID")
GRID_ID = os.getenv("GRAPHIVAC_GRID_ID")
GRID_TITLE = os.getenv("GRAPHIVAC_GRID_TITLE")
BASE_URL = os.getenv("GRAPHIVAC_BASE_URL")
FONT_CONFIGS={"family": "Serif", "style": "Oblique", "size": 20, "weight": "Lighter", "color": "string"}

if not all([ORG_ID, PROJECT_ID, GRID_ID]):
    raise ValueError("Missing required environment variables: GRAPHIVAC_ORG_ID, GRAPHIVAC_PROJECT_ID, or GRAPHIVAC_GRID_ID")

# Initialize managers
duct_manager = DuctManager(ORG_ID, PROJECT_ID, GRID_ID, GRID_TITLE, FONT_CONFIGS, BASE_URL)
pipe_manager = PipeManager(ORG_ID, PROJECT_ID, GRID_ID, GRID_TITLE, FONT_CONFIGS, BASE_URL)
custom_manager = CustomManager(ORG_ID, PROJECT_ID, GRID_ID, GRID_TITLE, FONT_CONFIGS, BASE_URL)
grid_manager = GridManager(ORG_ID, PROJECT_ID, GRID_ID, GRID_TITLE, FONT_CONFIGS, BASE_URL)
electric_manager = ElectricManager(ORG_ID, PROJECT_ID, GRID_ID, GRID_TITLE, FONT_CONFIGS, BASE_URL)
metadata_manager = MetadataManager(ORG_ID, PROJECT_ID, GRID_ID, GRID_TITLE, FONT_CONFIGS, BASE_URL)

# --- 2. REGISTER TOOLS ---
duct_tools.register_duct_tools(mcp, duct_manager)
pipe_tools.register_pipe_tools(mcp, pipe_manager)
custom_tools.register_custom_tools(mcp, custom_manager)
grid_tools.register_grid_tools(mcp, grid_manager)
electric_tools.register_electric_tools(mcp, electric_manager)
metadata_tools.register_metadata_tools(mcp, metadata_manager)

# --- 3. STREAMABLE HTTP TRANSPORT ---

# Extract the underlying low-level Server from FastMCP
# FastMCP._mcp_server provides the mcp.server.lowlevel.Server instance
server_instance = mcp._mcp_server

session_manager = StreamableHTTPSessionManager(
    app=server_instance,
    event_store=None,
    stateless=True, # As per tutorial for simple scaling
)

async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
    await session_manager.handle_request(scope, receive, send)

@contextlib.asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    """Context manager for session manager."""
    async with session_manager.run():
        logger.info("Application started with StreamableHTTP session manager!")
        try:
            yield
        finally:
            logger.info("Application shutting down...")

# Create the Starlette Application with Streamable HTTP
app = Starlette(
    debug=True,
    routes=[
        Mount("/mcp", app=handle_streamable_http),
    ],
    # Add CORS middleware to allow requests from the direct method on the mcp inspector
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ],
    lifespan=lifespan,
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)