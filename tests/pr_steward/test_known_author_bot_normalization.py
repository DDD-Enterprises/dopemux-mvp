from __future__ import annotations

from tools.pr_steward.classifier import _known_author, _normalize_bot_login


def test_normalize_bot_login_strips_bot_suffix():
    assert _normalize_bot_login("chatgpt-codex-connector[bot]") == "chatgpt-codex-connector"


def test_normalize_bot_login_is_noop_for_non_bot_login():
    assert _normalize_bot_login("hu3mann") == "hu3mann"


def test_known_author_matches_bot_suffixed_variant_of_roster_entry():
    known_reviewers = {"chatgpt-codex-connector"}
    assert _known_author(
        "chatgpt-codex-connector[bot]", None, known_reviewers, set()
    )


def test_known_author_matches_bare_variant_of_bot_suffixed_roster_entry():
    known_reviewers = {"chatgpt-codex-connector[bot]"}
    assert _known_author("chatgpt-codex-connector", None, known_reviewers, set())


def test_known_author_still_rejects_unknown_login():
    known_reviewers = {"chatgpt-codex-connector"}
    assert not _known_author("random-user[bot]", None, known_reviewers, set())
