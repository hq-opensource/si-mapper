import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

"""Main entrypoint for the SI-MAPPER Agent Service.

Boot sequence (order matters):
  1. apply_adk_patches()  — must run before any ag_ui_adk / google-genai import
  2. load_dotenv()        — must run before api.lifecycle reads os.getenv() at
                            module scope
  3. from api import create_app  — triggers the full import chain
"""

import os

# 1. Patches first — before any ADK import
from utils.adk_patch import apply_adk_patches
apply_adk_patches()

# 2. Load .env before anything reads env vars
from dotenv import load_dotenv
load_dotenv()

# 3. Now safe to import the api package
from utils.logging_config import configure_logging
from api import create_app

logger = configure_logging()

# ---------------------------------------------------------------------------
# Application instance (consumed by uvicorn / gunicorn via module reference)
# ---------------------------------------------------------------------------
app = create_app()


if __name__ == "__main__":
    import uvicorn

    if not os.getenv("GOOGLE_API_KEY"):
        logger.warning("GOOGLE_API_KEY environment variable not set!")

    port = int(os.getenv("PORT", 8001))
    logger.info(f"Starting Master Agent on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)