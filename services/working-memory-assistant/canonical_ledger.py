"""Canonical ledger path resolution for Dope-Memory services.

All Dope-Memory write paths MUST use this module to resolve the path to the
single canonical chronicle ledger.  ADR-213 requires:

  * Every capture adapter writes to the SAME SQLite file per project.
  * Global rollup is read-only.
  * Capture fails closed if repo root cannot be determined.

Canonical path: ``repo_root/.dopemux/chronicle.sqlite``
Override env:    ``DOPEMUX_CAPTURE_LEDGER_PATH``
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class CanonicalLedgerError(RuntimeError):
    """Raised when the canonical ledger path cannot be resolved.

    Capture fails closed — no fallback paths, no silent writes.
    """


# ---------------------------------------------------------------------------
# Repo root resolution (mirrors capture_client._repo_root_from_start)
# ---------------------------------------------------------------------------

def _find_repo_root(start_path: Path) -> Path:
    """Walk upward from *start_path* to find the first ``.git`` or ``.dopemux`` marker."""
    current = start_path.resolve()
    if current.is_file():
        current = current.parent

    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists() or (candidate / ".dopemux").exists():
            return candidate

    raise CanonicalLedgerError(
        f"No repository root found walking up from {start_path}.  "
        "Capture fails closed outside a recognised repo/workspace.  "
        "Set DOPEMUX_CAPTURE_LEDGER_PATH to provide an explicit ledger path."
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def resolve_canonical_ledger(
    workspace_id: Optional[str] = None,
) -> Path:
    """Resolve the canonical chronicle ledger path.

    Resolution order (first match wins):

    1. ``DOPEMUX_CAPTURE_LEDGER_PATH`` environment variable (explicit override).
    2. *workspace_id* interpreted as an absolute path with repo markers.
    3. Walk upward from ``cwd()`` to find repo root.
    4. **Fail closed** — raise :class:`CanonicalLedgerError`.

    Returns
    -------
    Path
        Absolute path to the canonical ``chronicle.sqlite``.
    """
    # 1. Explicit override (highest priority — used by tests and Docker).
    override = os.getenv("DOPEMUX_CAPTURE_LEDGER_PATH", "").strip()
    if override:
        ledger = Path(override).expanduser().resolve()
        ledger.parent.mkdir(parents=True, exist_ok=True)
        return ledger

    # 2. workspace_id as repo root path.
    if workspace_id and os.path.isabs(workspace_id):
        ws_path = Path(workspace_id)
        if (ws_path / ".git").exists() or (ws_path / ".dopemux").exists():
            ledger = (ws_path / ".dopemux" / "chronicle.sqlite").resolve()
            ledger.parent.mkdir(parents=True, exist_ok=True)
            return ledger

    # 3. Walk up from cwd.
    repo_root = _find_repo_root(Path.cwd())
    ledger = (repo_root / ".dopemux" / "chronicle.sqlite").resolve()
    ledger.parent.mkdir(parents=True, exist_ok=True)
    return ledger
