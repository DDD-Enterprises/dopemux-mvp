from __future__ import annotations

from datetime import datetime, timezone

from chatx.imessage.time import to_iso_utc, APPLE_EPOCH


def _parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace('Z', '+00:00'))


def test_seconds_micro_nano_equivalence():
    # 10 million seconds after Apple epoch
    seconds = 10_000_000
    micros = seconds * 1_000_000
    nanos = seconds * 1_000_000_000

    i1 = to_iso_utc(seconds)
    i2 = to_iso_utc(micros)
    i3 = to_iso_utc(nanos)

    assert i1 and i2 and i3
    assert _parse_iso(i1) == _parse_iso(i2) == _parse_iso(i3)


def test_iso_format_and_utc():
    raw = 1_234_567  # seconds
    iso = to_iso_utc(raw)
    assert iso is not None
    dt = _parse_iso(iso)
    assert dt.tzinfo is not None
    assert dt.tzinfo.utcoffset(dt) == timezone.utc.utcoffset(dt)


def test_out_of_range_returns_none():
    # Very large timestamp => well beyond 2100
    huge_nanos = 10**20
    assert to_iso_utc(huge_nanos) is None

