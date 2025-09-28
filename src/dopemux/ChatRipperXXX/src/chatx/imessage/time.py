"""Apple epoch → ISO-8601 UTC normalization helpers for iMessage timestamps.

Apple stores message times as seconds or sub-second units since 2001-01-01.
This module converts raw values (seconds, microseconds, nanoseconds) to
RFC 3339/ISO-8601 UTC strings suitable for the Canonical Message schema.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Optional, Union

Number = Union[int, float]

APPLE_EPOCH = datetime(2001, 1, 1, tzinfo=UTC)
LOWER_BOUND = datetime(1999, 1, 1, tzinfo=UTC)
UPPER_BOUND = datetime(2100, 1, 1, tzinfo=UTC)


def to_iso_utc(raw: Optional[Number]) -> Optional[str]:
    """Convert Apple-epoch raw value to ISO-8601 UTC.

    Accepts seconds, microseconds, or nanoseconds since 2001-01-01, depending
    on magnitude. Returns None only when input is None/invalid or the computed
    datetime falls outside safe bounds.
    """
    if raw in (None, 0):
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None

    # Infer units by magnitude
    # < 1e11 -> seconds
    # < 1e15 -> microseconds
    # >= 1e15 -> nanoseconds
    av = abs(value)
    # Prefer explicit divisibility hints near epoch for small magnitudes
    if av >= 1_000_000_000_000_000:
        # definitely nanoseconds
        seconds = value / 1_000_000_000.0
    elif av >= 100_000_000_000_000 and value % 1_000_000_000 == 0:
        # likely nanoseconds (e.g., one day: 86_400 * 1e9)
        seconds = value / 1_000_000_000.0
    elif av >= 1_000_000_000 and value % 1_000_000 == 0:
        # likely microseconds
        seconds = value / 1_000_000.0
    elif av < 100_000_000_000:
        # seconds
        seconds = float(value)
    else:
        # fallback to microseconds for mid-range magnitudes
        seconds = value / 1_000_000.0

    try:
        dt = APPLE_EPOCH + timedelta(seconds=seconds)
    except OverflowError:
        return None

    if dt < LOWER_BOUND or dt > UPPER_BOUND:
        return None

    return dt.isoformat().replace("+00:00", "Z")
