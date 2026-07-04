import json
import re
import sqlite3
from pathlib import Path

import pytest

from dopemux.memory import capture_client as capture_client_module
from dopemux.memory.capture_client import (
    CaptureError,
    emit_capture_event,
    emit_promotable_capture_event,
    resolve_capture_mode,
    resolve_repo_root_strict,
)
from dopemux.pm import writes as pm_writes
from dopemux.pm import api as pm_api
from dopemux.pm.models import PMTaskStatus
from dopemux.pm.api import PMWriteBoundary
from dopemux.pm.writes import PMWriteConfig, pm_log_decision, pm_transition_work_item


REPO_ROOT = Path(__file__).resolve().parents[2]


def _count_events(ledger_path: Path) -> int:
    conn = sqlite3.connect(str(ledger_path))
    try:
        return int(conn.execute("SELECT COUNT(*) FROM raw_activity_events").fetchone()[0])
    finally:
        conn.close()


def _event_payload(ledger_path: Path, event_id: str) -> dict:
    conn = sqlite3.connect(str(ledger_path))
    try:
        row = conn.execute(
            "SELECT payload_json FROM raw_activity_events WHERE id = ?",
            (event_id,),
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    return json.loads(row[0])


def test_plugin_and_cli_modes_share_single_ledger(tmp_path, monkeypatch):
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    plugin = emit_capture_event(
        {
            "event_type": "shell.command",
            "payload": {"command": "echo plugin"},
        },
        mode="plugin",
        repo_root=REPO_ROOT,
    )
    cli = emit_capture_event(
        {
            "event_type": "shell.command",
            "payload": {"command": "echo cli"},
        },
        mode="cli",
        repo_root=REPO_ROOT,
    )

    assert plugin.ledger_path == cli.ledger_path
    assert plugin.ledger_path == ledger_path.resolve()
    assert _count_events(plugin.ledger_path) == 2


def test_redaction_is_applied_consistently(tmp_path, monkeypatch):
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    result = emit_capture_event(
        {
            "event_type": "manual.note",
            "payload": {
                "summary": "test",
                "password": "super-secret",
                "token_line": "Bearer abcdef123456",
            },
        },
        mode="cli",
        repo_root=REPO_ROOT,
    )

    conn = sqlite3.connect(str(result.ledger_path))
    try:
        payload_json = conn.execute(
            "SELECT payload_json FROM raw_activity_events WHERE id = ?", (result.event_id,)
        ).fetchone()[0]
    finally:
        conn.close()

    payload = json.loads(payload_json)
    assert "password" not in payload
    assert payload["token_line"].startswith("[REDACTED")


def test_duplicate_retry_is_ignored(tmp_path, monkeypatch):
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    event = {
        "event_type": "shell.command",
        "source": "cli",
        "ts_utc": "2026-02-08T18:00:00+00:00",
        "payload": {"command": "pytest -q"},
    }

    first = emit_capture_event(event, mode="cli", repo_root=REPO_ROOT)
    second = emit_capture_event(event, mode="cli", repo_root=REPO_ROOT)

    assert first.event_id == second.event_id
    assert first.inserted is True
    assert second.inserted is False
    assert _count_events(first.ledger_path) == 1


def test_promotable_capture_event_rejects_non_allowlisted_type(tmp_path, monkeypatch):
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    with pytest.raises(CaptureError, match="Unsupported promotable"):
        emit_promotable_capture_event(
            "file.saved",
            {"path": "secret.py"},
            source="test",
            mode="cli",
            repo_root=REPO_ROOT,
        )

    assert not ledger_path.exists()


def test_promotable_capture_event_writes_authority_labeled_decision(tmp_path, monkeypatch):
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    result = emit_promotable_capture_event(
        "decision.logged",
        {
            "decision_id": "dec-1",
            "title": "Keep memory planes split",
            "rationale": "ConPort is decision authority; dope-memory is chronicle authority.",
            "authority": "conport",
        },
        source="dopemux.pm",
        mode="cli",
        repo_root=REPO_ROOT,
        emit_event_bus=False,
    )

    payload = _event_payload(ledger_path, result.event_id)
    assert result.event_type == "decision.logged"
    assert payload["authority"] == "conport"
    assert payload["decision_id"] == "dec-1"


def test_promotable_capture_event_accepts_underscore_event_type(tmp_path, monkeypatch):
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    result = emit_promotable_capture_event(
        "decision_logged",
        {
            "decision_id": "dec-underscore",
            "title": "Normalize event type",
            "rationale": "WMA promotion accepts underscore and dotted variants.",
        },
        source="dopemux.pm",
        mode="cli",
        repo_root=REPO_ROOT,
        emit_event_bus=False,
    )

    assert result.event_type == "decision.logged"
    assert _count_events(ledger_path) == 1


def test_raw_activity_event_id_is_primary_key(tmp_path, monkeypatch):
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    emit_capture_event(
        {
            "event_type": "manual.note",
            "payload": {"summary": "pk bootstrap"},
        },
        mode="cli",
        repo_root=REPO_ROOT,
    )

    conn = sqlite3.connect(str(ledger_path))
    try:
        rows = conn.execute("PRAGMA table_info(raw_activity_events)").fetchall()
    finally:
        conn.close()

    by_name = {row[1]: row for row in rows}
    assert "id" in by_name
    assert by_name["id"][5] == 1  # pk column in PRAGMA table_info


def test_deterministic_event_id_changes_with_payload(tmp_path, monkeypatch):
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    event_base = {
        "event_type": "shell.command",
        "source": "cli",
        "ts_utc": "2026-02-08T18:30:00+00:00",
        "payload": {"command": "pytest -q", "arg": "A"},
    }

    first = emit_capture_event(event_base, mode="cli", repo_root=REPO_ROOT)
    second = emit_capture_event(
        {
            **event_base,
            "payload": {"command": "pytest -q", "arg": "B"},
        },
        mode="cli",
        repo_root=REPO_ROOT,
    )

    assert first.event_id != second.event_id


def test_default_ledger_path_is_repo_local(tmp_path):
    repo_root = tmp_path / "repo"
    nested = repo_root / "nested"
    schema_dir = repo_root / "services" / "working-memory-assistant" / "chronicle"
    redactor_dir = repo_root / "services" / "working-memory-assistant" / "promotion"

    (repo_root / ".git").mkdir(parents=True)
    nested.mkdir(parents=True)
    schema_dir.mkdir(parents=True)
    (schema_dir / "migrations").mkdir(parents=True)
    redactor_dir.mkdir(parents=True)

    schema_dir.joinpath("schema.sql").write_text(
        """
CREATE TABLE IF NOT EXISTS raw_activity_events (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  instance_id TEXT NOT NULL,
  session_id TEXT,
  ts_utc TEXT NOT NULL,
  event_type TEXT NOT NULL,
  source TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  redaction_level TEXT NOT NULL,
  ttl_days INTEGER NOT NULL,
  created_at_utc TEXT NOT NULL
);
""".strip()
        + "\n",
        encoding="utf-8",
    )
    redactor_dir.joinpath("redactor.py").write_text(
        """class Redactor:
    def redact_payload(self, payload):
        return dict(payload)
""",
        encoding="utf-8",
    )
    schema_dir.joinpath("sqlite_migrations.py").write_text(
        """
import sqlite3
def apply_chronicle_migrations(conn, **kwargs):
    schema_path = kwargs.get('schema_path')
    if schema_path and schema_path.exists():
        conn.executescript(schema_path.read_text(encoding='utf-8'))
    return []
""",
        encoding="utf-8",
    )

    result = emit_capture_event(
        {
            "event_type": "manual.note",
            "payload": {"summary": "repo local"},
        },
        mode="cli",
        repo_root=repo_root,
    )

    assert result.ledger_path == (repo_root / ".dopemux" / "chronicle.sqlite").resolve()
    assert result.ledger_path.exists()


def test_schema_bootstrap_runs_once_per_ledger(tmp_path, monkeypatch):
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    init_calls = {"count": 0}
    real_initialize_schema = capture_client_module._ensure_schema_initialized

    def _counting_initialize_schema(conn, repo_root, schema_path, migrations_dir, ledger_path):
        ledger_key = str(ledger_path.resolve())
        if ledger_key not in capture_client_module._SCHEMA_READY_LEDGER_PATHS:
            init_calls["count"] += 1
        return real_initialize_schema(conn, repo_root, schema_path, migrations_dir, ledger_path)

    monkeypatch.setattr(
        capture_client_module,
        "_ensure_schema_initialized",
        _counting_initialize_schema,
    )

    emit_capture_event(
        {
            "event_type": "shell.command",
            "payload": {"command": "echo first"},
        },
        mode="cli",
        repo_root=REPO_ROOT,
    )
    emit_capture_event(
        {
            "event_type": "shell.command",
            "payload": {"command": "echo second"},
        },
        mode="cli",
        repo_root=REPO_ROOT,
    )

    assert init_calls["count"] == 1


def test_schema_bootstrap_runs_for_each_distinct_ledger(tmp_path, monkeypatch):
    first_ledger = tmp_path / "a.sqlite"
    second_ledger = tmp_path / "b.sqlite"

    init_calls = {"count": 0}
    real_initialize_schema = capture_client_module._ensure_schema_initialized

    def _counting_initialize_schema(conn, repo_root, schema_path, migrations_dir, ledger_path):
        ledger_key = str(ledger_path.resolve())
        if ledger_key not in capture_client_module._SCHEMA_READY_LEDGER_PATHS:
            init_calls["count"] += 1
        return real_initialize_schema(conn, repo_root, schema_path, migrations_dir, ledger_path)

    monkeypatch.setattr(
        capture_client_module,
        "_ensure_schema_initialized",
        _counting_initialize_schema,
    )

    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(first_ledger))
    emit_capture_event(
        {
            "event_type": "shell.command",
            "payload": {"command": "echo one"},
        },
        mode="cli",
        repo_root=REPO_ROOT,
    )

    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(second_ledger))
    emit_capture_event(
        {
            "event_type": "shell.command",
            "payload": {"command": "echo two"},
        },
        mode="cli",
        repo_root=REPO_ROOT,
    )

    assert init_calls["count"] == 2


