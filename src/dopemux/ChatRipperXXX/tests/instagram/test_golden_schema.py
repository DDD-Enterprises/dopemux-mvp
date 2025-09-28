from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from chatx.instagram.extract import extract_messages_from_zip
from chatx.utils.json_output import write_messages_with_validation
from tests.fixtures.instagram import (
    create_instagram_zip_fixture,
    get_expected_instagram_messages,
)


def test_instagram_zip_golden_and_schema(tmp_path: Path) -> None:
    zip_path = create_instagram_zip_fixture(tmp_path)
    messages = extract_messages_from_zip(
        zip_path, include_threads_with=["Me"], me_username="Me"
    )
    actual = [m.model_dump(exclude={"source_ref", "source_meta"}, mode="json") for m in messages]
    expected = get_expected_instagram_messages()

    assert len(actual) == len(expected)
    for msg_dict, exp in zip(actual, expected, strict=False):
        assert msg_dict["msg_id"] == exp["msg_id"]
        assert msg_dict["conv_id"] == exp["conv_id"]
        assert msg_dict["platform"] == exp["platform"]
        assert msg_dict["timestamp"] == exp["timestamp"]
        assert msg_dict["sender"] == exp["sender"]
        assert msg_dict["sender_id"] == exp["sender_id"]
        assert msg_dict["is_me"] == exp["is_me"]
        assert msg_dict["text"] == exp["text"]
        assert msg_dict["reply_to_msg_id"] == exp["reply_to_msg_id"]
        assert len(msg_dict["reactions"]) == len(exp["reactions"])
        for r_act, r_exp in zip(msg_dict["reactions"], exp["reactions"], strict=False):
            assert r_act["from_"] == r_exp["from"]
            assert r_act["kind"] == r_exp["kind"]
            assert r_act["ts"] == r_exp["ts"]
        assert len(msg_dict["attachments"]) == len(exp["attachments"])
        for a_act, a_exp in zip(msg_dict["attachments"], exp["attachments"], strict=False):
            assert a_act["type"] == a_exp["type"]
            assert a_act["filename"] == a_exp["filename"]

    schema = json.load(open(Path("schemas/message.schema.json"), encoding="utf-8"))
    for msg in messages:
        jsonschema.validate(msg.model_dump(mode="json", by_alias=True), schema)

    out_file = tmp_path / "instagram_messages.json"
    write_messages_with_validation(messages, out_file)
    data = json.load(open(out_file, encoding="utf-8"))
    assert data["total_count"] == len(expected)
    for msg in data["messages"]:
        jsonschema.validate(msg, schema)
