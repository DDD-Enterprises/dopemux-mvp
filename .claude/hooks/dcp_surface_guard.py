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


_MAX_ALIAS_FORMS = 64
_MAX_SYMLINK_HOPS = 40

_Form = tuple[tuple[str, bool], ...]


def _walk_alias_forms(
    path: str, hops: int, known: dict[_Form, list[_Form]]
) -> list[_Form]:
    """Forms of absolute ``path``; the first one is the fully resolved form.

    Each form lists the components after the anchor as
    ``(name, is_symlink_name)``. ``known`` remembers every spelling seen for
    each resolved directory, so ``..`` out of a symlink's target gets back the
    spellings of the directory it lands in. Raises OSError past
    ``_MAX_SYMLINK_HOPS``.
    """
    if hops > _MAX_SYMLINK_HOPS:
        raise OSError("too many levels of symbolic links")
    parts = Path(path).parts
    anchor = parts[0]
    real: _Form = ()
    forms: list[_Form] = [real]
    for name in parts[1:]:
        if name == ".":
            continue
        if name == "..":
            real = real[:-1]
            kept = [f[:-1] for f in forms if f and not f[-1][1]]
            forms = list(dict.fromkeys([real, *kept, *known.get(real, [])]))
            forms = forms[:_MAX_ALIAS_FORMS]
            continue
        parent = os.path.join(anchor, *(n for n, _ in real))
        entry = os.path.join(parent, name)
        if os.path.islink(entry):
            # Amendment 08: one hop, then walk the target as written, so a
            # name that appears only in the middle of a chain is kept too.
            target = os.path.join(parent, os.readlink(entry))
            reached = _walk_alias_forms(target, hops + 1, known)
            named = [f + ((name, True),) for f in forms]
            real = reached[0]
            forms = list(dict.fromkeys([*reached, *named]))
        else:
            real = real + ((name, False),)
            forms = [f + ((name, False),) for f in forms]
            forms = list(dict.fromkeys([real, *forms]))
        forms = forms[:_MAX_ALIAS_FORMS]
        seen = known.setdefault(real, [])
        seen.extend(f for f in forms if f not in seen)
    return forms


def _alias_forms(path: str) -> tuple[str, ...]:
    """Every spelling of absolute ``path`` that names the same file.

    The path is walked one component at a time, the way the filesystem
    resolves it. At a symlink both spellings are carried on: the link's own
    name, and every spelling of the link's target. The target is read one hop
    at a time (Amendment 08), so each link in a chain, and each symlink inside
    a target path, contributes its own spelling. ``..`` steps to the parent of
    where the walk really is, so a spelling whose last component is a symlink
    name is dropped there (its lexical parent is a different directory), and
    the spellings already seen for the directory it lands in are picked up.
    Components that do not exist yet are kept as typed.

    Each returned spelling resolves to the same file as ``path``. Returns ()
    for a relative path, a symlink loop, or a path that cannot be read. Never
    raises.
    """
    try:
        if not os.path.isabs(path):
            return ()
        anchor = Path(path).parts[0]
        forms = _walk_alias_forms(path, 0, {})
        return tuple(
            dict.fromkeys(os.path.join(anchor, *(n for n, _ in f)) for f in forms)
        )
    except (OSError, ValueError, RecursionError):
        return ()


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
    # Amendment 07: also read every alias spelling of the path. A spelling
    # such as ``<x>/../<root>/services/<symlink>/f`` is the same file as the
    # plain one, but raw does not sit under the root lexically and realpath
    # follows the symlink out of it, so neither reading matched. This only
    # adds candidates; the raw form is still read.
    for form in _alias_forms(file_path):
        if Path(form) not in candidates:
            candidates.append(Path(form))
    try:
        real = Path(os.path.realpath(file_path))
        if real not in candidates:
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


