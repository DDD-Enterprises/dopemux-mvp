You are the independent Tier-1 auditor (AGY / gemini-3.1-pro-high) for repository dopemux-mvp. This is ROUND 3: a DELTA RE-AUDIT of the remediation of your own round-2 residual finding F-001-A (ADR-226, 2026-09-03). Audit ONLY whether F-001-A is closed and whether the fix introduces a regression; do not re-open other findings.

## Context
ADR-226 narrows the DCP-RED-MERGE-SEAM-0001 red lane so that ONLY services/dope-context/eval/** (including eval/README.md) is exempt; every other path under services/dope-context — including the top-level services/dope-context/README.md — remains hard-denied by the PreToolUse hook .claude/hooks/dcp_surface_guard.py. (Correction to the round-2 prompt, which wrongly said the top-level README was carved out; and services/dope-context/src/mcp/server.py is not in the lane in this repo. Both are recorded as prompt errata in the round-2 provenance.) The hook is Edit/Write/NotebookEdit-only; text-level rules are enforced by a separate scanner (out of scope).

Round 1 (head 720991c41): FAIL, F-001 (lexical-only path normalisation bypass). Fixed in 1d87cb732.
Round 2 (head 1d87cb732): CLOSED_WITH_RISKS, residual F-001-A HIGH. Fixed in a4f86c48c. Bundle/ADR amendment committed in 9ef316d1b (docs + proof only; no hook/test/rule changes — verified: git diff a4f86c48c..9ef316d1b on those three files is empty).

Target of THIS audit: head 9ef316d1b1327e201184e7bdf5dbf943f88b8fa3.

## Your round-2 verdict (verbatim)
```json
{
 "auditor_model": "gemini-3.1-pro-high",
 "target_commit": "1d87cb73284b4019aff0d7cfe2525baa626cb7cf",
 "finding": "F-001",
 "verdict": "CLOSED_WITH_RISKS",
 "reasoning": "The fix successfully mitigates root-level case-variations by case-folding the root prefix, and addresses symlink/traversal bypasses by evaluating both raw and realpath candidates. However, the intra-repo path (the suffix) is preserved exactly as supplied. Since os.path.realpath on macOS does not correct the case of existing directory components, and the FORBIDDEN_PATHS regexes lack the re.IGNORECASE flag, an attacker can still bypass the guard on case-insensitive filesystems by altering the case of any intra-repo component (e.g., 'SERVICES/dope-context/src/mcp/server.py').",
 "residual_risks": [
  {
   "id": "F-001-A",
   "severity": "HIGH",
   "description": "Intra-repo path case-variation bypass. On case-insensitive filesystems like macOS, the OS allows accessing files using different casing. Because the _repo_relative_candidates case-folded check only normalizes the root prefix and Python's os.path.realpath does not correct case on macOS, the candidate paths retain their modified case (e.g., 'SERVICES/...'). The regex patterns lack re.IGNORECASE, so the block tier fails to match and allows the edit to proceed.",
   "recommended_action": "Either compile all FORBIDDEN_PATHS regexes with re.IGNORECASE, or convert the extracted relative path to lowercase before checking against the patterns."
  }
 ],
 "regressions_introduced": [],
 "bypass_attempts_considered": [
  "case-variant root (e.g., /USERS/...) - mitigated by case-folded prefix matching",
  "case-variant intra-repo path (e.g., SERVICES/...) - bypasses regexes because re.IGNORECASE is missing and realpath doesn't correct case on macOS",
  "symlinks outside repo pointing inside - mitigated by realpath candidate",
  "symlinks inside exempt dir pointing to blocked file - mitigated by realpath candidate",
  "relative paths with traversing segments (../) - mitigated because realpath resolves to absolute, then correctly matches root",
  "traversal bypassing negative lookahead (eval/../src/x.py) - mitigated by companion traversal regex and realpath candidate",
  "URL encoding (%2e%2e) - mitigated as OS does not decode it, resulting in new file creation rather than overwrite",
  "unicode normalization/homoglyphs (e.g., Cyrillic 'c') - mitigated as OS creates a new distinct file rather than overwriting",
  "trailing spaces/dots - mitigated by ntpath.realpath on Windows resolving to true path for existing files",
  "multiple slashes (//) - mitigated by pathlib.Path normalization",
  "Windows backslashes on POSIX - mitigated as OS treats them as regular filename characters"
 ]
}```

## Remediation under audit — commit a4f86c48c3f6f153330a1554141bcfc7e4ee2490
```diff
commit a4f86c48c3f6f153330a1554141bcfc7e4ee2490
Author: Claude <noreply@anthropic.com>
Date:   Thu Sep 3 09:31:31 2026 -0700

    fix(dcp-hook): case-fold red-lane path match in dcp_surface_guard (ADR-226 F-001-A)
    
    The PreToolUse hook matched repo-relative paths case-sensitively while the
    red lane (DCP-RED-MERGE-SEAM-0001) is intended to protect files on a
    case-insensitive default filesystem (macOS). A case-variant path such as
    SERVICES/dope-context/src/search/hybrid_search.py or
    src/dopemux_pr_merge_specialist/QUEUE_DRAIN.py resolved to a protected file
    but was allowed through.
    
    _repo_relative_candidates now yields the exact-case reading first and a
    case-folded reading second; any candidate matching the lane denies.
    Carve-out (eval/**) still passes in exact case; a case-variant of the
    carve-out itself (EVAL/) is denied fail-closed.
    
    Tests: 8 new case-variant/fold cases in tests/test_dcp_surface_guard.py
    (37 pass); scanner suite unchanged (32 pass).
    
    Audit: AGY/Gemini round-2 finding F-001-A (proof/pr_merge/embedded-audit/pr-1304/round2).

diff --git a/.claude/hooks/dcp_surface_guard.py b/.claude/hooks/dcp_surface_guard.py
index 3ae937a68..324744bf3 100644
--- a/.claude/hooks/dcp_surface_guard.py
+++ b/.claude/hooks/dcp_surface_guard.py
@@ -57,7 +57,10 @@ def _repo_relative_candidates(file_path: str, project_root: Path) -> tuple[str,
       2. ``os.path.realpath`` of the path relative to the root and to the
          root's own realpath (resolves ``..`` and symlinks, including a
          symlink placed inside an exempted directory);
-      3. a case-folded prefix match against those roots.
+      3. a case-folded prefix match against those roots;
+      4. the fully case-folded form of each of the above (re-audit residual
+         F-001-A: intra-repo case variants such as ``SERVICES/...`` on a
+         case-insensitive volume; ``realpath`` does not correct case).
 
     Paths that cannot be placed inside the root under any reading are not
     repo files (e.g. memory files under ``~/.claude``) and are returned as
@@ -99,6 +102,15 @@ def _repo_relative_candidates(file_path: str, project_root: Path) -> tuple[str,
                     found.append(tail.as_posix())
     if not found:
         return (raw.as_posix(),)
+    # ADR-226 re-audit residual F-001-A: on a case-insensitive filesystem
+    # `SERVICES/dope-context/src/x.py` is the same file as the lower-case
+    # spelling, `os.path.realpath` does NOT correct the case of existing
+    # components on macOS, and the red-lane patterns are lower-case literals.
+    # Adding the case-folded reading of every candidate can only ADD denials
+    # (the carve-out is a negative lookahead inside a deny pattern, so a
+    # folded candidate never widens it) and needs no filesystem I/O, so it is
+    # applied unconditionally rather than only on case-insensitive volumes.
+    found.extend([f.lower() for f in found])
     return tuple(dict.fromkeys(found))
 
 
diff --git a/tests/test_dcp_surface_guard.py b/tests/test_dcp_surface_guard.py
index f943b2db4..d9945269f 100644
--- a/tests/test_dcp_surface_guard.py
+++ b/tests/test_dcp_surface_guard.py
@@ -18,6 +18,7 @@ from dcp_surface_guard import (  # noqa: E402
     RED_LANE_ID,
     _FALLBACK_COMPILED,
     _repo_relative,
+    _repo_relative_candidates,
     surface_guard_block,
     surface_guard_warnings,
 )
@@ -259,6 +260,58 @@ def test_repo_relative_primary_reading_unchanged():
     assert _repo_relative(fp, _ROOT) == "services/dope-context/eval/run_eval.py"
 
 
+# ---------------------------------------------------------------------------
+# ADR-226 re-audit residual F-001-A (2026-09-03, CONFIRMED live on macOS):
+# intra-repo case variants. `realpath` keeps the supplied case of existing
+# components, so `SERVICES/dope-context/src/x.py` matched nothing while the
+# OS wrote to the real file. The case-folded candidate is filesystem-independent,
+# so these tests are unconditional (they also hold on case-sensitive volumes,
+# where the fold is a deliberate fail-closed over-block).
+# ---------------------------------------------------------------------------
+
+_CASE_VARIANT_TARGETS = (
+    "SERVICES/dope-context/src/search/hybrid_search.py",
+    "services/DOPE-CONTEXT/src/search/hybrid_search.py",
+    "services/dope-context/src/search/HYBRID_SEARCH.py",
+    "src/dopemux_pr_merge_specialist/QUEUE_DRAIN.py",
+    "SRC/dopemux_pr_merge_specialist/queue_drain.py",
+)
+
+
+def test_intra_repo_case_variant_is_blocked():
+    for rel in _CASE_VARIANT_TARGETS:
+        fp = str(_ROOT / rel)
+        result = surface_guard_block("Edit", {"file_path": fp}, _ROOT)
+        assert result is not None, fp
+        assert RED_LANE_ID in result
+
+
+def test_case_variant_root_and_intra_repo_combined_is_blocked():
+    fp = f"{str(_ROOT).swapcase()}/SERVICES/dope-context/src/search/hybrid_search.py"
+    result = surface_guard_block("Write", {"file_path": fp}, _ROOT)
+    assert result is not None, fp
+    assert RED_LANE_ID in result
+
+
+def test_case_folded_candidate_is_present():
+    fp = str(_ROOT / "SERVICES" / "dope-context" / "src" / "search" / "hybrid_search.py")
+    cands = _repo_relative_candidates(fp, _ROOT)
+    assert "services/dope-context/src/search/hybrid_search.py" in cands
+    # primary (exact-case) reading is unchanged and still first
+    assert cands[0] == "SERVICES/dope-context/src/search/hybrid_search.py"
+
+
+def test_case_variant_of_exempt_dir_is_fail_closed():
+    """`EVAL/` is not the carve-out spelling; blocking it is the fail-closed choice."""
+    fp = str(_ROOT / "services" / "dope-context" / "EVAL" / "new_probe.py")
+    assert surface_guard_block("Write", {"file_path": fp}, _ROOT) is not None
+
+
+def test_exact_case_exempt_path_still_allowed_after_fold():
+    fp = str(_ROOT / "services" / "dope-context" / "eval" / "run_eval.py")
+    assert surface_guard_block("Edit", {"file_path": fp}, _ROOT) is None
+
+
 # ---------------------------------------------------------------------------
 # Sync test: fallback ⊆ live FORBIDDEN_PATHS
 # ---------------------------------------------------------------------------
```

## Full post-fix file: .claude/hooks/dcp_surface_guard.py
```python
"""
DCP surface guard for PreToolUse.

Two tiers:
  BLOCK — hard deny on red-lane seam files (DCP-RED-MERGE-SEAM-0001).
  WARN  — one-time advisory when contract-sensitive DCP surfaces are edited.

All functions are pure and never raise; hook failures must not block work.
Reference: docs/03-reference/dcp/README.md, AGENTS.md DCP-RED-MERGE-SEAM-0001
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Red-lane block tier
# ---------------------------------------------------------------------------

RED_LANE_ID = "DCP-RED-MERGE-SEAM-0001"

# Hardcoded fallback patterns so the seam stays guarded even when the
# dopemux package import fails. Must remain ⊆ red_lane_rules.FORBIDDEN_PATHS.
# A sync test enforces this invariant.
_FALLBACK_FORBIDDEN: tuple[str, ...] = (
    r"^src/dopemux_pr_merge_specialist/queue_drain\.py$",
    r"^dopemux_pr_merge_specialist/queue_drain\.py$",
    r"^scripts/batch_resolve_and_merge\.py$",
)
_FALLBACK_COMPILED = tuple(re.compile(p) for p in _FALLBACK_FORBIDDEN)


def _forbidden_patterns() -> tuple[re.Pattern, ...]:
    """Prefer dopemux.dcp.red_lane_rules.FORBIDDEN_PATHS; fall back to hardcoded."""
    try:
        from dopemux.dcp.red_lane_rules import FORBIDDEN_PATHS  # type: ignore[import]
        return tuple(FORBIDDEN_PATHS)
    except Exception:
        return _FALLBACK_COMPILED


def _repo_relative_candidates(file_path: str, project_root: Path) -> tuple[str, ...]:
    """Every repo-relative reading of ``file_path`` that lands inside the root.

    Hardened after the ADR-226 independent audit (F-001): a purely lexical
    ``Path.relative_to`` let ``<root>/../<root>/x``, a case-variant root
    (``/USERS/...`` is the same file on macOS's default filesystem) and a
    symlink alias of the root yield strings that no ``^``-anchored red-lane
    pattern matches. The block tier therefore evaluates *all* of:

      1. the raw path relative to the root (lexical; an in-tree ``..`` is kept
         so the rules' own traversal guard can match it, a leading ``..`` is
         dropped as it escapes the root);
      2. ``os.path.realpath`` of the path relative to the root and to the
         root's own realpath (resolves ``..`` and symlinks, including a
         symlink placed inside an exempted directory);
      3. a case-folded prefix match against those roots;
      4. the fully case-folded form of each of the above (re-audit residual
         F-001-A: intra-repo case variants such as ``SERVICES/...`` on a
         case-insensitive volume; ``realpath`` does not correct case).

    Paths that cannot be placed inside the root under any reading are not
    repo files (e.g. memory files under ``~/.claude``) and are returned as
    given, which is the pre-existing behaviour.
    """
    raw = Path(file_path)
    candidates = [raw]
    try:
        real = Path(os.path.realpath(file_path))
        if real != raw:
            candidates.append(real)
    except (OSError, ValueError):
        pass
    roots = [Path(project_root)]
    try:
        real_root = Path(os.path.realpath(project_root))
        if real_root != roots[0]:
            roots.append(real_root)
    except (OSError, ValueError):
        pass

    found: list[str] = []
    for cand in candidates:
        for root in roots:
            try:
                rel = cand.relative_to(root)
            except ValueError:
                continue
            if rel.parts and rel.parts[0] == "..":
                continue  # lexically escapes the root; realpath reading covers it
            found.append(rel.as_posix())
    for cand in candidates:
        cand_s = cand.as_posix()
        for root in roots:
            root_s = root.as_posix().rstrip("/") + "/"
            if cand_s.lower().startswith(root_s.lower()):
                tail = Path(cand_s[len(root_s):])
                if not (tail.parts and tail.parts[0] == ".."):
                    found.append(tail.as_posix())
    if not found:
        return (raw.as_posix(),)
    # ADR-226 re-audit residual F-001-A: on a case-insensitive filesystem
    # `SERVICES/dope-context/src/x.py` is the same file as the lower-case
    # spelling, `os.path.realpath` does NOT correct the case of existing
    # components on macOS, and the red-lane patterns are lower-case literals.
    # Adding the case-folded reading of every candidate can only ADD denials
    # (the carve-out is a negative lookahead inside a deny pattern, so a
    # folded candidate never widens it) and needs no filesystem I/O, so it is
    # applied unconditionally rather than only on case-insensitive volumes.
    found.extend([f.lower() for f in found])
    return tuple(dict.fromkeys(found))


def _repo_relative(file_path: str, project_root: Path) -> str:
    """Normalize file_path to forward-slash repo-relative string (primary reading)."""
    return _repo_relative_candidates(file_path, project_root)[0]


def surface_guard_block(tool_name: str, tool_input: dict, project_root: Path) -> str | None:
    """Return a block reason when an edit targets a red-lane seam file, else None."""
    if tool_name not in {"Edit", "Write", "NotebookEdit"}:
        return None
    file_path = str((tool_input or {}).get("file_path") or "")
    if not file_path:
        return None
    patterns = _forbidden_patterns()
    for rel in _repo_relative_candidates(file_path, project_root):
        if any(p.search(rel) for p in patterns):
            return (
                f"🚫 `{rel}` is protected by red lane {RED_LANE_ID} "
                f"(merge-seam, execute=True). Edits are hard-blocked. "
                f"If this change is genuinely required, the seam must be lifted "
                f"via its own ADR + task packet — not an inline edit. "
                f"See docs/03-reference/dcp/README.md."
            )
    return None


# ---------------------------------------------------------------------------
# Contract-sensitive warn tier
# ---------------------------------------------------------------------------

_CACHE_FILENAME = ".surface-guard-warned.json"

# (glob_pattern, category_label) — matched against repo-relative posix paths
_CONTRACT_SURFACES: tuple[tuple[str, str], ...] = (
    ("schemas/dcp/**", "DCP authority contract schema"),
    ("schemas/proof/**", "proof contract schema (CI-enforced)"),
    ("schemas/audit/**", "audit contract schema (CI-enforced)"),
    ("services/dcp-readonly-facade/src/dcp_facade/route_manifest.py",
     "facade allow/deny authority (DENIED_TOKENS — canonical writer)"),
    ("docs/03-reference/dcp/chatgpt-mcp-readonly/TOOL_CONTRACT.md",
     "published DCP tool contract"),
    ("docs/03-reference/dcp/chatgpt-mcp-readonly/RESPONSE_ENVELOPE_SCHEMA.md",
     "published DCP response envelope contract"),
    ("docs/03-reference/dcp/chatgpt-mcp-readonly/SECURITY_MODEL.md",
     "DCP security model (loopback-only constraint)"),
    ("docs/03-reference/dcp/chatgpt-mcp-readonly/MULTI_PROJECT_REGISTRY_CONTRACT.md",
     "multi-project registry contract"),
    ("mcp_catalog.yaml", "MCP server catalog (canonical source of truth)"),
    (".mcp.json", "per-worktree MCP manifest"),
)


def _matches_contract_surface(rel: str) -> str | None:
    """Return the category label for the first matching surface, else None."""
    for pattern, label in _CONTRACT_SURFACES:
        if "**" in pattern:
            # fnmatch doesn't handle ** natively for path separators
            prefix = pattern.replace("/**", "")
            if rel.startswith(prefix + "/") or rel == prefix:
                return label
        elif fnmatch.fnmatch(rel, pattern) or rel == pattern:
            return label
    return None


def _proof_json_is_new(file_path: str) -> bool:
    """True when the target path is proof/**/PROOF.json and the file doesn't
    exist yet (scaffold flow) — suppress the warn-tier in that case."""
    if "proof" in file_path and file_path.endswith("PROOF.json"):
        return not Path(file_path).exists()
    return False


def _load_warn_cache(project_root: Path) -> dict:
    try:
        return json.loads((project_root / ".claude" / _CACHE_FILENAME).read_text())
    except Exception:
        return {}


def _save_warn_cache(project_root: Path, cache: dict) -> None:
    try:
        p = project_root / ".claude" / _CACHE_FILENAME
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(cache))
    except Exception:
        pass


def surface_guard_warnings(
    tool_name: str,
    tool_input: dict,
    project_root: Path,
    session_id: str | None = None,
) -> list[str]:
    """Return once-per-(session, path) advisory when editing a contract surface."""
    if tool_name not in {"Edit", "Write", "NotebookEdit"}:
        return []
    file_path = str((tool_input or {}).get("file_path") or "")
    if not file_path:
        return []

    # Don't warn on new proof/*/PROOF.json writes (that's the scaffold flow)
    if _proof_json_is_new(file_path):
        return []

    category = None
    for rel in _repo_relative_candidates(file_path, project_root):
        category = _matches_contract_surface(rel)
        if category:
            break
    if not category:
        return []

    session_key = session_id or "no-session"
    cache_key = f"{session_key}:{file_path}"
    cache = _load_warn_cache(project_root)
    if cache.get(cache_key):
        return []

    cache[cache_key] = True
    _save_warn_cache(project_root, cache)

    return [
        f"⚠️ Contract-sensitive surface ({category}): identify the canonical writer "
        f"and consumers before editing. See governance: contract-sensitive surfaces. "
        f"For facade surfaces, run /dcp:denylist-check after."
    ]
```

## Full post-fix file: tests/test_dcp_surface_guard.py
```python
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
```

## FORBIDDEN_PATHS (src/dopemux/dcp/red_lane_rules.py, unchanged since round 2)
```python
FORBIDDEN_PATHS = [
    re.compile(r"^src/dopemux" + r"_pr_merge_specialist/queue" + r"_drain\.py$"),
    re.compile(r"^dopemux" + r"_pr_merge_specialist/queue" + r"_drain\.py$"),
    re.compile(r"^scripts/batch" + r"_resolve_and_merge\.py$"),
    # DCP-RED-MERGE-SEAM-0001 narrow carve-out (ADR-224, TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001R
    # Phase A): exactly these two top-level workflow files are exempt from the path-level
    # block so their content can eventually be edited to wire embedded-audit schema
    # validation. Every other path under .github/workflows/ (including subdirectories and
    # any near-miss filename) remains hard-blocked. TEXT_RULES content scanning in
    # red_lane_scanner.py is untouched by this carve-out and still applies to these files.
    re.compile(
        r"^\.github/workflows/"
        r"(?!embedded-audit\.yml$)(?!pr-steward\.yml$)"
        r".*$"
    ),
    re.compile(r"^scripts/" + r"dopetask$"),
    re.compile(r"^scripts/" + r"taskx$"),
    re.compile(r"^services/task-orchestrator/.*$"),
    re.compile(r"^services/dopecon-bridge/.*$"),
    # DCP-RED-MERGE-SEAM-0001 narrow carve-out (ADR-226, TP-DOPECONTEXT-VECTOR-SPACE-0004
    # governance amendment 2026-09-03): the offline benchmark harness directory
    # services/dope-context/eval/ and exactly the three service files named in packet
    # 0004's Allowed Files are exempt from the path-level block. Every other path under
    # services/dope-context/ (the rest of src/ and tests/, Dockerfile, constraints,
    # near-miss filenames, same-named files in other directories) remains hard-blocked.
    # TEXT_RULES content scanning in red_lane_scanner.py is untouched by this carve-out
    # and still applies to the exempted paths.
    re.compile(
        r"^services/dope-context/"
        r"(?!eval/)"
        r"(?!src/pipeline/indexing_pipeline\.py$)"
        r"(?!src/mcp/server\.py$)"
        r"(?!tests/test_vector_space_invariants\.py$)"
        r".*$"
    ),
    # Companion to the carve-out above. The hook's primary path reading is lexical (no
    # `..` resolution); the realpath reading it also checks since the ADR-226 audit
    # (F-001) is defence-in-depth, so a directory-scoped exemption must still refuse any
    # traversal segment on its own or `services/dope-context/eval/../src/x.py` would
    # escape the block. Applies to the whole service subtree; an exact `..` segment is
    # the only thing it matches (`something..` or `..foo` are ordinary names).
    re.compile(r"^services/dope-context/(?:.*/)?\.\.(?:/|$)"),
    re.compile(r"^services/working-memory-assistant/.*$"),
    re.compile(r"^docker/mcp-servers-source/conport/.*$"),
    re.compile(r"^src/conport/.*$")
]

TEXT_RULES = [
    Rule(
        rule_id="MERGE_SEAM_001",
        category="MERGE_SEAM_VIOLATION",
        severity="BLOCKER",
        description="Forbidden merge-seam import or call",
        patterns=[
            re.compile(r"queue" + r"_drain"),
            re.compile(r"batch" + r"_resolve_and_merge"),
            re.compile(r"dopemux" + r"_pr_merge_specialist"),
            re.compile(r"gh pr " + r"merge"),
            re.compile(r"gh " + r"api"),
            re.compile(r"gh pr " + r"review"),
            re.compile(r"gh pr " + r"comment"),
            re.compile(r"gh pr " + r"edit")
        ],
        recommended_action="Remove merge-seam invocation. DCP Core must not orchestrate PR logic."
    ),
    Rule(
        rule_id="DOPETASK_001",
        category="DOPETASK_EXECUTION",
        severity="BLOCKER",
        description="Forbidden Dopetask execution path",
        patterns=[
            re.compile(r"dopetask " + r"tp"),
            re.compile(r"scripts/" + r"dopetask"),
            re.compile(r"scripts/" + r"taskx")
        ],
        recommended_action="Remove Dopetask invocation."
    ),
    Rule(
        rule_id="NETWORK_001",
        category="FORBIDDEN_CALL",
        severity="BLOCKER",
        description="Forbidden network library or sub" + "process call",
        patterns=[
            re.compile(r"sub" + r"process"),
            re.compile(r"requests" + r"\."),
            re.compile(r"httpx" + r"\."),
            re.compile(r"urllib"),
            re.compile(r"aiohttp")
        ],
        recommended_action="Remove network/sub" + "process calls from DCP Core."
    ),
    Rule(
        rule_id="EXTERNAL_WRITE_001",
        category="EXTERNAL_WRITE_STATUS",
        severity="BLOCKER",
        description="Forbidden external state mutation via Task-Orchestrator, memory, etc.",
        patterns=[
            re.compile(r"mem\.upsert"),
            re.compile(r"memory" + r"_store"),
            re.compile(r"/tools/memory" + r"_store"),
            re.compile(r"/tools/memory" + r"_correct"),
            re.compile(r"/api/" + r"decisions"),
            re.compile(r"/api/" + r"progress"),
            re.compile(r"/api/" + r"custom_data"),
            re.compile(r"/api/" + r"workflow"),
            re.compile(r"/api/" + r"pm"),
            re.compile(r"/route/" + r"pm")
        ],
        recommended_action="Remove external state mutations."
    ),
    Rule(
        rule_id="LIVE_WRITE_001",
        category="LIVE_WRITE_CREEP",
        severity="BLOCKER",
        description="Forbidden enablement of LIVE_WRITE_READY",
        patterns=[
            re.compile(r"LIVE_WRITE_READY\s*=\s*True"),
            re.compile(r"LIVE_WRITE_READY:\s*true"),
            re.compile(r"\"live_write_ready\":\s*true"),
            re.compile(r"\"live_write_status\":\s*\"ENABLED\""),
            re.compile(r"\"live_write_status\":\s*\"ACTIVE\"")
        ],
        recommended_action="Do not enable LIVE_WRITE_READY."
    )
]

def is_safe_false_positive(file_path: str) -> bool:
    """Check if the file is a scanner declaration that should be ignored. Test fixtures are NOT exempted and will be blocked."""
    if file_path.endswith("dcp/red_lane_rules.py") or file_path.endswith("dcp/red_lane_scanner.py"):
        return True
    return False

def redact_secret_like(text: str) -> str:
    """Redacts values that look like secrets (hex tokens, typical credentials)."""
    # Just a placeholder basic redaction logic. Real logic would match keys/tokens.
    # We redact tokens resembling hex/auth keys if found in match context.
    redacted = re.sub(r"([a-zA-Z0-9_-]{20,})", "***REDACTED***", text)
    return redacted
```

## Evidence provided by the implementer (not to be trusted without your own reasoning)
- pytest at 9ef316d1b1327e201184e7bdf5dbf943f88b8fa3: 69 passed in 0.14s (tests/test_dcp_surface_guard.py + tests/dcp/test_dcp_0005_red_lane_scanner.py).
- In-process probes of surface_guard_block('Write', {'file_path': <root>/<p>}, <root>) at 9ef316d1b1327e201184e7bdf5dbf943f88b8fa3:
```
services/dope-context/src/search/hybrid_search.py            blocked=True
SERVICES/dope-context/src/search/hybrid_search.py            blocked=True
services/DOPE-CONTEXT/src/search/hybrid_search.py            blocked=True
src/dopemux_pr_merge_specialist/QUEUE_DRAIN.py               blocked=True
services/dope-context/eval/run_eval.py                       blocked=False
services/dope-context/EVAL/run_eval.py                       blocked=True
services/dope-context/README.md                              blocked=True
services/dope-context/eval/../src/x.py                       blocked=True
```
- Known, accepted residuals already recorded in round2/REMEDIATION.json: the fold is a lexical str.lower() (not filesystem-aware; applied unconditionally, so on a case-SENSITIVE volume a distinct file named e.g. SERVICES/... would be over-denied — fail-closed); non-ASCII case (e.g. Turkish dotless i, casefold vs lower) is not folded, but no red-lane pattern contains non-ASCII letters; the EVAL/ case-variant of the carve-out is denied fail-closed.

## Required output
Return STRICT JSON only (no prose outside the JSON) with this shape:
{"auditor_model": "<your exact model id>", "target_commit": "9ef316d1b1327e201184e7bdf5dbf943f88b8fa3", "finding": "F-001-A", "verdict": "CLOSED" | "OPEN" | "CLOSED_WITH_RISKS", "reasoning": "<concise>", "residual_risks": [{"id": "...", "severity": "LOW|MEDIUM|HIGH", "description": "...", "recommended_action": "..."}], "regressions_introduced": [ ... same shape ... ], "bypass_attempts_considered": ["<list every path spelling / OS behaviour you reasoned about, e.g. mixed case in every segment, unicode case (ß, İ, K Kelvin sign), NFC/NFD normalisation, symlinks inside eval/, hard links, trailing slash, ./ segments, Windows separators, 8.3 short names, absolute vs relative, the empty-candidate fallback branch>"]}
