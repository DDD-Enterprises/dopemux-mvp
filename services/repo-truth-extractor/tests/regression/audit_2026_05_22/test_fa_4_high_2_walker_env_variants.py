"""
FA-4-HIGH-2 — Walker excludes .env / .env.* but NOT .env-* / .env_* variants.

The DEFAULT_SECRET_BEARING_EXCLUDE_GLOBS in lib/prescan/models.py covers
".env", ".env.*", "**/.env", "**/.env.*" — i.e., dot-suffixed variants.
But hyphenated and underscored variants like ".env-staging",
".env_dev", ".env-production" are NOT excluded; the walker INCLUDES
them in the corpus_manifest, leaking secrets into prompt INPUT.

Documented in:
  rte_audit_findings_FA4_security.md / FA-4-HIGH-2
  rte_audit_findings_FA7_preextractor.md / "F2-CRIT-2 closure PoC"
  rte_audit_findings_FA8_liverun.md / "FA-4-HIGH-2 confirmed at corpus_manifest level"

xfail until the glob list is extended.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SERVICE_ROOT = Path(__file__).resolve().parents[3]
if str(_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(_SERVICE_ROOT))

from lib.prescan.corpus_walker import CorpusWalker  # noqa: E402
from lib.prescan.models import (  # noqa: E402
    DEFAULT_PRESCAN_EXCLUDE_GLOBS,
    PrescanConfig,
)


def _build_walker(repo_root: Path) -> CorpusWalker:
    cfg = PrescanConfig(
        repo_root=repo_root,
        output_dir=repo_root / "_audit_out",
        exclude_globs=list(DEFAULT_PRESCAN_EXCLUDE_GLOBS),
    )
    return CorpusWalker(cfg)


# --- Positive regression: dot-suffix .env / .env.* MUST stay excluded ---
@pytest.mark.parametrize(
    "filename",
    [
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        ".env.test",
    ],
)
def test_dot_suffix_env_variants_excluded(filename: str, tmp_path: Path) -> None:
    """Positive: dot-suffixed .env variants must stay excluded."""
    (tmp_path / filename).write_text(
        "OPENAI_API_KEY=sk-test-fake1234567890\n", encoding="utf-8"
    )
    (tmp_path / "README.md").write_text("# test\n", encoding="utf-8")

    entries = _build_walker(tmp_path).walk()
    included_paths = [e.rel_path for e in entries if e.include]
    assert filename not in included_paths, (
        f"{filename} should be excluded by DEFAULT_SECRET_BEARING_EXCLUDE_GLOBS; "
        f"included paths: {included_paths}"
    )


# --- FA-4-HIGH-2 regression: hyphen/underscore variants should also be excluded ---
@pytest.mark.parametrize(
    "filename",
    [
        ".env-staging",
        ".env-production",
        ".env-dev",
        ".env_dev",
        ".env_production",
    ],
)
def test_hyphen_underscore_env_variants_should_be_excluded(
    filename: str, tmp_path: Path
) -> None:
    """Hyphen/underscore .env variants must be excluded."""
    (tmp_path / filename).write_text(
        "STAGING_SECRET=fake-staging-secret-xyz\n", encoding="utf-8"
    )
    (tmp_path / "README.md").write_text("# test\n", encoding="utf-8")

    entries = _build_walker(tmp_path).walk()
    included_paths = [e.rel_path for e in entries if e.include]
    assert filename not in included_paths, (
        f"{filename} should be excluded by DEFAULT_SECRET_BEARING_EXCLUDE_GLOBS; "
        f"included paths: {included_paths}"
    )


def test_generated_tree_excludes_still_hold(tmp_path: Path) -> None:
    """Positive regression: F2-CRIT-2 closure (generated trees excluded)."""
    for d in ("extraction", "proof", "out", "audit_prep", "claudedocs"):
        sub = tmp_path / d
        sub.mkdir()
        (sub / "poisoned.txt").write_text("should be excluded", encoding="utf-8")
    (tmp_path / "README.md").write_text("# test\n", encoding="utf-8")

    entries = _build_walker(tmp_path).walk()
    included_paths = [e.rel_path for e in entries if e.include]
    for excluded_dir in ("extraction", "proof", "out", "audit_prep", "claudedocs"):
        assert not any(
            p.startswith(excluded_dir + "/") for p in included_paths
        ), f"Generated tree {excluded_dir}/ should be excluded; got {included_paths}"
    assert "README.md" in included_paths
