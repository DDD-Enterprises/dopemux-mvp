"""F-23 (CRIT, security) — the secrets-redaction rule must be BINDING and reachable.

Finding F-23 (CONSOLIDATED-FINDINGS.md, one of two security CRITs gating PR #1043):
C8's SECRETS_RISK_LOCATIONS contract requires an *exact* `excerpt` (<=200 chars), so a
`hardcoded_secret` finding copies the real credential verbatim into the norm artifact AND
into paid-LLM context, then feeds R11 security synthesis. H1's redaction rule existed only
inside the "Legacy Context (for intent only; never as evidence)" block -- explicitly
non-binding, and the runtime injects no block by that name (run_extraction_v4.py:104-110).

What these tests CAN prove (and do):
  1. the rule exists in the BINDING body of the prompts that scan for secrets,
  2. it is not marooned in a Legacy Context block,
  3. it mandates masking the secret span (a specific token, not vague "be careful"),
  4. it actually reaches the model's context via the runtime PROMPTSET_RULES injection.

What they CANNOT prove: that a live model obeys the rule. That needs live evals and is
recorded as residual risk in the packet's PROOF.json. These tests pin the *instruction*,
not the behavior.

FAKE_SECRET below is a syntactically-valid but non-existent credential. It is never a real
key and must never be replaced with one.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

SERVICE_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = SERVICE_ROOT / "promptsets" / "v4" / "prompts"
RULES_PATH = SERVICE_ROOT / "promptsets" / "v4" / "PROMPTSET_RULES.md"

# A fake secret, used to prove the masking convention renders as intended.
# Shape mirrors a real AWS secret key; the value is invented and inert.
FAKE_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYFAKEKEY123"
FAKE_SECRET_LINE = f"AWS_SECRET_ACCESS_KEY={FAKE_SECRET}"
REDACTION_TOKEN = "<REDACTED>"

# The prompts whose binding body must carry a redaction rule. Each of these instructs the
# model to scan a surface where live credentials are routinely present.
SECRET_SCANNING_PROMPTS = {
    "C8": "PROMPT_C8_DETERMINISM___IDEMPOTENCY___CONCURRENCY_LOCATION_SCANS.md",
    "H1": "PROMPT_H1_KEYS___REFERENCES.md",
    "H7": "PROMPT_H7_SQLITE___STATE_DB_METADATA.md",
    "M3": "PROMPT_M3_CONPORT_EXPORT_SAFE.md",
    "M4": "PROMPT_M4_DOPE_CONTEXT_EXPORT_SAFE.md",
    "M5": "PROMPT_M5_MCP_HEALTH_EXPORT_SAFE.md",
}

LEGACY_HEADER = "## Legacy Context (for intent only; never as evidence)"


def _load_v5_runner():
    module_path = SERVICE_ROOT / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v5_redaction", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _binding_body(text: str) -> str:
    """Return the prompt text with the non-binding Legacy Context block removed.

    The Legacy Context block is explicitly declared "for intent only; never as evidence",
    so a rule that lives ONLY there is not binding. This is exactly the F-23 defect for H1.
    """
    head, _, _ = text.partition(LEGACY_HEADER)
    return head


def test_rules_file_has_binding_secret_redaction_section() -> None:
    """PROMPTSET_RULES.md must carry a top-level, binding Secret Redaction Rules section."""
    text = RULES_PATH.read_text(encoding="utf-8")
    assert re.search(r"^## Secret Redaction Rules", text, re.MULTILINE), (
        "PROMPTSET_RULES.md has no '## Secret Redaction Rules' section — F-23 regression"
    )
    assert "BINDING" in text
    assert REDACTION_TOKEN in text, "the rules must name the concrete masking token"
    # The rule must resolve the conflict with the exact-excerpt Evidence Rule explicitly,
    # otherwise a model following the Evidence Rules literally still emits the secret.
    assert "override" in text.lower() and "exact" in text.lower()


def test_redaction_rule_masks_the_secret_span_not_the_whole_line() -> None:
    """The mandated transform must mask the value and keep the key name.

    Applies the documented convention to a FAKE secret and asserts the result: the secret
    characters are gone, the key name survives (so the finding stays reviewable).
    """
    rendered = FAKE_SECRET_LINE.replace(FAKE_SECRET, REDACTION_TOKEN)
    assert rendered == f"AWS_SECRET_ACCESS_KEY={REDACTION_TOKEN}"
    assert FAKE_SECRET not in rendered
    assert "AWS_SECRET_ACCESS_KEY" in rendered, "over-redaction destroys reviewability"

    # And that exact worked example must be present in the binding rules, so the model is
    # shown the transform rather than left to infer it.
    rules = RULES_PATH.read_text(encoding="utf-8")
    assert f"AWS_SECRET_ACCESS_KEY={REDACTION_TOKEN}" in rules


@pytest.mark.parametrize("step_id", sorted(SECRET_SCANNING_PROMPTS))
def test_secret_scanning_prompt_has_binding_redaction_rule(step_id: str) -> None:
    """Every secret-touching prompt states the redaction rule OUTSIDE Legacy Context."""
    text = (PROMPTS_DIR / SECRET_SCANNING_PROMPTS[step_id]).read_text(encoding="utf-8")
    body = _binding_body(text)

    assert "BINDING" in body, f"{step_id}: no BINDING marker in the binding body"
    assert REDACTION_TOKEN in body, (
        f"{step_id}: binding body never names the {REDACTION_TOKEN} masking token — "
        "a vague 'redact if found' is what F-23 flagged as insufficient"
    )
    assert re.search(r"redact|mask", body, re.IGNORECASE), f"{step_id}: no redaction verb"


def test_h1_redaction_is_no_longer_legacy_only() -> None:
    """F-23/A3b F-6 regression pin: H1's redaction rule must not be Legacy-only.

    This is the precise defect A3b reported: 'secrets-redaction rules live exclusively in
    the Legacy Context block. The binding body of H1 instructs credential-reference
    extraction with no redaction constraint.'
    """
    text = (PROMPTS_DIR / SECRET_SCANNING_PROMPTS["H1"]).read_text(encoding="utf-8")
    assert LEGACY_HEADER in text, "test assumes H1 still has a Legacy Context block"
    body = _binding_body(text)
    assert "Never print" in body or "Never the value" in body or "never the value" in body.lower()
    assert "never emit a secret value" in body.lower()


def test_c8_secrets_worked_example_excerpt_is_redacted() -> None:
    """C8's worked example must model a redacted excerpt, not a live-looking one.

    Few-shot examples are load-bearing: an example carrying a real-looking secret teaches
    the opposite of the rule.
    """
    text = (PROMPTS_DIR / SECRET_SCANNING_PROMPTS["C8"]).read_text(encoding="utf-8")
    body = _binding_body(text)
    assert "SECRETS_RISK_LOCATIONS:7b19ad3c" in body, "C8 secrets worked example missing"
    assert f'OPENAI_API_KEY = \\"{REDACTION_TOKEN}\\"' in body


def test_binding_rules_reach_the_model_via_runtime_injection() -> None:
    """The rule is only real if it lands in the prompt the model actually receives.

    C8/H1/H7/M3/M4/M5 all point at PROMPTSET_RULES.md via '## Shared Rules' rather than
    inlining it. _inject_promptset_rules() is the runtime seam that makes that pointer
    resolve; without it the redaction section is a file nobody reads.
    """
    runner = _load_v5_runner()

    for step_id, filename in sorted(SECRET_SCANNING_PROMPTS.items()):
        prompt_text = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
        injected = runner._inject_promptset_rules(prompt_text)
        assert "## Secret Redaction Rules" in injected, (
            f"{step_id}: the binding redaction rules never reach the rendered prompt"
        )
        assert f"AWS_SECRET_ACCESS_KEY={REDACTION_TOKEN}" in injected, (
            f"{step_id}: the masking worked example is absent from the rendered prompt"
        )
