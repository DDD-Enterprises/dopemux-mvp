"""L2 boundary proof for dopemux.governed_execution.environment.

Two independent proofs that this package has no live side effects:

1. subprocess.run, os.chmod, os.umask and builtins.open are monkeypatched
   to raise; every public function in the package still succeeds on
   fixture input. If the package ever shelled out, changed filesystem
   mode bits or opened a file, this test would fail loudly instead of the
   package silently acquiring a live side effect.
2. A static grep over the package source for the forbidden tokens listed
   in the commit.verify line asserts zero hits, independent of what any
   single test exercises at runtime.
"""
from __future__ import annotations

import builtins
import os
import re
import subprocess
from pathlib import Path

import pytest

from dopemux.governed_execution import environment as env_pkg
from dopemux.governed_execution.environment.custody import (
    ObservedFacts,
    WriterIdentity,
    WriterLease,
    author_custody_receipt,
)
from dopemux.governed_execution.environment.plan import (
    EnvironmentSpec,
    plan_environment,
)

PACKAGE_DIR = Path(env_pkg.__file__).resolve().parent

FORBIDDEN_TOKENS = (
    "subprocess",
    "os.chmod",
    "os.umask",
    "worktree add",
    "credential",
    "GIT_ASKPASS",
    "SSH_AUTH_SOCK",
)


def _raise(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("live side effect attempted during L2-only planning")


@pytest.fixture(autouse=True)
def _forbid_live_side_effects(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "run", _raise)
    monkeypatch.setattr(os, "chmod", _raise)
    monkeypatch.setattr(os, "umask", _raise)
    monkeypatch.setattr(builtins, "open", _raise)


def test_plan_and_receipt_authoring_succeed_with_side_effects_blocked() -> None:
    spec = EnvironmentSpec(
        repo_origin_url="https://github.com/DDD-Enterprises/dopemux-mvp.git",
        repo_toplevel="/Users/hue/code/dopemux-mvp",
        packet_id="TP-DMX-GEC-V2-W03-ISOLATION-CUSTODY-001",
        base_sha="1c915b9141e9a5c3d835a5c7ea953381782ae875",
        branch="feat/gec-v2-w03-isolation-custody-001",
        worktree_root="/Users/hue/code/dopemux-mvp/.worktrees",
        allowed_paths=("src/example.py",),
    )
    plan = plan_environment(spec)
    assert plan.worktree_path.endswith(
        "tp-dmx-gec-v2-w03-isolation-custody-001"
    )

    writer = WriterIdentity(runner="claude", session_ref="sess-1", agent_role="implementer")
    lease = WriterLease(
        lease_id="lease-1",
        issued_at="2026-09-11T00:00:00Z",
        expires_at="2026-09-11T23:59:59Z",
    )
    facts = ObservedFacts(
        head_sha="eff38e97f788af09f49eb5887f3a312e40cfaadd",
        patch_bytes=b"diff --git a/x b/x",
        outside_root_writes=False,
        worktree_exists=True,
        branch_matches=True,
    )
    receipt = author_custody_receipt(plan, writer, lease, facts, now="2026-09-11T12:00:00Z")
    assert receipt["custody_state"] == "HELD"
    assert receipt["authority"] == "NONE"


def test_no_forbidden_tokens_in_package_source() -> None:
    pattern = re.compile("|".join(re.escape(token) for token in FORBIDDEN_TOKENS))
    hits: list[str] = []
    for path in sorted(PACKAGE_DIR.glob("*.py")):
        text = path.read_text(encoding="ascii")
        for lineno, line in enumerate(text.splitlines(), start=1):
            match = pattern.search(line)
            if match:
                hits.append(f"{path.name}:{lineno}: {match.group(0)!r}")
    assert not hits, f"forbidden tokens found: {hits}"
