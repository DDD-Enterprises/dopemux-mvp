"""Docker ownership classification (006R compose secondary evidence)."""

from dopemux.mcp.docker_inspect import DockerContainerInfo, classify_container_ownership


def test_compose_match_dnh_conport():
    c = DockerContainerInfo(
        id="abc",
        name="mcp-conport_dnh_crm_8d6d",
        labels={
            "com.docker.compose.project": "dopemux_dnh_crm_8d6d",
            "com.docker.compose.service": "conport",
        },
        published_ports=[3040, 3041, 4040],
    )
    st = classify_container_ownership(
        c,
        project_root="/Users/hue/code/dNh_CRM",
        workspace_id="/Users/hue/code/dNh_CRM",
        project_id="dnh_crm-9a4e9aa8a329cdd5",
        expected_ports=[3040, 3041, 4040],
        expected_name_substrings=["conport"],
        project_slug_hints=["dNh_CRM", "dnh_crm"],
    )
    assert st == "COMPOSE_MATCH"


def test_main_stack_memory_unlabeled_not_compose_match_for_dnh():
    c = DockerContainerInfo(
        id="xyz",
        name="dopemux-dope-memory-1",
        labels={
            "com.docker.compose.project": "dopemux",
            "com.docker.compose.project.working_dir": "/Users/hue/code/dopemux-mvp",
            "com.docker.compose.service": "dope-memory",
        },
        published_ports=[3020],
    )
    st = classify_container_ownership(
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
