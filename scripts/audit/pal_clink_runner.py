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

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from scripts.audit.auditor_router import _CLINK_CONF_DIR, load_route_from_clink_config
from scripts.audit.route_schema import AuditRoute, FORBIDDEN_CLI_NAMES
from tools.auditor_router.pal_clink import normalize_pal_clink_audit_output


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


def run_audit_and_capture_verdict(
    route: AuditRoute,
    prompt: str,
    *,
    route_record: dict[str, Any],
    raw_output_path: Path,
    report_path: str,
    report_file_path: Path | None = None,
    timeout_seconds: float = 300.0,
    subprocess_run: _SubprocessRunFn = subprocess.run,
    which_fn: Callable[[str], Optional[str]] = shutil.which,
) -> dict[str, Any]:
    """Run a PAL clink audit, persist raw output, and normalize a verdict.

    ``PAL_CLINK_AUDIT_OUTPUT.json`` records the host-side runner result,
    including timing and process output. The clink verdict payload is parsed
    from stdout and normalized through the existing embedded-audit policy in
    ``tools.auditor_router``.
    """
    output = run_audit(
        route,
        prompt,
        timeout_seconds=timeout_seconds,
        subprocess_run=subprocess_run,
        which_fn=which_fn,
    )
    raw_output_path.parent.mkdir(parents=True, exist_ok=True)
    raw_output_path.write_text(
        json.dumps(_audit_output_as_dict(output), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    verdict_payload = _verdict_payload_from_output(output)
    embedded_audit = normalize_pal_clink_audit_output(
        verdict_payload,
        route=route_record,
        report_path=report_path,
    )
    if _payload_is_fixture_only(verdict_payload):
        embedded_audit = {
            **embedded_audit,
            "status": "NEEDS_SUPERVISOR",
            "exit_code": 1,
            "remaining_risks": [
                "Fixture-only audit is blocking; no live external PAL clink CLI was invoked."
            ],
        }

    report_file = report_file_path or Path(report_path)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(_render_audit_report(embedded_audit), encoding="utf-8")
    return embedded_audit


def run_audit_and_capture_payload(
    route: AuditRoute,
    prompt: str,
    *,
    raw_output_path: Path,
    pal_output_path: Path,
    timeout_seconds: float = 300.0,
    subprocess_run: _SubprocessRunFn = subprocess.run,
    which_fn: Callable[[str], Optional[str]] = shutil.which,
) -> dict[str, Any]:
    """Run a PAL clink audit and persist both runner and verdict payloads.

    ``raw_output_path`` contains the host-side runner envelope for diagnostics.
    ``pal_output_path`` contains the normalized ToolOutput/verdict payload shape
    consumed by ``run_embedded_audit.py --pal-output-json``.
    """
    output = run_audit(
        route,
        prompt,
        timeout_seconds=timeout_seconds,
        subprocess_run=subprocess_run,
        which_fn=which_fn,
    )
    raw_output_path.parent.mkdir(parents=True, exist_ok=True)
    raw_output_path.write_text(
        json.dumps(_audit_output_as_dict(output), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    verdict_payload = _verdict_payload_from_output(output)
    pal_output_path.parent.mkdir(parents=True, exist_ok=True)
    pal_output_path.write_text(
        json.dumps(verdict_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return verdict_payload


def route_from_auditor_record(route_record: dict[str, Any]) -> AuditRoute:
    """Resolve an ``AUDITOR_ROUTE.json`` PAL clink record to an executable route."""
    if route_record.get("tool") != "pal-mcp-clink":
        raise ValueError("AUDITOR_ROUTE.json did not select pal-mcp-clink")
    if not route_record.get("audit_safe_config_proven"):
        raise ValueError("PAL clink route is not audit-safe")
    cli_name = str(route_record.get("clink_client_name") or "")
    if not cli_name:
        raise ValueError("PAL clink route is missing clink_client_name")

    config_path = route_record.get("clink_config_path")
    candidate_paths = []
    if config_path:
        candidate_paths.append(Path(str(config_path)))
    candidate_paths.append(_CLINK_CONF_DIR / f"{cli_name}.json")
    for candidate in candidate_paths:
        if not candidate.exists():
            continue
        route = load_route_from_clink_config(candidate)
        if route.cli_name == cli_name:
            return route
    raise ValueError(f"No PAL clink config found for {cli_name!r}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a PAL clink audit and capture embedded-audit payloads."
    )
    parser.add_argument("--route-json", required=True, type=Path)
    parser.add_argument("--prompt", required=True, type=Path)
    parser.add_argument("--pal-output-json", required=True, type=Path)
    parser.add_argument("--raw-output-json", required=True, type=Path)
    parser.add_argument("--timeout-seconds", default=300.0, type=float)
    return parser


def run_cli(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    route_record = _read_json_object(args.route_json)
    prompt = args.prompt.read_text(encoding="utf-8")
    route = route_from_auditor_record(route_record)
    run_audit_and_capture_payload(
        route,
        prompt,
        raw_output_path=args.raw_output_json,
        pal_output_path=args.pal_output_json,
        timeout_seconds=args.timeout_seconds,
    )
    return 0


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _audit_output_as_dict(output: PalClinkAuditOutput) -> dict[str, Any]:
    return {
        "cli_name": output.cli_name,
        "exit_code": output.exit_code,
        "stdout": output.stdout,
        "stderr": output.stderr,
        "timed_out": output.timed_out,
        "error": output.error,
        "duration_seconds": output.duration_seconds,
    }


def _verdict_payload_from_output(output: PalClinkAuditOutput) -> dict[str, Any]:
    if output.timed_out or output.exit_code != 0 or output.error:
        return {
            "status": "error",
            "content": output.stdout,
            "risks": [output.error or output.stderr or "PAL clink exited non-zero."],
        }
    try:
        payload = json.loads(output.stdout)
    except json.JSONDecodeError:
        return {"status": "success", "content": output.stdout}
    if isinstance(payload, dict):
        return _unwrap_tool_output_payload(payload)
    return {"status": "success", "content": output.stdout}


def _unwrap_tool_output_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("status") != "success" or "verdict" in payload:
        return payload
    content = payload.get("content")
    if not isinstance(content, str):
        return payload
    try:
        content_payload = json.loads(content)
    except json.JSONDecodeError:
        return payload
    if isinstance(content_payload, dict):
        return content_payload
    return payload


def _payload_is_fixture_only(payload: dict[str, Any]) -> bool:
    values: list[str] = []
    for item in payload.get("risks") or []:
        values.append(str(item))
    content = payload.get("content")
    if isinstance(content, str):
        values.append(content)
    text = "\n".join(values).lower()
    return "fixture run only" in text or "fixture-only audit" in text


def _render_audit_report(embedded_audit: dict[str, Any]) -> str:
    findings = embedded_audit.get("findings") or []
    risks = embedded_audit.get("remaining_risks") or []
    lines = [
        "# PAL Clink Audit Report",
        "",
        f"PAL clink audit verdict: {embedded_audit['status']}",
        f"Auditor tool: {embedded_audit['auditor_tool']}",
        f"Auditor model: {embedded_audit['auditor_model']}",
        f"Exit code: {embedded_audit['exit_code']}",
        "",
        "## Findings",
    ]
    if findings:
        for finding in findings:
            lines.append(f"- {finding['severity']} {finding['id']}: {finding['title']}")
    else:
        lines.append("- None")
    lines.extend(["", "## Remaining Risks"])
    if risks:
        lines.extend(f"- {risk}" for risk in risks)
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def main() -> int:
    try:
        return run_cli()
    except Exception as exc:
        print(f"pal_clink_runner failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
