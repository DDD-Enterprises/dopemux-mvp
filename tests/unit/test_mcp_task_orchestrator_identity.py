"""Unit tests for Task Orchestrator fixed-port identity (RUNTIME-005)."""

from __future__ import annotations

from pathlib import Path

from dopemux.mcp.task_orchestrator_identity import (
    TOIdentity,
    evaluate_fixed_port_state,
    match_target,
    merge_identity_sources,
    probe_http_info,
    probe_wrapper_metadata,
    write_wrapper_metadata,
)


def test_match_ok():
    obs = TOIdentity(project_id="dNh_CRM", project_root="/Users/hue/code/dNh_CRM")
    assert (
        match_target(obs, project_id="dNh_CRM", project_root="/Users/hue/code/dNh_CRM")
        == "OK"
    )


def test_match_wrong_project():
    obs = TOIdentity(
        project_id="dopemux-mvp", project_root="/Users/hue/code/dopemux-mvp"
    )
    assert (
        match_target(obs, project_id="dNh_CRM", project_root="/Users/hue/code/dNh_CRM")
        == "WRONG_PROJECT"
    )


def test_match_unknown_without_proof():
    assert match_target(None, project_id="x", project_root="/p") == "UNKNOWN"
    assert (
        match_target(TOIdentity(port=7890), project_id="x", project_root="/p")
        == "UNKNOWN"
    )


def test_match_conflict_id_ok_root_diff():
    obs = TOIdentity(project_id="dNh_CRM", project_root="/other/path")
    assert (
        match_target(obs, project_id="dNh_CRM", project_root="/Users/hue/code/dNh_CRM")
        == "CONFLICT"
    )


def test_port_only_never_ok():
    ev = evaluate_fixed_port_state(
        port=7890,
        target_project_id="dNh_CRM",
        target_project_root="/Users/hue/code/dNh_CRM",
        listening=True,
        skip_http=True,
        for_start=True,
    )
    assert ev.match == "UNKNOWN"
    assert ev.start_allowed is False
    assert ev.start_block_code == "TASK_ORCHESTRATOR_START_BLOCKED_UNKNOWN_OWNER"
    codes = {f["code"] for f in ev.findings}
    assert "TASK_ORCHESTRATOR_PROJECT_IDENTITY_UNKNOWN" in codes


def test_free_port_start_allowed():
    ev = evaluate_fixed_port_state(
        port=7890,
        target_project_id="dNh_CRM",
        target_project_root="/Users/hue/code/dNh_CRM",
        listening=False,
        for_start=True,
    )
    assert ev.match == "FREE"
    assert ev.start_allowed is True
    assert any(f["code"] == "TASK_ORCHESTRATOR_FIXED_PORT_FREE" for f in ev.findings)


def test_same_project_ok():
    ident = TOIdentity(
        project_id="dNh_CRM",
        project_root="/Users/hue/code/dNh_CRM",
        source="docker_labels",
        confidence="HIGH",
        evidence=["c1"],
    )
    ev = evaluate_fixed_port_state(
        port=7890,
        target_project_id="dNh_CRM",
        target_project_root="/Users/hue/code/dNh_CRM",
        listening=True,
        docker_identity=ident,
        skip_http=True,
        for_start=True,
    )
    assert ev.match == "OK"
    assert ev.start_allowed is True
    assert any(
        f["code"] == "TASK_ORCHESTRATOR_PROJECT_IDENTITY_OK" for f in ev.findings
    )


def test_wrong_project_blocks_start():
    ident = TOIdentity(
        project_id="dopemux-mvp",
        project_root="/Users/hue/code/dopemux-mvp",
        source="docker_labels",
        confidence="HIGH",
    )
    ev = evaluate_fixed_port_state(
        port=7890,
        target_project_id="dNh_CRM",
        target_project_root="/Users/hue/code/dNh_CRM",
        listening=True,
        docker_identity=ident,
        skip_http=True,
        for_start=True,
    )
    assert ev.match == "WRONG_PROJECT"
    assert ev.start_allowed is False
    assert ev.start_block_code == "TASK_ORCHESTRATOR_START_BLOCKED_WRONG_PROJECT"
    assert any(
        f["code"] == "TASK_ORCHESTRATOR_WRONG_PROJECT_RUNTIME" for f in ev.findings
    )


