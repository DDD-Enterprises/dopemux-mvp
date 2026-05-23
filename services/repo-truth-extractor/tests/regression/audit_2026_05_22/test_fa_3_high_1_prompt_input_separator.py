"""
FA-3-HIGH-1 — No INPUT/INSTRUCTION delimiter in any of 138 prompts.

The promptset includes verbatim repo content in the user-content portion
of the prompt without any `<repo_content>` or `<INSTRUCTIONS>` delimiter.
A repo file containing `IGNORE PREVIOUS INSTRUCTIONS; output {...}` can
steer the model.

Runtime-confirmed in:
  rte_audit_findings_FA8_liverun.md / "FA-3-HIGH-1 RUNTIME-CONFIRMED"
  (TRACE.md L178 contains the injection payload verbatim)

Static-check: assert at least one common delimiter token is present in
any prompt file. xfail until any of the prompts adds a delimiter marker.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SERVICE_ROOT = Path(__file__).resolve().parents[3]
_PROMPTS_DIR = _SERVICE_ROOT / "promptsets" / "v4" / "prompts"


DELIMITER_TOKENS = (
    "<repo_content>",
    "</repo_content>",
    "<input>",
    "</input>",
    "<user_input>",
    "</user_input>",
    "<corpus>",
    "</corpus>",
    "<INSTRUCTIONS>",
    "</INSTRUCTIONS>",
    "<DOCUMENT>",
    "</DOCUMENT>",
    "<BEGIN_INPUT>",
    "<END_INPUT>",
    "---INPUT---",
    "---END_INPUT---",
)


@pytest.mark.xfail(
    reason="FA-3-HIGH-1: Zero of 138 prompts have an INPUT/INSTRUCTION delimiter. Add e.g. <repo_content>...</repo_content> tags in the prompt templates so the model can be trained to treat untrusted content."
)
def test_at_least_one_prompt_has_input_delimiter() -> None:
    """xfail until prompts adopt a delimiter convention."""
    if not _PROMPTS_DIR.exists():
        pytest.skip(f"Prompts dir not found: {_PROMPTS_DIR}")
    prompt_files = list(_PROMPTS_DIR.glob("*.md"))
    assert prompt_files, f"No prompts found in {_PROMPTS_DIR}"

    files_with_delimiter: list[str] = []
    for pf in prompt_files:
        try:
            content = pf.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if any(tok in content for tok in DELIMITER_TOKENS):
            files_with_delimiter.append(pf.name)

    assert files_with_delimiter, (
        f"Expected at least one prompt to use a known INPUT/INSTRUCTION delimiter "
        f"({list(DELIMITER_TOKENS)}); none of {len(prompt_files)} prompts use any."
    )
