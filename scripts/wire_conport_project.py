#!/usr/bin/env python3
"""Legacy entrypoint that delegates ConPort wiring to packaged dopemux code."""

import argparse
import sys
from pathlib import Path


def _bootstrap_src_path() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    src_path = repo_root / "src"
    if src_path.exists():
        sys.path.insert(0, str(src_path))


def main() -> int:
    parser = argparse.ArgumentParser(description="Wire ConPort MCP to project config")
    parser.add_argument("--project", default=".", help="Project root path")
    parser.add_argument("--instance", help="Dopemux instance ID")
    args = parser.parse_args()

    _bootstrap_src_path()
    from dopemux.conport.wire_project import wire_conport_project

    try:
        config_path = wire_conport_project(project=args.project, instance=args.instance)
        print(f"✅ ConPort wired successfully in {config_path}")
        return 0
    except Exception as exc:
        print(f"❌ Error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
