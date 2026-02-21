from __future__ import annotations

import sqlite3
import importlib.util
from pathlib import Path


def _load_server_module():
    root = Path(__file__).resolve().parents[2]
    module_path = root / "services" / "webhook_receiver" / "server.py"
    spec = importlib.util.spec_from_file_location("webhook_receiver_server", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_insert_webhook_event_is_idempotent(tmp_path: Path) -> None:
    server = _load_server_module()
    db_path = tmp_path / "events.db"
    server.init_db(db_path)
    payload = {
        "id": "evt_abc",
        "type": "response.completed",
        "created_at": 123,
        "data": {
            "id": "resp_123",
            "metadata": {
                "run_id": "run_1",
                "phase": "D",
                "step_id": "D2",
                "partition_id": "D_P0001",
            },
        },
    }

    first = server.insert_webhook_event(db_path, "wh_1", payload)
    second = server.insert_webhook_event(db_path, "wh_1", payload)

    assert first is True
    assert second is False

    with sqlite3.connect(db_path) as conn:
        webhook_count = conn.execute("select count(*) from webhook_events").fetchone()[0]
        run_event_count = conn.execute("select count(*) from run_events").fetchone()[0]
    assert webhook_count == 1
    assert run_event_count == 1
