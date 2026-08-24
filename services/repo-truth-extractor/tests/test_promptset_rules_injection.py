from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


def _load_runner_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v5_rules", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_load_promptset_rules_returns_content() -> None:
    runner = _load_runner_module()
    rules = runner._load_promptset_rules()
    assert "Evidence Rules" in rules
    assert "Determinism Rules" in rules
    assert "Anti-Fabrication Rules" in rules
    assert "Failure Modes" in rules


def test_inject_promptset_rules_adds_to_shared_rules_prompt() -> None:
    runner = _load_runner_module()
    prompt = "# Test Prompt\n\n## Shared Rules\nRefer to PROMPTSET_RULES.md.\n"
    result = runner._inject_promptset_rules(prompt)
    assert "PROMPTSET_RULES.md (Injected)" in result
    assert "Evidence Rules" in result


def test_inject_promptset_rules_skips_unrelated_prompt() -> None:
    runner = _load_runner_module()
    prompt = "# Test Prompt\n\nNo shared rules reference here.\n"
    result = runner._inject_promptset_rules(prompt)
    assert result == prompt
    assert "Injected" not in result


def test_inject_promptset_rules_is_idempotent() -> None:
    runner = _load_runner_module()
    prompt = "# Test\n\n## Shared Rules\nRefer to PROMPTSET_RULES.md.\n"
    once = runner._inject_promptset_rules(prompt)
    twice = runner._inject_promptset_rules(once)
    assert once == twice
    assert twice.count("## PROMPTSET_RULES.md (Injected)") == 1


def test_load_promptset_rules_returns_synthesis_evidence_section() -> None:
    """F-29 (TP-RTE-TRUTH-R3-006): the new synthesis-tier evidence object must be part of
    the file `_load_promptset_rules()` reads -- the same file `_inject_promptset_rules()`
    appends to every prompt carrying a `## Shared Rules` pointer (128 of 136 v4 templates,
    including all five F-29 steps: R7/R8/S4/S5/S6)."""
    runner = _load_runner_module()
    rules = runner._load_promptset_rules()
    assert "Synthesis Evidence Rules" in rules
    assert "upstream_artifact" in rules
    assert "item_id" in rules


def test_inject_promptset_rules_delivers_synthesis_evidence_shape_to_r7() -> None:
    """Request-time reachability proof for F-29, mirroring TP-RTE-TRUTH-R3-004's pattern:
    compile the *real* run_extraction_v5.py and call the *real* _inject_promptset_rules()
    -- the exact function execute_step_for_partitions() calls before every dispatch (both
    the sync and async R-batch seams) -- against the shipped PROMPT_R7 text. A schema
    section present on disk but never reachable from the dispatch path would prove
    nothing; this proves it is reachable from the dispatch path.
    """
    runner = _load_runner_module()
    root = Path(__file__).resolve().parents[3]
    r7_path = (
        root
        / "services"
        / "repo-truth-extractor"
        / "promptsets"
        / "v4"
        / "prompts"
        / "PROMPT_R7_CONFLICT_LEDGER.md"
    )
    prompt_text = r7_path.read_text(encoding="utf-8")
    assert "Synthesis Evidence Rules" in prompt_text, "R7 must name the rule locally, not rely solely on injection"

    rendered = runner._inject_promptset_rules(prompt_text)
    assert "## PROMPTSET_RULES.md (Injected)" in rendered
    # The rendered (dispatch-bound) text carries the full object shape, not just the name.
    injected_section = rendered.split("## PROMPTSET_RULES.md (Injected)", 1)[1]
    assert "Synthesis Evidence Rules" in injected_section
    assert "upstream_artifact" in injected_section
    assert "item_id" in injected_section
    assert "excerpt" in injected_section
