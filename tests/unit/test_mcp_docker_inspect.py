"""Unit tests for dopemux.mcp.docker_inspect (mocked Docker + 006R compose)."""

from __future__ import annotations

import json
import subprocess
from types import SimpleNamespace

from dopemux.mcp import docker_inspect as di


def test_parse_docker_ps_json_lines():
    rows = [
        {
            "ID": "abc123456789",
            "Names": "mcp-conport_dnh",
            "Image": "conport:latest",
            "Status": "Up 2 hours",
            "Ports": "0.0.0.0:3041->3005/tcp",
            "Labels": "dopemux.project_root=/Users/hue/code/dNh_CRM,dopemux.workspace_id=/Users/hue/code/dNh_CRM",
        }
    ]
    text = "\n".join(json.dumps(r) for r in rows)
    containers = di.parse_docker_ps_json_lines(text)
    assert len(containers) == 1
    c = containers[0]
    assert c.name == "mcp-conport_dnh"
    assert 3041 in c.published_ports
    assert c.labels["dopemux.project_root"] == "/Users/hue/code/dNh_CRM"


def test_parse_empty_stdout():
    assert di.parse_docker_ps_json_lines("") == []
    assert di.parse_docker_ps_json_lines("\n\n") == []


def test_parse_malformed_json_skipped():
    good = json.dumps(
        {
            "ID": "deadbeef0001",
            "Names": "ok",
            "Ports": "127.0.0.1:3020->3020/tcp",
            "Labels": "",
        }
    )
    text = "not-json\n" + good + "\n{broken"
    containers = di.parse_docker_ps_json_lines(text)
    assert len(containers) == 1
    assert containers[0].name == "ok"
    assert 3020 in containers[0].published_ports


def test_parse_labels_absent_and_ports_absent():
    row = {"ID": "abc", "Names": "bare"}
    containers = di.parse_docker_ps_json_lines(json.dumps(row))
    assert len(containers) == 1
    assert containers[0].labels == {}
    assert containers[0].published_ports == []


def test_parse_multiple_containers():
    rows = [
        {"ID": "1", "Names": "a", "Ports": "0.0.0.0:1->1/tcp", "Labels": ""},
        {"ID": "2", "Names": "b", "Ports": "0.0.0.0:2->2/tcp", "Labels": "k=v"},
    ]
    containers = di.parse_docker_ps_json_lines("\n".join(json.dumps(r) for r in rows))
    assert len(containers) == 2
    assert {c.name for c in containers} == {"a", "b"}


def test_docker_unavailable_when_binary_missing(monkeypatch):
    monkeypatch.setattr(di.shutil, "which", lambda _: None)
    result = di.inspect_running_containers()
    assert result.available is False
    assert "docker" in (result.error or "").lower()


def test_docker_unavailable_on_nonzero_exit():
    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="Cannot connect to Docker daemon")

    result = di.inspect_running_containers(runner=fake_run)
    assert result.available is False
    assert "Docker" in (result.error or "") or "Cannot" in (result.error or "")


def test_docker_unavailable_on_timeout():
    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="docker ps", timeout=1)

    result = di.inspect_running_containers(runner=fake_run)
    assert result.available is False
    assert "timed out" in (result.error or "").lower()


def test_docker_empty_healthy_stdout():
    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    result = di.inspect_running_containers(runner=fake_run)
    assert result.available is True
    assert result.containers == []


def test_classify_labeled_match():
    c = di.DockerContainerInfo(
        id="1",
        name="mcp-conport",
        labels={
            "dopemux.project_root": "/proj/a",
            "dopemux.workspace_id": "/proj/a",
        },
        published_ports=[3041],
    )
    status = di.classify_container_ownership(
        c,
        project_root="/proj/a",
        workspace_id="/proj/a",
        project_id="a-hash",
        expected_ports=[3041],
        expected_name_substrings=["conport"],
    )
    assert status == "MATCH"


def test_classify_wrong_project():
    c = di.DockerContainerInfo(
        id="1",
        name="mcp-conport",
        labels={
            "dopemux.project_root": "/proj/other",
            "dopemux.workspace_id": "/proj/other",
        },
        published_ports=[3041],
    )
    status = di.classify_container_ownership(
        c,
        project_root="/proj/a",
        workspace_id="/proj/a",
        project_id="a-hash",
        expected_ports=[3041],
    )
    assert status == "WRONG_PROJECT"


def test_classify_unlabeled_matching_port():
    """Port-only / name evidence never proves ownership (UNLABELED)."""
    c = di.DockerContainerInfo(
        id="1",
        name="mcp-conport",
        labels={},
        published_ports=[3041],
    )
    status = di.classify_container_ownership(
        c,
        project_root="/proj/a",
        workspace_id="/proj/a",
        project_id="a-hash",
        expected_ports=[3041],
        expected_name_substrings=["conport"],
    )
    assert status == "UNLABELED"


