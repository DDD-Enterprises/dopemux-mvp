"""Snapshot entry point for the static cockpit renderer."""

from __future__ import annotations

import argparse
import sys

from .render import render_snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m dopemux.ui.cockpit")
    parser.add_argument("--snapshot", required=True, help="Snapshot size: 120x40, 100x32, or 80x24.")
    args = parser.parse_args(argv)
    sys.stdout.write(render_snapshot(args.snapshot))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
