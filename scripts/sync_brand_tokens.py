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
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    # Module-level assignments only — never function/class locals. (build_theme()
    # now defines local hue vars like `teal = "#2FFFF0"`; walking the whole tree
    # would scoop those into the constants dict.)
    for node in tree.body:
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
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r'\s*\$(\w[\w-]*):\s*(#[0-9a-fA-F]{6})', line)
        if m:
            variables[m.group(1)] = m.group(2).upper()
    return variables


def extract_ts_tokens(path: Path) -> dict[str, str]:
    """Extract key: '#hex' from theme.ts brandTokens.colors."""
    tokens = {}
    for line in path.read_text(encoding="utf-8").splitlines():
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

# Semantic status slots (resolved from the DEFAULT theme dict) -> downstream
# names. The PYTHON_TO_* maps above only cover module-level brand constants and
# miss the status slots inside build_theme() — exactly where the status-palette
# cutover had to hand-edit theme.py, dopemux.tcss, and theme.ts in parallel
# (e.g. the danger/red slot). These maps make that class of drift fail closed.
# NOTE on the TS asymmetry: theme.ts has a dedicated semantic `errorRed` token
# but no `successGreen`/`warningYellow` — success/warning are represented by the
# brand tokens `serumMint`/`giltEdge`, so the maps point there by design.
STATUS_SLOT_TO_TCSS = {"error": "red", "success": "green", "warning": "yellow"}
STATUS_SLOT_TO_TS = {"error": "errorRed", "success": "serumMint", "warning": "giltEdge"}
STATUS_SLOT_TO_TS_HEALTH = {"error": "critical", "success": "low", "warning": "high"}


def extract_theme_status_slots() -> dict[str, str]:
    """Resolve the default (mint-mojo) theme and return status slot -> #HEX.

    Fails closed: raises if the theme cannot be imported/built or if any required
    status slot (error/success/warning) is absent, so a broken theme surfaces as
    an error instead of silently passing the drift check.
    """
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        try:
            from src.dopemux.ui.theme import build_theme
        except ModuleNotFoundError:
            src_dir = str(ROOT / "src")
            if src_dir not in sys.path:
                sys.path.insert(0, src_dir)
            from dopemux.ui.theme import build_theme
        theme = build_theme("mint-mojo")
    except Exception as exc:  # fail closed on any import/build failure
        raise RuntimeError(f"could not resolve mint-mojo theme: {exc}") from exc
    slots: dict[str, str] = {}
    for slot in ("error", "success", "warning"):
        style = theme.styles.get(slot)
        if style and style.color and style.color.triplet:
            slots[slot] = style.color.triplet.hex.upper()
    missing = [s for s in ("error", "success", "warning") if s not in slots]
    if missing:
        raise RuntimeError(
            f"mint-mojo theme missing required status slots: {', '.join(missing)}"
        )
    return slots


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

    # Semantic status-slot drift: resolve the default theme and compare its
    # error/success/warning slots against the downstream tcss vars and ts tokens.
    # status_slots is fail-closed (raises if a slot is absent), so slot_val is
    # always present; a MISSING downstream var/token is itself treated as drift.
    status_slots = extract_theme_status_slots()
    for slot, tcss_name in STATUS_SLOT_TO_TCSS.items():
        slot_val = status_slots[slot]
        tcss_val = tcss_vars.get(tcss_name)
        if tcss_val is None:
            drift.append(f"TCSS status drift: theme '{slot}'={slot_val} but ${tcss_name} is missing")
        elif slot_val != tcss_val:
            drift.append(f"TCSS status drift: theme '{slot}'={slot_val} but ${tcss_name}={tcss_val}")
    for slot, ts_name in STATUS_SLOT_TO_TS.items():
        slot_val = status_slots[slot]
        ts_val = ts_tokens.get(ts_name)
        if ts_val is None:
            drift.append(f"TS status drift: theme '{slot}'={slot_val} but {ts_name} is missing")
        elif slot_val != ts_val:
            drift.append(f"TS status drift: theme '{slot}'={slot_val} but {ts_name}={ts_val}")
    # Health block is an optional convenience surface — only checked when present.
    for slot, ts_name in STATUS_SLOT_TO_TS_HEALTH.items():
        slot_val = status_slots[slot]
        ts_val = ts_tokens.get(ts_name)
        if ts_val and slot_val != ts_val:
            drift.append(f"TS health drift: theme '{slot}'={slot_val} but health.{ts_name}={ts_val}")

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
