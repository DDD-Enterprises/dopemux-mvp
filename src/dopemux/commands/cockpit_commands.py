"""Cockpit commands for dopemux CLI -- PM Textual TUI shell."""

from __future__ import annotations

import sys

import click

from ..ui.cockpit.app import run_cockpit
from ..ui.cockpit.render import TOO_SMALL_MESSAGE


_SIZE_PRESETS: dict[str, tuple[int, int]] = {
    "120x40": (120, 40),
    "100x32": (100, 32),
    "80x24": (80, 24),
}


def _parse_size(value: str) -> tuple[int, int]:
    if value in _SIZE_PRESETS:
        return _SIZE_PRESETS[value]
    raise click.BadParameter(
        f"unsupported size {value!r}; choose one of {sorted(_SIZE_PRESETS)}"
    )


@click.group()
def cockpit() -> None:
    """Dopemux Cockpit -- architecture-safe PM operator surface (static demo)."""


@cockpit.command("run")
@click.option(
    "--mode",
    type=click.Choice(["pm"], case_sensitive=False),
    default="pm",
    show_default=True,
    help="Cockpit mode (only PM is implemented in this slice).",
)
@click.option(
    "--size",
    "size_str",
    type=str,
    default="120x40",
    show_default=True,
    help="Viewport size: 120x40 | 100x32 | 80x24.",
)
@click.option(
    "--plain",
    is_flag=True,
    default=False,
    help="Render deterministic plain text (no Textual UI).",
)
@click.option(
    "--audit",
    is_flag=True,
    default=False,
    help="Audit-mode render (log-safe, deterministic, no Textual UI).",
)
def cockpit_run(mode: str, size_str: str, plain: bool, audit: bool) -> None:
    """Launch the cockpit (or render plain / audit text)."""
    cols, rows = _parse_size(size_str)
    if cols < 80 or rows < 24:
        click.echo(TOO_SMALL_MESSAGE)
        sys.exit(2)
    output = run_cockpit(
        mode=mode.lower(),
        size=(cols, rows),
        plain=plain,
        audit=audit,
    )
    if output is not None:
        click.echo(output)
