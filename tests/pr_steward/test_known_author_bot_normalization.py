from __future__ import annotations

from tools.pr_steward.classifier import _known_author, _normalize_bot_login


def test_normalize_bot_login_strips_bot_suffix():
    assert _normalize_bot_login("chatgpt-codex-connector[bot]") == "chatgpt-codex-connector"


def test_normalize_bot_login_strips_app_prefix():
    assert _normalize_bot_login("app/dependabot") == "dependabot"
    assert _normalize_bot_login("app/dependabot[bot]") == "dependabot"


def test_normalize_bot_login_is_noop_for_non_bot_login():
    assert _normalize_bot_login("hu3mann") == "hu3mann"


def test_known_author_matches_app_prefixed_variant_of_roster_entry():
    known_reviewers = {"dependabot[bot]", "dependabot"}
    assert _known_author(
        "app/dependabot", None, known_reviewers, set()
    )


def test_known_author_matches_bot_suffixed_variant_of_roster_entry():
    known_reviewers = {"chatgpt-codex-connector"}
    assert _known_author(
        "chatgpt-codex-connector[bot]", None, known_reviewers, set()
    )


def test_known_author_does_not_match_bare_login_against_bot_suffixed_roster_entry():
    # A roster entry recorded only as "foo[bot]" must not also trust a bare
    # human login "foo" that happens to reclaim the un-suffixed name —
    # normalization is one-directional (candidate only), never applied to the
    # roster itself.
    known_reviewers = {"chatgpt-codex-connector[bot]"}
    assert not _known_author("chatgpt-codex-connector", None, known_reviewers, set())


def test_known_author_matches_bot_suffixed_roster_entry_exactly():
    known_reviewers = {"chatgpt-codex-connector[bot]"}
    assert _known_author("chatgpt-codex-connector[bot]", None, known_reviewers, set())


def test_known_author_still_rejects_unknown_login():
    known_reviewers = {"chatgpt-codex-connector"}
    assert not _known_author("random-user[bot]", None, known_reviewers, set())


def test_known_author_rejects_unknown_app_prefixed_login():
    known_reviewers = {"dependabot"}
    assert not _known_author("app/malicious-app", None, known_reviewers, set())
