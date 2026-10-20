"""Recovered MP023 regression tests."""

import json
from pathlib import Path

import pytest

from dopemux_pr_merge_specialist.dopetask_bundle_loader import (
    BundleSchemaError,
    DopetaskBundleLoader,
)


def _write(tmp_path: Path, name: str, payload) -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def _write_raw(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


FULL_BUNDLE = {
    "tp_id": "123",
    "pr_id": "77",
    "artifacts": ["a.log", "b.json"],
    "status": "pass",
    "summary": "ok",
    "acceptance_checks": [],
    "validation": {},
    "manifest": {},
}


# ---------------------------------------------------------------------------
# RED on baseline: malformed shapes must raise BundleSchemaError, not
# AttributeError / silently load.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw",
    ["[]", "null", "42", '"just a string"', '["tp_id", "artifacts"]'],
)
def test_non_object_json_raises_schema_error(tmp_path, raw):
    path = _write_raw(tmp_path, "TP-1_PROOF_BUNDLE.json", raw)
    loader = DopetaskBundleLoader(tmp_path)
    with pytest.raises(BundleSchemaError):
        loader.load(path)


@pytest.mark.parametrize("artifacts", ["a.log", {"a": 1}, 3, None, True])
def test_artifacts_wrong_type_raises_schema_error(tmp_path, artifacts):
    path = _write(tmp_path, "TP-1_PROOF_BUNDLE.json", {"tp_id": "1", "artifacts": artifacts})
    loader = DopetaskBundleLoader(tmp_path)
    with pytest.raises(BundleSchemaError, match="artifacts"):
        loader.load(path)


@pytest.mark.parametrize("artifacts", [["a.log", 5], [None], [{"name": "x"}], [["nested"]]])
def test_artifacts_non_string_member_raises_schema_error(tmp_path, artifacts):
    path = _write(tmp_path, "TP-1_PROOF_BUNDLE.json", {"tp_id": "1", "artifacts": artifacts})
    loader = DopetaskBundleLoader(tmp_path)
    with pytest.raises(BundleSchemaError, match="artifacts"):
        loader.load(path)


@pytest.mark.parametrize("ident", [{"tp_id": None}, {"pr_id": None}, {"tp_id": None, "pr_id": None}])
def test_null_only_identity_raises_schema_error(tmp_path, ident):
    payload = {"artifacts": []}
    payload.update(ident)
    path = _write(tmp_path, "TP-1_PROOF_BUNDLE.json", payload)
    loader = DopetaskBundleLoader(tmp_path)
    with pytest.raises(BundleSchemaError, match="tp_id\\|pr_id"):
        loader.load(path)


@pytest.mark.parametrize(
    "ident",
    [
        {"tp_id": 123},
        {"pr_id": ["77"]},
        {"tp_id": {"id": "1"}},
        {"pr_id": True},
        {"tp_id": "1", "pr_id": False},
        {"pr_id": 77.0},
    ],
)
def test_non_string_identity_raises_schema_error(tmp_path, ident):
    payload = {"artifacts": []}
    payload.update(ident)
    path = _write(tmp_path, "TP-1_PROOF_BUNDLE.json", payload)
    loader = DopetaskBundleLoader(tmp_path)
    with pytest.raises(BundleSchemaError):
        loader.load(path)


@pytest.mark.parametrize(
    "ident",
    [{"tp_id": ""}, {"tp_id": "   "}, {"pr_id": ""}, {"tp_id": "1", "pr_id": " \t"}],
)
def test_blank_identity_raises_schema_error(tmp_path, ident):
    payload = {"artifacts": []}
    payload.update(ident)
    path = _write(tmp_path, "TP-1_PROOF_BUNDLE.json", payload)
    loader = DopetaskBundleLoader(tmp_path)
    with pytest.raises(BundleSchemaError):
        loader.load(path)


@pytest.mark.parametrize("artifacts", [[""], ["a.log", "   "]])
def test_blank_artifact_member_raises_schema_error(tmp_path, artifacts):
    path = _write(tmp_path, "TP-1_PROOF_BUNDLE.json", {"tp_id": "1", "artifacts": artifacts})
    loader = DopetaskBundleLoader(tmp_path)
    with pytest.raises(BundleSchemaError, match="artifacts"):
        loader.load(path)


def test_launcher_bundle_with_numeric_pr_id_loads(tmp_path):
    # DopetaskPacketLauncher copies context["pr_id"] into its bundle unconverted,
    # and PR numbers are ints elsewhere in this package (classification.py).
    payload = {
        "tp_id": "TP-PRMS-052",
        "pr_id": 1447,
        "run_id": "run-1",
        "status": "VALIDATED",
        "artifacts": [],
    }
    path = _write(tmp_path, "TP-PRMS-052_PROOF_BUNDLE.json", payload)
    loader = DopetaskBundleLoader(tmp_path)
    assert loader.load(path)["pr_id"] == 1447


