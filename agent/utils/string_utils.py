import re

def format_agent_name(name: str) -> str:
    """
    Formats agent names for better readability.
    Example: 'PipeTemperatureSensorsAgent' -> 'Pipe Temperature Sensors Agent'
    Example: 'si_mapper_agent' -> 'si mapper agent'
    """
    if not name:
        return ""

    # 1. Replace underscores with spaces
    formatted = name.replace('_', ' ')

    # 2. Split PascalCase/camelCase (insert space before capital letters)
    formatted = re.sub(r'([a-z])([A-Z])', r'\1 \2', formatted)

    # 3. Handle cases where multiple capital letters are together (e.g. "HVACAgent" -> "HVAC Agent")
    formatted = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', formatted)

    return formatted
