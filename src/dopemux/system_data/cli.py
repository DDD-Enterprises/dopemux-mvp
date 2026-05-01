"""Click command implementation for `dopemux system-data`."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from .executor import execute_plan, restore_manifest
from .models import ToolReport, stable_json, to_plain
from .planner import build_plan
from .proof import write_proof
from .reporters import plan_data, render_plan, render_scan, render_tool_report, scan_data, tool_report_data
from .scanner import scan
from .tools import INSTALL_COMMAND, ToolError, ToolRunner
from .tui import run_tui


PROOF_PATH = Path("proof/TP-OPS-MAC-SCRUBBER-001/PROOF.json")


def _home(path: str | None) -> Path:
    return Path(path).expanduser() if path else Path.home()


def _proof_dir(path: Path = PROOF_PATH, *, create: bool = True) -> Path:
    if create:
        path.parent.mkdir(parents=True, exist_ok=True)
    return path.parent


def _json_or_render(json_output: bool, data: dict, render) -> None:
    if json_output:
        click.echo(stable_json(data), nl=False)
    else:
        render()


def _missing_exit(report: ToolReport) -> None:
    if report.ok:
        return
    render_tool_report(report)
    raise click.ClickException(
        f"missing required tools: {', '.join(report.missing)}. Install with: {INSTALL_COMMAND}"
    )


@click.group("system-data")
def system_data() -> None:
    """Mac system-data diagnosis, cleanup planning, TUI, and proof."""


@system_data.command("doctor")
@click.option("--json", "json_output", is_flag=True)
@click.option("--home", "home_path", default=None, help="Override home root for tests/sandbox scans.")
def doctor(json_output: bool, home_path: str | None) -> None:
    runner = ToolRunner()
    report = runner.check_required_tools()
    data = {"tool_report": tool_report_data(report), "install_command": INSTALL_COMMAND}
    _json_or_render(json_output, data, lambda: render_tool_report(report))
    if not report.ok:
        sys.exit(1)
    # Build environment only after toolchain is valid.
    result = scan(_home(home_path), runner)
    if not json_output:
        render_scan(result)


@system_data.command("scan")
@click.option("--json", "json_output", is_flag=True)
@click.option("--home", "home_path", default=None, help="Override home root for tests/sandbox scans.")
def scan_cmd(json_output: bool, home_path: str | None) -> None:
    try:
        result = scan(_home(home_path))
    except ToolError as exc:
        raise click.ClickException(str(exc)) from exc
    _json_or_render(json_output, scan_data(result), lambda: render_scan(result))


@system_data.command("report")
@click.option("--json", "json_output", is_flag=True)
@click.option("--home", "home_path", default=None, help="Override home root for tests/sandbox scans.")
def report(json_output: bool, home_path: str | None) -> None:
    try:
        result = scan(_home(home_path))
    except ToolError as exc:
        raise click.ClickException(str(exc)) from exc
    _json_or_render(json_output, scan_data(result), lambda: render_scan(result))


@system_data.command("plan")
@click.option("--json", "json_output", is_flag=True)
@click.option("--dry-run", is_flag=True, default=True, help="Kept for CLI symmetry; plan never mutates.")
@click.option("--target", "targets", multiple=True, help="Finding id or category to include.")
@click.option("--quarantine-dir", type=click.Path(path_type=Path), default=None)
@click.option("--home", "home_path", default=None, help="Override home root for tests/sandbox scans.")
def plan_cmd(json_output: bool, dry_run: bool, targets: tuple[str, ...], quarantine_dir: Path | None, home_path: str | None) -> None:
    try:
        result = scan(_home(home_path))
    except ToolError as exc:
        raise click.ClickException(str(exc)) from exc
    plan_result = build_plan(result, quarantine_dir=quarantine_dir, targets=targets)
    _json_or_render(json_output, plan_data(plan_result), lambda: render_plan(plan_result))


@system_data.command("clean")
@click.option("--json", "json_output", is_flag=True)
@click.option("--dry-run/--execute", default=True, show_default=True)
@click.option("--yes", is_flag=True, help="Required with --execute for non-interactive mutation.")
@click.option("--target", "targets", multiple=True, help="Finding id or category to include.")
@click.option("--quarantine-dir", type=click.Path(path_type=Path), default=None)
@click.option("--home", "home_path", default=None, help="Override home root for tests/sandbox scans.")
def clean(json_output: bool, dry_run: bool, yes: bool, targets: tuple[str, ...], quarantine_dir: Path | None, home_path: str | None) -> None:
    if not dry_run and not yes:
        raise click.ClickException("--execute requires --yes. No hidden mutation.")
    try:
        result = scan(_home(home_path))
    except ToolError as exc:
        raise click.ClickException(str(exc)) from exc
    plan_result = build_plan(result, quarantine_dir=quarantine_dir, targets=targets)
    records = execute_plan(
        plan_result.actions,
        dry_run=dry_run,
        yes=yes,
        proof_dir=_proof_dir(create=not dry_run),
        quarantine_dir=quarantine_dir,
    )
    data = {"dry_run": dry_run, "records": to_plain(records)}
    _json_or_render(json_output, data, lambda: click.echo(stable_json(data)))


@system_data.command("restore")
@click.option("--json", "json_output", is_flag=True)
@click.option("--list", "list_only", is_flag=True, default=False)
@click.option("--manifest", type=click.Path(path_type=Path), default=None)
@click.option("--execute", is_flag=True, default=False)
def restore(json_output: bool, list_only: bool, manifest: Path | None, execute: bool) -> None:
    proof_dir = _proof_dir(create=False)
    manifests = sorted(proof_dir.glob("*-manifest.json")) if proof_dir.exists() else []
    if list_only or manifest is None:
        data = {"manifests": [str(path) for path in manifests]}
        _json_or_render(json_output, data, lambda: click.echo(stable_json(data)))
        return
    record = restore_manifest(manifest, dry_run=not execute)
    data = {"record": to_plain(record)}
    _json_or_render(json_output, data, lambda: click.echo(stable_json(data)))


@system_data.command("tui")
@click.option("--home", "home_path", default=None, help="Override home root for tests/sandbox scans.")
@click.option("--quarantine-dir", type=click.Path(path_type=Path), default=None)
def tui(home_path: str | None, quarantine_dir: Path | None) -> None:
    try:
        result = scan(_home(home_path))
    except ToolError as exc:
        raise click.ClickException(str(exc)) from exc
    plan_result = build_plan(result, quarantine_dir=quarantine_dir)
    run_tui(result, plan_result)


@system_data.command("proof")
@click.option("--json", "json_output", is_flag=True)
def proof(json_output: bool) -> None:
    runner = ToolRunner()
    report = runner.check_required_tools()
    bundle = write_proof(
        PROOF_PATH,
        repo_root=Path.cwd(),
        tool_report=report,
        implementation={
            "features_delivered": [
                "system-data command group",
                "required external tool preflight",
                "external-tool-backed scanner",
                "planner/executor/proof pipeline",
                "Textual TUI shell",
            ]
        },
        tests={"commands": [], "results": [], "coverage_notes": ["generated before validation"]},
        runtime_validation={"tool_preflight": tool_report_data(report)},
        docs={
            "files": [
                "docs/03-reference/features/mac-system-data-scrubber.md",
                "docs/02-how-to/operations/mac-system-data-scrubber-operator-guide.md",
                "docs/03-reference/features/mac-system-data-scrubber-safety-model.md",
            ],
            "status": "drafted",
        },
        acceptance={"criteria": [], "pass_fail": {}, "unresolved": []},
        unresolved=[] if report.ok else [f"missing required tools: {', '.join(report.missing)}"],
    )
    data = to_plain(bundle)
    _json_or_render(json_output, data, lambda: click.echo(f"Proof written: {PROOF_PATH}"))
