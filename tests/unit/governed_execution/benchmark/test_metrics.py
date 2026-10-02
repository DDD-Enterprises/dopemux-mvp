"""Metric-by-metric tests for scripts/governed_execution/benchmark.py.

Every expected value below is hand-computed against the committed fixture
files in ``fixtures/before/`` and ``fixtures/after/``; see the docstring of
each extractor in ``benchmark.py`` for the rule being exercised. Fixture
sha256 values are always computed here via :func:`hashlib.sha256`, never
typed by hand.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.governed_execution import benchmark as bm

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
BEFORE_DIR = FIXTURES_DIR / "before"
AFTER_DIR = FIXTURES_DIR / "after"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_before_manifest(before_dir: Path, extra_missing: bool = True) -> dict:
    entries = []
    for candidate in sorted(before_dir.rglob("*")):
        if not candidate.is_file():
            continue
        rel = candidate.relative_to(before_dir).as_posix()
        entries.append({"path": rel, "status": "PRESENT", "sha256": _sha256_file(candidate)})
    if extra_missing:
        entries.append({"path": "proof/PKG-C/PROOF.json", "status": "MISSING", "sha256": None})
    return {"entries": entries}


def _before_corpus() -> bm.Corpus:
    manifest = _build_before_manifest(BEFORE_DIR)
    return bm.build_baseline_corpus(BEFORE_DIR, manifest)


def _after_corpus() -> bm.Corpus:
    return bm.build_after_corpus(AFTER_DIR)


# --------------------------------------------------------------------------
# BASELINE metrics
# --------------------------------------------------------------------------


def test_baseline_audit_calls() -> None:
    result = bm.extract_audit_calls_baseline(_before_corpus())
    assert result.status == "KNOWN"
    assert result.value == 1
    assert result.evidence == ("proof/PKG-A/PROOF.json",)


def test_baseline_cycle_time() -> None:
    result = bm.extract_cycle_time_baseline(_before_corpus())
    assert result.status == "KNOWN"
    assert result.value == 86400


def test_baseline_maintenance_cost() -> None:
    result = bm.extract_maintenance_cost(_before_corpus())
    assert result.status == "KNOWN"
    assert result.value == 1
    assert result.evidence == ("proof/PKG-A/review_bundle/CANDIDATE_UNIFIED_DIFF.txt",)


def test_baseline_model_calls() -> None:
    result = bm.extract_model_calls_baseline(_before_corpus())
    assert result.status == "KNOWN"
    assert result.value == 10


def test_baseline_operator_touches() -> None:
    result = bm.extract_operator_touches_baseline(_before_corpus())
    assert result.status == "KNOWN"
    assert result.value == 2
    assert result.evidence == (
        "proof/PKG-A/PROOF.json",
        "task-packets/PKG-A/PKG-A.json",
    )


def test_baseline_proof_churn() -> None:
    result = bm.extract_proof_churn_baseline(_before_corpus())
    assert result.status == "KNOWN"
    assert result.value == 1
    assert result.evidence == ("proof/PKG-A/review_bundle/SUPERSEDED_old_note.txt",)


def test_baseline_repair_loops() -> None:
    result = bm.extract_repair_loops_baseline(_before_corpus())
    assert result.status == "KNOWN"
    assert result.value == 2
    assert result.evidence == ("proof/PKG-A/PROOF.json",)


def test_baseline_review_calls() -> None:
    result = bm.extract_review_calls_baseline(_before_corpus())
    assert result.status == "KNOWN"
    assert result.value == 1


def test_baseline_safety_regressions() -> None:
    result = bm.extract_safety_regressions_baseline(_before_corpus())
    assert result.status == "KNOWN"
    assert result.value == 1
    assert result.evidence == ("proof/PKG-A/AUDITOR_REPORT.md",)


def test_baseline_stale_head_rework() -> None:
    result = bm.extract_stale_head_rework_baseline(_before_corpus())
    assert result.status == "KNOWN"
    assert result.value == 1
    assert result.evidence == ("proof/PKG-A/PROOF.json",)


def test_baseline_supervisor_relays_is_unknown() -> None:
    result = bm.extract_supervisor_relays_baseline(_before_corpus())
    assert result.status == "UNKNOWN"
    assert result.value is None


# --------------------------------------------------------------------------
# AFTER metrics
# --------------------------------------------------------------------------


def test_after_audit_calls() -> None:
    result = bm.extract_audit_calls_after(_after_corpus())
    assert result.status == "KNOWN"
    assert result.value == 2


def test_after_cycle_time() -> None:
    result = bm.extract_cycle_time_after(_after_corpus())
    assert result.status == "KNOWN"
    assert result.value == 7200


def test_after_maintenance_cost() -> None:
    result = bm.extract_maintenance_cost(_after_corpus())
    assert result.status == "KNOWN"
    assert result.value == 2
    assert result.evidence == ("CANDIDATE_UNIFIED_DIFF.txt",)


def test_after_model_calls() -> None:
    result = bm.extract_model_calls_after(_after_corpus())
    assert result.status == "KNOWN"
    assert result.value == 12


def test_after_operator_touches() -> None:
    result = bm.extract_operator_touches_after(_after_corpus())
    assert result.status == "KNOWN"
    assert result.value == 4
    assert result.evidence == ("OPERATOR_DECISIONS_G0.md", "OPERATOR_GATE_RECEIPT_G0.md")


def test_after_proof_churn() -> None:
    result = bm.extract_proof_churn_after(_after_corpus())
    assert result.status == "KNOWN"
    assert result.value == 1
    assert result.evidence == ("W02_FREEZE_RECEIPT_SUPERSEDED_1.json",)


def test_after_repair_loops() -> None:
    result = bm.extract_repair_loops_after(_after_corpus())
    assert result.status == "KNOWN"
    assert result.value == 1
    assert result.evidence == ("W02_REPAIR_REQUEST_1.md",)


def test_after_review_calls() -> None:
    result = bm.extract_review_calls_after(_after_corpus())
    assert result.status == "KNOWN"
    assert result.value == 1
    assert result.evidence == ("W01_VALIDATION_20260201.txt",)


def test_after_safety_regressions() -> None:
    result = bm.extract_safety_regressions_after(_after_corpus())
    assert result.status == "KNOWN"
    assert result.value == 1
    assert result.evidence == ("evidence/a2-audit-run2/A2_AUDIT_RECORD.md",)


def test_after_stale_head_rework() -> None:
    result = bm.extract_stale_head_rework_after(_after_corpus())
    assert result.status == "KNOWN"
    assert result.value == 1
    assert result.evidence == (
        "W02_RETURN.md",
        "evidence/a2-audit-run2/A2_AUDIT_RECORD.md",
    )
    assert result.gaps == ()


def test_after_supervisor_relays() -> None:
    result = bm.extract_supervisor_relays_after(_after_corpus())
    assert result.status == "KNOWN"
    assert result.value == 3
    assert result.evidence == ("G0_RETURN.md", "W01_RETURN.md", "W02_RETURN.md")


# --------------------------------------------------------------------------
# UNKNOWN propagation: missing evidence category, empty after-dir
# --------------------------------------------------------------------------


def test_empty_after_dir_every_metric_is_unknown(tmp_path: Path) -> None:
    empty_dir = tmp_path / "empty_after"
    empty_dir.mkdir()
    corpus = bm.build_after_corpus(empty_dir)
    for name, extractor in bm.AFTER_EXTRACTORS.items():
        result = extractor(corpus)
        assert result.status == "UNKNOWN", f"{name} expected UNKNOWN on empty after-dir"
        assert result.value is None


def test_missing_baseline_manifest_entry_is_recorded_not_dropped() -> None:
    corpus = _before_corpus()
    missing = [e for e in corpus.entries if e.path == "proof/PKG-C/PROOF.json"]
    assert len(missing) == 1
    assert missing[0].status == "MISSING"
    assert missing[0].sha256 is None
    assert missing[0].text is None
    # A MISSING entry never contributes to any evidence list.
    for extractor in bm.BASELINE_EXTRACTORS.values():
        result = extractor(corpus)
        assert "proof/PKG-C/PROOF.json" not in result.evidence


def test_baseline_manifest_sha256_mismatch_excludes_content() -> None:
    """A file whose on-disk sha256 no longer matches the manifest is
    treated as unusable evidence, like MISSING -- never like a match.
    """
    manifest = _build_before_manifest(BEFORE_DIR, extra_missing=False)
    for entry in manifest["entries"]:
        if entry["path"] == "proof/PKG-B/PROOF.json":
            entry["sha256"] = "0" * 64
    corpus = bm.build_baseline_corpus(BEFORE_DIR, manifest)
    mismatched = [e for e in corpus.entries if e.path == "proof/PKG-B/PROOF.json"]
    assert len(mismatched) == 1
    assert mismatched[0].status == "MISMATCH"
    assert mismatched[0].text is None
    # PKG-B contributed 6 to model_calls (out of 10 total); with it
    # excluded only PKG-A's 4 remains.
    result = bm.extract_model_calls_baseline(corpus)
    assert result.status == "KNOWN"
    assert result.value == 4


def test_missing_after_dir_returns_exit_code_2(tmp_path: Path) -> None:
    out = tmp_path / "report.json"
    out_md = tmp_path / "report.md"
    manifest_path = tmp_path / "baseline.json"
    manifest_path.write_text(json.dumps(_build_before_manifest(BEFORE_DIR)), encoding="utf-8")
    exit_code = bm.main(
        [
            "--repo",
            str(BEFORE_DIR),
            "--baseline-manifest",
            str(manifest_path),
            "--after-dir",
            str(tmp_path / "does-not-exist"),
            "--out",
            str(out),
            "--out-md",
            str(out_md),
        ]
    )
    assert exit_code == 2
    assert not out.exists()


def test_stale_head_rework_gap_for_unmatched_audit_record(tmp_path: Path) -> None:
    after_dir = tmp_path / "after"
    (after_dir / "evidence" / "a9-audit-run9").mkdir(parents=True)
    (after_dir / "evidence" / "a9-audit-run9" / "A9_AUDIT_RECORD.md").write_text(
        "WORKSTREAM_ID=W77\nSUBJECT_SHA=5555555555555555555555555555555555555555\n",
        encoding="utf-8",
    )
    corpus = bm.build_after_corpus(after_dir)
    result = bm.extract_stale_head_rework_after(corpus)
    assert result.status == "KNOWN"
    assert result.value == 0
    assert result.gaps == ("evidence/a9-audit-run9/A9_AUDIT_RECORD.md",)


def test_model_calls_after_non_integer_value_is_unknown(tmp_path: Path) -> None:
    after_dir = tmp_path / "after"
    after_dir.mkdir()
    (after_dir / "W01_RETURN.md").write_text(
        "WORKSTREAM_ID=W01\nMODEL_CALLS=UNKNOWN\n",
        encoding="utf-8",
    )
    corpus = bm.build_after_corpus(after_dir)
    result = bm.extract_model_calls_after(corpus)
    assert result.status == "UNKNOWN"
    assert result.value is None


# --------------------------------------------------------------------------
# Deltas
# --------------------------------------------------------------------------


def test_deltas_only_computed_when_both_sides_numeric() -> None:
    baseline_metrics = {name: fn(_before_corpus()) for name, fn in bm.BASELINE_EXTRACTORS.items()}
    post_metrics = {name: fn(_after_corpus()) for name, fn in bm.AFTER_EXTRACTORS.items()}
    deltas = bm._compute_deltas(baseline_metrics, post_metrics)
    # model_calls: baseline 10 (KNOWN), post 12 (KNOWN) -> delta 2.
    assert deltas["model_calls"] == {"status": "KNOWN", "value": 2}
    # supervisor_relays: baseline UNKNOWN, post KNOWN -> delta UNKNOWN.
    assert deltas["supervisor_relays"] == {"status": "UNKNOWN", "value": None}


# --------------------------------------------------------------------------
# Retirement candidates
# --------------------------------------------------------------------------


def test_retirement_candidates_from_fixture_after_are_keep() -> None:
    """The fixture AFTER corpus has safety_regressions == 1 (not safe) and
    every non-gate relay metric > 0 (measurably useful), so every
    candidate must recommend KEEP, and the operator gate must never
    appear.
    """
    post_metrics = {name: fn(_after_corpus()) for name, fn in bm.AFTER_EXTRACTORS.items()}
    candidates = bm.build_retirement_candidates(post_metrics)
    names = {c["relay"] for c in candidates}
    assert "operator_decision_gate" not in names
    assert len(candidates) == 5
    for candidate in candidates:
        assert candidate["recommendation"] == "KEEP"
        assert candidate["safe"] is False


def test_retirement_candidates_recommend_retire_when_safe_and_unused() -> None:
    post_metrics = {
        "audit_calls": bm._known(5, ["a"]),
        "cycle_time": bm._unknown(),
        "maintenance_cost": bm._unknown(),
        "model_calls": bm._unknown(),
        "operator_touches": bm._known(2, ["b"]),
        "proof_churn": bm._known(0, []),
        "repair_loops": bm._known(0, []),
        "review_calls": bm._unknown(),
        "safety_regressions": bm._known(0, []),
        "stale_head_rework": bm._known(0, []),
        "supervisor_relays": bm._known(3, ["c"]),
    }
    candidates = {c["relay"]: c for c in bm.build_retirement_candidates(post_metrics)}
    assert candidates["freeze_proof_relay"]["recommendation"] == "RECOMMEND_RETIRE"
    assert candidates["repair_loop_relay"]["recommendation"] == "RECOMMEND_RETIRE"
    assert candidates["independent_audit_dispatch_relay"]["recommendation"] == "KEEP"
    assert candidates["supervisor_return_relay"]["recommendation"] == "KEEP"
    assert candidates["review_ci_relay"]["recommendation"] == "INSUFFICIENT_EVIDENCE"
    assert "operator_decision_gate" not in candidates