def file_repo_root(file_path: str, fallback: Path) -> Path:
    """Root of the checkout that owns ``file_path``, else ``fallback``.

    The red-lane rules are repo-relative, so an edit must be read against the
    repo the file lives in, not the session's project root: a sibling worktree's
    ``services/task-orchestrator/x.py`` is red-lane there too. Takes the realpath
    (a relative path is read against ``fallback``), steps up to its nearest
    existing ancestor (the file and its parent directories may not exist yet),
    then walks up to the first directory holding a ``.git`` entry, a directory
    for a main checkout or a file for a linked worktree. No subprocess and no
    git command: this runs before every edit. Never raises.
    """
    try:
        fallback = Path(fallback)
        joined = file_path if os.path.isabs(file_path) else os.path.join(fallback, file_path)
        cur = os.path.realpath(joined)
        while not os.path.lexists(cur):
            parent = os.path.dirname(cur)
            if parent == cur:
                return fallback
            cur = parent
        if not os.path.isdir(cur):
            cur = os.path.dirname(cur)
        while True:
            if os.path.lexists(os.path.join(cur, ".git")):
                return Path(cur)
            parent = os.path.dirname(cur)
            if parent == cur:
                return fallback
            cur = parent
    except (OSError, ValueError):
        return Path(fallback)


def _guard_roots(file_path: str, project_root: Path) -> tuple[Path, ...]:
    """Every root the guard reads ``file_path`` against, without duplicates.

    ``project_root`` first, then each ancestor directory of the file's nearest
    existing ancestor that holds a ``.git`` entry (file or directory), nearest
    first. A ``.git`` entry planted inside a checkout can only add a reading,
    never hide the project-root or enclosing-checkout one. No subprocess; never
    raises.
    """
    roots = [Path(project_root)]
    for start in _guard_starts(file_path, project_root):
        try:
            cur = start
            while not os.path.lexists(cur):
                parent = os.path.dirname(cur)
                if parent == cur:
                    break
                cur = parent
            if not os.path.isdir(cur):
                cur = os.path.dirname(cur)
            while True:
                if os.path.lexists(os.path.join(cur, ".git")):
                    roots.append(Path(cur))
                parent = os.path.dirname(cur)
                if parent == cur:
                    break
                cur = parent
        except (OSError, ValueError):
            continue
    return tuple(dict.fromkeys(roots))


def _absolute_bases(file_path: str, project_root: Path) -> tuple[str, ...]:
    """``file_path`` as absolute path(s), with ``..`` and symlinks left as typed.

    A relative path is joined to ``project_root`` and to the process cwd,
    since either may be where the edit lands. Never raises.
    """
    if os.path.isabs(file_path):
        return (file_path,)
    bases = [os.path.join(project_root, file_path)]
    try:
        bases.append(os.path.join(os.getcwd(), file_path))
    except OSError:
        pass
    return tuple(dict.fromkeys(bases))


def _guard_starts(file_path: str, project_root: Path) -> tuple[str, ...]:
    """Absolute forms of ``file_path`` that root discovery walks up from.

    Amendment 03. A relative path is read both against ``project_root`` and
    against the process cwd, since either may be where the edit lands. Each
    form is taken lexically (``..`` collapsed, symlinks kept) and resolved
    (``os.path.realpath``): a symlink inside a sibling checkout must not move
    discovery out of that checkout. Forms are only ever added. Never raises.
    """
    starts: list[str] = []
    try:
        for base in _absolute_bases(file_path, project_root):
            starts.append(os.path.normpath(base))
            starts.append(os.path.realpath(base))
            # Amendment 07: also walk up from every alias spelling.
            # ``<symlink>/../<sibling>/<symlinked dir>/f`` collapses lexically
            # to a path outside the sibling and realpath follows the inner
            # symlink out of it, so neither start found its root.
            starts.extend(_alias_forms(base))
    except (OSError, ValueError):
        pass
    return tuple(dict.fromkeys(starts))


def _guard_readings(file_path: str, root: Path, project_root: Path) -> tuple[str, ...]:
    """Repo-relative readings of ``file_path`` against ``root``.

    A relative path is resolved by ``os.path.realpath`` against the process cwd,
    which need not be ``project_root``; so its ``project_root``-joined form is
    read too. Readings are only ever added.
    """
    readings = list(_repo_relative_candidates(file_path, root))
    if not os.path.isabs(file_path):
        # Amendment 03/07: the project-root and cwd forms, joined without
        # collapsing ``..`` so a symlink before it is still followed.
        for base in _absolute_bases(file_path, project_root):
            readings.extend(_repo_relative_candidates(base, root))
    return tuple(dict.fromkeys(readings))


