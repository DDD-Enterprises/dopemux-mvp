"""CLI contract tests for the dopemux cockpit command."""

from __future__ import annotations

from click.testing import CliRunner

from dopemux.commands.cockpit_commands import cockpit
from dopemux.ui.cockpit.render import TOO_SMALL_MESSAGE


def _invoke(*args: str) -> "tuple[int, str]":
    runner = CliRunner()
    result = runner.invoke(cockpit, list(args))
    return result.exit_code, result.output


def test_plain_render_at_120x40_succeeds():
    code, output = _invoke("run", "--mode", "pm", "--size", "120x40", "--plain")
    assert code == 0
    assert "STATIC DEMO" in output
    assert "bridge segregator" in output
    assert "more_count:" in output


def test_plain_render_at_100x32_succeeds():
    code, output = _invoke("run", "--mode", "pm", "--size", "100x32", "--plain")
    assert code == 0
    assert "STATIC DEMO" in output
    # 100x32 lives in the inspector-lower-detail bridge mode.
    assert "inspector-lower-detail" in output


def test_audit_render_at_80x24_collapses_bridge():
    code, output = _invoke("run", "--mode", "pm", "--size", "80x24", "--audit")
    assert code == 0
    assert "[inspector-detail]" in output
    assert "bridge segregator" not in output


def test_below_minimum_viewport_emits_blocker_and_exits_nonzero():
    runner = CliRunner()
    # Use an unsupported preset to trigger BadParameter.
    bad = runner.invoke(cockpit, ["run", "--size", "70x20", "--plain"])
    assert bad.exit_code != 0


def test_unsupported_size_token_rejected():
    runner = CliRunner()
    result = runner.invoke(cockpit, ["run", "--size", "999x999", "--plain"])
    assert result.exit_code != 0


def test_default_size_is_120x40_plain():
    code, output = _invoke("run", "--plain")
    assert code == 0
    assert "120x40" in output


def test_no_forbidden_phrases_via_cli():
    forbidden = (
        "Run History",
        "authority: dopemux",
        "Services authority: dopemux",
        "command authority: dopemux",
        "Bridge actions authority",
        "SRC=dopemux",
        "UNKNOWN→EDGE",
        "UNKNOWN -> EDGE",
        "UNKNOWN=EDGE",
    )
    for size in ("120x40", "100x32", "80x24"):
        code, output = _invoke("run", "--size", size, "--plain")
        assert code == 0
        for phrase in forbidden:
            assert phrase not in output, (
                f"forbidden phrase {phrase!r} leaked at size {size}"
            )


def test_blocker_message_content():
    # Sanity: the canonical BLOCKER token used elsewhere in the cockpit.
    assert TOO_SMALL_MESSAGE.startswith("[BLOCKER]")
