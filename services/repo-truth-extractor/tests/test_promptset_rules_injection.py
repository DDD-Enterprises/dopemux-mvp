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
    assert once == twice or "PROMPTSET_RULES" in twice