def tool_edit_path(tool_input: dict) -> str:
    """The path an Edit/Write/NotebookEdit targets: ``file_path``, else
    ``notebook_path``, else ``""``. Only non-empty strings are read."""
    for key in ("file_path", "notebook_path"):
        value = (tool_input or {}).get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def tool_edit_paths(tool_input: dict) -> list[str]:
    """Every path an Edit/Write/NotebookEdit names: ``file_path`` then
    ``notebook_path``, each only when it is a non-empty string, without
    repeats. Amendment 02: the guard checks all of them, so a harmless
    ``file_path`` cannot hide a ``notebook_path``."""
    paths: list[str] = []
    for key in ("file_path", "notebook_path"):
        value = (tool_input or {}).get(key)
        if isinstance(value, str) and value and value not in paths:
            paths.append(value)
    return paths


def _repo_relative(file_path: str, project_root: Path) -> str:
    """Normalize file_path to forward-slash repo-relative string (primary reading)."""
    return _repo_relative_candidates(file_path, project_root)[0]


_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


def _has_control_chars(s: str) -> bool:
    """True if ``s`` contains any ASCII control byte (0x00-0x1F, 0x7F)."""
    return bool(_CONTROL_CHARS.search(s))


def surface_guard_block(tool_name: str, tool_input: dict, project_root: Path) -> str | None:
    """Return a block reason when an edit targets a red-lane seam file, else None."""
    if tool_name not in {"Edit", "Write", "NotebookEdit"}:
        return None
    # Amendment 02: check every path the call names (file_path and
    # notebook_path); the first one that is blocked wins.
    for file_path in tool_edit_paths(tool_input):
        reason = _block_reason_for_path(file_path, project_root)
        if reason:
            return reason
    return None


def _block_reason_for_path(file_path: str, project_root: Path) -> str | None:
    """Return a block reason when one edit path is a red-lane seam file, else None."""
    # TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-001: a control character (most
    # notably a newline) embedded in file_path can make an `^`-anchored,
    # `.*`-tailed forbidden pattern fail to match anywhere in the string — the
    # match silently falls through to "not blocked" instead of either matching
    # or correctly failing the exemption lookahead. red_lane_rules.py now
    # anchors every pattern with `\Z` under `re.DOTALL` to close that at the
    # regex level; this is the second, pattern-independent layer: no legitimate
    # file_path contains a control character, so fail closed unconditionally
    # rather than depend on every current and future FORBIDDEN_PATHS entry
    # getting its anchoring exactly right.
    if _has_control_chars(file_path):
        return (
            f"🚫 file_path contains a control character (e.g. embedded newline) "
            f"and is hard-blocked by red lane {RED_LANE_ID} as a precaution — "
            f"no legitimate edit target has one. If this is unexpected, inspect "
            f"the literal tool_input.file_path value."
        )
    patterns = _forbidden_patterns()
    for root in _guard_roots(file_path, project_root):
        for rel in _guard_readings(file_path, root, project_root):
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


def _contract_surface_for_path(file_path: str, project_root: Path) -> str | None:
    """Return the contract-surface label any reading of one path matches, else None."""
    for root in _guard_roots(file_path, project_root):
        for rel in _guard_readings(file_path, root, project_root):
            category = _matches_contract_surface(rel)
            if category:
                return category
    return None


def surface_guard_warnings(
    tool_name: str,
    tool_input: dict,
    project_root: Path,
    session_id: str | None = None,
) -> list[str]:
    """Return once-per-(session, path) advisory when editing a contract surface."""
    if tool_name not in {"Edit", "Write", "NotebookEdit"}:
        return []

    # Amendment 02: check every path the call names (file_path and
    # notebook_path). Amendment 03: the warn cache is checked per path, so an
    # already-warned first path cannot hide a new second one; the first
    # contract surface not yet warned in this session is the one reported.
    session_key = session_id or "no-session"
    cache: dict | None = None
    category = None
    cache_key = ""
    for candidate in tool_edit_paths(tool_input):
        # Don't warn on new proof/*/PROOF.json writes (that's the scaffold flow)
        if _proof_json_is_new(candidate):
            continue
        found = _contract_surface_for_path(candidate, project_root)
        if not found:
            continue
        if cache is None:
            cache = _load_warn_cache(project_root)
        key = f"{session_key}:{candidate}"
        if cache.get(key):
            continue
        category = found
        cache_key = key
        break
    if not category or cache is None:
        return []

    cache[cache_key] = True
    _save_warn_cache(project_root, cache)

    return [
        f"⚠️ Contract-sensitive surface ({category}): identify the canonical writer "
        f"and consumers before editing. See governance: contract-sensitive surfaces. "
        f"For facade surfaces, run /dcp:denylist-check after."
    ]
