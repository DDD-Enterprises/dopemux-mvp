from __future__ import annotations

from pathlib import Path


PROMPT_FILES = [
    "PROMPT_S7_DEDUPE_SORT.md",
    "PROMPT_S8_DRIFT_CHECK.md",
    "PROMPT_S9_PROMOTION_READINESS.md",
    "PROMPT_S10_REDACTION_PASS.md",
    "PROMPT_S11_CONTRACT_LINTER.md",
    "PROMPT_S12_STABILITY_SIGNATURE.md",
]


def test_phase_s_posttail_prompts_exist_and_match_contract() -> None:
    root = Path(__file__).resolve().parents[3]
    prompt_root = root / "services" / "repo-truth-extractor" / "prompts" / "phase_s"
    for filename in PROMPT_FILES:
        path = prompt_root / filename
        assert path.exists(), f"Missing prompt file: {filename}"
        text = path.read_text(encoding="utf-8")
        assert "OUTPUTS:" in text
        assert "Output JSON only." in text
        assert ("FAIL_CLOSED" in text) or ("fail closed" in text.lower())
        assert "print the secret" not in text.lower()
        assert "sk-" not in text.lower()
        assert "api_key=" not in text.lower()
