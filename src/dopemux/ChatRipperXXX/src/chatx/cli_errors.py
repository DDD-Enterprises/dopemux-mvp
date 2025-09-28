from __future__ import annotations

import json
import sys
from pathlib import Path


def redact_path(p: Path | str) -> str:
    try:
        s = str(p)
        home = str(Path.home())
        return s.replace(home, "~")
    except Exception:
        return str(p)


def build_problem(*, code: str, title: str, status: int, detail: str, instance: str | None = None) -> dict:
    base_url = "https://chatx.local/problems/"
    return {
        "type": f"{base_url}{code}",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": instance or "",
        "code": code,
    }


def emit_problem(*, code: str, title: str, status: int, detail: str, instance: str | None = None) -> None:
    problem = build_problem(code=code, title=title, status=status, detail=detail, instance=instance)
    sys.stderr.write(json.dumps(problem) + "\n")

