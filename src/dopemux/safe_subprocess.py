"""Safe subprocess execution utilities.

Provides hardened wrappers around subprocess.run / asyncio subprocess APIs:
- No shell execution
- Mandatory timeout
- Command allowlisting (optional)
- Structured logging of execution metadata (redacting secrets)
- Exception translation to SafeSubprocessError
"""
from __future__ import annotations

import subprocess
import shlex
import logging
from typing import List, Sequence, Optional, Dict, Any

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30

class SafeSubprocessError(Exception):
    def __init__(self, message: str, returncode: Optional[int] = None, stdout: str = "", stderr: str = ""):
        super().__init__(message)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

# Optional allowlist (empty == allow all)
ALLOWED_COMMANDS: List[str] = []

REDACT_TOKENS = ["API_KEY", "TOKEN", "SECRET", "PASSWORD"]

def _redact(arg: str) -> str:
    upper = arg.upper()
    if any(tok in upper for tok in REDACT_TOKENS):
        return "***REDACTED***"
    return arg

def run(cmd: Sequence[str] | str, *, timeout: int = DEFAULT_TIMEOUT, capture_output: bool = True, text: bool = True, check: bool = True, allowed: Optional[Sequence[str]] = None) -> subprocess.CompletedProcess:
    """Execute a command safely.

    Args:
        cmd: Command list or string. If string provided it is shlex split.
        timeout: Timeout in seconds (default 30)
        capture_output: Capture stdout/stderr (default True)
        text: Return text output (default True)
        check: Raise SafeSubprocessError on non-zero exit
        allowed: Optional override allowlist for this call
    """
    if isinstance(cmd, str):
        cmd_list = shlex.split(cmd)
    else:
        cmd_list = list(cmd)

    # Allowlist enforcement
    active_allow = list(allowed) if allowed is not None else ALLOWED_COMMANDS
    if active_allow and cmd_list and cmd_list[0] not in active_allow:
        raise SafeSubprocessError(f"Command '{cmd_list[0]}' not in allowlist", returncode=None)

    try:
        logger.debug("Executing command", extra={
            "cmd": [ _redact(a) for a in cmd_list ],
            "timeout": timeout
        })
        result = subprocess.run(cmd_list, timeout=timeout, capture_output=capture_output, text=text)
    except subprocess.TimeoutExpired as e:
        raise SafeSubprocessError(f"Command timed out: {cmd_list[0]}", returncode=None, stdout=e.stdout or "", stderr=e.stderr or "") from e
    except Exception as e:  # Narrowing can be done later
        raise SafeSubprocessError(f"Subprocess failure: {e}") from e

    if check and result.returncode != 0:
        raise SafeSubprocessError(
            f"Command failed ({result.returncode}): {cmd_list[0]}",
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    return result

async def arun(cmd: Sequence[str] | str, *, timeout: int = DEFAULT_TIMEOUT, capture_output: bool = True, text: bool = True, allowed: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """Async safe execution using asyncio subprocess.

    Returns dict with {returncode, stdout, stderr}.
    """
    import asyncio
    if isinstance(cmd, str):
        cmd_list = shlex.split(cmd)
    else:
        cmd_list = list(cmd)

    active_allow = list(allowed) if allowed is not None else ALLOWED_COMMANDS
    if active_allow and cmd_list and cmd_list[0] not in active_allow:
        raise SafeSubprocessError(f"Command '{cmd_list[0]}' not in allowlist", returncode=None)

    try:
        proc = await asyncio.create_subprocess_exec(*cmd_list, stdout=asyncio.subprocess.PIPE if capture_output else None, stderr=asyncio.subprocess.PIPE if capture_output else None)
        try:
            await asyncio.wait_for(proc.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            raise SafeSubprocessError(f"Command timed out: {cmd_list[0]}")
        stdout = (await proc.stdout.read()).decode() if capture_output and proc.stdout else ""
        stderr = (await proc.stderr.read()).decode() if capture_output and proc.stderr else ""
    except SafeSubprocessError:
        raise
    except Exception as e:
        raise SafeSubprocessError(f"Async subprocess failure: {e}") from e

    if proc.returncode != 0:
        raise SafeSubprocessError(
            f"Command failed ({proc.returncode}): {cmd_list[0]}",
            returncode=proc.returncode,
            stdout=stdout,
            stderr=stderr,
        )
    return {"returncode": proc.returncode, "stdout": stdout, "stderr": stderr}
