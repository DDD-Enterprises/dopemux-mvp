"""Tests for scripts/ci/clobber_guard.py (the stale-clobber / delete-heavy guard)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_GUARD_PATH = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "clobber_guard.py"
_spec = importlib.util.spec_from_file_location("clobber_guard", _GUARD_PATH)
assert _spec is not None and _spec.loader is not None
cg = importlib.util.module_from_spec(_spec)
sys.modules["clobber_guard"] = cg  # required so @dataclass fields resolve
_spec.loader.exec_module(cg)


# --- classification ---------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "tests/unit/test_mcp_runtime_registry.py",
        "src/pkg/test_thing.py",
        "src/pkg/thing_test.py",
        "services/x/conftest.py",
        "ui/src/components/__tests__/Accessibility.test.tsx",
        "ui/src/foo.spec.ts",
    ],
)
def test_is_test_file_true(path):
    assert cg.is_test_file(path) is True


@pytest.mark.parametrize(
    "path",
    ["src/dopemux/mcp/runtime_registry.py", "ui/src/App.tsx", "README.md", "docs/x.md"],
)
def test_is_test_file_false(path):
    assert cg.is_test_file(path) is False


def test_is_source_file_excludes_tests_and_docs():
    assert cg.is_source_file("src/dopemux/mcp/port_leases.py") is True
    assert cg.is_source_file("ui/src/App.tsx") is True
    assert cg.is_source_file("tests/unit/test_x.py") is False  # a test, not source
    assert cg.is_source_file("docs/guide.md") is False
    assert cg.is_source_file("proof/TP/PROOF.json") is False


# --- evaluate rules ---------------------------------------------------------


def test_clean_pr_passes():
    r = cg.evaluate([], 0, [], allow_intentional=False)
    assert r.exit_code == 0
    assert not r.violations and not r.warnings


def test_large_deletion_by_lines():
    r = cg.evaluate(["a.py"], 1501, [], allow_intentional=False)
    assert r.exit_code == 1
    assert any("LARGE_DELETION" in v for v in r.violations)


def test_large_deletion_by_files():
    files = [f"m{i}.md" for i in range(16)]  # 16 > 15, docs so no codeletion
    r = cg.evaluate(files, 10, [], allow_intentional=False)
    assert r.exit_code == 1
    assert any("LARGE_DELETION" in v for v in r.violations)


def test_source_and_test_codeletion():
    r = cg.evaluate(
        ["src/dopemux/mcp/runtime_registry.py", "tests/unit/test_mcp_runtime_registry.py"],
        50,
        [],
        allow_intentional=False,
    )
    assert r.exit_code == 1
    assert any("SOURCE_AND_TEST_CODELETION" in v for v in r.violations)


def test_pure_test_cleanup_does_not_trip_codeletion():
    # Deleting only test files (no source) is a legit test cleanup — no codeletion flag.
    r = cg.evaluate(["tests/unit/test_old.py"], 30, [], allow_intentional=False)
    assert not any("CODELETION" in v for v in r.violations)
    assert r.exit_code == 0


def test_pure_source_deletion_small_passes():
    # Deleting a small source file with no tests and under thresholds is fine.
    r = cg.evaluate(["src/pkg/dead.py"], 40, [], allow_intentional=False)
    assert r.exit_code == 0


def test_stale_clobber_flag():
    r = cg.evaluate(["src/dopemux/mcp/doctor.py"], 20, ["src/dopemux/mcp/doctor.py"], allow_intentional=False)
    assert r.exit_code == 1
    assert any("STALE_CLOBBER" in v for v in r.violations)


def test_intentional_label_downgrades_to_warnings():
    r = cg.evaluate(
        ["src/x.py", "tests/unit/test_x.py"],
        5000,
        ["src/x.py"],
        allow_intentional=True,
    )
    assert r.exit_code == 0
    assert r.warnings and not r.violations
    assert len(r.warnings) == 3  # large + codeletion + stale, all as warnings


def test_1025_scenario_multiple_violations():
    # The real incident: many files, huge deletions, code+tests together.
    deleted = (
        [f"src/dopemux/mcp/m{i}.py" for i in range(17)]
        + [f"tests/unit/test_mcp_{i}.py" for i in range(17)]
        + [f"proofs/b{i}.json" for i in range(80)]
    )
    r = cg.evaluate(deleted, 27676, [], allow_intentional=False)
    assert r.exit_code == 1
    kinds = " ".join(r.violations)
    assert "LARGE_DELETION" in kinds and "SOURCE_AND_TEST_CODELETION" in kinds
