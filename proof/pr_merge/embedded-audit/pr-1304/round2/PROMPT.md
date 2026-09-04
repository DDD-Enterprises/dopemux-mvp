You are the independent Tier-1 auditor (AGY / gemini-3.1-pro-high) for repository dopemux-mvp. This is a DELTA RE-AUDIT of one finding from your own audit of ADR-226 earlier today (2026-09-03). Audit ONLY the remediation of F-001; do not re-open other findings unless the fix itself introduces a regression.

## Context
ADR-226 narrows the DCP-RED-MERGE-SEAM-0001 red lane to allow edits to services/dope-context/eval/** and services/dope-context/README.md (a directory-scoped carve-out) while every other path under services/dope-context remains hard-denied by the PreToolUse hook .claude/hooks/dcp_surface_guard.py. Repo-relative path normalisation is the primary reading; a companion FORBIDDEN_PATHS regex in src/dopemux/dcp/red_lane_rules.py refuses any `..` segment under services/dope-context.

## Your finding F-001 (verbatim from the amended ADR)
## Independent audit (2026-09-03)

Route: AGY (`agy --model gemini-3.1-pro-high --output-format json
--print=...`), Tier-1 route #1, on frozen head `720991c41`; the CLI log
records the requested model propagated to the backend
(`promptLength=211583, model="gemini-3.1-pro-high"`). Verdict on that
head: **FAIL**, one BLOCKER.

* **F-001 CONFIRMED (pre-existing, fixed here).** `_repo_relative` in
  `.claude/hooks/dcp_surface_guard.py` was purely lexical, so
  `<root>/../<worktree>/<blocked>`, a case-variant root (`/USERS/...` is
  the same file on macOS's default filesystem) and a symlink alias of the
  root all produced strings no `^`-anchored pattern matched — for every
  red-lane path, `queue_drain.py` included. Reproduced programmatically
  before the fix. Fix: `_repo_relative_candidates` evaluates the raw,
  realpath and case-folded readings and the block tier denies if any
  matches; the same candidates feed the warn tier. Seven tests pin the
  bypass forms plus the two things that must keep working (new file under
  `eval/`, paths outside the root).
* **F-002 REJECTED.** Claimed the packet-0004 diff was absent from the PR;
  the prompt contained all 11 diff headers including
  `task-packets/dope-context/TP-DOPECONTEXT-VECTOR-SPACE-0004.md`.
* **F-003 REJECTED.** Claimed the traversal regex matches names ending in
  `..`; it matches only an exact `..` segment (`something..`, `..foo`,
  `a../b.py` do not match — verified).
* **F-004** (test coverage for the bypass forms) is subsumed by the F-001
  fix.
* Auditor's one unverifiable claim (README's `--corpus` guard) is
  verified at `services/dope-context/eval/run_eval.py:662`.

The proof bundle, raw auditor output and the re-audit on the post-fix
frozen head live under `proof/pr_merge/embedded-audit/pr-1304/`.

## Consequences

## Remediation under audit — commit 1d87cb73284b4019aff0d7cfe2525baa626cb7cf
```diff
commit 1d87cb73284b4019aff0d7cfe2525baa626cb7cf
fix(hooks): ADR-226 F-001 — dcp_surface_guard evaluates every lexical + realpath reading of a path

Closes AGY re-audit finding F-001 (independent audit 2026-09-03): a
`..` traversal or case-folded spelling of a DCP-RED-MERGE-SEAM-0001
file could reach the carve-out branch via the single normalised reading.
The guard now collects the raw lexical reading (in-tree `..` kept so the
red-lane traversal regex matches), the case-folded reading, and the
realpath reading, and fails closed if ANY of them is blocked. Adds
regression tests; ADR-226 amended (Independent audit / Consequences).

Co-Authored-By: Claude <noreply@anthropic.com>


diff --git a/.claude/hooks/dcp_surface_guard.py b/.claude/hooks/dcp_surface_guard.py
index 62fa3c076..3ae937a68 100644
--- a/.claude/hooks/dcp_surface_guard.py
+++ b/.claude/hooks/dcp_surface_guard.py
@@ -12,6 +12,7 @@ from __future__ import annotations
 
 import fnmatch
 import json
+import os
 import re
 from pathlib import Path
 
@@ -41,13 +42,69 @@ def _forbidden_patterns() -> tuple[re.Pattern, ...]:
         return _FALLBACK_COMPILED
 
 
-def _repo_relative(file_path: str, project_root: Path) -> str:
-    """Normalize file_path to forward-slash repo-relative string."""
+def _repo_relative_candidates(file_path: str, project_root: Path) -> tuple[str, ...]:
+    """Every repo-relative reading of ``file_path`` that lands inside the root.
+
+    Hardened after the ADR-226 independent audit (F-001): a purely lexical
+    ``Path.relative_to`` let ``<root>/../<root>/x``, a case-variant root
+    (``/USERS/...`` is the same file on macOS's default filesystem) and a
+    symlink alias of the root yield strings that no ``^``-anchored red-lane
+    pattern matches. The block tier therefore evaluates *all* of:
+
+      1. the raw path relative to the root (lexical; an in-tree ``..`` is kept
+         so the rules' own traversal guard can match it, a leading ``..`` is
+         dropped as it escapes the root);
+      2. ``os.path.realpath`` of the path relative to the root and to the
+         root's own realpath (resolves ``..`` and symlinks, including a
+         symlink placed inside an exempted directory);
+      3. a case-folded prefix match against those roots.
+
+    Paths that cannot be placed inside the root under any reading are not
+    repo files (e.g. memory files under ``~/.claude``) and are returned as
+    given, which is the pre-existing behaviour.
+    """
+    raw = Path(file_path)
+    candidates = [raw]
+    try:
+        real = Path(os.path.realpath(file_path))
+        if real != raw:
+            candidates.append(real)
+    except (OSError, ValueError):
+        pass
+    roots = [Path(project_root)]
     try:
-        rel = Path(file_path).relative_to(project_root)
-    except ValueError:
-        rel = Path(file_path)
-    return rel.as_posix()
+        real_root = Path(os.path.realpath(project_root))
+        if real_root != roots[0]:
+            roots.append(real_root)
+    except (OSError, ValueError):
+        pass
+
+    found: list[str] = []
+    for cand in candidates:
+        for root in roots:
+            try:
+                rel = cand.relative_to(root)
+            except ValueError:
+                continue
+            if rel.parts and rel.parts[0] == "..":
+                continue  # lexically escapes the root; realpath reading covers it
+            found.append(rel.as_posix())
+    for cand in candidates:
+        cand_s = cand.as_posix()
+        for root in roots:
+            root_s = root.as_posix().rstrip("/") + "/"
+            if cand_s.lower().startswith(root_s.lower()):
+                tail = Path(cand_s[len(root_s):])
+                if not (tail.parts and tail.parts[0] == ".."):
+                    found.append(tail.as_posix())
+    if not found:
+        return (raw.as_posix(),)
+    return tuple(dict.fromkeys(found))
+
+
+def _repo_relative(file_path: str, project_root: Path) -> str:
+    """Normalize file_path to forward-slash repo-relative string (primary reading)."""
+    return _repo_relative_candidates(file_path, project_root)[0]
 
 
 def surface_guard_block(tool_name: str, tool_input: dict, project_root: Path) -> str | None:
@@ -57,9 +114,9 @@ def surface_guard_block(tool_name: str, tool_input: dict, project_root: Path) ->
     file_path = str((tool_input or {}).get("file_path") or "")
     if not file_path:
         return None
-    rel = _repo_relative(file_path, project_root)
-    for pattern in _forbidden_patterns():
-        if pattern.search(rel):
+    patterns = _forbidden_patterns()
+    for rel in _repo_relative_candidates(file_path, project_root):
+        if any(p.search(rel) for p in patterns):
             return (
                 f"🚫 `{rel}` is protected by red lane {RED_LANE_ID} "
                 f"(merge-seam, execute=True). Edits are hard-blocked. "
@@ -150,8 +207,11 @@ def surface_guard_warnings(
     if _proof_json_is_new(file_path):
         return []
 
-    rel = _repo_relative(file_path, project_root)
-    category = _matches_contract_surface(rel)
+    category = None
+    for rel in _repo_relative_candidates(file_path, project_root):
+        category = _matches_contract_surface(rel)
+        if category:
+            break
     if not category:
         return []
 
diff --git a/docs/90-adr/adr-226-dope-context-seam-narrow-carveout.md b/docs/90-adr/adr-226-dope-context-seam-narrow-carveout.md
index 866e56ecc..80eefa7fc 100644
--- a/docs/90-adr/adr-226-dope-context-seam-narrow-carveout.md
+++ b/docs/90-adr/adr-226-dope-context-seam-narrow-carveout.md
@@ -123,9 +123,12 @@ Constraints:
   carved-out paths.
 * Only paths already named in packet 0004's Allowed Files are exempted. No
   other file under `services/dope-context/` becomes editable.
-* The hook's path normalizer (`_repo_relative`) is lexical — it does not
-  resolve `..` — so a directory-scoped exemption must be paired with an
-  explicit traversal guard.
+* The hook's primary path reading (`_repo_relative`) is lexical — it does
+  not resolve `..` — so a directory-scoped exemption must be paired with an
+  explicit traversal guard. Since the independent audit (F-001, see
+  "Independent audit" below) the block tier also evaluates a realpath
+  reading and a case-folded root match; the traversal guard stays as
+  defence-in-depth.
 * The change must not disturb the sibling service blankets or the
   fallback ⊆ live sync invariant.
 
@@ -181,7 +184,9 @@ Invariants:
   continues to hold without modification.
 * No symlinks may exist under `services/dope-context/eval/` (a symlink
   inside the exempted directory could write through to a blocked path). A
-  filesystem test pins this.
+  filesystem test pins this, and since audit F-001 the hook also resolves
+  an existing symlink at edit time and blocks when its target is a blocked
+  path.
 
 Non-goals:
 
@@ -263,6 +268,39 @@ Relocation note (2026-09-03): the results file now lives at
 under `claudedocs/` or `docs/` regardless of this carve-out; the historical
 path references above are kept as written.
 
+## Independent audit (2026-09-03)
+
+Route: AGY (`agy --model gemini-3.1-pro-high --output-format json
+--print=...`), Tier-1 route #1, on frozen head `720991c41`; the CLI log
+records the requested model propagated to the backend
+(`promptLength=211583, model="gemini-3.1-pro-high"`). Verdict on that
+head: **FAIL**, one BLOCKER.
+
+* **F-001 CONFIRMED (pre-existing, fixed here).** `_repo_relative` in
+  `.claude/hooks/dcp_surface_guard.py` was purely lexical, so
+  `<root>/../<worktree>/<blocked>`, a case-variant root (`/USERS/...` is
+  the same file on macOS's default filesystem) and a symlink alias of the
+  root all produced strings no `^`-anchored pattern matched — for every
+  red-lane path, `queue_drain.py` included. Reproduced programmatically
+  before the fix. Fix: `_repo_relative_candidates` evaluates the raw,
+  realpath and case-folded readings and the block tier denies if any
+  matches; the same candidates feed the warn tier. Seven tests pin the
+  bypass forms plus the two things that must keep working (new file under
+  `eval/`, paths outside the root).
+* **F-002 REJECTED.** Claimed the packet-0004 diff was absent from the PR;
+  the prompt contained all 11 diff headers including
+  `task-packets/dope-context/TP-DOPECONTEXT-VECTOR-SPACE-0004.md`.
+* **F-003 REJECTED.** Claimed the traversal regex matches names ending in
+  `..`; it matches only an exact `..` segment (`something..`, `..foo`,
+  `a../b.py` do not match — verified).
+* **F-004** (test coverage for the bypass forms) is subsumed by the F-001
+  fix.
+* Auditor's one unverifiable claim (README's `--corpus` guard) is
+  verified at `services/dope-context/eval/run_eval.py:662`.
+
+The proof bundle, raw auditor output and the re-audit on the post-fix
+frozen head live under `proof/pr_merge/embedded-audit/pr-1304/`.
+
 ## Consequences
 
 * **Easier**: the benchmark harness can be committed and iterated, and
@@ -286,10 +324,12 @@ path references above are kept as written.
 * **Failure modes introduced**: one considered and closed. A directory
   exemption plus a lexical normalizer would have allowed
   `eval/../src/x.py`; the companion `..`-segment pattern and its tests
-  close it. Residual: a symlink placed under `eval/` after this lands
-  would be caught by the filesystem test only when the suite runs, not by
-  the hook at edit time. Accepted and pinned as a stop condition in the
-  packet amendment.
+  close it. The independent audit then found the pre-existing, wider
+  form of the same weakness (F-001) and it is fixed in this change — see
+  "Independent audit" below. Residual: a symlink created under `eval/`
+  between the hook check and the write (TOCTOU) is caught only by the
+  filesystem test. Accepted and pinned as a stop condition in the packet
+  amendment.
 
 ────────────────────────────────────────────────────────────
 
@@ -318,7 +358,8 @@ pushed at draft time, so no remote state to unwind.
 ## Verification
 
 * Tests added: `tests/test_dcp_surface_guard.py` (4 new functions,
-  table-driven) and `tests/dcp/test_dcp_0005_red_lane_scanner.py` (3 new).
+  table-driven, plus 7 F-001 bypass tests) and
+  `tests/dcp/test_dcp_0005_red_lane_scanner.py` (3 new).
 * Commands to run:
   `PYTHONPATH=src python -m pytest tests/test_dcp_surface_guard.py tests/dcp/test_dcp_0005_red_lane_scanner.py -v`
 * Expected signals: full pass, including the pre-existing ADR-224 tests
diff --git a/src/dopemux/dcp/red_lane_rules.py b/src/dopemux/dcp/red_lane_rules.py
index f145c83c1..56594b484 100644
--- a/src/dopemux/dcp/red_lane_rules.py
+++ b/src/dopemux/dcp/red_lane_rules.py
@@ -47,10 +47,12 @@ FORBIDDEN_PATHS = [
         r"(?!tests/test_vector_space_invariants\.py$)"
         r".*$"
     ),
-    # Companion to the carve-out above. The hook's path normalizer is lexical (no `..`
-    # resolution), so a directory-scoped exemption must refuse any traversal segment or
-    # `services/dope-context/eval/../src/x.py` would escape the block. Applies to the
-    # whole service subtree; an exact `..` segment is the only thing it matches.
+    # Companion to the carve-out above. The hook's primary path reading is lexical (no
+    # `..` resolution); the realpath reading it also checks since the ADR-226 audit
+    # (F-001) is defence-in-depth, so a directory-scoped exemption must still refuse any
+    # traversal segment on its own or `services/dope-context/eval/../src/x.py` would
+    # escape the block. Applies to the whole service subtree; an exact `..` segment is
+    # the only thing it matches (`something..` or `..foo` are ordinary names).
     re.compile(r"^services/dope-context/(?:.*/)?\.\.(?:/|$)"),
     re.compile(r"^services/working-memory-assistant/.*$"),
     re.compile(r"^docker/mcp-servers-source/conport/.*$"),
