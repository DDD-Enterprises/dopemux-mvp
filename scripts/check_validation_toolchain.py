#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from typing import Dict


TOOLS: Dict[str, Dict[str, str]] = {
    "pip_audit": {
        "binary": "pip-audit",
        "install": 'Install repo dev dependencies with `pip install -e ".[dev]"`.',
    },
    "bandit": {
        "binary": "bandit",
        "install": 'Install repo dev dependencies with `pip install -e ".[dev]"`.',
    },
    "semgrep": {
        "binary": "semgrep",
        "install": 'Install repo dev dependencies with `pip install -e ".[dev]"`.',
    },
    "gitleaks": {
        "binary": "gitleaks",
        "install": "Install the external `gitleaks` binary (for example `brew install gitleaks`) and ensure it is on PATH.",
    },
}


def build_report() -> Dict[str, object]:
    tools = {}
    missing = []
    for name, config in TOOLS.items():
        binary = config["binary"]
        resolved = shutil.which(binary)
        present = resolved is not None
        tools[name] = {
            "binary": binary,
            "present": present,
            "resolved_path": resolved,
            "install_guidance": config["install"] if not present else "",
        }
        if not present:
            missing.append(name)
    return {
        "status": "pass" if not missing else "fail",
        "missing_tools": missing,
        "tools": tools,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check local scanner prerequisites for repo-truth-extractor live validation."
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"status={report['status']}")
        for name, info in report["tools"].items():
            status = "present" if info["present"] else "missing"
            print(f"{name}: {status}")
            if info["resolved_path"]:
                print(f"  path={info['resolved_path']}")
            if info["install_guidance"]:
                print(f"  install={info['install_guidance']}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
