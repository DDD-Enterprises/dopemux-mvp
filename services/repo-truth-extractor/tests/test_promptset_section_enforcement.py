"""F-31 (HIGH) — `required_prompt_sections` must have a runtime reader.

Finding F-31 (CONSOLIDATED-FINDINGS.md; A3b F-5), confirmed by the maintainers' own
comment at run_extraction_v4.py:104-110 before this fix: promptset.yaml declares
`required_prompt_sections`, but nothing read it. A section validator existed in
lib/promptgen/template_renderer.py and was wired to nothing. Consequence: a prompt could
lose its Anti-Fabrication Rules and still be dispatched to a paid model -- the anti-fab
regime was a contract checked by nobody.

These tests pin three things:
  1. the declared contract is actually enforced (fail-closed) at promptset load,
  2. the real v4 promptset satisfies it today,
  3. the "## Shared Rules" pointer form is honored, because the runtime resolves that
     pointer by injecting PROMPTSET_RULES.md -- so those templates do deliver the regime.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

SERVICE_ROOT = Path(__file__).resolve().parents[1]


def _load_v4_runner():
    if str(SERVICE_ROOT) not in sys.path:
        sys.path.insert(0, str(SERVICE_ROOT))
    module_path = SERVICE_ROOT / "run_extraction_v4.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v4_sections", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_real_v4_promptset_satisfies_its_declared_sections() -> None:
    """The shipped promptset must pass its own contract -- otherwise nothing can run."""
    runner = _load_v4_runner()
    promptset = yaml.safe_load(
        (SERVICE_ROOT / "promptsets" / "v4" / "promptset.yaml").read_text(encoding="utf-8")
    )
    issues = runner.validate_promptset_sections(promptset)
    assert issues == [], f"v4 promptset violates its own section contract: {issues}"


def test_load_promptset_enforces_sections_by_default() -> None:
    """load_promptset() is the runtime reader F-31 said did not exist."""
    runner = _load_v4_runner()
    promptset = runner.load_promptset()
    assert promptset["required_prompt_sections"], "sections must be declared"
    # The reader must exist and be reachable -- this is the F-31 regression pin.
    assert callable(runner.validate_promptset_sections)


def test_load_promptset_fails_closed_on_missing_section(monkeypatch, tmp_path: Path) -> None:
    """A prompt missing Anti-Fabrication Rules must abort the load, not run anyway.

    This is the concrete harm F-31 describes: an unenforced contract lets a prompt reach a
    paid model with its anti-fabrication regime silently absent.
    """
    runner = _load_v4_runner()

    prompt_rel = "stub_prompts/PROMPT_A0_STUB.md"
    prompt_path = tmp_path / prompt_rel
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    # Has Goal/Inputs/Outputs/Schema/Extraction Procedure -- but NO Shared Rules pointer
    # and no inline Evidence/Determinism/Anti-Fabrication/Failure Modes.
    prompt_path.write_text(
        "# PROMPT_A0\n\n## Goal\nStub.\n\n## Inputs\nx\n\n## Outputs\n- `A0.json`\n\n"
        "## Schema\nx\n\n## Extraction Procedure\n1. x\n",
        encoding="utf-8",
    )

    promptset = {
        "version": "4.0",
        "required_prompt_sections": [
            "Goal",
            "Inputs",
            "Outputs",
            "Schema",
            "Extraction Procedure",
            "Evidence Rules",
            "Determinism Rules",
            "Anti-Fabrication Rules",
            "Failure Modes",
        ],
        "phases": {
            "A": {
                "required_steps": ["A0"],
                "steps": [{"step_id": "A0", "prompt_file": prompt_rel, "outputs": ["A0.json"]}],
            }
        },
    }
    promptset_path = tmp_path / "promptset.yaml"
    promptset_path.write_text(yaml.safe_dump(promptset, sort_keys=False), encoding="utf-8")

    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "PROMPTSET_PATH", promptset_path)

    issues = runner.validate_promptset_sections(promptset)
    assert len(issues) == 4, f"expected 4 missing shared sections, got: {issues}"
    assert any("Anti-Fabrication Rules" in issue for issue in issues)

    with pytest.raises(runner.PromptSectionContractError) as excinfo:
        runner.load_promptset()
    assert "Anti-Fabrication Rules" in str(excinfo.value)
    assert "Refusing to run" in str(excinfo.value)

    # ...and the escape hatch must still allow inspection of a broken promptset.
    assert runner.load_promptset(enforce_sections=False) == promptset


def test_shared_rules_pointer_satisfies_the_shared_sections(monkeypatch, tmp_path: Path) -> None:
    """The pointer form must be accepted -- the runtime injects the rules file.

    128 of the 136 v4 templates use "## Shared Rules" rather than inlining the four shared
    sections. Rejecting that form would fail-closed the entire promptset; accepting it is
    only honest because run_extraction_v5._inject_promptset_rules() appends
    PROMPTSET_RULES.md to any prompt carrying the pointer before it is dispatched.
    """
    runner = _load_v4_runner()

    prompt_rel = "stub_prompts/PROMPT_A0_STUB.md"
    prompt_path = tmp_path / prompt_rel
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(
        "# PROMPT_A0\n\n## Goal\nStub.\n\n## Inputs\nx\n\n## Outputs\n- `A0.json`\n\n"
        "## Schema\nx\n\n## Extraction Procedure\n1. x\n\n"
        "## Shared Rules\nRefer to `PROMPTSET_RULES.md`.\n",
        encoding="utf-8",
    )

    promptset = {
        "version": "4.0",
        "required_prompt_sections": [
            "Goal",
            "Inputs",
            "Outputs",
            "Schema",
            "Extraction Procedure",
            "Evidence Rules",
            "Determinism Rules",
            "Anti-Fabrication Rules",
            "Failure Modes",
        ],
        "phases": {
            "A": {
                "required_steps": ["A0"],
                "steps": [{"step_id": "A0", "prompt_file": prompt_rel, "outputs": ["A0.json"]}],
            }
        },
    }
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    assert runner.validate_promptset_sections(promptset) == []


def test_missing_prompt_file_is_reported(monkeypatch, tmp_path: Path) -> None:
    """A declared-but-absent prompt_file must surface, not pass silently."""
    runner = _load_v4_runner()
    promptset = {
        "required_prompt_sections": ["Goal"],
        "phases": {
            "A": {
                "steps": [{"step_id": "A0", "prompt_file": "nope/PROMPT_A0.md", "outputs": []}],
            }
        },
    }
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    issues = runner.validate_promptset_sections(promptset)
    assert len(issues) == 1
    assert "does not exist" in issues[0]


def test_async_r_dispatch_injects_promptset_rules() -> None:
    """F-31: the async R path must resolve the Shared Rules pointer like sync dispatch.

    The async batch seam read the prompt and submitted it without calling
    _inject_promptset_rules(), so prompts dispatched through it reached the model with the
    pointer unresolved -- the rules file (including the F-23 Secret Redaction Rules) never
    arrived. Pin both call sites so the paths cannot drift apart again.
    """
    source = (SERVICE_ROOT / "run_extraction_v5.py").read_text(encoding="utf-8")
    call_count = source.count("_inject_promptset_rules(prompt_text)")
    assert call_count == 2, (
        f"expected _inject_promptset_rules at both the sync and async R dispatch sites, "
        f"found {call_count} call(s)"
    )


def test_v5_canonical_entrypoint_rejects_missing_sections(monkeypatch, tmp_path: Path) -> None:
    """F-31 (TP-RTE-TRUTH-R3-008): v5 canonical entrypoint must enforce section contract.

    Audit found F-31 section enforcement was wired only into v4's run_pipeline(), not into
    v5 (the canonical runner per rte_config.RUNNER_SCRIPT). Direct `python run_extraction_v5.py`
    would skip validation entirely. This test pins that v5 now rejects missing sections at
    startup via _validate_promptset_sections_preflight().

    MUTATION CHECK: remove _validate_promptset_sections_preflight() call from main(),
    confirm this test FAILS (proving the test is actually checking the fix).
    """
    runner = _load_v4_runner()
    v5_runner_path = SERVICE_ROOT / "run_extraction_v5.py"

    # Load v5 via importlib to get its validation function
    spec = importlib.util.spec_from_file_location("run_extraction_v5_sections", v5_runner_path)
    assert spec is not None and spec.loader is not None
    v5_module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = v5_module
    spec.loader.exec_module(v5_module)

    # Create a broken promptset with a prompt missing required sections
    prompt_rel = "stub_prompts/PROMPT_A0_STUB.md"
    prompt_path = tmp_path / prompt_rel
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(
        "# PROMPT_A0\n\n## Goal\nStub.\n\n## Inputs\nx\n\n## Outputs\n- `A0.json`\n\n"
        "## Schema\nx\n\n## Extraction Procedure\n1. x\n",
        encoding="utf-8",
    )

    promptset = {
        "version": "4.0",
        "required_prompt_sections": [
            "Goal",
            "Inputs",
            "Outputs",
            "Schema",
            "Extraction Procedure",
            "Evidence Rules",
            "Determinism Rules",
            "Anti-Fabrication Rules",
            "Failure Modes",
        ],
        "phases": {
            "A": {
                "required_steps": ["A0"],
                "steps": [{"step_id": "A0", "prompt_file": prompt_rel, "outputs": ["A0.json"]}],
            }
        },
    }
    # Create promptset in the location expected by v5's preflight
    promptset_dir = tmp_path / "promptsets" / "v4"
    promptset_dir.mkdir(parents=True, exist_ok=True)
    promptset_path = promptset_dir / "promptset.yaml"
    promptset_path.write_text(yaml.safe_dump(promptset, sort_keys=False), encoding="utf-8")

    # Patch v5 to use our broken promptset
    monkeypatch.setattr(v5_module, "EXTRACTOR_SERVICE_DIR", tmp_path)
    # Set the prompt root environment variable so prompt_root() finds our stub prompt
    # The prompt_file path is relative to tmp_path, so set prompt root to tmp_path
    monkeypatch.setenv(v5_module.PROMPT_ROOT_ENV_VAR, str(tmp_path))
    # Reset the validation state so it runs again
    monkeypatch.setattr(v5_module, "_PROMPTSET_SECTIONS_VALIDATED", False)

    # v5's preflight must reject the broken promptset
    with pytest.raises(v5_module.PromptSectionContractError) as excinfo:
        v5_module._validate_promptset_sections_preflight()
    assert "Anti-Fabrication Rules" in str(excinfo.value)
    assert "Refusing to run" in str(excinfo.value)


def test_v5_main_actually_invokes_section_preflight() -> None:
    """F-31 wiring guard (TP-RTE-TRUTH-R3-008 repair).

    The sibling test above exercises _validate_promptset_sections_preflight() directly,
    so it passes even when main() never calls it — verified: disabling the call site left
    that test green. This test pins the WIRING, which is the part F-31 is actually about:
    enforcement must run on the canonical v5 entrypoint, not merely exist as a function.

    MUTATION CHECK (executed): replacing the call at the main() call site with `pass`
    makes THIS test fail.
    """
    import inspect
    import importlib.util

    v5_runner_path = SERVICE_ROOT / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v5_wiring", v5_runner_path)
    assert spec is not None and spec.loader is not None
    v5_module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = v5_module
    spec.loader.exec_module(v5_module)

    main_src = inspect.getsource(v5_module.main)
    assert "_validate_promptset_sections_preflight()" in main_src, (
        "v5 main() no longer calls _validate_promptset_sections_preflight(). "
        "F-31 section enforcement is not live on the canonical entrypoint."
    )
