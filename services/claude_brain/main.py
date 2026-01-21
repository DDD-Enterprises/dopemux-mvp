# Helper methods
def _simplify_meta_prompt(prompt: str) -> str:
    """Simplify meta-prompt for high cognitive load."""
    # Remove complex sections, keep essential guidance
    lines = prompt.split('\n')
    simplified = []

    for line in lines:
        if any(keyword in line.lower() for keyword in ['essential', 'key', 'important', 'basic']):
            simplified.append(line)
        elif len(line.split()) < 20:  # Short, clear instructions
            simplified.append(line)

    return '\n'.join(simplified[:10])  # Limit length