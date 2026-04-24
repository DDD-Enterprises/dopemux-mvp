"""Guarded CLI wrapper for the static cockpit renderer."""

from __future__ import annotations

import click

from dopemux.ui.cockpit import render_snapshot

BLOCKED_WITHOUT_STATIC_DEMO = (
    "[BLOCKER] cockpit CLI wrapper disabled.\n"
    "Problem: this slice exposes only a deterministic static demo.\n"
    "Why: live cockpit surfaces are out of scope in DMX-COCKPIT-STATIC-002.\n"
    "Fix: rerun with dopemux cockpit --static-demo --snapshot 120x40.\n"
    "NEXT: use --static-demo or invoke python -m dopemux.ui.cockpit --snapshot 120x40."
)


@click.command("cockpit")
@click.option(
    "--static-demo",
    is_flag=True,
    help="Expose the deterministic static cockpit demo only.",
)
@click.option(
    "--snapshot",
    type=click.Choice(["120x40", "100x32", "80x24"]),
    required=True,
    help="Render a fixed static cockpit snapshot size.",
)
def cockpit(static_demo: bool, snapshot: str) -> None:
    """Render the deterministic seed-only cockpit snapshot."""

    if not static_demo:
        click.echo(BLOCKED_WITHOUT_STATIC_DEMO)
        raise SystemExit(1)
    click.echo(render_snapshot(snapshot))
