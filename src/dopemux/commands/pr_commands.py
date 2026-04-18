"""
PR Merge Commands

Delegates `dopemux pr-merge` invocations to the argparse-based
`dopemux_pr_merge_specialist.cli` so the specialist's full subcommand
surface (preflight, queue-scan, pr-plan, pr-apply, pr-merge, queue-drain,
pr-fix, self-check, flight-deck, fusion, ops) is exposed through the
top-level `dopemux` CLI.
"""

import logging

import click

logger = logging.getLogger(__name__)


@click.command(
    name="pr-merge",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
    add_help_option=False,
)
@click.pass_context
def pr_merge_group(ctx):
    """Delegate PR merge specialist commands to the argparse-based specialist CLI."""
    from dopemux_pr_merge_specialist.cli import build_parser

    parser = build_parser()
    argv = list(ctx.args)
    if not argv:
        argv = ["--help"]
    parsed = parser.parse_args(argv)
    raise SystemExit(parsed.func(parsed))
