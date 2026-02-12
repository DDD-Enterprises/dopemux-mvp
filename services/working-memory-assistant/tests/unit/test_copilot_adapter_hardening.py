from pathlib import Path

from dopemux.memory.adapters.copilot import CopilotCaptureAdapter, _normalize_ts


def test_timestamp_normalization_naive():
    ts = _normalize_ts("2026-02-11T12:00:00")
    assert ts.endswith("+00:00")


def test_timestamp_missing_returns_none():
    ts = _normalize_ts(None)
    assert ts is None


def test_stats_skip_event_without_timestamp(monkeypatch, tmp_path):
    session_id = "sess-no-ts"
    session_dir = tmp_path / session_id
    session_dir.mkdir(parents=True)
    (session_dir / "events.jsonl").write_text("", encoding="utf-8")

    class _FakeParser:
        def __init__(self, _path: str):
            pass

        def parse_events(self, since=None):
            return [
                {
                    "id": "cop-evt-0",
                    "type": "user.message",
                    # timestamp intentionally omitted
                }
            ]

    monkeypatch.setattr("dopemux.memory.adapters.copilot.JSONLParser", _FakeParser)
    monkeypatch.setattr(
        "dopemux.memory.adapters.copilot.EventTypeMapper.map_event_type",
        lambda _event_type: "assistant.message",
    )
    monkeypatch.setattr(
        "dopemux.memory.adapters.copilot.EventTypeMapper.extract_payload",
        lambda _event: {"text": "silence"},
    )

    def _assert_not_called(*args, **kwargs):
        raise AssertionError("emit_capture_event should not be invoked for invalid ts")

    monkeypatch.setattr(
        "dopemux.memory.adapters.copilot.emit_capture_event",
        _assert_not_called,
    )

    adapter = CopilotCaptureAdapter(repo_root=Path(tmp_path), copilot_session_dir=tmp_path)
    stats = adapter.ingest_session(session_id=session_id)

    assert stats["errors"] == 1
    assert stats["skipped"] == 0
    assert stats["inserted"] == 0
    assert stats["deduplicated"] == 0


def test_stats_separates_errors_from_skipped(monkeypatch, tmp_path):
    session_id = "sess-1"
    session_dir = tmp_path / session_id
    session_dir.mkdir(parents=True)
    (session_dir / "events.jsonl").write_text("", encoding="utf-8")

    class _FakeParser:
        def __init__(self, _path: str):
            pass

        def parse_events(self, since=None):
            return [
                {
                    "id": "cop-evt-1",
                    "type": "user.message",
                    "timestamp": "2026-02-11T12:00:00",
                }
            ]

    monkeypatch.setattr("dopemux.memory.adapters.copilot.JSONLParser", _FakeParser)
    monkeypatch.setattr(
        "dopemux.memory.adapters.copilot.EventTypeMapper.map_event_type",
        lambda _event_type: "assistant.message",
    )
    monkeypatch.setattr(
        "dopemux.memory.adapters.copilot.EventTypeMapper.extract_payload",
        lambda _event: {"text": "hello"},
    )

    def _raise_emit(*args, **kwargs):
        raise RuntimeError("emit failed")

    monkeypatch.setattr("dopemux.memory.adapters.copilot.emit_capture_event", _raise_emit)

    adapter = CopilotCaptureAdapter(repo_root=Path(tmp_path), copilot_session_dir=tmp_path)
    stats = adapter.ingest_session(session_id=session_id)

    assert stats["errors"] == 1
    assert stats["skipped"] == 0
