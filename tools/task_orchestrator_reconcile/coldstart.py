from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .resolve import coldstart_report


def build_coldstart_report(conn: sqlite3.Connection, repo_root: Path) -> dict[str, Any]:
    return coldstart_report(conn, repo_root)
