"""
DCP facade denylist nudge for PostToolUse.

When an edit touches a DCP facade adapter file (not route_manifest.py, not tests/),
scan the file content for denied-route tokens and emit one advisory.

This makes the packet-0008 denylist regression continuous: you see it at edit time
instead of at packet-end review.

All functions are pure and never raise; hook failures must not block work.
Reference: services/dcp-readonly-facade/src/dcp_facade/route_manifest.py (DENIED_TOKENS)
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_FACADE_SRC = "services/dcp-readonly-facade/src/dcp_facade"
_CACHE_FILENAME = ".denylist-nudge-cache.json"

# Module-level cache for DENIED_TOKENS (loaded once per process)
_denied_tokens_cache: tuple[str, ...] | None = None


def _denied_tokens(project_root: Path) -> tuple[str, ...]:
    """Load DENIED_TOKENS from route_manifest.py via importlib-from-file.
    Caches result in module global. Returns () on any failure (fail-open)."""
    global _denied_tokens_cache
    if _denied_tokens_cache is not None:
        return _denied_tokens_cache
    try:
        manifest_path = project_root / _FACADE_SRC / "route_manifest.py"
        spec = importlib.util.spec_from_file_location("dcp_route_manifest", manifest_path)
        if spec is None or spec.loader is None:
            return ()
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        tokens = tuple(getattr(mod, "DENIED_TOKENS", ()))
        _denied_tokens_cache = tokens
        return tokens
    except Exception:
        return ()


def _load_cache(project_root: Path) -> dict:
    try:
        return json.loads((project_root / ".claude" / _CACHE_FILENAME).read_text())
    except Exception:
        return {}


def _save_cache(project_root: Path, cache: dict) -> None:
    try:
        p = project_root / ".claude" / _CACHE_FILENAME
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(cache))
    except Exception:
        pass


def _is_facade_adapter(file_path: str, project_root: Path) -> bool:
    """True if file_path is under _FACADE_SRC but is NOT route_manifest.py
    and NOT under tests/."""
    try:
        rel = Path(file_path).relative_to(project_root).as_posix()
    except ValueError:
        rel = Path(file_path).as_posix()
    if not rel.startswith(_FACADE_SRC + "/"):
        return False
    if rel.endswith("route_manifest.py"):
        return False  # denylist data itself
    if "/tests/" in rel:
        return False  # assertions are acceptable
    return True


def on_facade_edit(
    project_root: Path,
    file_path: str,
    session_id: str | None,
) -> str | None:
    """If file_path is a facade adapter, scan for denied tokens.
    Returns one advisory naming token + line numbers, or None.
    Cooldown: once per (session, file, token-set-hash). Never raises."""
    try:
        if not _is_facade_adapter(file_path, project_root):
            return None

        tokens = _denied_tokens(project_root)
        if not tokens:
            return None

        # Read the file content
        try:
            content = Path(file_path).read_text(errors="replace")
        except Exception:
            return None

        # Find hits: token → [line_numbers]
        hits: dict[str, list[int]] = {}
        for lineno, line in enumerate(content.splitlines(), start=1):
            for token in tokens:
                if token in line:
                    hits.setdefault(token, []).append(lineno)

        if not hits:
            return None

        # Cooldown: cache key includes token-set hash so a new token triggers again
        token_hash = str(hash(tokens))
        session_key = session_id or "no-session"
        cache_key = f"{session_key}:{file_path}:{token_hash}"
        cache = _load_cache(project_root)
        if cache.get(cache_key):
            return None

        cache[cache_key] = True
        _save_cache(project_root, cache)

        # Format hits: "memory_store@L5, L12; other_token@L3"
        hit_parts = []
        for token, lines in hits.items():
            line_refs = ", ".join(f"L{n}" for n in lines[:5])
            if len(lines) > 5:
                line_refs += f", …+{len(lines)-5}"
            hit_parts.append(f"`{token}`@{line_refs}")

        rel = Path(file_path).name
        return (
            f"⚠️ Denied-route token(s) in {rel}: {'; '.join(hit_parts)}. "
            f"Acceptable only as denylist data (route_manifest), docstrings, or test assertions "
            f"— never in an adapter call path. "
            f"Run /dcp:denylist-check for the authoritative classification before "
            f"filing this slice's notes."
        )
    except Exception:
        return None
