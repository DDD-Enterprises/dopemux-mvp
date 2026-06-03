from event_normalization import normalize_event, normalize_file_activity, normalize_workspace_switch


def test_normalize_event_accepts_underscored_aliases():
    event_type, payload = normalize_event("progress_updated", {"task_id": "abc", "status": "DONE"})

    assert event_type == "progress.updated"
    assert payload["task_id"] == "abc"
    assert payload["status"] == "DONE"


def test_normalize_workspace_switch_uses_nested_file_activity():
    payload = normalize_workspace_switch({
        "from_workspace": "/tmp/one",
        "to_workspace": "/tmp/two",
        "adhd_context_capture": {
            "file_activity": {
                "files_modified": 3,
            }
        },
    })

    assert payload["from_workspace"] == "/tmp/one"
    assert payload["to_workspace"] == "/tmp/two"
    assert payload["file_activity"] == {
        "has_recent_activity": True,
        "files_modified": 3,
        "seconds_since_last_save": None,
    }
    assert "adhd_context_capture" not in payload


def test_normalize_workspace_switch_strips_content_bearing_top_level_fields():
    payload = normalize_workspace_switch({
        "from_workspace": "one",
        "to_workspace": "two",
        "file_activity": {"files_modified": 1},
        "most_recent_file": "src/private_prompt.py",
        "file_path": "/repo/src/private_prompt.py",
        "prompt": "private prompt text",
        "code": "def leaked(): pass",
        "content": "raw editor content",
    })

    assert payload == {
        "from_workspace": "one",
        "to_workspace": "two",
        "file_activity": {
            "has_recent_activity": True,
            "files_modified": 1,
            "seconds_since_last_save": None,
        },
        "from_app": None,
        "to_app": None,
        "switch_type": None,
        "workspace_id": "two",
    }
    serialized = repr(payload)
    for forbidden in [
        "src/private_prompt.py",
        "/repo/src/private_prompt.py",
        "private prompt text",
        "def leaked",
        "raw editor content",
    ]:
        assert forbidden not in serialized


def test_normalize_file_activity_strips_content_bearing_fields():
    payload = normalize_file_activity({
        "files_modified": 2,
        "seconds_since_last_save": 8,
        "most_recent_file": "src/private_prompt.py",
        "file_path": "/repo/src/private_prompt.py",
        "prompt": "private prompt text",
        "code": "def leaked(): pass",
        "content": "raw editor content",
    })

    assert payload == {
        "has_recent_activity": True,
        "files_modified": 2,
        "seconds_since_last_save": 8,
    }
    serialized = repr(payload)
    for forbidden in [
        "src/private_prompt.py",
        "private prompt text",
        "def leaked",
        "raw editor content",
    ]:
        assert forbidden not in serialized
