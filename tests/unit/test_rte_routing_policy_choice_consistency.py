"""TP-RTE-TRUTH-R4-004 (F-43): the `--routing-policy` Click Choice list was
spelled out three times: `src/dopemux/cli.py::_ROUTING_POLICY_CHOICES`
(used by `rte run`/`rte preflight`/`rte validate-live`),
`src/dopemux/commands/audit_commands.py::_ROUTING_POLICY_CHOICES` (used by
`audit wizard`, mounted at `rte wizard`), and a THIRD, narrower 4-item
inline Choice list on the dead `dopemux truth` command. The first two were
identical in practice but had no structural guarantee of staying that way;
the third was actually different (4 items vs 8), rejecting valid policies
before `truth` even got to raise its "blocked" ClickException. All three
now import `dopemux.commands.rte_shared.ROUTING_POLICY_CHOICES`.

These tests invoke the real CLI (`--help` for the Choice metavar, plus a
Click UsageError probe for `truth`) rather than importing the shared
constant and asserting on it in isolation -- the whole point of F-43 is
that structural sharing must be visible at the wired surface, not just
present in a python module a test could import while the CLI still uses
stale duplicates.
"""

from __future__ import annotations

from click.testing import CliRunner

import dopemux.cli as dopemux_cli
from dopemux.commands.rte_shared import ROUTING_POLICY_CHOICES


def _choice_metavar_line(help_output: str) -> str:
    for line in help_output.splitlines():
        if "--routing-policy" in line and "[" in line:
            return line
    raise AssertionError(f"--routing-policy line not found in help output:\n{help_output}")


def test_rte_run_help_lists_every_canonical_routing_policy() -> None:
    """`rte run` renders the Choice list in --help (no metavar override), so
    this can assert directly against the rendered text."""
    runner = CliRunner()
    rte_run_help = runner.invoke(dopemux_cli.cli, ["rte", "run", "--help"]).output
    run_line = _choice_metavar_line(rte_run_help)

    for policy in ROUTING_POLICY_CHOICES:
        assert policy in run_line, f"{policy} missing from `rte run --help`"


def test_rte_wizard_param_object_shares_the_same_routing_policy_choices() -> None:
    """`audit wizard` (mounted at `rte wizard`) sets `metavar="TEXT"` on
    `--routing-policy`, so the choice list doesn't render in --help text --
    inspect the real, wired Click parameter object instead of parsing help
    output. This still checks the actual registered command (not an
    isolated helper), matching what Click itself validates input against."""
    wizard_command = dopemux_cli.rte.commands["wizard"]
    routing_param = next(
        p for p in wizard_command.params if p.name == "routing_policy"
    )
    assert list(routing_param.type.choices) == list(ROUTING_POLICY_CHOICES)


def test_rte_wizard_accepts_every_canonical_routing_policy_value() -> None:
    """Cross-check the param-object inspection above against real argument
    parsing: every canonical policy must clear Click's Choice validator for
    `rte wizard` (whatever happens after parsing -- e.g. a missing
    `questionary` dependency -- is out of scope here)."""
    runner = CliRunner()
    for policy in ROUTING_POLICY_CHOICES:
        result = runner.invoke(
            dopemux_cli.cli, ["rte", "wizard", "--routing-policy", policy]
        )
        assert "Invalid value for '--routing-policy'" not in result.output, (
            f"{policy} rejected by `rte wizard`: {result.output}"
        )


def test_dead_truth_command_now_accepts_the_full_canonical_choice_set() -> None:
    """Before F-43, `dopemux truth --routing-policy openrouter` was REJECTED
    by Click argument parsing (UsageError, exit code 2) before `truth`'s own
    body ever ran to raise its "blocked, use rte" ClickException -- because
    its inline Choice list only had 4 of the 8 canonical policies. Now it
    parses through to the expected blocked-command error for every
    canonical policy."""
    runner = CliRunner()
    for policy in ROUTING_POLICY_CHOICES:
        result = runner.invoke(dopemux_cli.cli, ["truth", "--routing-policy", policy])
        assert "No such option" not in result.output
        assert "Error: Invalid value for '--routing-policy'" not in result.output
        assert "not a supported Repo Truth Extractor entrypoint" in result.output


def test_routing_policy_choices_has_no_duplicates_and_is_nonempty() -> None:
    assert len(ROUTING_POLICY_CHOICES) == len(set(ROUTING_POLICY_CHOICES))
    assert len(ROUTING_POLICY_CHOICES) >= 4
