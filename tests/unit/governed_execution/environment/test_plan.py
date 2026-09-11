"""Tests for dopemux.governed_execution.environment.plan.

Covers the happy path, rejection of '..' and absolute allowed paths, and
deterministic (sorted, deduplicated) ordering of allowed_paths.
"""
from __future__ import annotations

import pytest

from dopemux.governed_execution.environment.plan import (
    EnvironmentSpec,
    PlanRejected,
    plan_environment,
)

BASE_SHA = "1c915b9141e9a5c3d835a5c7ea953381782ae875"
BRANCH = "feat/gec-v2-w03-isolation-custody-001"
ORIGIN_URL = "https://github.com/DDD-Enterprises/dopemux-mvp.git"
TOPLEVEL = "/Users/hue/code/dopemux-mvp"
WORKTREE_ROOT = "/Users/hue/code/dopemux-mvp/.worktrees"


def make_spec(**overrides: object) -> EnvironmentSpec:
    fields: dict[str, object] = {
        "repo_origin_url": ORIGIN_URL,
        "repo_toplevel": TOPLEVEL,
        "packet_id": "TP-DMX-GEC-V2-W03-ISOLATION-CUSTODY-001",
        "base_sha": BASE_SHA,
        "branch": BRANCH,
        "worktree_root": WORKTREE_ROOT,
        "allowed_paths": ("src/dopemux/governed_execution/environment/plan.py",),
    }
    fields.update(overrides)
    return EnvironmentSpec(**fields)  # type: ignore[arg-type]


def test_happy_path_produces_expected_plan() -> None:
    spec = make_spec()
    plan = plan_environment(spec)

    assert plan.repo_identity.origin_url == ORIGIN_URL
    assert plan.repo_identity.toplevel == TOPLEVEL
    assert plan.packet_id == spec.packet_id
    assert plan.base_sha == BASE_SHA
    assert plan.branch == BRANCH
    assert plan.worktree_root == WORKTREE_ROOT
    assert plan.worktree_path == (
        f"{WORKTREE_ROOT}/tp-dmx-gec-v2-w03-isolation-custody-001"
    )
    assert plan.filesystem_root == plan.worktree_path
    assert plan.allowed_paths == (
        "src/dopemux/governed_execution/environment/plan.py",
    )
    assert plan.rollback_locality.strategy == "RESET_TO_BASE"
    assert plan.rollback_locality.boundary == f"branch:{BRANCH}"


def test_worktree_root_trailing_slash_is_normalised() -> None:
    spec = make_spec(worktree_root=f"{WORKTREE_ROOT}/")
    plan = plan_environment(spec)
    assert plan.worktree_path == (
        f"{WORKTREE_ROOT}/tp-dmx-gec-v2-w03-isolation-custody-001"
    )


def test_rejects_dotdot_segment() -> None:
    spec = make_spec(allowed_paths=("src/../etc/passwd",))
    with pytest.raises(PlanRejected) as excinfo:
        plan_environment(spec)
    assert ".." in excinfo.value.reason


def test_rejects_leading_dotdot() -> None:
    spec = make_spec(allowed_paths=("../outside.py",))
    with pytest.raises(PlanRejected):
        plan_environment(spec)


def test_rejects_absolute_path() -> None:
    spec = make_spec(allowed_paths=("/etc/passwd",))
    with pytest.raises(PlanRejected) as excinfo:
        plan_environment(spec)
    assert "absolute" in excinfo.value.reason


def test_rejects_empty_allowed_paths() -> None:
    spec = make_spec(allowed_paths=())
    with pytest.raises(PlanRejected):
        plan_environment(spec)


def test_rejects_empty_string_path() -> None:
    spec = make_spec(allowed_paths=("",))
    with pytest.raises(PlanRejected):
        plan_environment(spec)


def test_rejects_packet_id_with_no_slug_characters() -> None:
    spec = make_spec(packet_id="___")
    with pytest.raises(PlanRejected):
        plan_environment(spec)


def test_allowed_paths_are_sorted_and_deduplicated() -> None:
    spec = make_spec(
        allowed_paths=(
            "b/two.py",
            "a/one.py",
            "b/two.py",
            "c/three.py",
        )
    )
    plan = plan_environment(spec)
    assert plan.allowed_paths == ("a/one.py", "b/two.py", "c/three.py")


def test_ordering_is_deterministic_regardless_of_input_order() -> None:
    forward = make_spec(allowed_paths=("a/one.py", "b/two.py", "c/three.py"))
    reverse = make_spec(allowed_paths=("c/three.py", "b/two.py", "a/one.py"))
    assert plan_environment(forward).allowed_paths == plan_environment(
        reverse
    ).allowed_paths


def test_packet_id_slug_lowercases_and_replaces_non_alnum() -> None:
    spec = make_spec(packet_id="TP-DMX-GEC-V2-W03-ISOLATION-CUSTODY-001")
    plan = plan_environment(spec)
    assert plan.worktree_path.endswith(
        "tp-dmx-gec-v2-w03-isolation-custody-001"
    )


def test_plan_is_frozen() -> None:
    plan = plan_environment(make_spec())
    with pytest.raises(Exception):
        plan.branch = "other"  # type: ignore[misc]
