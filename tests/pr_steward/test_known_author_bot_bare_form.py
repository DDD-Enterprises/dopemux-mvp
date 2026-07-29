"""Bare app-login roster entries for APIs that omit the [bot] suffix."""

from tools.pr_steward.classifier import _known_author


def test_explicit_bare_roster_entry_matches_app_api_login():
    """GitHub may harvest app reviews as bare login; list that form explicitly."""
    known = {"ddd-release-gate[bot]", "ddd-release-gate", "hu3mann"}
    assert _known_author("ddd-release-gate", "NONE", known, set()) is True
    assert _known_author("ddd-release-gate[bot]", "NONE", known, set()) is True


def test_bot_suffixed_roster_alone_does_not_trust_bare_login():
    """One-way normalization: roster foo[bot] must not invent trust for bare foo."""
    known = {"other[bot]"}
    assert _known_author("other", "NONE", known, set()) is False
    assert _known_author("other[bot]", "NONE", known, set()) is True
    assert _known_author("unrelated", "NONE", known, set()) is False
