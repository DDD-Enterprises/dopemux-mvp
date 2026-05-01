from click.testing import CliRunner

from dopemux.system_data.cli import system_data
from dopemux.system_data.models import (
    EnvironmentSnapshot,
    Finding,
    ScanResult,
    ToolReport,
    ToolStatus,
)


def _scan_result() -> ScanResult:
    env = EnvironmentSnapshot(
        hostname="test",
        platform="Darwin",
        macos_version="15.0",
        home="/tmp",
        disk_pressure="healthy",
        free_bytes=100,
        total_bytes=1000,
        full_disk_access="likely",
        docker_cli_installed=False,
        docker_daemon_reachable=False,
    )
    finding = Finding(
        finding_id="F1",
        category="clear-safe-path",
        path="/tmp/cache",
        size_bytes=10,
        kind="directory",
        risk_level="safe_clear",
        reclaim_mode="delete",
        reclaim_estimate_bytes=10,
        same_volume_quarantine_effective=False,
        recommended_action="clear_safe_path",
        requires_app_quit=(),
        rationale="test",
    )
    return ScanResult(
        tool_report=ToolReport(required=(), statuses=()),
        environment=env,
        findings=(finding,),
    )


def test_system_data_commands_registered():
    runner = CliRunner()

    result = runner.invoke(system_data, ["--help"])

    assert result.exit_code == 0
    for command in ("doctor", "scan", "report", "plan", "clean", "restore", "tui"):
        assert command in result.output


def test_doctor_missing_required_tool_exits_nonzero(monkeypatch):
    class DummyRunner:
        def check_required_tools(self):
            return ToolReport(
                required=("dust",),
                statuses=(ToolStatus(name="dust", path=None, version=None, available=False),),
            )

    monkeypatch.setattr("dopemux.system_data.cli.ToolRunner", DummyRunner)

    result = CliRunner().invoke(system_data, ["doctor"])

    assert result.exit_code == 1
    assert "brew install dust duf btop procs gdu dua-cli ncdu" in result.output


def test_scan_json_uses_scan_result(monkeypatch):
    monkeypatch.setattr("dopemux.system_data.cli.scan", lambda home: _scan_result())

    result = CliRunner().invoke(system_data, ["scan", "--json", "--home", "/tmp"])

    assert result.exit_code == 0
    assert '"finding_id": "F1"' in result.output


def test_clean_execute_requires_yes(monkeypatch):
    monkeypatch.setattr("dopemux.system_data.cli.scan", lambda home: _scan_result())

    result = CliRunner().invoke(system_data, ["clean", "--execute"])

    assert result.exit_code != 0
    assert "--execute requires --yes" in result.output
