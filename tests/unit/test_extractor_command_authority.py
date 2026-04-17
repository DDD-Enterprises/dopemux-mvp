from __future__ import annotations

from click.testing import CliRunner

from dopemux.commands.extract_commands import extract
from dopemux.commands.extractor_commands import extractor


def test_legacy_extractor_help_points_to_truth_run() -> None:
    result = CliRunner().invoke(extractor, ["--help"])

    assert result.exit_code == 0
    assert "legacy promptset/prescan cockpit" in result.output.lower()
    assert "dopemux extract truth-run" in result.output


def test_legacy_extractor_run_warns_about_canonical_truth_run() -> None:
    result = CliRunner().invoke(extractor, ["run"])

    assert result.exit_code == 0
    assert "legacy promptset tooling" in result.output
    assert "dopemux extract truth-run" in result.output
    assert "canonical operator path" in result.output.lower()


def test_legacy_extractor_status_help_marks_promptset_scope() -> None:
    result = CliRunner().invoke(extractor, ["status", "--help"])

    assert result.exit_code == 0
    assert "promptset status" in result.output.lower()
    assert "not the canonical runtime run-status surface" in result.output.lower()


def test_legacy_extractor_status_alias_warns_and_accepts_runtime_options() -> None:
    from unittest.mock import patch

    with patch("dopemux.commands.extractor_commands._run_extractor_runner") as mocked:
        result = CliRunner().invoke(
            extractor,
            ["status", "--pipeline-version", "v4", "--run-id", "rid2"],
        )

    assert result.exit_code == 0
    assert "legacy alias" in result.output.lower()
    mocked.assert_called_once_with(
        pipeline_version="v4",
        args=["--status", "--run-id", "rid2"],
    )


def test_truth_run_help_remains_canonical_operator_surface() -> None:
    result = CliRunner().invoke(extract, ["truth-run", "--help"])

    assert result.exit_code == 0
    assert "v5 extraction" in result.output.lower()
    assert "--doctor" in result.output
    assert "--import-v3" in result.output


def test_cli_import_does_not_override_legacy_extractor_run_command() -> None:
    import dopemux.cli  # noqa: F401

    result = CliRunner().invoke(extractor, ["run"])

    assert result.exit_code == 0
    assert "legacy promptset tooling" in result.output
    assert "direct execution is disabled" in result.output.lower()
