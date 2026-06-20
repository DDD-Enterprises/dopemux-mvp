"""
dopemux.pcp.cli — CLI entry point for Project Control Plane commands.

Provides a ``pcp`` Click group with an ``export`` subcommand that inspects a
Git repository and emits a JSON evidence export to stdout or a file.

Usage::

    python -m dopemux.pcp.cli export --help
    python -m dopemux.pcp.cli export --repo /path/to/repo
    python -m dopemux.pcp.cli export --repo /path/to/repo --output evidence.json
"""

from __future__ import annotations

import json
import sys

import click

from .exporter import export_evidence


@click.group()
def pcp() -> None:
    """Project Control Plane — read-only repo evidence commands."""


@pcp.command("export")
@click.option(
    "--repo",
    default=".",
    show_default=True,
    metavar="PATH",
    help="Path to the Git repository to inspect.  Defaults to the current directory.",
)
@click.option(
    "--output",
    "-o",
    default=None,
    metavar="PATH",
    help="Write JSON output to PATH instead of stdout.",
)
@click.option(
    "--indent",
    default=2,
    show_default=True,
    type=int,
    help="JSON indentation level.",
)
def export_cmd(repo: str, output: str | None, indent: int) -> None:
    """Emit a Project Control Plane evidence export for REPO.

    Inspects the Git repository at REPO and prints (or writes) a JSON object
    that validates against
    schemas/project_control_plane/project_evidence_export.schema.json.

    This command is strictly read-only: it makes no writes to the repository,
    performs no network calls, and mutates no external state.
    """
    try:
        evidence = export_evidence(repo)
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    json_text = json.dumps(evidence, indent=indent)

    if output is None:
        click.echo(json_text)
    else:
        with open(output, "w", encoding="utf-8") as fh:
            fh.write(json_text)
            fh.write("\n")
        click.echo(f"Evidence export written to {output}", err=True)


if __name__ == "__main__":
    pcp()
