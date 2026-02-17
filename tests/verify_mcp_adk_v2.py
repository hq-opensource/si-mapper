import asyncio
import json
import os
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Correct imports from google.adk
from google.adk.tools.mcp_tool.mcp_session_manager import streamablehttp_client, StreamableHTTPConnectionParams

async def verify_mcp():
    url = "http://localhost:8080/mcp/"
    print(f"Connecting to MCP server via Streamable HTTP at {url}...")
    
    try:
        from mcp import ClientSession
        
        async with streamablehttp_client(
            url=url,
            timeout=30.0
        ) as (read, write, get_id):
            print("Successfully connected to streams. Initializing ClientSession...")
            async with ClientSession(read, write) as session:
                 await session.initialize()
                 print("Session initialized. Calling 'read_grid'...")
                 result = await session.call_tool("read_grid", arguments={})
            
            print("\n--- Tool Result ---")
            # Result objects in mcp-python-sdk have a content list
            output = {
                "content": [{"type": "text", "text": c.text} for c in result.content if hasattr(c, 'text')],
                "isError": result.isError
            }
            print(json.dumps(output, indent=2))
            
            # Print any structured content if available (FastMCP specialty)
            # In the low-level SDK Result, this might be in extra attributes
            # but let's just see what's in the object
            print(f"\nRaw Result: {result}")

    except Exception as e:
        print(f"Error: {e}")
        if hasattr(e, 'exceptions'):
            for sub_e in e.exceptions:
                print(f"  Sub-error: {sub_e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_mcp())
