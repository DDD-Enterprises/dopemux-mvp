from click.testing import CliRunner

from dopemux.cli import cli
from dopemux.ui.cockpit import render_snapshot
from dopemux.commands.cockpit_commands import BLOCKED_WITHOUT_STATIC_DEMO


def test_cockpit_requires_static_demo_flag() -> None:
    result = CliRunner().invoke(cli, ["cockpit", "--snapshot", "120x40"])

    assert result.exit_code == 1
    assert BLOCKED_WITHOUT_STATIC_DEMO in result.output


def test_cockpit_cli_matches_renderer_output_for_120x40() -> None:
    result = CliRunner().invoke(cli, ["cockpit", "--static-demo", "--snapshot", "120x40"])

    assert result.exit_code == 0
    assert result.output == render_snapshot("120x40") + "\n"


def test_cockpit_cli_supports_all_snapshot_sizes() -> None:
    runner = CliRunner()

    for size in ("120x40", "100x32", "80x24"):
        result = runner.invoke(cli, ["cockpit", "--static-demo", "--snapshot", size])
        assert result.exit_code == 0
        assert "mode Services" in result.output
        assert "[UNKNOWN]" not in result.output
        assert "6 RTE" not in result.output


def test_cockpit_cli_no_color_output_has_no_ansi() -> None:
    runner = CliRunner(env={"NO_COLOR": "1"})
    result = runner.invoke(cli, ["cockpit", "--static-demo", "--snapshot", "120x40"])

    assert result.exit_code == 0
    assert "\x1b[" not in result.output
    assert "SRC=" in result.output
    assert "authority:" in result.output
    assert "[EDGE] bridge is adapter/proxy o" in result.output
