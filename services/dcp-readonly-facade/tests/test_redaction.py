"""Redaction: absolute paths + secret patterns, including nested structures."""

from __future__ import annotations

from dcp_facade import redaction as R


def test_redact_registered_abs_root():
    clean, changed = R.redact_abs_paths("see /work/proj/file.txt here", ["/work/proj"])
    assert "/work/proj" not in clean
    assert "<redacted-path>" in clean
    assert changed is True


def test_redact_generic_home_path():
    clean, changed = R.redact_abs_paths("at /Users/alice/secret/x", [])
    assert "/Users/alice" not in clean
    assert changed is True


def test_redact_secret_patterns():
    for raw in (
        "key sk-ABCDEFGH12345678",
        "Authorization: Bearer abc.def-123",
        "API_KEY=supersecretvalue",
        "PASSWORD = hunter2hunter2",
        "ghp_0123456789ABCDEFabcdef",
    ):
        clean, changed = R.redact_secrets(raw)
        assert changed is True
        assert "<redacted>" in clean


def test_no_false_change_on_clean_text():
    clean, changed = R.redact_secrets("just some ordinary prose")
    assert changed is False
    assert clean == "just some ordinary prose"


def test_redact_deep_absolute_path_not_in_known_roots():
    clean, changed = R.redact_abs_paths("config at /var/lib/dopemux/secrets/x.yaml", [])
    assert "/var/lib/dopemux" not in clean
    assert changed is True


def test_short_route_like_path_preserved():
    # 2-segment route strings are NOT redacted (avoid over-redacting doc content)
    clean, changed = R.redact_abs_paths("GET /api/decisions returns json", [])
    assert "/api/decisions" in clean
    assert changed is False


def test_redact_secret_in_dict_key():
    clean, cats = R.redact_value({"API_KEY=topsecret123456": "v"}, [])
    assert R.SECRETS in cats
    assert "topsecret123456" not in str(clean)


def test_redact_value_walks_nested_and_reports_categories():
    payload = {
        "path": "/Users/bob/ws/code.py",
        "items": ["normal", "token=abcdef12345"],
        "nested": {"k": "Bearer zzz.yyy"},
        "count": 7,
    }
    clean, cats = R.redact_value(payload, ["/Users/bob/ws"])
    assert R.ABS_PATHS in cats
    assert R.SECRETS in cats
    assert "/Users/bob" not in str(clean)
    assert "abcdef12345" not in str(clean)
    assert clean["count"] == 7  # non-strings untouched
