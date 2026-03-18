"""Stage 3: Prompt system setup — check or initialise the extraction promptset."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import questionary

from dopemux.console import console

from .display import render_educational_panel, render_health_check
from .stages import StageResult, StageStatus, WizardState


def run_prompt_setup(state: WizardState) -> StageResult:
    """Stage 3 — Validate or create the extraction promptset."""
    promptset_dir = state.repo_root / "extraction" / "promptset"
    checks: list[tuple[str, bool, str]] = []

    # Check for promptset directory
    if promptset_dir.is_dir():
        prompt_files = list(promptset_dir.glob("*.yaml")) + list(promptset_dir.glob("*.yml"))
        prompt_files += list(promptset_dir.glob("*.json"))
        checks.append(("Promptset directory", True, str(promptset_dir.relative_to(state.repo_root))))
        checks.append(("Prompt files found", len(prompt_files) > 0, f"{len(prompt_files)} file(s)"))

        # Check for key files
        for key_file in ("FEATURE_MAP.yaml", "SCOPE_OVERRIDES.yaml", "PROJECT_FINGERPRINT.json"):
            key_path = promptset_dir / key_file
            checks.append((key_file, key_path.exists(), "present" if key_path.exists() else "missing"))

        render_health_check(checks)

        all_present = all(passed for _, passed, _ in checks)
        if all_present:
            state.promptset_ready = True
            console.print("\n  [success]✓  Promptset is ready for extraction[/success]\n")
            return StageResult(
                status=StageStatus.COMPLETED,
                message="Promptset validated",
                data={"files": len(prompt_files)},
            )
        else:
            console.print("\n  [warning]⚠  Some promptset files are missing[/warning]\n")
    else:
        checks.append(("Promptset directory", False, "not found"))
        render_health_check(checks)
        console.print("\n  [warning]No promptset found — needed for extraction[/warning]\n")

    # Educational panel
    if state.educate_mode:
        render_educational_panel(
            "What is a promptset?",
            "The promptset contains customised instructions for the extraction pipeline.\n"
            "It maps your repository's features, defines scope overrides, and creates a\n"
            "project fingerprint so the LLMs know exactly what to extract.\n\n"
            "Without a promptset, extraction cannot run. You can generate one\n"
            "interactively with 'dopemux extractor init --interactive'.",
        )

    # Offer to generate
    style = questionary.Style([
        ("selected", "fg:ansiblue bold"),
        ("pointer", "fg:ansicyan"),
    ])

    action = questionary.select(
        "Generate promptset now?",
        choices=["Yes — run extractor init", "Skip — I'll do it later"],
        default="Yes — run extractor init",
        use_indicator=True,
        style=style,
    ).ask()

    if action is None:
        return StageResult(status=StageStatus.SKIPPED, message="User cancelled")

    if action.startswith("Yes"):
        console.print("\n[mint]Running extractor init…[/mint]\n")
        init_result = subprocess.run(
            [sys.executable, "-m", "dopemux", "extractor", "init", "--interactive"],
            cwd=str(state.repo_root),
        )
        if init_result.returncode == 0:
            state.promptset_ready = True
            return StageResult(status=StageStatus.COMPLETED, message="Promptset generated")
        else:
            console.print(f"[error]Extractor init failed (exit {init_result.returncode})[/error]")
            return StageResult(status=StageStatus.FAILED, message="Promptset generation failed")
    else:
        state.promptset_ready = False
        return StageResult(status=StageStatus.SKIPPED, message="Promptset setup skipped")
