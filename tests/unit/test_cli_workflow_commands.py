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

