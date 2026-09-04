"""Import side-effect isolation tests.

The semantic core must import without provider SDK, socket, filesystem,
environment, credential, subprocess, or network I/O. Two deterministic checks:
an AST import-allowlist sweep over the package source, and a subprocess smoke
import that asserts the working directory remains untouched.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[3] / "src" / "dopemux" / "uag"

STDLIB_ALLOWLIST = {
    "__future__",
    "dataclasses",
    "enum",
    "hashlib",
    "json",
    "re",
    "typing",
}


def _imported_top_levels(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module.split(".")[0])
    return names


def test_package_imports_are_stdlib_only():
    offenders: list[tuple[str, str]] = []
    for path in sorted(PACKAGE_DIR.glob("*.py")):
        imported = _imported_top_levels(path.read_text(encoding="utf-8"))
        bad = imported - STDLIB_ALLOWLIST - {"dopemux"}
        if bad:
            offenders.append((path.name, sorted(bad)))
    assert not offenders, f"non-stdlib imports in package: {offenders}"


def test_import_has_no_filesystem_side_effects(tmp_path):
    # Import in a subprocess with a clean cwd; assert nothing is written there.
    env = dict(os.environ)
    env["PYTHONPATH"] = str(PACKAGE_DIR.parents[1])  # src/
    result = subprocess.run(
        [sys.executable, "-c", "import dopemux.uag"],
        cwd=str(tmp_path),
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert list(tmp_path.iterdir()) == []
