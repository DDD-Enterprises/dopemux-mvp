from __future__ import annotations

import json
from pathlib import Path

from tools.pr_steward.classifier import load_trusted_security_approvers


def test_missing_key_returns_empty_list(tmp_path: Path):
    path = tmp_path / "known_reviewers.json"
    path.write_text(json.dumps({"known_reviewers": [], "trusted_author_associations": []}))
    assert load_trusted_security_approvers(path) == []


def test_populated_key_returns_list(tmp_path: Path):
    path = tmp_path / "known_reviewers.json"
    path.write_text(
        json.dumps(
            {
                "known_reviewers": [],
                "trusted_author_associations": [],
                "trusted_security_release_approvers": ["alice", "bob"],
            }
        )
    )
    assert load_trusted_security_approvers(path) == ["alice", "bob"]


def test_repo_known_reviewers_file_roster_is_operator_owned():
    """Trusted security-release approvers are an operator decision.

    Solo-owner repositories may list exactly one human (the owner). Multi-owner
    repositories list non-author humans. An empty list remains valid but means
    no security-release path can approve until operators populate the roster.
    """
    from pathlib import Path as _P

    repo_path = _P(__file__).resolve().parents[2] / "tools" / "pr_steward" / "known_reviewers.json"
    roster = load_trusted_security_approvers(repo_path)
    assert isinstance(roster, list)
    assert all(isinstance(item, str) and item.strip() for item in roster)
    # No duplicates; logins are exact GitHub handles.
    assert len(roster) == len(set(roster))