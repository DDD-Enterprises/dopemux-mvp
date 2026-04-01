import json

from click.testing import CliRunner

from src.dopemux.cli import cli


class _Response:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)
        self.content = b"{}"

    def json(self):
        return self._payload


def test_workflow_ideas_add_posts_expected_payload(monkeypatch):
    captured = {}

    def _fake_request(method, url, json=None, params=None, timeout=None):
        captured["method"] = method
        captured["url"] = url
        captured["json"] = json
        captured["params"] = params
        captured["timeout"] = timeout
        return _Response(201, {"idea_id": "idea_1"})

    monkeypatch.setattr("requests.request", _fake_request)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "workflow",
            "ideas",
            "add",
            "--title",
            "Idea title",
            "--description",
            "Idea description",
            "--source",
            "brainstorm",
            "--creator",
            "tester",
            "--tag",
            "one",
            "--tag",
            "two",
        ],
    )

    assert result.exit_code == 0, result.output
    assert captured["method"] == "POST"
    assert captured["url"].endswith("/api/workflow/ideas")
    assert captured["json"] == {
        "title": "Idea title",
        "description": "Idea description",
        "source": "brainstorm",
        "creator": "tester",
        "tags": ["one", "two"],
    }


def test_workflow_ideas_promote_posts_sync_flag_and_priority(monkeypatch):
    captured = {}

    def _fake_request(method, url, json=None, params=None, timeout=None):
        captured["method"] = method
        captured["url"] = url
        captured["json"] = json
        return _Response(
            201,
            {"idea_id": "idea_1", "epic_id": "epic_1", "leantime_project_id": None},
        )

    monkeypatch.setattr("requests.request", _fake_request)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "workflow",
            "ideas",
            "promote",
            "idea_1",
            "--no-sync-leantime",
            "--priority",
            "high",
            "--business-value",
            "Faster delivery",
            "--criterion",
            "criterion-a",
            "--tag",
            "roadmap",
        ],
    )

    assert result.exit_code == 0, result.output
    assert captured["method"] == "POST"
    assert captured["url"].endswith("/api/workflow/ideas/idea_1/promote")
    assert captured["json"]["sync_to_leantime"] is False
    assert captured["json"]["priority"] == "high"
    assert captured["json"]["business_value"] == "Faster delivery"
    assert captured["json"]["acceptance_criteria"] == ["criterion-a"]
    assert captured["json"]["tags"] == ["roadmap"]


def test_workflow_epics_list_sends_expected_filters(monkeypatch):
    captured = {}

    def _fake_request(method, url, json=None, params=None, timeout=None):
        captured["method"] = method
        captured["url"] = url
        captured["params"] = params
        return _Response(200, {"count": 0, "epics": []})

    monkeypatch.setattr("requests.request", _fake_request)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "workflow",
            "epics",
            "list",
            "--status",
            "planned",
            "--priority",
            "low",
            "--tag",
            "ops",
            "--limit",
            "7",
        ],
    )

    assert result.exit_code == 0, result.output
    assert captured["method"] == "GET"
    assert captured["url"].endswith("/api/workflow/epics")
    assert captured["params"] == {
        "limit": 7,
        "status": "planned",
        "priority": "low",
        "tag": "ops",
    }


def test_local_workflow_init_status_resume_cancel_and_inspect(tmp_path, monkeypatch):
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    nested = workspace / "src" / "feature"
    nested.mkdir(parents=True)
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(workspace))
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", "main")

    init_result = runner.invoke(
        cli,
        ["workflow", "init", "--max-iterations", "9", "--max-minutes", "45"],
    )
    assert init_result.exit_code == 0, init_result.output
    state_paths = list((workspace / ".dopemux" / "workflows").glob("*/state.json"))
    assert len(state_paths) == 1
    state_path = state_paths[0]
    assert state_path.exists()
    workflow_id = json.loads(state_path.read_text())["workflow_id"]

    monkeypatch.chdir(nested)
    status_result = runner.invoke(cli, ["workflow", "status", "--json-output"])
    assert status_result.exit_code == 0, status_result.output
    status_payload = json.loads(status_result.output)
    assert status_payload["workflow_id"] == workflow_id
    assert status_payload["phase"] == "brief"

    resume_result = runner.invoke(cli, ["workflow", "resume", "--workflow-id", workflow_id])
    assert resume_result.exit_code == 0, resume_result.output
    resumed_state = json.loads(state_path.read_text())
    assert resumed_state["workflow_id"] == workflow_id
    assert resumed_state["status"] == "active"

    inspect_result = runner.invoke(
        cli,
        ["workflow", "inspect", "--workflow-id", workflow_id, "--json-output"],
    )
    assert inspect_result.exit_code == 0, inspect_result.output
    inspect_payload = json.loads(inspect_result.output)
    assert inspect_payload["inspection"]["workflow_id"] == workflow_id
    assert inspect_payload["inspection"]["phase"] == "brief"
    assert inspect_payload["state"]["checkpoints"] == []

    cancel_result = runner.invoke(cli, ["workflow", "cancel", "--workflow-id", workflow_id])
    assert cancel_result.exit_code == 0, cancel_result.output
    cancelled_state = json.loads(state_path.read_text())
    assert cancelled_state["status"] == "cancelled"


def test_local_workflow_resume_resolves_separate_main_and_worktree_roots(tmp_path, monkeypatch):
    runner = CliRunner()
    main_workspace = tmp_path / "main-workspace"
    worktree_workspace = tmp_path / "secondary-worktree"
    main_workspace.mkdir()
    worktree_workspace.mkdir()
    (main_workspace / "nested").mkdir()
    (worktree_workspace / "nested").mkdir()

    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(main_workspace))
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", "main")
    init_main = runner.invoke(cli, ["workflow", "init"])
    assert init_main.exit_code == 0, init_main.output
    main_state_path = next((main_workspace / ".dopemux" / "workflows").glob("*/state.json"))
    main_workflow_id = json.loads(main_state_path.read_text())["workflow_id"]

    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(worktree_workspace))
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", "B")
    init_worktree = runner.invoke(cli, ["workflow", "init"])
    assert init_worktree.exit_code == 0, init_worktree.output
    worktree_state_path = next((worktree_workspace / ".dopemux" / "workflows").glob("*/state.json"))
    worktree_workflow_id = json.loads(worktree_state_path.read_text())["workflow_id"]

    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(main_workspace))
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", "main")
    monkeypatch.chdir(main_workspace / "nested")
    main_resume = runner.invoke(cli, ["workflow", "resume"])
    assert main_resume.exit_code == 0, main_resume.output
    main_status = runner.invoke(cli, ["workflow", "status", "--json-output"])
    assert main_status.exit_code == 0, main_status.output
    assert json.loads(main_status.output)["workflow_id"] == main_workflow_id

    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(worktree_workspace))
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", "B")
    monkeypatch.chdir(worktree_workspace / "nested")
    worktree_resume = runner.invoke(cli, ["workflow", "resume"])
    assert worktree_resume.exit_code == 0, worktree_resume.output
    worktree_status = runner.invoke(cli, ["workflow", "status", "--json-output"])
    assert worktree_status.exit_code == 0, worktree_status.output
    assert json.loads(worktree_status.output)["workflow_id"] == worktree_workflow_id
