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
