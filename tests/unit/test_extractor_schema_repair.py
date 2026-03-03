"""Unit tests for _attempt_schema_repair_path_items — TP-EXTR-REPAIR-BEFORE-ESCALATE-0001.

Network-free. No env vars. Tests the deterministic repair logic only.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

RUNNER_PATH = (
    Path(__file__).resolve().parents[2]
    / "services"
    / "repo-truth-extractor"
    / "run_extraction_v3.py"
)
SPEC = importlib.util.spec_from_file_location("run_extraction_v3", RUNNER_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)

repair = runner._attempt_schema_repair_path_items
schema_gate = runner.artifacts_pass_schema_gate


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _artifact(items):
    for item in items:
        if "line_range" not in item:
            item["line_range"] = [1, 10]
    return [{"artifact_name": "TEST.json", "payload": {"items": items}}]


# ──────────────────────────────────────────────────────────────────────────────
# Rule 1: single item / single file → must repair
# ──────────────────────────────────────────────────────────────────────────────

def test_single_item_single_file_repaired():
    arts = _artifact([{"id": "foo", "name": "bar"}])
    files = ["src/foo.py"]
    repaired, did, method = repair(arts, "schema_missing_key:path", files)
    assert did is True
    assert method == "single_item_single_file"
    assert repaired[0]["payload"]["items"][0]["path"] == "src/foo.py"


def test_single_item_single_file_empty_path_repaired():
    arts = _artifact([{"id": "foo", "path": ""}])
    files = ["src/foo.py"]
    repaired, did, _ = repair(arts, "schema_empty_key:path", files)
    assert did is True
    assert repaired[0]["payload"]["items"][0]["path"] == "src/foo.py"


def test_single_item_single_file_does_not_alter_existing_valid_path():
    arts = _artifact([{"id": "foo", "path": "already/set.py"}])
    files = ["src/foo.py"]
    repaired, did, _ = repair(arts, "schema_missing_key:path", files)
    # No items need repair — path already set → should return did=True (all filled OK)
    assert repaired[0]["payload"]["items"][0]["path"] == "already/set.py"


def test_single_item_single_file_survives_schema_gate():
    arts = _artifact([{"id": "x", "path": None}])
    files = ["src/x.py"]
    repaired, did, _ = repair(arts, "schema_empty_key:path", files)
    assert did is True
    ok, _ = schema_gate(repaired, ("TEST.json",))
    assert ok


# ──────────────────────────────────────────────────────────────────────────────
# Rule 2: ambiguous basename (two files share same basename) → fail closed
# ──────────────────────────────────────────────────────────────────────────────

def test_ambiguous_basename_fails_closed():
    arts = _artifact([
        {"id": "foo", "name": "foo.py"},
        {"id": "bar", "name": "foo.py"},
    ])
    files = ["pkg_a/foo.py", "pkg_b/foo.py"]  # same basename, two files
    _, did, method = repair(arts, "schema_missing_key:path", files)
    assert did is False


# ──────────────────────────────────────────────────────────────────────────────
# Rule 3: multiple items, partition_files length mismatch (many→many ambiguous)
# ──────────────────────────────────────────────────────────────────────────────

def test_multiple_items_multiple_files_no_match_fails_closed():
    arts = _artifact([
        {"id": "item1"},
        {"id": "item2"},
    ])
    files = ["src/a.py", "src/b.py"]  # no unique mapping available per item
    _, did, _ = repair(arts, "schema_missing_key:path", files)
    assert did is False


# ──────────────────────────────────────────────────────────────────────────────
# Rule 4: id contains basename that uniquely matches
# ──────────────────────────────────────────────────────────────────────────────

def test_id_basename_unique_match_repaired():
    arts = _artifact([{"id": "path/to/utils.py", "description": "something"}])
    # Two files but id uniquely resolves to one
    files = ["src/utils.py", "src/helpers.py"]
    repaired, did, method = repair(arts, "schema_missing_key:path", files)
    assert did is True
    assert repaired[0]["payload"]["items"][0]["path"] == "src/utils.py"
    assert method == "field_or_basename_match"


def test_id_basename_ambiguous_match_fails_closed():
    arts = _artifact([{"id": "utils.py"}])
    files = ["src/utils.py", "tests/utils.py"]  # same basename in id, two candidates
    _, did, _ = repair(arts, "schema_missing_key:path", files)
    assert did is False


# ──────────────────────────────────────────────────────────────────────────────
# Guard: wrong schema_reason → not_applicable, no repair
# ──────────────────────────────────────────────────────────────────────────────

def test_wrong_schema_reason_does_not_repair():
    arts = _artifact([{"id": "x"}])
    _, did, method = repair(arts, "schema_missing_key:id", ["src/x.py"])
    assert did is False
    assert method == "not_applicable"


def test_empty_schema_reason_does_not_repair():
    arts = _artifact([{"id": "x"}])
    _, did, _ = repair(arts, "", ["src/x.py"])
    assert did is False


# ──────────────────────────────────────────────────────────────────────────────
# Guard: no partition_files → no_partition_files
# ──────────────────────────────────────────────────────────────────────────────

def test_no_partition_files_fails_closed():
    arts = _artifact([{"id": "x"}])
    _, did, method = repair(arts, "schema_missing_key:path", [])
    assert did is False
    assert method == "no_partition_files"


# ──────────────────────────────────────────────────────────────────────────────
# Guard: no mutation of original artifacts on failure
# ──────────────────────────────────────────────────────────────────────────────

def test_original_not_mutated_on_ambiguous():
    arts = _artifact([{"id": "foo"}])
    files = ["pkg_a/foo.py", "pkg_b/foo.py"]
    original_id = arts[0]["payload"]["items"][0]["id"]
    repair(arts, "schema_missing_key:path", files)
    assert arts[0]["payload"]["items"][0]["id"] == original_id
    assert "path" not in arts[0]["payload"]["items"][0]


# ──────────────────────────────────────────────────────────────────────────────
# Counters are updated
# ──────────────────────────────────────────────────────────────────────────────

def test_repair_counters_increment():
    before_attempted = runner._REPAIR_COUNTERS["attempted"]
    before_succeeded = runner._REPAIR_COUNTERS["succeeded"]
    arts = _artifact([{"id": "z"}])
    repair(arts, "schema_missing_key:path", ["src/z.py"])
    assert runner._REPAIR_COUNTERS["attempted"] == before_attempted + 1
    assert runner._REPAIR_COUNTERS["succeeded"] == before_succeeded + 1
