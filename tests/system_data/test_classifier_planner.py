from pathlib import Path

from dopemux.system_data.classifier import classify_path
from dopemux.system_data.models import (
    EnvironmentSnapshot,
    EvidenceRecord,
    Finding,
    ScanResult,
    ToolReport,
)
from dopemux.system_data.planner import build_plan


def _scan_result(
    path: Path,
    *,
    pressure: str = "healthy",
    finding: Finding | None = None,
    docker_installed: bool = False,
    docker_reachable: bool = False,
) -> ScanResult:
    finding = finding or Finding(
        finding_id="safe-1",
        category="clear-safe-path",
        path=str(path),
        size_bytes=4096,
        kind="directory",
        risk_level="safe_clear",
        reclaim_mode="delete",
        reclaim_estimate_bytes=4096,
        same_volume_quarantine_effective=False,
        recommended_action="clear_safe_path",
        requires_app_quit=(),
        rationale="test",
        evidence=(
            EvidenceRecord(source="dust", path=str(path), data={"size_bytes": 4096}),
        ),
    )
    env = EnvironmentSnapshot(
        hostname="test",
        platform="Darwin",
        macos_version="15.0",
        home=str(path.parent),
        disk_pressure=pressure,
        free_bytes=100,
        total_bytes=1000,
        full_disk_access="likely",
        docker_cli_installed=docker_installed,
        docker_daemon_reachable=docker_reachable,
    )
    return ScanResult(
        tool_report=ToolReport(required=(), statuses=()),
        environment=env,
        findings=(finding,),
    )


def _finding(
    *,
    path: str,
    risk: str,
    action: str,
    category: str = "tool-mediated",
) -> Finding:
    finding = Finding(
        finding_id="finding-1",
        category=category,
        path=path,
        size_bytes=4096,
        kind="directory",
        risk_level=risk,
        reclaim_mode="tool" if risk == "tool_mediated" else "delete",
        reclaim_estimate_bytes=4096,
        same_volume_quarantine_effective=False,
        recommended_action=action,
        requires_app_quit=(),
        rationale="test",
        evidence=(
            EvidenceRecord(source="dust", path=path, data={"size_bytes": 4096}),
        ),
    )
    return finding


def test_classifier_mobile_sms_tmp_safe_clear():
    risk, mode, action, rationale, apps = classify_path(
        Path("~/Library/Containers/com.apple.MobileSMS/Data/tmp").expanduser()
    )

    assert risk == "safe_clear"
    assert mode == "delete"
    assert action == "clear_safe_path"
    assert "Messages" in apps
    assert "temporary" in rationale


def test_classifier_messages_attachments_review_first():
    risk, mode, action, _, _ = classify_path(
        Path("~/Library/Messages/Attachments").expanduser()
    )

    assert risk == "review_first"
    assert mode == "quarantine_or_explicit_delete"
    assert action == "review_attachments"


def test_same_volume_quarantine_reports_zero_reclaim(tmp_path):
    source = tmp_path / "cache"
    source.mkdir()
    quarantine = tmp_path / "quarantine"
    quarantine.mkdir()

    plan = build_plan(_scan_result(source), quarantine_dir=quarantine)

    assert plan.actions[0].action_type == "quarantine"
    assert plan.actions[0].expected_reclaim_bytes == 0
    assert "same-volume quarantine" in " ".join(plan.warnings)


def test_critical_disk_prefers_delete_for_safe_clear_same_volume(tmp_path):
    source = tmp_path / "cache"
    source.mkdir()
    quarantine = tmp_path / "quarantine"
    quarantine.mkdir()

    plan = build_plan(_scan_result(source, pressure="critical"), quarantine_dir=quarantine)

    assert plan.actions[0].action_type == "clear_safe_path"
    assert plan.actions[0].expected_reclaim_bytes == 4096
    assert plan.actions[0].rollback_mode == "delete_in_place"


def test_docker_daemon_unavailable_blocks_prune(tmp_path):
    docker_finding = _finding(
        path=str(tmp_path / ".docker"),
        risk="tool_mediated",
        action="docker_prune",
    )

    plan = build_plan(
        _scan_result(
            tmp_path,
            finding=docker_finding,
            docker_installed=True,
            docker_reachable=False,
        )
    )

    assert plan.actions[0].action_type == "blocked"
    assert plan.actions[0].expected_reclaim_bytes == 0
    assert "daemon" in plan.actions[0].blocked_reason


def test_docker_daemon_available_allows_prune(tmp_path):
    docker_finding = _finding(
        path=str(tmp_path / ".docker"),
        risk="tool_mediated",
        action="docker_prune",
    )

    plan = build_plan(
        _scan_result(
            tmp_path,
            finding=docker_finding,
            docker_installed=True,
            docker_reachable=True,
        )
    )

    assert plan.actions[0].action_type == "docker_prune"
    assert plan.actions[0].expected_reclaim_bytes == 4096


def test_homebrew_cache_is_tool_mediated():
    risk, mode, action, rationale, _ = classify_path(
        Path("~/Library/Caches/Homebrew").expanduser()
    )

    assert risk == "tool_mediated"
    assert mode == "tool"
    assert action == "homebrew_cleanup"
    assert "brew cleanup" in rationale


def test_ios_backups_are_review_first():
    risk, _, action, _, _ = classify_path(
        Path("~/Library/Application Support/MobileSync/Backup").expanduser()
    )

    assert risk == "review_first"
    assert action == "review_ios_backups"
