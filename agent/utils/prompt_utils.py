import os
from utils.logging_config import configure_logging

PROMPT_FILENAME = "prompt.md"
logger = configure_logging()

def load_prompt_instruction(filename: str = PROMPT_FILENAME) -> str:
    """Loads the agent instruction prompt from a markdown file."""
    try:
        # Assuming the prompt file is in the agent directory (parent of utils)
        # The original code used: current_dir = os.path.dirname(os.path.abspath(__file__))
        # which was agent/agent.py. So current_dir was agent/.
        # Now __file__ is agent/utils/prompt_utils.py. So current_dir is agent/utils.
        # We need to go up one level to find prompt.md if it stays in agent/.
        
        # Let's check where prompt.md is. It is in agent/prompt.md based on file list.
        # So from agent/utils/prompt_utils.py, we need to go to ../prompt.md
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        agent_dir = os.path.dirname(current_dir) # Go up to agent/
        prompt_path = os.path.join(agent_dir, filename)
        
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {prompt_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading prompt: {e}")
        raise
