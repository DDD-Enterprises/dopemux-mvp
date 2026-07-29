from tools.pr_steward.classifier import _known_author


def test_trusted_app_bare_login_matches_bot_roster_entry():
    known = {"ddd-release-gate[bot]", "hu3mann"}
    assert _known_author("ddd-release-gate", "NONE", known, set()) is True
    assert _known_author("ddd-release-gate[bot]", "NONE", known, set()) is True


def test_human_does_not_match_bot_roster_by_bare_invention():
    known = {"other[bot]"}
    assert _known_author("other", "NONE", known, set()) is True
    assert _known_author("unrelated", "NONE", known, set()) is False
