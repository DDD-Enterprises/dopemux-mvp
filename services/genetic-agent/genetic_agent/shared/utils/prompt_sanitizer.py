"""Prompt sanitization utilities to prevent injection attacks."""

import re
from typing import List, Set


class PromptSanitizer:
    """Sanitizes user input to prevent LLM prompt injection attacks."""

    # Dangerous patterns that could override instructions
    DANGEROUS_PATTERNS = [
        # System prompt override attempts
        r'(?i)(system\s+prompt|system\s+message|system\s+instructions?)\s*[:=]\s*',
        r'(?i)(ignore\s+(all\s+)?previous\s+instructions?|override\s+instructions?)',
        r'(?i)(you\s+are\s+now|act\s+as|pretend\s+to\s+be|role-play\s+as)',

        # Code execution attempts
        r'(?i)(execute\s+code|run\s+command|shell\s+command)\s*[:=]\s*',
        r'(?i)(eval|exec|system|subprocess|os\.system|os\.popen)',

        # File system access
        r'(?i)(read\s+file|write\s+file|delete\s+file|access\s+file)\s*[:=]\s*',
        r'(?i)(open\s*\(|file\s*\(|pathlib|os\.path)',

        # Network access
        r'(?i)(http|https|ftp|ssh|telnet|netcat)\s*[:=]\s*',
        r'(?i)(requests|urllib|socket|urllib)',

        # Dangerous separators that might break prompt structure
        r'(?i)(end\s+of\s+input|end\s+of\s+prompt|end\s+of\s+message)',
        r'(?i)(new\s+conversation|reset\s+conversation|clear\s+context)',
    ]

    # Safe character whitelist
    SAFE_CHARS = re.compile(r'[^a-zA-Z0-9\s\.,!?\-\'\"():;]')

    @classmethod
    def sanitize_input(cls, text: str, max_length: int = 1000) -> str:
        """Sanitize user input to prevent prompt injection.

        Args:
            text: The input text to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized text safe for LLM prompts
        """
        if not text:
            return ""

        # Truncate to maximum length
        text = text[:max_length]

        # Remove dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            text = re.sub(pattern, "[FILTERED]", text, flags=re.IGNORECASE)

        # Remove potentially dangerous characters while preserving readability
        text = cls.SAFE_CHARS.sub('', text)

        # Normalize whitespace
        text = ' '.join(text.split())

        # Ensure text doesn't start or end with potentially dangerous content
        text = text.strip()
        if text.startswith(('http', 'ftp', 'file:', 'data:')):
            text = "[FILTERED_URL]"

        return text

    @classmethod
    def sanitize_bug_description(cls, description: str) -> str:
        """Sanitize bug descriptions specifically."""
        if not description:
            return "No description provided"

        # Sanitize the basic input
        sanitized = cls.sanitize_input(description, max_length=500)

        # Additional checks for bug descriptions
        if len(sanitized) < 10:
            sanitized = f"Brief issue: {sanitized}"

        # Remove any remaining potentially problematic words
        dangerous_words = [
            'system', 'admin', 'root', 'password', 'secret', 'key',
            'token', 'credential', 'auth', 'login', 'sudo', 'chmod'
        ]

        words = sanitized.split()
        filtered_words = []
        for word in words:
            if word.lower() not in dangerous_words:
                filtered_words.append(word)
            else:
                filtered_words.append("[FILTERED]")

        return ' '.join(filtered_words)

    @classmethod
    def sanitize_file_path(cls, file_path: str) -> str:
        """Sanitize file paths to prevent directory traversal."""
        if not file_path:
            return ""

        # Remove dangerous path components
        sanitized = re.sub(r'\.\./|\.\./|~|\$HOME|\$USER|\$PWD', '', file_path)

        # Only allow safe characters for file paths
        safe_path_chars = re.compile(r'[^a-zA-Z0-9_/\-\.]')
        sanitized = safe_path_chars.sub('', sanitized)

        # Limit path depth and length
        parts = sanitized.split('/')
        if len(parts) > 5:  # Limit directory depth
            parts = parts[-5:]
        sanitized = '/'.join(parts)

        # Ensure it doesn't start with dangerous prefixes
        if sanitized.startswith(('/', '../', './', '~/')):
            sanitized = sanitized.lstrip('/').lstrip('../').lstrip('./').lstrip('~/')

        return sanitized[:200]  # Limit total length

    @classmethod
    def create_safe_prompt(cls, template: str, **kwargs) -> str:
        """Create a safe prompt by sanitizing all inputs.

        Args:
            template: Prompt template with {variable} placeholders
            **kwargs: Variables to substitute

        Returns:
            Safe prompt with sanitized inputs
        """
        # Sanitize all input variables
        sanitized_kwargs = {}
        for key, value in kwargs.items():
            if key in ['bug_description', 'description']:
                sanitized_kwargs[key] = cls.sanitize_bug_description(str(value))
            elif key in ['file_path', 'filepath']:
                sanitized_kwargs[key] = cls.sanitize_file_path(str(value))
            else:
                sanitized_kwargs[key] = cls.sanitize_input(str(value))

        # Format the template
        try:
            return template.format(**sanitized_kwargs)
        except (KeyError, ValueError) as e:
            # If formatting fails, return a safe fallback
            return f"Error formatting prompt: {str(e)}. Using safe fallback."

    @classmethod
    def validate_prompt_output(cls, prompt: str) -> bool:
        """Validate that a generated prompt is safe.

        Args:
            prompt: The prompt to validate

        Returns:
            True if safe, False if potentially dangerous
        """
        if not prompt:
            return False

        # Check for dangerous patterns in the final prompt
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, prompt, re.IGNORECASE):
                return False

        # Check prompt length
        if len(prompt) > 4000:  # Reasonable maximum
            return False

        return True