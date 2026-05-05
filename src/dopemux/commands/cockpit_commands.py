"""Cockpit commands for dopemux CLI -- PM shell and runtime primitives."""

from __future__ import annotations

import json
import sys

import click

from ..ui.cockpit.app import run_cockpit
from ..ui.cockpit.render import TOO_SMALL_MESSAGE
from ..ui.cockpit.runtime_contract import (
    PackageLoadError,
    RuntimeContractError,
    render_runtime_snapshot,
    runtime_snapshot_payload,
)


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


RUNTIME_RENDER_BLOCKER = (
    "[BLOCKER] cockpit runtime renderer requires explicit --runtime-render "
    "and --package-dir"
)


@click.group(invoke_without_command=True)
@click.option(
    "--runtime-render",
    is_flag=True,
    default=False,
    help="Render local-only package-derived runtime primitives.",
)
@click.option(
    "--package-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=str),
    default=None,
    help="Accepted Cockpit IA package-remediation directory.",
)
@click.option(
    "--snapshot",
    "snapshot_str",
    type=str,
    default="120x40",
    show_default=True,
    help="Runtime-render snapshot size: 120x40 | 100x32 | 80x24.",
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    default=False,
    help="Emit the runtime-render snapshot as JSON.",
)
@click.pass_context
def cockpit(
    ctx: click.Context,
    runtime_render: bool,
    package_dir: str | None,
    snapshot_str: str,
    json_output: bool,
) -> None:
    """Dopemux Cockpit -- guarded operator and runtime-render surfaces."""
    if ctx.invoked_subcommand is not None:
        return
    if not runtime_render:
        click.echo(RUNTIME_RENDER_BLOCKER)
        ctx.exit(2)
    if package_dir is None:
        click.echo(RUNTIME_RENDER_BLOCKER)
        ctx.exit(2)
    try:
        snapshot = _parse_size(snapshot_str)
        if json_output:
            click.echo(
                json.dumps(
                    runtime_snapshot_payload(package_dir, snapshot=snapshot),
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            click.echo(
                render_runtime_snapshot(
                    package_dir,
                    snapshot=snapshot,
                ),
                nl=False,
            )
    except (PackageLoadError, RuntimeContractError, click.BadParameter) as exc:
        click.echo(str(exc))
        ctx.exit(2)


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
