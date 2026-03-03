from __future__ import annotations

import subprocess
from typing import Optional


def run_gemini(prompt: str, input_text: str, command: Optional[str] = None) -> str:
    """
    Invoke Gemini CLI with a prompt and input text.
    
    Default command is 'gemini chat --system {prompt}' and passing input via stdin.
    """
    if command is None:
        # Correct command for Gemini CLI non-interactive mode
        cmd = ["gemini", "--prompt", prompt]
    else:
        cmd = command.split()

    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout, stderr = process.communicate(input=input_text)

    if process.returncode != 0:
        raise RuntimeError(f"Gemini CLI failed (exit {process.returncode}): {stderr}")

    return stdout.strip()
