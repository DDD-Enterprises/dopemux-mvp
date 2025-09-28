from __future__ import annotations

import secrets

from chatx.identity.normalize import _normalize_text, normalize_sender, pseudonymize


def test_normalize_text_phone_and_email():
    assert _normalize_text(" +1 (555) 123-4567 ") in ("+15551234567", "15551234567", "5551234567")
    assert _normalize_text("Friend@Example.COM ") == "friend@example.com"
    assert _normalize_text("  user  name  ") == "user name"


def test_pseudonymize_stable_and_salted():
    salt1 = secrets.token_bytes(32)
    salt2 = secrets.token_bytes(32)
    t = "friend@example.com"
    pid1 = pseudonymize(t, salt1)
    pid1_again = pseudonymize(t, salt1)
    pid2 = pseudonymize(t, salt2)

    assert pid1 == pid1_again
    assert pid1 != pid2
    assert pid1.startswith("pid_")
    assert len(pid1) > 8


def test_normalize_sender_api():
    salt = secrets.token_bytes(32)
    out = normalize_sender("Friend", salt)
    assert out["sender_display"] == "Friend"
    assert out["sender_id"].startswith("pid_")

