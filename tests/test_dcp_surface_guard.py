"""
Tests for .claude/hooks/dcp_surface_guard.py

Mirrors style of tests/test_orchestrator_enforcement_hooks.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parents[1] / ".claude" / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

_ROOT = Path(__file__).resolve().parents[1]

from dcp_surface_guard import (  # noqa: E402
    RED_LANE_ID,
    _FALLBACK_COMPILED,
    _repo_relative,
    surface_guard_block,
    surface_guard_warnings,
)


# ---------------------------------------------------------------------------
# Block tier — red-lane seam files
# ---------------------------------------------------------------------------

def test_blocks_queue_drain_src_path():
    inp = {"file_path": str(_ROOT / "src/dopemux_pr_merge_specialist/queue_drain.py")}
    result = surface_guard_block("Edit", inp, _ROOT)
    assert result is not None
    assert RED_LANE_ID in result
    assert "hard-blocked" in result


def test_blocks_queue_drain_bare_path():
    """Bare path variant (no src/ prefix) must also be blocked."""
    inp = {"file_path": str(_ROOT / "dopemux_pr_merge_specialist/queue_drain.py")}
    result = surface_guard_block("Edit", inp, _ROOT)
    assert result is not None
    assert RED_LANE_ID in result


def test_blocks_batch_resolve_script():
    inp = {"file_path": str(_ROOT / "scripts/batch_resolve_and_merge.py")}
    result = surface_guard_block("Write", inp, _ROOT)
    assert result is not None
    assert RED_LANE_ID in result


def test_does_not_block_red_lane_scanner_itself():
    """red_lane_scanner.py is the enforcement tool — must not be blocked."""
    inp = {"file_path": str(_ROOT / "src/dopemux/dcp/red_lane_scanner.py")}
    result = surface_guard_block("Edit", inp, _ROOT)
    assert result is None


def test_does_not_block_unrelated_file():
    inp = {"file_path": str(_ROOT / "src/dopemux/cli.py")}
    result = surface_guard_block("Edit", inp, _ROOT)
    assert result is None


def test_read_tool_never_blocked():
    """Read/Bash must never be blocked regardless of path."""
    for tool in ("Read", "Bash", "Grep"):
        inp = {"file_path": str(_ROOT / "scripts/batch_resolve_and_merge.py")}
        result = surface_guard_block(tool, inp, _ROOT)
        assert result is None, f"Expected no block for {tool}"


def test_no_file_path_returns_none():
    result = surface_guard_block("Edit", {}, _ROOT)
    assert result is None


# ---------------------------------------------------------------------------
# ADR-224 / TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001R Phase A: narrow workflow carve-out
# ---------------------------------------------------------------------------

def test_embedded_audit_workflow_is_carved_out():
    inp = {"file_path": str(_ROOT / ".github/workflows/embedded-audit.yml")}
    result = surface_guard_block("Edit", inp, _ROOT)
    assert result is None


def test_pr_steward_workflow_is_carved_out():
    inp = {"file_path": str(_ROOT / ".github/workflows/pr-steward.yml")}
    result = surface_guard_block("Write", inp, _ROOT)
    assert result is None


def test_other_workflow_files_remain_blocked():
    """The carve-out must be exact-filename scoped, not a blanket exemption."""
    inp = {"file_path": str(_ROOT / ".github/workflows/ci-complete.yml")}
    result = surface_guard_block("Edit", inp, _ROOT)
    assert result is not None
    assert RED_LANE_ID in result


def test_near_miss_backup_filename_remains_blocked():
    """A file that merely starts with the carved-out name must still be blocked."""
    inp = {"file_path": str(_ROOT / ".github/workflows/embedded-audit.yml.bak")}
    result = surface_guard_block("Edit", inp, _ROOT)
    assert result is not None
    assert RED_LANE_ID in result


def test_nested_carved_out_filename_remains_blocked():
    """Carve-out is top-level only; a same-named file in a subdirectory is not exempt."""
    inp = {"file_path": str(_ROOT / ".github/workflows/sub/embedded-audit.yml")}
    result = surface_guard_block("Edit", inp, _ROOT)
    assert result is not None
    assert RED_LANE_ID in result


# ---------------------------------------------------------------------------
# ADR-226 / TP-DOPECONTEXT-VECTOR-SPACE-0004 governance amendment (2026-09-03):
# narrow services/dope-context carve-out — eval/ directory + three exact files
# ---------------------------------------------------------------------------

_DOPE_CONTEXT_CARVED_OUT = (
    "services/dope-context/eval/run_eval.py",
    "services/dope-context/eval/queries.jsonl",
    "services/dope-context/eval/results/2026-09-03/run.md",
    "services/dope-context/src/pipeline/indexing_pipeline.py",
    "services/dope-context/src/mcp/server.py",
    "services/dope-context/tests/test_vector_space_invariants.py",
)

_DOPE_CONTEXT_STILL_BLOCKED = (
    "services/dope-context/src/search/hybrid_search.py",
    "services/dope-context/src/preprocessing/code_chunker.py",
    "services/dope-context/src/embeddings/model_registry.py",
    "services/dope-context/tests/conftest.py",
    "services/dope-context/Dockerfile",
    "services/dope-context/evaluation.py",  # near-miss of the eval/ directory name
    "services/dope-context/eval",  # bare name is not the directory
    "services/dope-context/src/mcp/server.py.bak",  # near-miss filename
    "services/dope-context/src/mcp/sub/server.py",  # nested same-named file
    "services/dope-context/src/server.py",  # same name, other directory
    "services/dope-context/eval/../src/mcp/server.py",  # traversal out of eval/
    "services/dope-context/eval/sub/../../src/search/hybrid_search.py",
    "services/dope-context/../dope-context/src/search/hybrid_search.py",
)


def test_dope_context_carved_out_paths_are_editable():
    for rel in _DOPE_CONTEXT_CARVED_OUT:
        for tool in ("Edit", "Write", "NotebookEdit"):
            inp = {"file_path": str(_ROOT / rel)}
            assert surface_guard_block(tool, inp, _ROOT) is None, (tool, rel)


def test_dope_context_other_paths_remain_blocked():
    """Exact-file / single-directory carve-out — not a service-wide lift."""
    for rel in _DOPE_CONTEXT_STILL_BLOCKED:
        result = surface_guard_block("Edit", {"file_path": str(_ROOT / rel)}, _ROOT)
        assert result is not None, rel
        assert RED_LANE_ID in result, rel


def test_sibling_mcp_services_remain_fully_blocked():
    """The carve-out is dope-context-only; sibling service blankets are untouched."""
    for rel in (
        "services/task-orchestrator/app/main.py",
        "services/dopecon-bridge/eval/run_eval.py",
        "services/working-memory-assistant/src/mcp/server.py",
    ):
        result = surface_guard_block("Edit", {"file_path": str(_ROOT / rel)}, _ROOT)
        assert result is not None, rel
        assert RED_LANE_ID in result, rel


def test_no_symlinks_under_dope_context_eval():
    """A symlink inside the exempted directory could write through to a blocked path."""
    eval_dir = _ROOT / "services" / "dope-context" / "eval"
    if not eval_dir.exists():
        return
    links = [p for p in eval_dir.rglob("*") if p.is_symlink()]
    assert links == [], f"symlinks under carved-out eval/: {links}"


# ---------------------------------------------------------------------------
# Sync test: fallback ⊆ live FORBIDDEN_PATHS
# ---------------------------------------------------------------------------

def test_fallback_patterns_covered_by_live_rules():
    """_FALLBACK_COMPILED patterns must all be covered by red_lane_rules.FORBIDDEN_PATHS.

    Specifically: every path that matches a fallback pattern must also match
    at least one pattern in the live FORBIDDEN_PATHS list.
    """
    try:
        from dopemux.dcp.red_lane_rules import FORBIDDEN_PATHS
    except ImportError:
        import pytest
        pytest.skip("dopemux package not importable — skipping live sync test")

    test_paths = [
        "src/dopemux_pr_merge_specialist/queue_drain.py",
        "dopemux_pr_merge_specialist/queue_drain.py",
        "scripts/batch_resolve_and_merge.py",
    ]
    for path in test_paths:
        matched_fallback = any(p.search(path) for p in _FALLBACK_COMPILED)
        matched_live = any(p.search(path) for p in FORBIDDEN_PATHS)
        assert matched_live or not matched_fallback, (
            f"Fallback guards `{path}` but live FORBIDDEN_PATHS does not. "
            f"Update _FALLBACK_FORBIDDEN in dcp_surface_guard.py."
        )


# ---------------------------------------------------------------------------
# Warn tier — contract-sensitive surfaces
# ---------------------------------------------------------------------------

def test_warn_on_dcp_schema(tmp_path):
    schema_file = tmp_path / "schemas" / "dcp" / "some.schema.json"
    schema_file.parent.mkdir(parents=True)
    schema_file.touch()
    inp = {"file_path": str(schema_file)}
    warnings = surface_guard_warnings("Edit", inp, tmp_path, "sess-1")
    assert len(warnings) == 1
    assert "DCP authority contract schema" in warnings[0]


def test_warn_on_route_manifest(tmp_path):
    rf = tmp_path / "services" / "dcp-readonly-facade" / "src" / "dcp_facade" / "route_manifest.py"
    rf.parent.mkdir(parents=True)
    rf.touch()
    inp = {"file_path": str(rf)}
    warnings = surface_guard_warnings("Edit", inp, tmp_path, "sess-2")
    assert len(warnings) == 1
    assert "DENIED_TOKENS" in warnings[0]


def test_warn_on_mcp_catalog(tmp_path):
    cat = tmp_path / "mcp_catalog.yaml"
    cat.touch()
    inp = {"file_path": str(cat)}
    warnings = surface_guard_warnings("Edit", inp, tmp_path, "sess-3")
    assert len(warnings) == 1
    assert "canonical source of truth" in warnings[0]


def test_no_warn_on_unrelated_file(tmp_path):
    f = tmp_path / "src" / "dopemux" / "cli.py"
    f.parent.mkdir(parents=True)
    f.touch()
    inp = {"file_path": str(f)}
    warnings = surface_guard_warnings("Edit", inp, tmp_path, "sess-4")
    assert warnings == []


def test_cooldown_same_session(tmp_path):
    cat = tmp_path / "mcp_catalog.yaml"
    cat.touch()
    inp = {"file_path": str(cat)}
    first = surface_guard_warnings("Edit", inp, tmp_path, "sess-A")
    assert len(first) == 1
    second = surface_guard_warnings("Edit", inp, tmp_path, "sess-A")
    assert second == []


def test_cooldown_different_session(tmp_path):
    cat = tmp_path / "mcp_catalog.yaml"
    cat.touch()
    inp = {"file_path": str(cat)}
    first = surface_guard_warnings("Edit", inp, tmp_path, "sess-A")
    assert len(first) == 1
    second = surface_guard_warnings("Edit", inp, tmp_path, "sess-B")
    assert len(second) == 1


def test_no_warn_for_new_proof_json(tmp_path):
    """Write to a new proof/TP-X/PROOF.json (scaffold flow) must not warn."""
    # File does not exist yet (new scaffold)
    proof = tmp_path / "proof" / "TP-X" / "PROOF.json"
    inp = {"file_path": str(proof)}
    warnings = surface_guard_warnings("Write", inp, tmp_path, "sess-5")
    assert warnings == []


def test_read_tool_never_warns():
    for tool in ("Read", "Bash", "Grep"):
        inp = {"file_path": str(_ROOT / "mcp_catalog.yaml")}
        warnings = surface_guard_warnings(tool, inp, _ROOT, "sess-6")
        assert warnings == [], f"Expected no warn for {tool}"
