import json
from pathlib import Path

import yaml

from dopemux.profile_manager import DopemuxProfile
from dopemux.project_init import ProjectInitializer


class _ProfileManager:
    def __init__(self) -> None:
        self.profile = DopemuxProfile(
            name="adhd-default",
            description="Test profile",
        )

    def list_profiles(self) -> list[DopemuxProfile]:
        return [self.profile]

    def get_profile(self, name: str) -> DopemuxProfile | None:
        if name == self.profile.name:
            return self.profile
        return None

    def set_active_profile(self, workspace: Path, profile_name: str) -> None:
        marker = workspace / ".dopemux" / "active_profile"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(profile_name, encoding="utf-8")


def _initializer(workspace: Path) -> ProjectInitializer:
    initializer = ProjectInitializer(workspace)
    initializer.profile_manager = _ProfileManager()
    return initializer


def test_init_scaffolds_pr_steward_workflows_and_policy(tmp_path: Path) -> None:
    initializer = _initializer(tmp_path)

    assert initializer.initialize(profile_name="adhd-default") is True

    pr_steward_workflow = tmp_path / ".github" / "workflows" / "pr-steward.yml"
    embedded_audit_workflow = tmp_path / ".github" / "workflows" / "embedded-audit.yml"
    pr_steward_policy = tmp_path / "config" / "pr_steward" / "policy.json"
    merge_policy = tmp_path / "config" / "pr_merge_specialist" / "policy.yaml"

    assert pr_steward_workflow.exists()
    assert embedded_audit_workflow.exists()
    assert pr_steward_policy.exists()
    assert merge_policy.exists()

    pr_steward_yaml = yaml.safe_load(pr_steward_workflow.read_text(encoding="utf-8"))
    embedded_audit_yaml = yaml.safe_load(embedded_audit_workflow.read_text(encoding="utf-8"))
    pr_steward_config = json.loads(pr_steward_policy.read_text(encoding="utf-8"))
    merge_config = yaml.safe_load(merge_policy.read_text(encoding="utf-8"))

    pr_steward_runs = [
        step["run"]
        for step in pr_steward_yaml["jobs"]["pr-steward"]["steps"]
        if "run" in step
    ]
    embedded_audit_runs = [
        step["run"]
        for step in embedded_audit_yaml["jobs"]["embedded-audit"]["steps"]
        if "run" in step
    ]

    assert any(
        "python -m dopemux.cli pr-steward intake" in run for run in pr_steward_runs
    )
    assert any(
        "python -m dopemux.cli pr-steward audit" in run for run in embedded_audit_runs
    )
    assert pr_steward_config["mode"] == "check_only"
    assert pr_steward_config["mutates_github"] is False
    assert merge_config["governed_automerge"]["enabled"] is False


def test_init_force_does_not_clobber_existing_pr_steward_files(tmp_path: Path) -> None:
    pr_steward_workflow = tmp_path / ".github" / "workflows" / "pr-steward.yml"
    merge_policy = tmp_path / "config" / "pr_merge_specialist" / "policy.yaml"
    pr_steward_workflow.parent.mkdir(parents=True)
    merge_policy.parent.mkdir(parents=True)
    pr_steward_workflow.write_text("name: custom\n", encoding="utf-8")
    merge_policy.write_text("custom: true\n", encoding="utf-8")

    initializer = _initializer(tmp_path)

    assert initializer.initialize(profile_name="adhd-default", force=True) is True

    assert pr_steward_workflow.read_text(encoding="utf-8") == "name: custom\n"
    assert merge_policy.read_text(encoding="utf-8") == "custom: true\n"
