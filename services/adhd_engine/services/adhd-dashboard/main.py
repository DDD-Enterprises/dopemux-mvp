"""Compatibility shim for the canonical ADHD dashboard backend."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import uvicorn


def _load_backend_module():
    backend_path = Path(__file__).resolve().parents[3] / "adhd-dashboard" / "backend.py"
    backend_dir = str(backend_path.parent)
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    spec = importlib.util.spec_from_file_location("canonical_adhd_dashboard_backend", backend_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


_backend = _load_backend_module()
app = _backend.app


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8097)
