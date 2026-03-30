"""Smoke-test that the FastAPI lifespan runs bootstrap_session correctly
without 'asyncio.run() cannot be called from a running event loop'."""
import asyncio
import sys
sys.path.insert(0, '.')

from utils.adk_patch import apply_adk_patches
apply_adk_patches()
from dotenv import load_dotenv
load_dotenv()


async def main():
    from api.app import create_app
    from api import lifecycle

    app = create_app()
    print(f"App created: {app.title}")

    # Simulate uvicorn triggering the lifespan startup
    async with app.router.lifespan_context(app):
        print(f"Lifespan startup OK")
        print(f"  session_id : {lifecycle.current_session_id}")
        print(f"  session_name: {lifecycle.current_session_name}")
        print(f"  adk_agent  : {lifecycle.holder.adk_agent is not None}")

    print("Lifespan shutdown OK")
    print("ALL CHECKS PASSED")


asyncio.run(main())

