import json

from workspace_mapper import WorkspaceMapper


def test_workspace_mapper_reads_config_and_matches_case_insensitively(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "app_mappings": {
            "Claude Code": "/tmp/dopemux",
            "Slack": None,
        },
        "default_workspace": "/tmp/default",
    }))

    mapper = WorkspaceMapper(config_path=str(config_path))

    assert mapper.get_workspace("claude code") == "/tmp/dopemux"
    assert mapper.get_workspace("Slack") is None
    assert mapper.get_workspace("Unknown App") == "/tmp/default"


def test_workspace_mapper_partial_match_uses_known_app(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "app_mappings": {
            "Visual Studio Code": "/tmp/project",
        }
    }))

    mapper = WorkspaceMapper(config_path=str(config_path))

    assert mapper.get_workspace("Code") == "/tmp/project"
    assert mapper.is_development_app("Code") is True
