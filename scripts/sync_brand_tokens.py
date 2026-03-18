#!/usr/bin/env python3
"""Brand token sync validator.

Reads theme.py as source of truth, validates dopemux.tcss and theme.ts match.
Exit 0 = all synced, Exit 1 = drift detected.

Usage:
    python scripts/sync_brand_tokens.py
"""

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def extract_python_constants(path: Path) -> dict[str, str]:
    """Extract color hex constants from theme.py."""
    constants = {}
    source = path.read_text()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                    val = node.value.value
                    if isinstance(val, str) and val.startswith("#") and len(val) == 7:
                        constants[target.id] = val.upper()
    return constants


def extract_tcss_variables(path: Path) -> dict[str, str]:
    """Extract $variable: #hex from dopemux.tcss."""
    variables = {}
    for line in path.read_text().splitlines():
        m = re.match(r'\s*\$(\w[\w-]*):\s*(#[0-9a-fA-F]{6})', line)
        if m:
            variables[m.group(1)] = m.group(2).upper()
    return variables


def extract_ts_tokens(path: Path) -> dict[str, str]:
    """Extract key: '#hex' from theme.ts brandTokens.colors."""
    tokens = {}
    for line in path.read_text().splitlines():
        m = re.search(r"(\w+):\s*['\"](#[0-9a-fA-F]{6})['\"]", line)
        if m:
            tokens[m.group(1)] = m.group(2).upper()
    return tokens


# Expected mappings: python_const -> tcss_var
PYTHON_TO_TCSS = {
    "INK_BLACK": "base",
    "VOID_NAVY": "mantle",
    "RITUAL_CYAN": "blue",
    "SERUM_MINT": "green",
    "GREMLIN_PINK": "pink",
    "AFTERCARE_VIOLET": "mauve",
    "GILT_EDGE": "yellow",
    "SAINT_GOLD": "peach",
    "TEXT_PRIMARY": "text",
}

# Expected mappings: python_const -> ts_key
PYTHON_TO_TS = {
    "INK_BLACK": "inkBlack",
    "VOID_NAVY": "voidNavy",
    "RITUAL_CYAN": "ritualCyan",
    "SERUM_MINT": "serumMint",
    "GREMLIN_PINK": "gremlinPink",
    "AFTERCARE_VIOLET": "aftercareViolet",
    "GILT_EDGE": "giltEdge",
    "SAINT_GOLD": "saintGold",
}


def main() -> int:
    py_path = ROOT / "src/dopemux/ui/theme.py"
    tcss_path = ROOT / "src/dopemux/ui/dopemux.tcss"
    ts_path = ROOT / "ui-dashboard/src/theme.ts"

    py_consts = extract_python_constants(py_path)
    tcss_vars = extract_tcss_variables(tcss_path)
    ts_tokens = extract_ts_tokens(ts_path)

    drift = []

    for py_name, tcss_name in PYTHON_TO_TCSS.items():
        py_val = py_consts.get(py_name)
        tcss_val = tcss_vars.get(tcss_name)
        if py_val and tcss_val and py_val != tcss_val:
            drift.append(f"TCSS drift: {py_name}={py_val} but ${tcss_name}={tcss_val}")

    for py_name, ts_name in PYTHON_TO_TS.items():
        py_val = py_consts.get(py_name)
        ts_val = ts_tokens.get(ts_name)
        if py_val and ts_val and py_val != ts_val:
            drift.append(f"TS drift: {py_name}={py_val} but {ts_name}={ts_val}")

    if drift:
        print("❌ Brand token drift detected:")
        for d in drift:
            print(f"  • {d}")
        return 1
    else:
        print("✅ All brand tokens in sync across theme.py, dopemux.tcss, theme.ts")
        return 0


if __name__ == "__main__":
    sys.exit(main())