diff --git a/tests/test_dcp_surface_guard.py b/tests/test_dcp_surface_guard.py
index c183b8953..f943b2db4 100644
--- a/tests/test_dcp_surface_guard.py
+++ b/tests/test_dcp_surface_guard.py
@@ -183,6 +183,82 @@ def test_no_symlinks_under_dope_context_eval():
     assert links == [], f"symlinks under carved-out eval/: {links}"
 
 
+# ---------------------------------------------------------------------------
+# ADR-226 independent audit F-001 (2026-09-03): path-normalization bypasses.
+# A purely lexical `_repo_relative` let `<root>/../<root>/x`, a case-variant
+# root and a symlink alias of the root escape every `^`-anchored pattern.
+# ---------------------------------------------------------------------------
+
+_BYPASS_TARGETS = (
+    "src/dopemux_pr_merge_specialist/queue_drain.py",
+    "services/dope-context/src/search/hybrid_search.py",
+)
+
+
+def test_pre_prefix_traversal_is_blocked():
+    for rel in _BYPASS_TARGETS:
+        fp = f"{_ROOT}/../{_ROOT.name}/{rel}"
+        result = surface_guard_block("Edit", {"file_path": fp}, _ROOT)
+        assert result is not None, fp
+        assert RED_LANE_ID in result
+
+
+def test_case_variant_root_is_blocked():
+    """macOS's default filesystem is case-insensitive: /USERS/x/repo/f is /Users/x/repo/f."""
+    for rel in _BYPASS_TARGETS:
+        fp = f"{str(_ROOT).swapcase()}/{rel}"
+        result = surface_guard_block("Write", {"file_path": fp}, _ROOT)
+        assert result is not None, fp
+        assert RED_LANE_ID in result
+
+
+def _scaffold_repo(tmp_path):
+    root = tmp_path / "repo"
+    blocked = root / "services" / "dope-context" / "src" / "search" / "hybrid_search.py"
+    blocked.parent.mkdir(parents=True)
+    blocked.write_text("# blocked\n")
+    (root / "services" / "dope-context" / "eval").mkdir()
+    return root, blocked
+
+
+def test_symlink_alias_of_root_is_blocked(tmp_path):
+    root, blocked = _scaffold_repo(tmp_path)
+    alias = tmp_path / "alias"
+    alias.symlink_to(root, target_is_directory=True)
+    via_alias = alias / blocked.relative_to(root)
+    # alias path, real root
+    assert surface_guard_block("Edit", {"file_path": str(via_alias)}, root) is not None
+    # real path, alias root
+    assert surface_guard_block("Edit", {"file_path": str(blocked)}, alias) is not None
+
+
+def test_symlink_inside_exempt_dir_pointing_at_blocked_file_is_blocked(tmp_path):
+    root, blocked = _scaffold_repo(tmp_path)
+    link = root / "services" / "dope-context" / "eval" / "link.py"
+    link.symlink_to(Path("..") / "src" / "search" / "hybrid_search.py")
+    result = surface_guard_block("Edit", {"file_path": str(link)}, root)
+    assert result is not None
+    assert RED_LANE_ID in result
+
+
+def test_new_file_under_exempt_dir_still_allowed(tmp_path):
+    root, _ = _scaffold_repo(tmp_path)
+    new = root / "services" / "dope-context" / "eval" / "new_probe.py"
+    assert not new.exists()
+    assert surface_guard_block("Write", {"file_path": str(new)}, root) is None
+
+
+def test_path_outside_root_is_not_a_repo_file(tmp_path):
+    root, _ = _scaffold_repo(tmp_path)
+    outside = tmp_path / "elsewhere" / "src" / "dopemux_pr_merge_specialist" / "queue_drain.py"
+    assert surface_guard_block("Edit", {"file_path": str(outside)}, root) is None
+
+
+def test_repo_relative_primary_reading_unchanged():
+    fp = str(_ROOT / "services" / "dope-context" / "eval" / "run_eval.py")
+    assert _repo_relative(fp, _ROOT) == "services/dope-context/eval/run_eval.py"
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
      3. a case-folded prefix match against those roots.

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

