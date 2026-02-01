"""Prompt sanitizer for secure input handling."""

import re

def sanitize_bug_description(description: str) -> str:
    """Sanitize bug description for safe use in prompts."""
    # Remove dangerous characters and patterns
    dangerous_patterns = [
        r'<script.*?>.*?</script>',  # Script tags
        r'on\w+.*?=.*?["\']',  # Event handlers
        r'javascript:',  # JavaScript URLs
        r'vbscript:',  # VBScript URLs
        r'<!--.*-->',  # HTML comments
        r'/\*.*?\*/',  # CSS/JS comments
    ]

    sanitized = description
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

    # Limit length
    if len(sanitized) > 1000:
        sanitized = sanitized[:1000] + " [truncated]"

    # Remove excessive whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()

    return sanitized

def sanitize_file_path(file_path: str) -> str:
    """Sanitize file path for safe use."""
    # Remove directory traversal
    sanitized = re.sub(r'\.\./', '', file_path)
    sanitized = re.sub(r'\\', '/', sanitized)  # Normalize separators
    sanitized = re.sub(r'/+', '/', sanitized)  # Normalize separators

    # Remove dangerous characters
    dangerous_chars = ['..', '/', '\\', '|']
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '_')

    return sanitized