def test_numeric_pr_id_alone_satisfies_identity(tmp_path):
    path = _write(tmp_path, "TP-9_PROOF_BUNDLE.json", {"pr_id": 1447, "artifacts": []})
    loader = DopetaskBundleLoader(tmp_path)
    assert loader.load(path)["pr_id"] == 1447


def test_load_canonical_rejects_non_object_with_schema_error(tmp_path):
    path = _write_raw(tmp_path, "TP-1_PROOF_BUNDLE.json", "[]")
    loader = DopetaskBundleLoader(tmp_path)
    with pytest.raises(BundleSchemaError):
        loader.load_canonical(path)


# ---------------------------------------------------------------------------
# Negative regressions: valid inputs and pre-existing error contracts preserved.
# ---------------------------------------------------------------------------

def test_lean_manifest_with_only_tp_id_and_artifacts_loads(tmp_path):
    path = _write(tmp_path, "closed_loop_MANIFEST.json", {"tp_id": "9", "artifacts": ["x.log"]})
    loader = DopetaskBundleLoader(tmp_path)
    assert loader.load(path) == {"tp_id": "9", "artifacts": ["x.log"]}


def test_lean_bundle_with_only_pr_id_loads(tmp_path):
    path = _write(tmp_path, "TP-9_PROOF_BUNDLE.json", {"pr_id": "77", "artifacts": []})
    loader = DopetaskBundleLoader(tmp_path)
    assert loader.load(path)["pr_id"] == "77"


def test_null_other_identity_tolerated_when_one_is_string(tmp_path):
    path = _write(tmp_path, "TP-9_PROOF_BUNDLE.json", {"tp_id": "9", "pr_id": None, "artifacts": []})
    loader = DopetaskBundleLoader(tmp_path)
    assert loader.load(path)["tp_id"] == "9"


def test_full_bundle_loads_and_load_canonical_accepts(tmp_path):
    path = _write(tmp_path, "TP-123_PROOF_BUNDLE.json", FULL_BUNDLE)
    loader = DopetaskBundleLoader(tmp_path)
    assert loader.load(path) == FULL_BUNDLE
    assert loader.load_canonical(path) == FULL_BUNDLE


def test_load_canonical_still_reports_missing_expected_fields(tmp_path):
    path = _write(tmp_path, "TP-9_PROOF_BUNDLE.json", {"tp_id": "9", "artifacts": [], "status": "pass"})
    loader = DopetaskBundleLoader(tmp_path)
    assert loader.load(path)["tp_id"] == "9"
    with pytest.raises(BundleSchemaError, match="canonical fields"):
        loader.load_canonical(path)


def test_missing_artifacts_still_reports_required_fields(tmp_path):
    path = _write(tmp_path, "TP-9_PROOF_BUNDLE.json", {"tp_id": "9"})
    loader = DopetaskBundleLoader(tmp_path)
    with pytest.raises(BundleSchemaError, match="artifacts"):
        loader.load(path)


def test_missing_identity_still_reports_tp_id_or_pr_id(tmp_path):
    path = _write(tmp_path, "TP-9_PROOF_BUNDLE.json", {"artifacts": []})
    loader = DopetaskBundleLoader(tmp_path)
    with pytest.raises(BundleSchemaError, match="tp_id\\|pr_id"):
        loader.load(path)


def test_invalid_json_still_raises_json_decode_error(tmp_path):
    path = _write_raw(tmp_path, "TP-9_PROOF_BUNDLE.json", "{not json")
    loader = DopetaskBundleLoader(tmp_path)
    with pytest.raises(json.JSONDecodeError):
        loader.load(path)


def test_missing_file_still_raises_file_not_found(tmp_path):
    loader = DopetaskBundleLoader(tmp_path)
    with pytest.raises(FileNotFoundError):
        loader.load(tmp_path / "nope.json")


def test_find_bundle_search_order_unchanged(tmp_path):
    loader = DopetaskBundleLoader(tmp_path)
    assert loader.find_bundle("1") is None
    generic = _write(tmp_path, "zz_BUNDLE.json", {"tp_id": "1", "artifacts": []})
    assert loader.find_bundle("1") == generic
    manifest = _write(tmp_path, "a_MANIFEST.json", {"tp_id": "1", "artifacts": []})
    assert loader.find_bundle("1") == manifest
    canonical = _write(tmp_path, "TP-1_PROOF_BUNDLE.json", {"tp_id": "1", "artifacts": []})
    assert loader.find_bundle("1") == canonical
