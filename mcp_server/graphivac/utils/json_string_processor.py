import re


def extract_json_from_markdown(markdown_text: str) -> str | None:
    """
    Finds and extracts a JSON string from a Markdown code block.

    Args:
        markdown_text: A string potentially containing a JSON code block
                       (e.g., ```json...```).

    Returns:
        The cleaned JSON string if a code block is found, otherwise None.
    """
    # Regex to find a JSON code block, ignoring case and allowing for newlines
    # It captures the content between the fences.
    pattern = r"```\s*json\s*\n(.*?)\n```"
    
    match = re.search(pattern, markdown_text, re.DOTALL | re.IGNORECASE)
    
    if match:
        # The actual JSON content is in the first capturing group
        json_string = match.group(1).strip()
        return json_string
        
    return None

def string_to_dict(text: str) -> dict:
    """
    Converts a multi-line key-value string into a dictionary.

    Args:
        text: A string with key-value pairs on new lines 
              (e.g., "key1 value1\nkey2 value2").

    Returns:
        A dictionary created from the key-value pairs.
    """
    result_dict = {}
    for line in text.strip().split('\n'):
        if line:
            key, value = line.split(' ', 1)
            result_dict[key] = value
    return result_dict