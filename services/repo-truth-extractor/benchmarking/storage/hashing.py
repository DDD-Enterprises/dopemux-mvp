from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def stable_json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def hash_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def hash_json(payload: Any) -> str:
    return hash_bytes(stable_json_dumps(payload).encode("utf-8"))


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(8192)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()

