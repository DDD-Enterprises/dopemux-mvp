from click.testing import CliRunner
import yaml

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

    init_result = runner.invoke(
        cli,
        ["workflow", "init", "--instance-id", "main", "--max-iterations", "9", "--max-minutes", "45"],
    )
    assert init_result.exit_code == 0, init_result.output
    init_payload = yaml.safe_load(init_result.output)
    workflow_id = init_payload["workflow_id"]

    state_path = workspace / ".dopemux" / "workflows" / workflow_id / "state.json"
    assert state_path.exists()

    monkeypatch.chdir(nested)
    status_result = runner.invoke(cli, ["workflow", "status"])
    assert status_result.exit_code == 0, status_result.output
    status_payload = yaml.safe_load(status_result.output)
    assert status_payload["workflow_id"] == workflow_id
    assert status_payload["phase"] == "brief"

    resume_result = runner.invoke(cli, ["workflow", "resume", "--instance-id", "main"])
    assert resume_result.exit_code == 0, resume_result.output
    resume_payload = yaml.safe_load(resume_result.output)
    assert resume_payload["workflow_id"] == workflow_id

    inspect_result = runner.invoke(cli, ["workflow", "inspect"])
    assert inspect_result.exit_code == 0, inspect_result.output
    inspect_payload = yaml.safe_load(inspect_result.output)
    assert inspect_payload["validation"]["can_stop"] is False
    assert inspect_payload["checkpoints"]["brief"] is None

    cancel_result = runner.invoke(cli, ["workflow", "cancel", "--reason", "operator stop"])
    assert cancel_result.exit_code == 0, cancel_result.output
    cancel_payload = yaml.safe_load(cancel_result.output)
    assert cancel_payload["status"] == "cancelled"


def test_local_workflow_resume_resolves_separate_main_and_worktree_roots(tmp_path, monkeypatch):
    runner = CliRunner()
    main_workspace = tmp_path / "main-workspace"
    worktree_workspace = tmp_path / "secondary-worktree"
    main_workspace.mkdir()
    worktree_workspace.mkdir()
    (main_workspace / "nested").mkdir()
    (worktree_workspace / "nested").mkdir()

    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(main_workspace))
    init_main = runner.invoke(cli, ["workflow", "init", "--workflow-id", "wf-main", "--instance-id", "main"])
    assert init_main.exit_code == 0, init_main.output

    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(worktree_workspace))
    init_worktree = runner.invoke(cli, ["workflow", "init", "--workflow-id", "wf-worktree", "--instance-id", "B"])
    assert init_worktree.exit_code == 0, init_worktree.output

    main_resume = runner.invoke(
        cli,
        ["workflow", "resume", "--path", str(main_workspace / "nested"), "--instance-id", "main"],
    )
    assert main_resume.exit_code == 0, main_resume.output
    assert yaml.safe_load(main_resume.output)["workflow_id"] == "wf-main"

    worktree_resume = runner.invoke(
        cli,
        ["workflow", "resume", "--path", str(worktree_workspace / "nested"), "--instance-id", "B"],
    )
    assert worktree_resume.exit_code == 0, worktree_resume.output
    assert yaml.safe_load(worktree_resume.output)["workflow_id"] == "wf-worktree"
