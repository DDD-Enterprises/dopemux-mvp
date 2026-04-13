from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


POLICY_ROOT = Path(__file__).resolve().parent


@lru_cache(maxsize=None)
def load_policy_pack(filename: str) -> dict[str, Any]:
    path = POLICY_ROOT / filename
    return json.loads(path.read_text(encoding="utf-8"))