def test_source_conflict():
    a = TOIdentity(project_id="a", project_root="/a", source="http_info")
    b = TOIdentity(project_id="b", project_root="/b", source="docker_labels")
    merged, findings = merge_identity_sources([a, b])
    assert merged is None
    assert any(
        f["code"] == "TASK_ORCHESTRATOR_RUNTIME_METADATA_CONFLICT" for f in findings
    )


def test_wrapper_metadata_roundtrip(tmp_path: Path):
    ident = TOIdentity(
        project_id="dNh_CRM",
        project_root="/Users/hue/code/dNh_CRM",
        worktree_root="/Users/hue/code/dNh_CRM",
        instance_id="8d6d",
        source="wrapper_metadata",
    )
    path = write_wrapper_metadata(ident, base=tmp_path)
    assert path is not None
    loaded = probe_wrapper_metadata(instance_id="8d6d", base=tmp_path)
    assert loaded is not None
    assert loaded.project_root == "/Users/hue/code/dNh_CRM"
    assert loaded.source == "wrapper_metadata"


def test_write_metadata_refuses_other_project(tmp_path: Path):
    a = TOIdentity(
        project_id="a",
        project_root="/a",
        instance_id="x",
    )
    write_wrapper_metadata(a, base=tmp_path)
    b = TOIdentity(project_id="b", project_root="/b", instance_id="x")
    try:
        write_wrapper_metadata(b, base=tmp_path)
        raised = False
    except RuntimeError:
        raised = True
    assert raised


def test_http_info_opener():
    def opener(url: str):
        return {
            "identity": {
                "project_id": "dNh_CRM",
                "project_root": "/Users/hue/code/dNh_CRM",
            }
        }

    ident = probe_http_info(7890, opener=opener)
    assert ident is not None
    assert ident.project_id == "dNh_CRM"
    assert ident.source == "http_info"


def test_dry_run_metadata_no_write(tmp_path: Path):
    ident = TOIdentity(project_id="a", project_root="/a", instance_id="z")
    assert write_wrapper_metadata(ident, base=tmp_path, dry_run=True) is None
    assert not list(tmp_path.rglob("*.json"))


def test_wrapper_metadata_alone_not_live_proof(tmp_path: Path):
    """Occupied port + wrapper metadata only must stay UNKNOWN (P1)."""
    write_wrapper_metadata(
        TOIdentity(
            project_id="dNh_CRM",
            project_root="/Users/hue/code/dNh_CRM",
            instance_id="8d6d",
            source="wrapper_metadata",
        ),
        base=tmp_path,
    )
    ev = evaluate_fixed_port_state(
        port=7890,
        target_project_id="dNh_CRM",
        target_project_root="/Users/hue/code/dNh_CRM",
        target_instance_id="8d6d",
        listening=True,
        skip_http=True,
        metadata_base=tmp_path,
        for_start=True,
    )
    assert ev.match == "UNKNOWN"
    assert ev.start_allowed is False
    codes = {f["code"] for f in ev.findings}
    assert "TASK_ORCHESTRATOR_WRAPPER_METADATA_NOT_LIVE" in codes
    assert "TASK_ORCHESTRATOR_PROJECT_IDENTITY_UNKNOWN" in codes


def test_wrapper_metadata_corroborates_live_docker(tmp_path: Path):
    """Wrapper metadata may merge when live Docker proof already exists."""
    write_wrapper_metadata(
        TOIdentity(
            project_id="dNh_CRM",
            project_root="/Users/hue/code/dNh_CRM",
            instance_id="8d6d",
            source="wrapper_metadata",
        ),
        base=tmp_path,
    )
    docker_ident = TOIdentity(
        project_id="dNh_CRM",
        project_root="/Users/hue/code/dNh_CRM",
        source="docker_labels",
        confidence="HIGH",
        evidence=["c1"],
    )
    ev = evaluate_fixed_port_state(
        port=7890,
        target_project_id="dNh_CRM",
        target_project_root="/Users/hue/code/dNh_CRM",
        target_instance_id="8d6d",
        listening=True,
        docker_identity=docker_ident,
        skip_http=True,
        metadata_base=tmp_path,
        for_start=True,
    )
    assert ev.match == "OK"
    assert ev.start_allowed is True
