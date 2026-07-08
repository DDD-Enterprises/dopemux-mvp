"""Unit tests for dopemux.mcp.docker_inspect (mocked Docker)."""

from __future__ import annotations

import json
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