def test_repo_root_resolution_is_stable(tmp_path):
    repo = tmp_path / "workspace"
    nested = repo / "a" / "b"
    (repo / ".git").mkdir(parents=True)
    nested.mkdir(parents=True)

    resolved = resolve_repo_root_strict(nested)
    assert resolved == repo.resolve()


def test_capture_fails_closed_outside_repo(tmp_path, monkeypatch):
    non_repo = tmp_path / "outside"
    non_repo.mkdir(parents=True)
    monkeypatch.chdir(non_repo)

    with pytest.raises(CaptureError, match="fails closed"):
        emit_capture_event(
            {
                "event_type": "manual.note",
                "payload": {"summary": "outside repo"},
            },
            mode="cli",
        )


def test_capture_fails_when_schema_dependency_errors(tmp_path, monkeypatch):
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    def _raise_missing_schema(_repo_root):
        raise CaptureError("WMA schema not found: forced test path")

    monkeypatch.setattr(
        capture_client_module,
        "_resolve_wma_schema_path",
        _raise_missing_schema,
    )

    with pytest.raises(CaptureError, match="WMA schema not found"):
        emit_capture_event(
            {
                "event_type": "manual.note",
                "payload": {"summary": "schema failure"},
            },
            mode="cli",
            repo_root=REPO_ROOT,
        )


