"""Persona fleet contract: packaged personas are a generated subset of canonical.

Canonical authoring surface: .claude/personas/*.agent.md
Packaged subset (wheel data): src/dopemux/personas/*.agent.md

Drift gate: packaged files must be byte-identical to canonical, the packaged
directory must contain no undeclared .agent.md files, and every declared stem
must exist canonically. Sync with scripts/sync_personas.py.
"""

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_DIR = REPO_ROOT / ".claude" / "personas"
PACKAGED_DIR = REPO_ROOT / "src" / "dopemux" / "personas"
SYNC_SCRIPT = REPO_ROOT / "scripts" / "sync_personas.py"


def _load_sync_module():
    spec = importlib.util.spec_from_file_location("sync_personas", SYNC_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_packaged_subset_matches_declared_list():
    sync = _load_sync_module()
    declared = {f"{stem}.agent.md" for stem in sync.PACKAGED_PERSONAS}
    on_disk = {path.name for path in PACKAGED_DIR.glob("*.agent.md")}
    assert on_disk == declared, (
        f"packaged dir drift: undeclared={sorted(on_disk - declared)}, "
        f"missing={sorted(declared - on_disk)}"
    )


def test_every_declared_stem_exists_canonically():
    sync = _load_sync_module()
    missing = [
        stem
        for stem in sync.PACKAGED_PERSONAS
        if not (CANONICAL_DIR / f"{stem}.agent.md").is_file()
    ]
    assert not missing, f"declared stems missing canonical source: {missing}"


def test_packaged_personas_are_byte_identical_to_canonical():
    sync = _load_sync_module()
    drifted = [
        stem
        for stem in sync.PACKAGED_PERSONAS
        if (CANONICAL_DIR / f"{stem}.agent.md").is_file()
        and (PACKAGED_DIR / f"{stem}.agent.md").is_file()
        and (CANONICAL_DIR / f"{stem}.agent.md").read_bytes()
        != (PACKAGED_DIR / f"{stem}.agent.md").read_bytes()
    ]
    assert not drifted, (
        f"packaged personas drifted from canonical: {drifted}; "
        "run `python scripts/sync_personas.py`"
    )


def test_no_packaged_persona_is_archived_canonical():
    archived = {
        path.name for path in (CANONICAL_DIR / "archive").glob("*.agent.md")
    } if (CANONICAL_DIR / "archive").is_dir() else set()
    packaged = {path.name for path in PACKAGED_DIR.glob("*.agent.md")}
    assert not (archived & packaged), (
        f"packaged personas whose canonical source was archived: {sorted(archived & packaged)}"
    )
