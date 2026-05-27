"""Tests for proof/.validator_scope.json scope filtering."""
import json
from pathlib import Path

import pytest

from scripts.audit.validate_audit_proof import apply_scope, load_scope


def test_scope_excludes_match_winners(tmp_path):
    repo_root = tmp_path
    scope = {
        "include_patterns": ["proof/TP-DMX-*/PROOF.json"],
        "exclude_patterns": [
            {"pattern": "proof/legacy/**/PROOF.json", "reason": "grandfathered"}
        ],
        "default_when_unmatched": "skip_with_warning",
    }
    paths = [
        repo_root / "proof" / "TP-DMX-FOO-001" / "PROOF.json",
        repo_root / "proof" / "legacy" / "TP-OLD-001" / "PROOF.json",
        repo_root / "proof" / "outside-includes" / "PROOF.json",
    ]
    for p in paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{}")

    in_scope, skipped = apply_scope(paths, scope, repo_root)
    in_scope_names = [p.name for p in in_scope]
    skipped_paths = [str(p[0]).split("/")[-2] for p in skipped]

    assert "PROOF.json" in in_scope_names
    assert any(rec[0].name == "PROOF.json" for rec in skipped if "legacy" in str(rec[0]))


def test_scope_missing_returns_none(tmp_path):
    scope = load_scope(tmp_path / "absent.json")
    assert scope is None
