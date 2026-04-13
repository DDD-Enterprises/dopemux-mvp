from __future__ import annotations

import sys
from pathlib import Path


def _prepend(path: Path) -> None:
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = REPO_ROOT / "services" / "repo-truth-extractor"
SRC_ROOT = REPO_ROOT / "src"

_prepend(SRC_ROOT)
_prepend(SERVICE_ROOT)