## FORBIDDEN_PATHS (src/dopemux/dcp/red_lane_rules.py, post-fix)
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
```

## Evidence provided by the implementer (not to be trusted without your own reasoning)
- pytest: 93 passed (tests/test_dcp_surface_guard.py + tests/dcp/test_dcp_0005_red_lane_scanner.py + tests/test_orchestrator_enforcement_hooks.py).
- Live dispatcher probes through src/dopemux/claude/native_hooks.py: `<root>/../<rootname>/src/dopemux_pr_merge_specialist/queue_drain.py` → exit 2 (deny); upper-cased root spelling of services/dope-context/src/search/hybrid_search.py → exit 2 (deny); services/dope-context/eval/run_eval.py → exit 0 (allow).

## Required output
Return STRICT JSON only (no prose outside the JSON) with this shape:
{"auditor_model": "<your exact model id>", "target_commit": "1d87cb73284b4019aff0d7cfe2525baa626cb7cf", "finding": "F-001", "verdict": "CLOSED" | "OPEN" | "CLOSED_WITH_RISKS", "reasoning": "<concise>", "residual_risks": [{"id": "...", "severity": "LOW|MEDIUM|HIGH", "description": "...", "recommended_action": "..."}], "regressions_introduced": [ ... same shape ... ], "bypass_attempts_considered": ["<list every path spelling / OS behaviour you reasoned about, e.g. symlinks, case-insensitive FS, unicode normalisation, absolute vs relative, trailing slash, Windows separators>"]}
