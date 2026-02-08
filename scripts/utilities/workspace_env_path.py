#!/usr/bin/env python3
"""Print the per-workspace env file path, creating it if necessary."""

from __future__ import annotations

import argparse
import importlib.util
import sys
import types
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
PACKAGE_NAME = "dopemux"
PACKAGE_PATH = SRC_PATH / PACKAGE_NAME

if PACKAGE_NAME not in sys.modules:
    pkg = types.ModuleType(PACKAGE_NAME)
    pkg.__path__ = [str(PACKAGE_PATH)]  # type: ignore[attr-defined]
    sys.modules[PACKAGE_NAME] = pkg


def _load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {module_name} from {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[assignment]
    return module


workspace_detection = _load_module(
    f"{PACKAGE_NAME}.workspace_detection",
    PACKAGE_PATH / "workspace_detection.py",
)
workspace_env = _load_module(
    f"{PACKAGE_NAME}.workspace_env",
    PACKAGE_PATH / "workspace_env.py",
)

get_workspace_root = workspace_detection.get_workspace_root
ensure_workspace_artifacts = workspace_env.ensure_workspace_artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, help="Workspace path (defaults to auto-detect)")
    parser.add_argument(
        "--set-default",
        action="store_true",
        help="Record this workspace as the global default",
    )
    args = parser.parse_args()

    workspace_path = (args.workspace or get_workspace_root()).expanduser().resolve()
    try:
        artifacts = ensure_workspace_artifacts(workspace_path, set_default=args.set_default)
    except OSError as exc:
        print(f"[error] Unable to persist workspace artifacts: {exc}", file=sys.stderr)
        sys.exit(1)

    print(artifacts.env_path)


if __name__ == "__main__":
    main()
