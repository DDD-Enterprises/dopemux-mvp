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
    _repo_relative_candidates,
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
# ADR-226 / TP-DOPECONTEXT-VECTOR-SPACE-0004 governance amendment (2026-09-03,
# extended by amendment A2 2026-09-04): narrow services/dope-context carve-out —
# eval/ directory + five exact files. A2 added src/index_profile.py and
# src/embeddings/model_registry.py, the canonical writers the settled D1 decision
# needs; model_registry.py was previously pinned here as a still-blocked case.
# ---------------------------------------------------------------------------

_DOPE_CONTEXT_CARVED_OUT = (
    "services/dope-context/eval/run_eval.py",
    "services/dope-context/eval/queries.jsonl",
    "services/dope-context/eval/results/2026-09-03/run.md",
    "services/dope-context/src/pipeline/indexing_pipeline.py",
    "services/dope-context/src/mcp/server.py",
    "services/dope-context/src/index_profile.py",  # ADR-226 A2
    "services/dope-context/src/embeddings/model_registry.py",  # ADR-226 A2
    "services/dope-context/tests/test_vector_space_invariants.py",
)

_DOPE_CONTEXT_STILL_BLOCKED = (
    "services/dope-context/src/search/hybrid_search.py",
    "services/dope-context/src/preprocessing/code_chunker.py",
    "services/dope-context/src/pipeline/docs_pipeline.py",
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
    # ADR-226 A2 near-misses: the two newly-exempted files must not widen the lane.
    # voyage_embedder.py is the same-directory neighbour of model_registry.py —
    # exactly the case the anchored lookaheads have to survive.
    "services/dope-context/src/embeddings/voyage_embedder.py",
    "services/dope-context/src/embeddings/model_registry.py.tmp",
    "services/dope-context/src/index_profile.py.bak",
    "services/dope-context/src/index_profile.py.orig",
    "services/dope-context/src/search/index_profile.py",  # same name, other directory
    "services/dope-context/src/embeddings/sub/model_registry.py",  # nested same name
    "services/dope-context/eval/../src/index_profile.py",  # traversal out of eval/
    "services/dope-context/src/embeddings/../search/dense_search.py",
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
# ADR-226 independent audit F-001 (2026-09-03): path-normalization bypasses.
# A purely lexical `_repo_relative` let `<root>/../<root>/x`, a case-variant
# root and a symlink alias of the root escape every `^`-anchored pattern.
# ---------------------------------------------------------------------------

_BYPASS_TARGETS = (
    "src/dopemux_pr_merge_specialist/queue_drain.py",
    "services/dope-context/src/search/hybrid_search.py",
)


def test_pre_prefix_traversal_is_blocked():
    for rel in _BYPASS_TARGETS:
        fp = f"{_ROOT}/../{_ROOT.name}/{rel}"
        result = surface_guard_block("Edit", {"file_path": fp}, _ROOT)
        assert result is not None, fp
        assert RED_LANE_ID in result


def test_case_variant_root_is_blocked():
    """macOS's default filesystem is case-insensitive: /USERS/x/repo/f is /Users/x/repo/f."""
    for rel in _BYPASS_TARGETS:
        fp = f"{str(_ROOT).swapcase()}/{rel}"
        result = surface_guard_block("Write", {"file_path": fp}, _ROOT)
        assert result is not None, fp
        assert RED_LANE_ID in result


def _scaffold_repo(tmp_path):
    root = tmp_path / "repo"
    blocked = root / "services" / "dope-context" / "src" / "search" / "hybrid_search.py"
    blocked.parent.mkdir(parents=True)
    blocked.write_text("# blocked\n")
    (root / "services" / "dope-context" / "eval").mkdir()
    return root, blocked


def test_symlink_alias_of_root_is_blocked(tmp_path):
    root, blocked = _scaffold_repo(tmp_path)
    alias = tmp_path / "alias"
    alias.symlink_to(root, target_is_directory=True)
    via_alias = alias / blocked.relative_to(root)
    # alias path, real root
    assert surface_guard_block("Edit", {"file_path": str(via_alias)}, root) is not None
    # real path, alias root
    assert surface_guard_block("Edit", {"file_path": str(blocked)}, alias) is not None


def test_symlink_inside_exempt_dir_pointing_at_blocked_file_is_blocked(tmp_path):
    root, blocked = _scaffold_repo(tmp_path)
    link = root / "services" / "dope-context" / "eval" / "link.py"
    link.symlink_to(Path("..") / "src" / "search" / "hybrid_search.py")
    result = surface_guard_block("Edit", {"file_path": str(link)}, root)
    assert result is not None
    assert RED_LANE_ID in result


def test_new_file_under_exempt_dir_still_allowed(tmp_path):
    root, _ = _scaffold_repo(tmp_path)
    new = root / "services" / "dope-context" / "eval" / "new_probe.py"
    assert not new.exists()
    assert surface_guard_block("Write", {"file_path": str(new)}, root) is None


def test_path_outside_root_is_not_a_repo_file(tmp_path):
    root, _ = _scaffold_repo(tmp_path)
    outside = tmp_path / "elsewhere" / "src" / "dopemux_pr_merge_specialist" / "queue_drain.py"
    assert surface_guard_block("Edit", {"file_path": str(outside)}, root) is None


def test_repo_relative_primary_reading_unchanged():
    fp = str(_ROOT / "services" / "dope-context" / "eval" / "run_eval.py")
    assert _repo_relative(fp, _ROOT) == "services/dope-context/eval/run_eval.py"


# ---------------------------------------------------------------------------
# ADR-226 re-audit residual F-001-A (2026-09-03, CONFIRMED live on macOS):
# intra-repo case variants. `realpath` keeps the supplied case of existing
# components, so `SERVICES/dope-context/src/x.py` matched nothing while the
# OS wrote to the real file. The case-folded candidate is filesystem-independent,
# so these tests are unconditional (they also hold on case-sensitive volumes,
# where the fold is a deliberate fail-closed over-block).
# ---------------------------------------------------------------------------

_CASE_VARIANT_TARGETS = (
    "SERVICES/dope-context/src/search/hybrid_search.py",
    "services/DOPE-CONTEXT/src/search/hybrid_search.py",
    "services/dope-context/src/search/HYBRID_SEARCH.py",
    "src/dopemux_pr_merge_specialist/QUEUE_DRAIN.py",
    "SRC/dopemux_pr_merge_specialist/queue_drain.py",
)


def test_intra_repo_case_variant_is_blocked():
    for rel in _CASE_VARIANT_TARGETS:
        fp = str(_ROOT / rel)
        result = surface_guard_block("Edit", {"file_path": fp}, _ROOT)
        assert result is not None, fp
        assert RED_LANE_ID in result


def test_case_variant_root_and_intra_repo_combined_is_blocked():
    fp = f"{str(_ROOT).swapcase()}/SERVICES/dope-context/src/search/hybrid_search.py"
    result = surface_guard_block("Write", {"file_path": fp}, _ROOT)
    assert result is not None, fp
    assert RED_LANE_ID in result


def test_case_folded_candidate_is_present():
    fp = str(_ROOT / "SERVICES" / "dope-context" / "src" / "search" / "hybrid_search.py")
    cands = _repo_relative_candidates(fp, _ROOT)
    assert "services/dope-context/src/search/hybrid_search.py" in cands
    # primary (exact-case) reading is unchanged and still first
    assert cands[0] == "SERVICES/dope-context/src/search/hybrid_search.py"


def test_case_variant_of_exempt_dir_is_fail_closed():
    """`EVAL/` is not the carve-out spelling; blocking it is the fail-closed choice."""
    fp = str(_ROOT / "services" / "dope-context" / "EVAL" / "new_probe.py")
    assert surface_guard_block("Write", {"file_path": fp}, _ROOT) is not None


def test_exact_case_exempt_path_still_allowed_after_fold():
    fp = str(_ROOT / "services" / "dope-context" / "eval" / "run_eval.py")
    assert surface_guard_block("Edit", {"file_path": fp}, _ROOT) is None


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
