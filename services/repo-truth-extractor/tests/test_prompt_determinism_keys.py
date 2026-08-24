"""F-27 / F-33 — legacy prompt blocks must not mandate determinism-violating keys.

F-27 (HIGH) and F-33 (MED) in CONSOLIDATED-FINDINGS.md: the Gen-1 "Legacy Context" JSON
container shapes in the A- and H-phase prompts required `generated_at` (and `run_id`),
directly contradicting the binding Determinism Rules in PROMPTSET_RULES.md:

    "Norm outputs MUST NOT contain: generated_at, timestamp, created_at, updated_at, run_id"

A model shown a contradiction resolves it arbitrarily; the shapes were the only field-level
spec for several H steps, so the contradicting one was the more concrete of the two.

Scope note: the T-phase share of F-27 (TP_BACKLOG_TOPN) is owned by TP-RTE-TRUTH-R3-005c
and is deliberately NOT covered here.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "promptsets" / "v4" / "prompts"
RULES_PATH = Path(__file__).resolve().parents[1] / "promptsets" / "v4" / "PROMPTSET_RULES.md"

# Keys the binding Determinism Rules forbid in norm outputs.
FORBIDDEN_KEY_RE = re.compile(
    r'^\s*"(generated_at|timestamp|created_at|updated_at|run_id)"\s*:', re.MULTILINE
)

# T-phase carries the remaining F-27 violations; owned by R3-005c, excluded here so this
# test does not fail on work another packet has not landed yet.
OUT_OF_SCOPE_PREFIXES = ("PROMPT_T",)


def _in_scope_prompts() -> list[Path]:
    return sorted(
        p
        for p in PROMPTS_DIR.glob("PROMPT_*.md")
        if not p.name.startswith(OUT_OF_SCOPE_PREFIXES)
    )


def test_determinism_rules_still_forbid_these_keys() -> None:
    """Pin the rule this test enforces, so the two cannot silently diverge."""
    rules = RULES_PATH.read_text(encoding="utf-8")
    for key in ("generated_at", "timestamp", "created_at", "updated_at", "run_id"):
        assert key in rules, f"Determinism Rules no longer mention {key}"


@pytest.mark.parametrize("prompt_path", _in_scope_prompts(), ids=lambda p: p.stem)
def test_prompt_does_not_mandate_forbidden_determinism_keys(prompt_path: Path) -> None:
    """No A/H (or other in-scope) prompt may specify a forbidden key in a JSON shape.

    Checks the whole file, not just the binding body: the Legacy Context block is where
    these lived, and a contradictory concrete shape misleads the model even when labelled
    "intent only".
    """
    text = prompt_path.read_text(encoding="utf-8")
    hits = [m.group(1) for m in FORBIDDEN_KEY_RE.finditer(text)]
    assert hits == [], (
        f"{prompt_path.name} mandates determinism-violating key(s) {sorted(set(hits))}, "
        f"contradicting PROMPTSET_RULES.md § Determinism Rules"
    )
