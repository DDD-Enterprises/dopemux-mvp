#!/usr/bin/env python3
"""Compatibility entrypoint for packaged PR review settlement."""

from dopemux_pr_steward.review_settlement import main


if __name__ == "__main__":
    raise SystemExit(main())
