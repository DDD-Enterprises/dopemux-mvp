from __future__ import annotations

from tools.pr_steward.security_release_gate import classify_security_release_paths


def test_ordinary_files_are_not_required():
    result = classify_security_release_paths(["src/foo.py", "docs/readme.md"])
    assert result.required is False
    assert result.categories == ()
    assert result.matched_paths == ()


def test_workflow_file_is_required_ci_workflow():
    result = classify_security_release_paths([".github/workflows/pr-steward.yml"])
    assert result.required is True
    assert "ci_workflow" in result.categories
    assert (".github/workflows/pr-steward.yml", "ci_workflow") in result.matched_paths


def test_codeowners_is_required():
    result = classify_security_release_paths(["CODEOWNERS"])
    assert result.required is True
    assert "codeowners" in result.categories


def test_nested_codeowners_is_required():
    result = classify_security_release_paths([".github/CODEOWNERS"])
    assert result.required is True
    assert "codeowners" in result.categories


def test_schema_file_is_required_schema_contract():
    result = classify_security_release_paths(["schemas/pr_steward/merge_readiness.schema.json"])
    assert result.required is True
    assert "schema_contract" in result.categories


def test_secrets_like_path_is_required():
    result = classify_security_release_paths(["config/secrets/prod.env"])
    assert result.required is True
    assert "secrets" in result.categories


def test_dcp_forbidden_path_is_required_dcp_boundary():
    result = classify_security_release_paths(
        ["services/task-orchestrator/src/index.ts"]
    )
    assert result.required is True
    assert "dcp_boundary" in result.categories


def test_multiple_categories_all_recorded():
    result = classify_security_release_paths(
        [".github/workflows/pr-steward.yml", "CODEOWNERS", "src/foo.py"]
    )
    assert result.required is True
    assert set(result.categories) == {"ci_workflow", "codeowners"}
    assert len(result.matched_paths) == 2


def test_empty_changed_files_not_required():
    result = classify_security_release_paths([])
    assert result.required is False


def test_github_action_file_is_required_ci_workflow():
    result = classify_security_release_paths([".github/actions/example/action.yml"])
    assert result.required is True
    assert "ci_workflow" in result.categories


def test_pr_steward_trust_root_files_are_required():
    trust_root_paths = [
        "tools/pr_steward/known_reviewers.json",
        "tools/pr_steward/security_release_gate.py",
        "tools/pr_steward/security_release_approval.py",
        "tools/pr_steward/classifier.py",
        "tools/pr_steward/collector.py",
        "tools/pr_steward/intake.py",
    ]
    for path in trust_root_paths:
        result = classify_security_release_paths([path])
        assert result.required is True, path
        assert "pr_steward_trust_root" in result.categories, path


def test_result_is_frozen():
    result = classify_security_release_paths([])
    import dataclasses

    with_replace = dataclasses.replace(result, required=True)
    assert with_replace.required is True
    assert result.required is False
