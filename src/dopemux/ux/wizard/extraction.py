"""Stage 7: Phase-by-phase extraction via the canonical v5 runner."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from rich.panel import Panel

from dopemux.console import console

from ..questionary_support import MissingInteractiveDependencyError, require_questionary
from .display import render_educational_panel, render_stage_header
from .stages import PHASE_INFO, PHASES, StageResult, StageStatus, WizardState


def _wizard_pythonpath(repo_root: Path) -> str:
    src_root = repo_root / "src"
    existing = os.environ.get("PYTHONPATH", "").strip()
    if existing:
        return os.pathsep.join([str(src_root), existing])
    return str(src_root)


def _runner_path(repo_root: Path) -> Path:
    return repo_root / "services" / "repo-truth-extractor" / "run_extraction_v5.py"


def _promptset_root(repo_root: Path) -> Path:
    return repo_root / "extraction" / "promptset"


def _build_wizard_phase_command(state: WizardState, phase_key: str) -> list[str]:
    cmd = [
        sys.executable,
        str(_runner_path(state.repo_root)),
        "--phase",
        phase_key,
        "--run-id",
        state.run_id,
        "--partition-workers",
        str(state.workers),
        "--routing-policy",
        state.selected_policy,
        "--promptset-root",
        str(_promptset_root(state.repo_root)),
        "--ui",
        "rich",
        "--resume",
    ]
    if state.max_cost is not None:
        cmd.extend(["--max-cost-usd", str(state.max_cost)])
    if not state.validate_live:
        cmd.append("--skip-pre-live-validator")
        console.print(
            "[yellow]Pre-live validator is disabled for this run; the runner will skip the validator-first gate.[/yellow]"
        )
    if state.skip_hygiene:
        console.print(
            "[yellow]Wizard skip-hygiene does not map to the canonical v5 runner and will not be forwarded.[/yellow]"
        )
    if state.prescan_dir:
        cmd.extend(["--prescan-dir", state.prescan_dir, "--skip-prescan"])
    cmd.append("--execute")
    return cmd


def run_extraction(state: WizardState) -> StageResult:
    """Stage 7 — Walk through extraction phases with interactive confirmation.

    In preview mode (default), shows what would run without executing.
    With --execute, delegates each phase to the canonical v5 runner.
    """
    if not state.execute_mode:
        console.print(
            Panel(
                "[yellow]Preview mode — no extraction will run.\n"
                "Use [bold]--execute[/bold] to enable actual extraction.[/yellow]",
                border_style="yellow",
            )
        )

        # Show what would run
        console.print("\n[bold]Phases that would execute:[/bold]\n")
        for phase_key in PHASES:
            info = PHASE_INFO[phase_key]
            console.print(f"  {info['icon']}  [bold]{phase_key}[/bold] — {info['name']}")
            console.print(f"      [dim]{info['desc']}[/dim]")

        console.print(
            f"\n  [dim]Policy: {state.selected_policy}  •  "
            f"Workers: {state.workers}  •  Run ID: {state.run_id}[/dim]\n"
        )

        return StageResult(
            status=StageStatus.SKIPPED,
            message="Preview mode — run with --execute to extract",
        )

    # ── Execute mode ────────────────────────────────────────────────────
    if state.educate_mode:
        render_educational_panel(
            "Phase-by-phase extraction",
            "Each phase will be executed via the canonical 'run_extraction_v5.py' runner.\n"
            "You can Run, Skip, or Abort at each phase.\n\n"
            "This keeps routing-policy, promptset-root, resume state, cost cap,\n"
            "and validator enforcement aligned with the runtime authority.\n\n"
            "Completed phases write artifacts to:\n"
            f"  extraction/repo-truth-extractor/v5/runs/{state.run_id}/",
        )

    try:
        questionary = require_questionary()
    except MissingInteractiveDependencyError as exc:
        console.print(f"[red]{exc}[/red]")
        return StageResult(status=StageStatus.FAILED, message=str(exc))

    style = questionary.Style(
        [
            ("selected", "fg:ansiblue bold"),
            ("pointer", "fg:ansicyan"),
        ]
    )

    completed_count = 0
    skipped_count = 0

    for phase_key in PHASES:
        info = PHASE_INFO[phase_key]
        console.print()
        console.rule(
            f"[bold bright_cyan]  Phase {phase_key}  •  {info['icon']}  {info['name']}  [/bold bright_cyan]"
        )
        console.print(f"\n  [dim]{info['desc']}[/dim]\n")

        action = questionary.select(
            f"Run phase {phase_key} ({info['name']})?",
            choices=["Run", "Skip", "Abort wizard"],
            default="Run",
            use_indicator=True,
            style=style,
        ).ask()

        if action is None or action == "Abort wizard":
            console.print("\n[yellow]Wizard aborted by user.[/yellow]")
            break

        if action == "Skip":
            state.phase_results[phase_key] = StageResult(
                status=StageStatus.SKIPPED, message="User skipped"
            )
            skipped_count += 1
            continue

        cmd = _build_wizard_phase_command(state, phase_key)

        console.print(f"\n  [bold cyan]Executing:[/bold cyan] {' '.join(cmd)}\n")

        try:
            proc_env = dict(os.environ)
            proc_env["PYTHONPATH"] = _wizard_pythonpath(state.repo_root)
            for env_var, value in state.provider_key_overrides.items():
                if str(value).strip():
                    proc_env[env_var] = str(value).strip()
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=str(state.repo_root),
                env=proc_env,
            )
            for line in proc.stdout:
                print(line, end="", flush=True)
            proc.wait()

            if proc.returncode == 0:
                state.phase_results[phase_key] = StageResult(
                    status=StageStatus.COMPLETED, message="Phase completed successfully"
                )
                completed_count += 1
                console.print(f"\n  [green]✓  Phase {phase_key} complete[/green]")
            else:
                state.phase_results[phase_key] = StageResult(
                    status=StageStatus.FAILED,
                    message=f"Exit code {proc.returncode}",
                )
                console.print(
                    f"\n  [red]✗  Phase {phase_key} failed (exit {proc.returncode})[/red]"
                )
                # Ask whether to continue
                cont = questionary.confirm(
                    "Continue with remaining phases?", default=True
                ).ask()
                if not cont:
                    break

        except (OSError, subprocess.SubprocessError) as exc:
            state.phase_results[phase_key] = StageResult(
                status=StageStatus.FAILED, message=str(exc)
            )
            console.print(f"\n  [red]✗  Phase {phase_key} error: {exc}[/red]")

    msg_parts = []
    if completed_count:
        msg_parts.append(f"{completed_count} completed")
    if skipped_count:
        msg_parts.append(f"{skipped_count} skipped")
    failed_count = sum(1 for r in state.phase_results.values() if r.status == StageStatus.FAILED)
    if failed_count:
        msg_parts.append(f"{failed_count} failed")

    return StageResult(
        status=StageStatus.COMPLETED if not failed_count else StageStatus.FAILED,
        message=", ".join(msg_parts) or "No phases executed",
    )
