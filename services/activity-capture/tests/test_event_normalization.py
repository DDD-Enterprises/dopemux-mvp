from event_normalization import normalize_event, normalize_workspace_switch


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
        "most_recent_file": None,
        "seconds_since_last_save": None,
    }
    assert "adhd_context_capture" not in payload
