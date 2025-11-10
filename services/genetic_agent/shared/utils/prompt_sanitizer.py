"""Prompt sanitizer for secure input handling."""

import re
import unicodedata
from typing import Set

# Comprehensive dangerous patterns for LLM prompts
DANGEROUS_PATTERNS = [
    # Script injection
    r'<script[^>]*>.*?</script>',  # Script tags with attributes
    r'javascript:[^\'"\s]*',  # JavaScript URLs
    r'vbscript:[^\'"\s]*',  # VBScript URLs
    r'on\w+\s*=\s*["\'][^"\']*["\']',  # Event handlers
    r'on\w+\s*=\s*[^\s>]+',  # Event handlers without quotes

    # Template injection patterns
    r'\{\{.*?\}\}',  # Template literals
    r'\$\{.*?\}',  # JavaScript template strings
    r'<%.*?%>',  # ERB/JSP templates
    r'<#.*?#>',  # FreeMarker templates

    # Code injection
    r'eval\s*\([^)]*\)',  # eval() calls
    r'exec\s*\([^)]*\)',  # exec() calls
    r'import\s+\w+',  # Import statements
    r'from\s+\w+',  # From imports

    # File system access
    r'\.\./',  # Directory traversal
    r'~\/',  # Home directory
    r'/etc/passwd',  # Common file paths
    r'C:\\',  # Windows paths

    # HTML/XML injection
    r'<!\[CDATA\[.*?\]\]>',  # CDATA sections
    r'<!--.*?-->',  # HTML comments
    r'</?[^>]+>',  # All HTML/XML tags

    # SQL injection patterns
    r';\s*(select|insert|update|delete|drop)',  # SQL statements
    r'union\s+select',  # SQL union attacks

    # Command injection
    r';\s*(ls|cat|rm|cp|mv)',  # Shell commands
    r'\|\s*(grep|awk|sed)',  # Pipe commands

    # Unicode normalization attacks
    r'\u200B',  # Zero-width space
    r'\u200C',  # Zero-width non-joiner
    r'\u200D',  # Zero-width joiner
    r'\uFEFF',  # Zero-width no-break space
]

# Characters to completely remove
DANGEROUS_CHARS: Set[str] = {
    '\x00',  # Null byte
    '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07',  # Control chars
    '\x08', '\x0B', '\x0C', '\x0E', '\x0F',  # More control chars
    '\x10', '\x11', '\x12', '\x13', '\x14', '\x15', '\x16', '\x17',
    '\x18', '\x19', '\x1A', '\x1B', '\x1C', '\x1D', '\x1E', '\x1F',
    '\x7F',  # DEL character
}

def sanitize_bug_description(description: str) -> str:
    """Sanitize bug description for safe use in prompts with comprehensive protection."""
    if not description:
        return ""

    sanitized = str(description)  # Ensure string type

    # Apply unicode normalization to detect hidden characters
    try:
        sanitized = unicodedata.normalize('NFKC', sanitized)
    except (TypeError, ValueError):
        pass  # Skip normalization if it fails

    # Remove dangerous characters
    sanitized = ''.join(c for c in sanitized if c not in DANGEROUS_CHARS)

    # Remove dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        try:
            sanitized = re.sub(pattern, '[FILTERED]', sanitized, flags=re.IGNORECASE | re.DOTALL)
        except re.error:
            # Skip invalid regex patterns
            continue

    # Additional security checks
    sanitized = _remove_suspicious_keywords(sanitized)
    sanitized = _validate_length_and_content(sanitized)

    return sanitized

def _remove_suspicious_keywords(text: str) -> str:
    """Remove or replace suspicious keywords that could be used for attacks."""
    suspicious_keywords = [
        'system', 'exec', 'eval', 'import', 'open', 'file', 'read', 'write',
        'delete', 'remove', 'rm', 'cp', 'mv', 'chmod', 'chown', 'sudo',
        'password', 'secret', 'key', 'token', 'auth', 'credential',
        '__import__', '__builtins__', 'globals', 'locals', 'vars',
        'getattr', 'setattr', 'hasattr', 'delattr'
    ]

    # Replace suspicious keywords with safe alternatives
    for keyword in suspicious_keywords:
        text = re.sub(rf'\b{re.escape(keyword)}\b', f'[{keyword.upper()}]', text, flags=re.IGNORECASE)

    return text

def _validate_length_and_content(text: str) -> str:
    """Validate and limit content length and structure."""
    # Limit total length
    max_length = 1000
    if len(text) > max_length:
        text = text[:max_length] + " [TRUNCATED_DUE_TO_LENGTH]"

    # Ensure minimum content (not just filtered tags)
    if len(re.sub(r'\[FILTERED\]|\[.*?\]', '', text).strip()) < 10:
        return "[CONTENT_FILTERED]"

    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Remove leading/trailing brackets from over-filtering
    text = re.sub(r'^\s*\[FILTERED\]\s*', '', text)
    text = re.sub(r'\s*\[FILTERED\]\s*$', '', text)

    return text

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


class PromptSanitizer:
    """Class wrapper for prompt sanitization functions."""

    @staticmethod
    def sanitize_bug_description(description: str) -> str:
        """Sanitize bug description."""
        return sanitize_bug_description(description)

    @staticmethod
    def sanitize_file_path(file_path: str) -> str:
        """Sanitize file path."""
        return sanitize_file_path(file_path)