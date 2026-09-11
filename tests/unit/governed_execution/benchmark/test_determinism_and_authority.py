"""Determinism, authority-constant, and module-purity tests for
scripts/governed_execution/benchmark.py.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from scripts.governed_execution import benchmark as bm

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
BEFORE_DIR = FIXTURES_DIR / "before"
AFTER_DIR = FIXTURES_DIR / "after"

FORBIDDEN_RUNTIME_MODULES = {
    "requests",
    "urllib",
    "urllib3",
    "http.client",
    "socket",
    "anthropic",
    "openai",
    "litellm",
}


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_baseline_manifest(tmp_path: Path) -> Path:
    entries = []
    for candidate in sorted(BEFORE_DIR.rglob("*")):
        if not candidate.is_file():
            continue
        rel = candidate.relative_to(BEFORE_DIR).as_posix()
        entries.append({"path": rel, "status": "PRESENT", "sha256": _sha256_file(candidate)})
    manifest_path = tmp_path / "baseline_manifest.json"
    manifest_path.write_text(json.dumps({"entries": entries}), encoding="utf-8")
    return manifest_path


def _run_cli(tmp_path: Path, suffix: str) -> tuple[int, Path, Path]:
    manifest_path = _write_baseline_manifest(tmp_path)
    out = tmp_path / f"report_{suffix}.json"
    out_md = tmp_path / f"report_{suffix}.md"
    exit_code = bm.main(
        [
            "--repo",
            str(BEFORE_DIR),
            "--baseline-manifest",
            str(manifest_path),
            "--after-dir",
            str(AFTER_DIR),
            "--out",
            str(out),
            "--out-md",
            str(out_md),
        ]
    )
    return exit_code, out, out_md


def test_two_runs_are_byte_identical(tmp_path: Path) -> None:
    exit_a, out_a, md_a = _run_cli(tmp_path, "a")
    exit_b, out_b, md_b = _run_cli(tmp_path, "b")
    assert exit_a == 0
    assert exit_b == 0
    assert out_a.read_bytes() == out_b.read_bytes()
    assert md_a.read_bytes() == md_b.read_bytes()


def test_exit_code_zero_on_success(tmp_path: Path) -> None:
    exit_code, out, out_md = _run_cli(tmp_path, "ok")
    assert exit_code == 0
    assert out.exists()
    assert out_md.exists()


def test_exit_code_two_when_after_dir_missing(tmp_path: Path) -> None:
    manifest_path = _write_baseline_manifest(tmp_path)
    exit_code = bm.main(
        [
            "--repo",
            str(BEFORE_DIR),
            "--baseline-manifest",
            str(manifest_path),
            "--after-dir",
            str(tmp_path / "nope"),
            "--out",
            str(tmp_path / "out.json"),
            "--out-md",
            str(tmp_path / "out.md"),
        ]
    )
    assert exit_code == 2


def test_retirement_authorized_and_authority_are_constant(tmp_path: Path) -> None:
    _exit_code, out, _out_md = _run_cli(tmp_path, "const")
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["retirement_authorized"] is False
    assert report["authority"] == "NONE"
    # Also true for a corpus built from arbitrary/empty input.
    empty_dir = tmp_path / "another_empty"
    empty_dir.mkdir()
    empty_corpus = bm.build_after_corpus(empty_dir)
    baseline_corpus = bm.Corpus(entries=())
    arbitrary_report = bm.build_report(baseline_corpus, empty_corpus)
    assert arbitrary_report["retirement_authorized"] is False
    assert arbitrary_report["authority"] == "NONE"


def test_operator_gate_never_in_retirement_candidates(tmp_path: Path) -> None:
    after_dir = tmp_path / "after_with_gate"
    after_dir.mkdir()
    (after_dir / "OPERATOR_GATE_RECEIPT_X.md").write_text("Operator gate receipt.\n", encoding="utf-8")
    (after_dir / "OPERATOR_DECISIONS_G0.md").write_text("D1: something.\n", encoding="utf-8")
    corpus = bm.build_after_corpus(after_dir)
    post_metrics = {name: fn(corpus) for name, fn in bm.AFTER_EXTRACTORS.items()}
    candidates = bm.build_retirement_candidates(post_metrics)
    for candidate in candidates:
        assert "operator" not in candidate["relay"]
    assert len(candidates) == len(bm.RELAY_CATALOG) - 1


def test_module_imports_no_network_model_or_process_module() -> None:
    for name in list(sys.modules):
        if name == "scripts.governed_execution.benchmark" or name.startswith("scripts.governed_execution.benchmark."):
            del sys.modules[name]
    before = set(sys.modules)
    import scripts.governed_execution.benchmark  # noqa: F401

    after = set(sys.modules)
    delta = after - before
    leaked = delta & FORBIDDEN_RUNTIME_MODULES
    assert not leaked, f"benchmark.py pulled in forbidden modules: {sorted(leaked)}"
