"""Stage 4: Session-local provider API key overrides."""

from __future__ import annotations

import os

from rich.box import ROUNDED
from rich.panel import Panel

from dopemux.console import console

from ..questionary_support import MissingInteractiveDependencyError, require_questionary
from .display import render_educational_panel
from .stages import StageResult, StageStatus, WizardState

PROVIDER_KEY_FIELDS = [
    ("OpenAI", "OPENAI_API_KEY"),
    ("OpenRouter", "OPENROUTER_API_KEY"),
    ("Gemini", "GEMINI_API_KEY"),
    ("xAI", "XAI_API_KEY"),
    ("Anthropic", "ANTHROPIC_API_KEY"),
]


def _effective_status(state: WizardState, env_var: str) -> str:
    if state.provider_key_overrides.get(env_var, "").strip():
        return "override set"
    if os.environ.get(env_var, "").strip():
        return "shell default"
    return "missing"


def _render_override_status(state: WizardState) -> None:
    lines = []
    for provider_name, env_var in PROVIDER_KEY_FIELDS:
        status = _effective_status(state, env_var)
        color = "green" if status != "missing" else "red"
        lines.append(f"  • {provider_name} ({env_var}): [{color}]{status}[/{color}]")
    console.print(
        Panel(
            "\n".join(lines),
            title="[bold white]Provider Key Overrides[/bold white]",
            border_style="bright_cyan",
            box=ROUNDED,
            padding=(1, 2),
        )
    )


def run_provider_overrides(state: WizardState) -> StageResult:
    """Stage 4 — collect optional session-local provider key overrides."""
    if state.educate_mode:
        render_educational_panel(
            "Provider API key overrides",
            "This step lets you inject session-local provider keys for the wizard.\n\n"
            "Overrides are applied only to the extraction subprocess environment.\n"
            "They do not modify your shell profile, .env files, or repo config.\n\n"
            "Use this when you want the wizard to test a different provider account\n"
            "or temporarily fill in missing keys for a bounded run.",
        )

    _render_override_status(state)

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

    while True:
        choices = []
        for provider_name, env_var in PROVIDER_KEY_FIELDS:
            status = _effective_status(state, env_var)
            choices.append(f"{provider_name} ({env_var}) [{status}]")
        choices.append("Continue")

        selected = questionary.select(
            "Select a provider to override, or continue:",
            choices=choices,
            default="Continue",
            use_indicator=True,
            style=style,
        ).ask()

        if selected is None:
            return StageResult(status=StageStatus.SKIPPED, message="User cancelled")
        if selected == "Continue":
            break

        provider_name, env_var = next(
            (item for item in PROVIDER_KEY_FIELDS if selected.startswith(item[0])),
            (None, None),
        )
        if not env_var:
            continue

        current = state.provider_key_overrides.get(env_var, "").strip()
        prompt = (
            f"Enter session override for {provider_name} ({env_var}). "
            "Submit an empty value to clear the override:"
        )
        value = questionary.password(
            prompt,
            default=current or "",
            style=style,
        ).ask()

        if value is None:
            return StageResult(status=StageStatus.SKIPPED, message="User cancelled")
        if str(value).strip():
            state.provider_key_overrides[env_var] = str(value).strip()
        else:
            state.provider_key_overrides.pop(env_var, None)

        _render_override_status(state)

    override_count = len(state.provider_key_overrides)
    message = (
        f"{override_count} override(s) configured"
        if override_count
        else "No provider overrides configured"
    )
    return StageResult(
        status=StageStatus.COMPLETED,
        message=message,
        data={"provider_key_overrides": sorted(state.provider_key_overrides)},
    )
