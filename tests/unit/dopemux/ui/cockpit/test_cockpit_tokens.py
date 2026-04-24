import pytest

from dopemux.ui.cockpit.tokens import (
    ALLOWED_STATUS_CHIPS,
    normalize_status_chip,
    validate_rendered_text,
    validate_status_chip,
)


def test_status_chip_set_is_closed() -> None:
    assert ALLOWED_STATUS_CHIPS == {
        "LIVE",
        "BLOCKER",
        "OVERRIDE",
        "LOGGED",
        "AFTERCARE",
        "EDGE",
    }
    for chip in ALLOWED_STATUS_CHIPS:
        assert validate_status_chip(chip) == chip


def test_unknown_is_rejected_as_direct_status_chip() -> None:
    with pytest.raises(ValueError):
        validate_status_chip("UNKNOWN")


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("DEGRADED", "OVERRIDE"),
        ("FAILED", "BLOCKER"),
        ("BLOCKED", "BLOCKER"),
        ("SYNC", "AFTERCARE"),
        ("UNKNOWN", "EDGE"),
    ],
)
def test_web_and_rte_statuses_normalize_to_closed_chips(source: str, expected: str) -> None:
    assert normalize_status_chip(source) == expected


@pytest.mark.parametrize("text", ["bad → arrow", "bad ⇒ arrow", "bad ➜ arrow"])
def test_unicode_arrows_are_rejected(text: str) -> None:
    with pytest.raises(ValueError):
        validate_rendered_text(text)


@pytest.mark.parametrize("text", ["probably", "magic", "everything looks good", "next-gen"])
def test_forbidden_copy_is_rejected(text: str) -> None:
    with pytest.raises(ValueError):
        validate_rendered_text(text)


def test_unknown_plain_text_after_edge_is_allowed() -> None:
    validate_rendered_text("[EDGE] placeholder mode. UNKNOWN: not wired. NEXT: implement.")
