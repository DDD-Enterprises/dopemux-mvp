import json
import os
import shutil
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

import pytest
import yaml

from dopemux.profile_manager import DopemuxProfile
from dopemux.project_init import ProjectInitializer


ROOT = Path(__file__).resolve().parents[2]


def _run_checked(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=300,
        check=False,
    )
    assert result.returncode == 0, (
        f"command failed ({result.returncode}): {' '.join(command)}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    return result


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
    embedded_audit_yaml = yaml.safe_load(
        embedded_audit_workflow.read_text(encoding="utf-8")
    )
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
    assert any(
        "python -m dopemux.cli pr-steward settlement fetch" in run
        for run in pr_steward_runs
    )
    assert any(
        "python -m dopemux.cli pr-steward settlement compare" in run
        for run in pr_steward_runs
    )
    assert any(
        "--proof-path independent-audit/PROOF.json" in run for run in pr_steward_runs
    )
    assert any(
        'python -m pip install "$DOPEMUX_INSTALL_SPEC"' in run
        for run in pr_steward_runs
    )
    assert any(
        'python -m pip install "$DOPEMUX_INSTALL_SPEC"' in run
        for run in embedded_audit_runs
    )
    assert (
        pr_steward_yaml["jobs"]["pr-steward"]["env"]["DOPEMUX_INSTALL_SPEC"]
        == "git+https://github.com/DDD-Enterprises/dopemux-mvp.git"
    )
    assert (
        embedded_audit_yaml["jobs"]["embedded-audit"]["env"]["DOPEMUX_INSTALL_SPEC"]
        == "git+https://github.com/DDD-Enterprises/dopemux-mvp.git"
    )
    rendered_steward = pr_steward_workflow.read_text(encoding="utf-8")
    assert 'event = str(run.get("event") or "")' in rendered_steward
    assert 'event != "workflow_dispatch"' in rendered_steward
    assert 'head_branch = str(run.get("head_branch") or "")' in rendered_steward
    assert "repository.default_branch" in rendered_steward
    assert "head_branch != default_branch" in rendered_steward
    assert 'path == ".github/workflows/embedded-audit.yml"' in rendered_steward
    assert 'path.endswith("embedded-audit.yml")' not in rendered_steward
    assert "pip install -e ." not in rendered_steward
    assert "python -m tools.pr_steward" not in rendered_steward
    assert "scripts.audit" not in rendered_steward

    assert set(embedded_audit_yaml["on"]) == {"workflow_dispatch"}
    audit_inputs = embedded_audit_yaml["on"]["workflow_dispatch"]["inputs"]
    assert set(audit_inputs) == {"pr_number", "head_sha", "proof_path"}
    assert audit_inputs["pr_number"]["required"] is True
    assert audit_inputs["head_sha"]["required"] is True
    assert audit_inputs["proof_path"]["required"] is True

    audit_steps = embedded_audit_yaml["jobs"]["embedded-audit"]["steps"]
    upload_steps = [
        step for step in audit_steps if step.get("uses") == "actions/upload-artifact@v4"
    ]
    assert len(upload_steps) == 1
    upload = next(
        step for step in audit_steps if step.get("name") == "Upload bound proof"
    )
    assert upload["with"]["name"] == (
        "embedded-audit-pr-${{ steps.target.outputs.pr_number }}-"
        "head-${{ steps.target.outputs.head_sha }}-proof"
    )
    assert upload["with"]["path"] == "independent-audit/PROOF.json"
    assert upload["with"]["if-no-files-found"] == "error"

    rendered_audit = embedded_audit_workflow.read_text(encoding="utf-8")
    assert 'git show "${HEAD_SHA}:${PROOF_PATH}"' in rendered_audit
    assert "live_pr_head_sha" in rendered_audit
    assert "base.repo.full_name" in rendered_audit
    assert "jq -e --argjson pr" in rendered_audit
    assert "jq -e --arg head" in rendered_audit
    assert "actions/checkout@v4" in rendered_audit
    assert "ref: ${{ github.event.repository.default_branch }}" in rendered_audit
    assert "ref: ${{ inputs.head_sha }}" not in rendered_audit
    assert pr_steward_config["mode"] == "check_only"
    assert pr_steward_config["mutates_github"] is False
    assert merge_config["governed_automerge"]["enabled"] is False
    assert (
        merge_config["steward_gate"]["merge_readiness_path"]
        == "{out_dir}/pr-steward/pr-{pr_id}/MERGE_READINESS.json"
    )
    assert (
        merge_config["steward_gate"]["audit_proof_path"]
        == "{out_dir}/embedded-audit/pr-{pr_id}/PROOF.json"
    )


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


@pytest.mark.slow
def test_built_wheel_runs_pr_steward_and_materializes_templates_off_tree(
    tmp_path: Path,
) -> None:
    uv = shutil.which("uv")
    assert uv is not None

    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    _run_checked(
        [uv, "build", "--wheel", "--out-dir", str(dist_dir)],
        cwd=ROOT,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1
    wheel = wheels[0]

    dcp_source = ROOT / "src" / "dopemux" / "dcp"
    dcp_package_census = {
        ".".join(path.parent.relative_to(ROOT / "src").parts)
        for path in dcp_source.rglob("__init__.py")
    }
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    declared_dcp_packages = {
        package
        for package in pyproject["tool"]["setuptools"]["packages"]
        if package == "dopemux.dcp" or package.startswith("dopemux.dcp.")
    }
    assert declared_dcp_packages == dcp_package_census

    required_dcp_members = {
        path.relative_to(ROOT / "src").as_posix() for path in dcp_source.rglob("*.py")
    }
    with zipfile.ZipFile(wheel) as archive:
        wheel_members = set(archive.namelist())
    assert required_dcp_members <= wheel_members

    required_wheel_members = {
        "dopemux_pr_steward/review_settlement.py",
        "dopemux/templates/init/.github/workflows/embedded-audit.yml",
        "dopemux/templates/init/.github/workflows/pr-steward.yml",
        "dopemux/templates/init/.github/workflows/pr-readiness-invalidator.yml",
        "dopemux/templates/init/.github/workflows/pr-readiness-invalidation-writer.yml",
    }
    assert required_wheel_members <= wheel_members

    venv_dir = tmp_path / "venv"
    _run_checked([sys.executable, "-m", "venv", str(venv_dir)], cwd=tmp_path)
    venv_python = venv_dir / "bin" / "python"

    requirements = tmp_path / "requirements.txt"
    _run_checked(
        [
            uv,
            "export",
            "--frozen",
            "--no-dev",
            "--no-emit-project",
            "--format",
            "requirements.txt",
            "--output-file",
            str(requirements),
        ],
        cwd=ROOT,
    )
    _run_checked(
        [
            uv,
            "pip",
            "install",
            "--python",
            str(venv_python),
            "--requirements",
            str(requirements),
        ],
        cwd=tmp_path,
    )
    _run_checked(
        [
            uv,
            "pip",
            "install",
            "--python",
            str(venv_python),
            "--no-deps",
            "--no-index",
            str(wheel),
        ],
        cwd=tmp_path,
    )

    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    runtime_env = os.environ.copy()
    runtime_env.pop("PYTHONPATH", None)
    runtime_env["PYTHONNOUSERSITE"] = "1"
    runtime_env["PYTHONDONTWRITEBYTECODE"] = "1"
    runtime_env["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"

    probe = _run_checked(
        [
            str(venv_python),
            "-I",
            "-c",
            (
                "import json; import dopemux; import dopemux.dcp; "
                "print(json.dumps({'dopemux': dopemux.__file__, "
                "'dcp': dopemux.dcp.__file__}, sort_keys=True))"
            ),
        ],
        cwd=runtime_dir,
        env=runtime_env,
    )
    imported = json.loads(probe.stdout)
    assert venv_dir.resolve() in Path(imported["dopemux"]).resolve().parents
    assert venv_dir.resolve() in Path(imported["dcp"]).resolve().parents
    assert "PYTHONPATH" not in runtime_env
    assert ROOT.resolve() not in runtime_dir.resolve().parents

    fetch_help = _run_checked(
        [
            str(venv_python),
            "-I",
            "-m",
            "dopemux.cli",
            "pr-steward",
            "settlement",
            "fetch",
            "--help",
        ],
        cwd=runtime_dir,
        env=runtime_env,
    )
    assert "ModuleNotFoundError" not in fetch_help.stderr

    settled = {
        "status": "SETTLED",
        "fingerprint": "wheel-runtime-fixture",
        "repository": "DDD-Enterprises/dopemux-mvp",
        "pr_number": 1287,
        "live_head_sha": "0f5ad8d384eafc156397d49aef5630f5d6be831b",
    }
    before = runtime_dir / "before.json"
    after = runtime_dir / "after.json"
    before.write_text(json.dumps(settled), encoding="utf-8")
    after.write_text(json.dumps(settled), encoding="utf-8")
    compare = _run_checked(
        [
            str(venv_python),
            "-I",
            "-m",
            "dopemux.cli",
            "pr-steward",
            "settlement",
            "compare",
            "--before",
            str(before),
            "--after",
            str(after),
        ],
        cwd=runtime_dir,
        env=runtime_env,
    )
    assert json.loads(compare.stdout)["status"] == "MATCH"

    materialized = runtime_dir / "materialized"
    _run_checked(
        [
            str(venv_python),
            "-I",
            "-c",
            (
                "from pathlib import Path; "
                "from dopemux.project_init import ProjectInitializer; "
                f"target=Path({str(materialized)!r}); target.mkdir(); "
                "initializer=object.__new__(ProjectInitializer); "
                "initializer.workspace=target; initializer.install_templates()"
            ),
        ],
        cwd=runtime_dir,
        env=runtime_env,
    )
    required_workflows = {
        "embedded-audit.yml",
        "pr-steward.yml",
        "pr-readiness-invalidator.yml",
        "pr-readiness-invalidation-writer.yml",
    }
    materialized_workflows = {
        path.name
        for path in (materialized / ".github" / "workflows").iterdir()
        if path.is_file()
    }
    assert required_workflows <= materialized_workflows