def test_capture_fails_when_redactor_dependency_errors(tmp_path, monkeypatch):
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    def _raise_missing_redactor(_repo_root):
        raise CaptureError("WMA redactor not found: forced test path")

    monkeypatch.setattr(
        capture_client_module,
        "_load_wma_redactor",
        _raise_missing_redactor,
    )

    with pytest.raises(CaptureError, match="WMA redactor not found"):
        emit_capture_event(
            {
                "event_type": "manual.note",
                "payload": {"summary": "redactor failure"},
            },
            mode="cli",
            repo_root=REPO_ROOT,
        )


def test_event_bus_toggle_paths(tmp_path, monkeypatch):
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    emitted_events: list[dict] = []

    def _record_event(event):
        emitted_events.append(event)

    monkeypatch.setattr(capture_client_module, "_emit_to_event_stream", _record_event)

    # Default false path: env unset and no explicit flag
    monkeypatch.delenv("DOPEMUX_CAPTURE_EMIT_EVENTBUS", raising=False)
    emit_capture_event(
        {
            "event_type": "manual.note",
            "payload": {"summary": "default false"},
        },
        mode="cli",
        repo_root=REPO_ROOT,
    )
    assert emitted_events == []

    # Env-driven true path
    monkeypatch.setenv("DOPEMUX_CAPTURE_EMIT_EVENTBUS", "true")
    emit_capture_event(
        {
            "event_type": "manual.note",
            "payload": {"summary": "env true"},
        },
        mode="cli",
        repo_root=REPO_ROOT,
    )
    assert len(emitted_events) == 1

    # Explicit false overrides env true
    emit_capture_event(
        {
            "event_type": "manual.note",
            "payload": {"summary": "explicit false"},
        },
        mode="cli",
        repo_root=REPO_ROOT,
        emit_event_bus=False,
    )
    assert len(emitted_events) == 1


def test_mode_resolution_explicit_overrides_all(monkeypatch):
    monkeypatch.setenv("DOPEMUX_CAPTURE_MODE", "mcp")
    monkeypatch.setenv("DOPEMUX_CAPTURE_CONTEXT", "plugin")
    monkeypatch.setenv("CLAUDE_SESSION_ID", "session-1")

    assert resolve_capture_mode("cli", repo_root=REPO_ROOT) == "cli"


def test_mode_resolution_env_overrides_config_and_context(monkeypatch):
    monkeypatch.setenv("DOPEMUX_CAPTURE_MODE", "mcp")
    monkeypatch.setenv("DOPEMUX_CAPTURE_CONTEXT", "plugin")

    monkeypatch.setattr(
        capture_client_module,
        "_read_capture_mode_from_project_config",
        lambda _repo_root: "cli",
    )

    assert resolve_capture_mode("auto", repo_root=REPO_ROOT) == "mcp"


