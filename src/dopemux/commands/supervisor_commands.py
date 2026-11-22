"""Explicit seam to the lean supervisor; no work occurs during registration."""

import click


@click.command(
    "supervise",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.argument("arguments", nargs=-1, type=click.UNPROCESSED)
def supervise(arguments):
    """Run bounded local mandates (use python -m dopemux.supervisor for lean startup)."""
    from ..supervisor.__main__ import main

    raise SystemExit(main(list(arguments)))
