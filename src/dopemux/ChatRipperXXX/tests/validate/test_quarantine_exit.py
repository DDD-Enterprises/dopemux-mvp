from __future__ import annotations

import json
from pathlib import Path
from typing import List

import pytest

from chatx.schemas.message import CanonicalMessage, SourceRef


def _make_msg(i: int) -> CanonicalMessage:
    return CanonicalMessage(
        msg_id=f"m{i}",
        conv_id="c1",
        platform="imessage",
        timestamp="2001-01-01T00:00:10Z",
        sender="Me",
        sender_id="me",
        is_me=True,
        text=f"hello {i}",
        reply_to_msg_id=None,
        reactions=[],
        attachments=[],
        source_ref=SourceRef(guid="g1", path="/tmp/chat.db"),
        source_meta={},
    )


def test_quarantine_exit_mixed(monkeypatch, tmp_path: Path) -> None:
    # First row valid, second row invalid according to jsonschema validator
    calls: List[int] = []

    def fake_validate_data(msg: dict, schema_name: str, strict: bool = False):  # type: ignore
        calls.append(1)
        return (True, []) if len(calls) == 1 else (False, ["boom"])

    import chatx.utils.json_output as jo
    monkeypatch.setattr(jo, "validate_data", fake_validate_data)

    from chatx.utils.json_output import write_messages_with_validation

    out = tmp_path / "messages.json"
    valid, invalid = write_messages_with_validation([_make_msg(1), _make_msg(2)], out)

    # One valid written, one quarantined
    assert valid == 1 and invalid == 1
    data = json.loads(out.read_text())
    assert data["total_count"] == 1
    q = tmp_path / "quarantine" / "messages_bad.jsonl"
    assert q.exists()
    assert sum(1 for _ in q.open()) == 1


def test_quarantine_exit_zero_valid(monkeypatch, tmp_path: Path) -> None:
    # All rows invalid → zero valid count and quarantine entries present
    def always_invalid(msg: dict, schema_name: str, strict: bool = False):  # type: ignore
        return False, ["schema error"]

    import chatx.utils.json_output as jo
    monkeypatch.setattr(jo, "validate_data", always_invalid)

    from chatx.utils.json_output import write_messages_with_validation

    out = tmp_path / "messages.json"
    valid, invalid = write_messages_with_validation([_make_msg(1), _make_msg(2)], out)

    assert valid == 0 and invalid == 2
    data = json.loads(out.read_text())
    assert data["total_count"] == 0
    q = tmp_path / "quarantine" / "messages_bad.jsonl"
    assert q.exists()
    assert sum(1 for _ in q.open()) == 2