def test_mode_resolution_config_overrides_context_and_heuristics(monkeypatch):
    monkeypatch.delenv("DOPEMUX_CAPTURE_MODE", raising=False)
    monkeypatch.setenv("DOPEMUX_CAPTURE_CONTEXT", "plugin")
    monkeypatch.setenv("CLAUDE_SESSION_ID", "session-2")

    monkeypatch.setattr(
        capture_client_module,
        "_read_capture_mode_from_project_config",
        lambda _repo_root: "mcp",
    )

    assert resolve_capture_mode("auto", repo_root=REPO_ROOT) == "mcp"


def test_pm_log_decision_emits_decision_logged_after_conport_write(monkeypatch):
    emitted: list[tuple[str, dict, dict]] = []
    conport_calls: list[tuple] = []

    class ConPort:
        def record_progress(self, *args, **kwargs):
            conport_calls.append((args, kwargs))

    monkeypatch.setattr(
        pm_writes,
        "try_emit_promotable_capture_event",
        lambda event_type, payload, **kwargs: emitted.append((event_type, payload, kwargs)),
    )

    receipt = pm_log_decision(
        PMWriteConfig(
            leantime_client=None,
            orchestrator_client=None,
            conport_client=ConPort(),
            memory_client=None,
            project_id="proj-1",
        ),
        task_id="task-1",
        decision_notes="Use source-event capture instead of hook spam.",
        idempotency_key="idem-1",
    )

    assert receipt.success is True
    assert conport_calls
    assert emitted == [
        (
            "decision.logged",
            {
                "decision_id": "task-1",
                "title": "Decision for task-1",
                "rationale": "Use source-event capture instead of hook spam.",
                "project_id": "proj-1",
                "task_id": "task-1",
                "work_item_id": "task-1",
                "canonical_system": "conport",
                "operation_type": "decision_log",
                "authority": "conport",
            },
            {
                "source": "dopemux.pm",
                "mode": "auto",
                "emit_event_bus": None,
            },
        )
    ]


def test_pm_transition_emits_workflow_and_task_events_after_orchestrator_write(monkeypatch):
    emitted: list[tuple[str, dict, dict]] = []
    transition_calls: list[dict] = []

    class Orchestrator:
        def transition(self, **kwargs):
            transition_calls.append(kwargs)

    monkeypatch.setattr(
        pm_writes,
        "try_emit_promotable_capture_event",
        lambda event_type, payload, **kwargs: emitted.append((event_type, payload, kwargs)),
    )

    receipt = pm_transition_work_item(
        PMWriteConfig(
            leantime_client=None,
            orchestrator_client=Orchestrator(),
            conport_client=None,
            memory_client=None,
            project_id="proj-1",
        ),
        task_id="task-2",
        new_status=PMTaskStatus.DONE,
        reason="implementation merged",
        idempotency_key="idem-2",
        expected_version=4,
    )

    assert receipt.success is True
    assert transition_calls
    assert [event_type for event_type, _payload, _kwargs in emitted] == [
        "workflow.phase_changed",
        "task.completed",
    ]
    assert emitted[0][1]["canonical_system"] == "task-orchestrator"
    assert emitted[0][1]["to_phase"] == "deployment"
    assert emitted[1][1]["status"] == "DONE"
    assert emitted[0][2]["mode"] == "auto"


@pytest.mark.asyncio
async def test_async_pm_transition_maps_done_to_deployment_phase(monkeypatch):
    emitted: list[tuple[str, dict]] = []

    class Orchestrator:
        async def transition_task(self, *_args, **_kwargs):
            return {"success": True}

    monkeypatch.setattr(
        pm_api,
        "emit_pm_promotable_source_event",
        lambda event_type, **kwargs: emitted.append((event_type, kwargs["payload"])),
    )

    boundary = PMWriteBoundary(orchestrator_client=Orchestrator(), project_id="proj-1")
    result = await boundary.pm_transition_work_item("task-3", "done")

    assert result["success"] is True
    workflow_events = [
        payload for event_type, payload in emitted if event_type == "workflow.phase_changed"
    ]
    assert workflow_events[0]["to_phase"] == "deployment"


def test_no_implicit_injection_defaults_in_memory_capture_surfaces():
    files = [
        REPO_ROOT / "src" / "dopemux" / "memory" / "capture_client.py",
        REPO_ROOT / "src" / "dopemux" / "memory" / "global_rollup.py",
        REPO_ROOT / "src" / "dopemux" / "cli.py",
    ]
    pattern = re.compile(r"(auto_?inject|implicit_?inject)\s*=\s*true", re.IGNORECASE)

    for path in files:
        text = path.read_text(encoding="utf-8")
        assert not pattern.search(text), f"implicit injection default detected in {path}"