def test_classify_port_only_no_name_hint():
    c = di.DockerContainerInfo(
        id="1",
        name="random-service",
        labels={},
        published_ports=[3041],
    )
    status = di.classify_container_ownership(
        c,
        project_root="/proj/alpha_crm",
        workspace_id="/proj/alpha_crm",
        project_id="alpha_crm-deadbeef",
        expected_ports=[3041],
        expected_name_substrings=["conport"],
        project_slug_hints=["alpha_crm"],
    )
    # Port evidence alone must never become COMPOSE_MATCH ownership proof
    assert status == "UNLABELED"


def test_find_containers_by_port_and_name():
    docker = di.DockerInspectResult(
        available=True,
        containers=[
            di.DockerContainerInfo(
                id="1",
                name="random",
                published_ports=[9999],
            ),
            di.DockerContainerInfo(
                id="2",
                name="mcp-conport_x",
                published_ports=[3041],
            ),
        ],
    )
    found = di.find_containers_for_service(
        docker,
        service_name="conport",
        expected_ports=[3041],
        name_hints=["conport"],
    )
    assert len(found) == 1
    assert found[0].name == "mcp-conport_x"


def test_no_matching_container():
    docker = di.DockerInspectResult(
        available=True,
        containers=[
            di.DockerContainerInfo(id="1", name="redis", published_ports=[6379]),
        ],
    )
    found = di.find_containers_for_service(
        docker, service_name="conport", expected_ports=[3041], name_hints=["conport"]
    )
    assert found == []


def test_compose_match_dnh_conport():
    c = di.DockerContainerInfo(
        id="abc",
        name="mcp-conport_dnh_crm_8d6d",
        labels={
            "com.docker.compose.project": "dopemux_dnh_crm_8d6d",
            "com.docker.compose.service": "conport",
        },
        published_ports=[3040, 3041, 4040],
    )
    st = di.classify_container_ownership(
        c,
        project_root="/Users/hue/code/dNh_CRM",
        workspace_id="/Users/hue/code/dNh_CRM",
        project_id="dnh_crm-9a4e9aa8a329cdd5",
        expected_ports=[3040, 3041, 4040],
        expected_name_substrings=["conport"],
        project_slug_hints=["dNh_CRM", "dnh_crm"],
    )
    assert st == "COMPOSE_MATCH"


def test_compose_project_mismatch_not_compose_match():
    c = di.DockerContainerInfo(
        id="abc",
        name="mcp-conport_other",
        labels={
            "com.docker.compose.project": "dopemux_other_proj",
            "com.docker.compose.service": "conport",
        },
        published_ports=[3041],
    )
    st = di.classify_container_ownership(
        c,
        project_root="/Users/hue/code/dNh_CRM",
        workspace_id="/Users/hue/code/dNh_CRM",
        project_id="dnh_crm",
        expected_ports=[3041],
        expected_name_substrings=["conport"],
        project_slug_hints=["dNh_CRM"],
    )
    assert st == "UNLABELED"


def test_main_stack_memory_unlabeled_not_compose_match_for_dnh():
    c = di.DockerContainerInfo(
        id="xyz",
        name="dopemux-dope-memory-1",
        labels={
            "com.docker.compose.project": "dopemux",
            "com.docker.compose.project.working_dir": "/Users/hue/code/dopemux-mvp",
            "com.docker.compose.service": "dope-memory",
        },
        published_ports=[3020],
    )
    st = di.classify_container_ownership(
        c,
        project_root="/Users/hue/code/dNh_CRM",
        workspace_id="/Users/hue/code/dNh_CRM",
        project_id="dNh_CRM",
        expected_ports=[3020],
        expected_name_substrings=["dope-memory"],
        project_slug_hints=["dNh_CRM"],
    )
    # Main stack compose project "dopemux" does not slug-match dNh → UNLABELED
    assert st in {"UNLABELED", "UNKNOWN"}


def test_explicit_labels_outrank_compose_heuristics():
    c = di.DockerContainerInfo(
        id="1",
        name="mcp-conport_dnh_crm_8d6d",
        labels={
            "dopemux.project_root": "/other/project",
            "com.docker.compose.project": "dopemux_dnh_crm_8d6d",
            "com.docker.compose.service": "conport",
        },
        published_ports=[3041],
    )
    st = di.classify_container_ownership(
        c,
        project_root="/Users/hue/code/dNh_CRM",
        workspace_id="/Users/hue/code/dNh_CRM",
        project_id="dnh_crm",
        expected_ports=[3041],
        expected_name_substrings=["conport"],
        project_slug_hints=["dNh_CRM"],
    )
    assert st == "WRONG_PROJECT"
