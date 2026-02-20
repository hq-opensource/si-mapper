import os
from utils.logging_config import configure_logging

PROMPT_FILENAME = "prompt.md"
logger = configure_logging()

def load_prompt_instruction(filename: str = PROMPT_FILENAME) -> str:
    """Loads the agent instruction prompt from a markdown file."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        agent_dir = os.path.dirname(current_dir) # Go up to agent/
        
        # If filename is already an absolute path, use it directly
        if os.path.isabs(filename):
            prompt_path = filename
        else:
            prompt_path = os.path.join(agent_dir, filename)
        
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {prompt_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading prompt: {e}")
        raise

def load_composed_prompt(main_prompt_path: str, skill_paths: list[str]) -> str:
    """
    Loads a main prompt and appends a 'Skills & Knowledge Base' section containing 
    the content of provided skill files.
    """
    main_prompt = load_prompt_instruction(main_prompt_path)
    
    if not skill_paths:
        return main_prompt
        
    skills_content = "\n\n## " + ("-" * 60) + "\n"
    skills_content += "## SKILLS & KNOWLEDGE BASE REFERENCE\n"
    skills_content += "Use the following technical specifications to interpret technical files.\n"
    
    for path in skill_paths:
        skill_text = load_prompt_instruction(path)
        
        # Strip potential YAML frontmatter (--- ... ---)
        import re
        skill_text = re.sub(r'^---.*?---\s*', '', skill_text, flags=re.DOTALL)
        
        skills_content += f"\n### SECTION: {os.path.basename(os.path.dirname(path)).upper()}\n"
        skills_content += f"{skill_text.strip()}\n"
        
    return main_prompt + skills_content
