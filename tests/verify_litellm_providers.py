import os
import asyncio
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from dotenv import load_dotenv
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "agent"))
from utils.models import get_adk_model

# Load env vars from the agent directory
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "agent", ".env"))

def mock_tool(input_text: str) -> str:
    """A mock tool to verify tool-calling parity."""
    return f"Tool successfully called for: {input_text}"

async def run_test(model_name: str, provider: str):
    print(f"\n--- Testing Provider: {provider} ({model_name}) ---")
    
    model = get_adk_model(model_name)
    
    agent = Agent(
        name=f"test_agent_{provider.replace(' ', '_').replace('(', '').replace(')', '')}",
        model=model,
        instruction=f"You are a test agent for {provider}. Call the mock_tool with YOUR provider name (e.g. 'Anthropic'). Do not use emojis.",
        tools=[mock_tool]
    )
    
    session_service = InMemorySessionService()
    session_slug = provider.replace(' ', '_').replace('(', '').replace(')', '')
    await session_service.create_session(
        app_name="test_app",
        user_id="test_user",
        session_id=f"session_{session_slug}"
    )
    
    runner = Runner(
        agent=agent,
        app_name="test_app",
        session_service=session_service
    )
    
    content = types.Content(role='user', parts=[types.Part(text="Please call the tool.")])
    
    try:
        async for event in runner.run_async(
            user_id="test_user", 
            session_id=f"session_{session_slug}", 
            new_message=content
        ):
            if event.is_final_response():
                print(f"Final Response: {event.content.parts[0].text if event.content and event.content.parts else 'No parts'}")
                break
    except Exception as e:
        print(f"Error testing {provider}: {e}")

async def main():
    # Tests based on CONTEXT.md supported models
    tests = [
        ("gemini-3.1-pro-preview-customtools", "Google (Native)"),
        ("claude-sonnet-4-6", "Anthropic (LiteLLM)"),
        ("gpt-5.4-2026-03-05", "OpenAI (LiteLLM)")
    ]
    
    for model_name, provider in tests:
        await run_test(model_name, provider)

if __name__ == "__main__":
    asyncio.run(main())
