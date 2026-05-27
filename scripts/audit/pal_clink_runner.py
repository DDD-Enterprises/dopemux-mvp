"""Host-side PAL clink audit runner.

Executes an audit by invoking the selected clink CLI (claude-audit or
gemini-audit) as a subprocess.  The audit prompt is delivered via stdin.
Captures stdout/stderr, timeout, and exit code.  No config creation —
reuses existing PAL clink configs loaded by auditor_router.

Codex is explicitly forbidden as a runner target (defense-in-depth; also
enforced at the AuditRoute dataclass layer via FORBIDDEN_CLI_NAMES).

Usage:
    from scripts.audit.auditor_router import default_routes, select_route
    from scripts.audit.pal_clink_runner import run_audit

    route = select_route(default_routes())
    if route is None:
        raise RuntimeError("No audit CLI available on this host")
    output = run_audit(route, prompt="Audit this diff: ...")
    if output.timed_out:
        print("Audit timed out")
    elif output.exit_code != 0:
        print("Audit exited non-zero:", output.stderr)
    else:
        print(output.stdout)
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Optional

from scripts.audit.route_schema import AuditRoute, FORBIDDEN_CLI_NAMES


@dataclass(frozen=True)
class PalClinkAuditOutput:
    """Normalized output from a single PAL clink audit invocation.

    Attributes:
        cli_name:         Logical name of the CLI that ran (e.g. "claude-audit").
        exit_code:        Process exit code, or None when timed_out is True or
                          when a pre-flight check prevents invocation.
        stdout:           Captured standard output (UTF-8, decode errors replaced).
        stderr:           Captured standard error (UTF-8, decode errors replaced).
        timed_out:        True when the process was killed after the timeout.
        error:            Human-readable error string for pre-flight failures or
                          timeout; None on clean invocation.
        duration_seconds: Wall-clock seconds elapsed from subprocess start to
                          completion or timeout; None when pre-flight failed.
    """

    cli_name: str
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool
    error: str | None
    duration_seconds: float | None


def build_invocation(route: AuditRoute) -> list[str]:
    """Return the argv list for a PAL clink audit invocation.

    The audit prompt is NOT included — it is delivered via stdin so that
    both claude and gemini CLIs receive it through the same channel.

    Args:
        route: The selected AuditRoute.

    Returns:
        Argv list: [command, *additional_args].
    """
    return [route.command, *route.additional_args]


# Type alias for the injectable subprocess runner.
_SubprocessRunFn = Callable[..., subprocess.CompletedProcess[bytes]]


def run_audit(
    route: AuditRoute,
    prompt: str,
    *,
    timeout_seconds: float = 300.0,
    subprocess_run: _SubprocessRunFn = subprocess.run,
    which_fn: Callable[[str], Optional[str]] = shutil.which,
) -> PalClinkAuditOutput:
    """Run a PAL clink audit and return normalized output.

    Performs a pre-flight capability check, then invokes the CLI with the
    audit prompt delivered via stdin.  A timeout returns output with
    ``timed_out=True`` rather than raising, so callers can log and decide.

    Env merge semantics: ``{**os.environ, **route.env}`` — route.env values
    override matching keys from os.environ.  If a key in route.env shadows a
    system variable (e.g. PATH), the shadow takes effect for the subprocess.

    Args:
        route:            Selected AuditRoute (must not be a codex variant).
        prompt:           Audit prompt delivered to the CLI via stdin.
        timeout_seconds:  Seconds before the subprocess is killed.
        subprocess_run:   Injectable subprocess.run for testing.
        which_fn:         Injectable shutil.which for capability probe.

    Returns:
        PalClinkAuditOutput with all fields populated.

    Raises:
        ValueError: If route names a forbidden CLI (codex defense-in-depth).
    """
    # Defense-in-depth: AuditRoute.__post_init__ already rejects forbidden
    # cli_names, but guard both cli_name and command here in case of
    # serialization or duck-type bypass (e.g. cli_name="safe", command="codex").
    if route.cli_name in FORBIDDEN_CLI_NAMES or route.command in {"codex", "codex-audit"}:
        raise ValueError(
            f"Forbidden CLI in runner: cli_name={route.cli_name!r} command={route.command!r}"
        )

    # Pre-flight capability check.
    if which_fn(route.command) is None:
        return PalClinkAuditOutput(
            cli_name=route.cli_name,
            exit_code=None,
            stdout="",
            stderr="",
            timed_out=False,
            error=f"command {route.command!r} not found on PATH",
            duration_seconds=None,
        )

    argv = build_invocation(route)
    env = {**os.environ, **route.env}
    input_bytes = prompt.encode("utf-8")

    start = time.perf_counter()
    try:
        result = subprocess_run(
            argv,
            input=input_bytes,
            capture_output=True,
            timeout=timeout_seconds,
            env=env,
        )
        duration = time.perf_counter() - start
        return PalClinkAuditOutput(
            cli_name=route.cli_name,
            exit_code=result.returncode,
            stdout=result.stdout.decode("utf-8", errors="replace"),
            stderr=result.stderr.decode("utf-8", errors="replace"),
            timed_out=False,
            error=None,
            duration_seconds=duration,
        )
    except subprocess.TimeoutExpired:
        duration = time.perf_counter() - start
        return PalClinkAuditOutput(
            cli_name=route.cli_name,
            exit_code=None,
            stdout="",
            stderr="",
            timed_out=True,
            error=f"timed out after {timeout_seconds}s",
            duration_seconds=duration,
        )
