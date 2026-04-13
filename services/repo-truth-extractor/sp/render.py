"""SP prompt rendering with template variable substitution."""

import json
import re
from pathlib import Path
from typing import Any, Dict

from .models import SPStep

_PROMPT_ROOT = Path(__file__).resolve().parents[1] / "prompts" / "phase_s"


def render_sp_prompt(
    step: SPStep,
    context: Dict[str, Any],
) -> str:
    """Render an SP prompt by substituting template variables.

    Args:
        step: SPStep definition with template_vars tuple
        context: Dict mapping variable names to JSON-serializable values
                 (e.g., {"CANONICAL_JSON": {...}, "SCHEMA_JSON": {...}})

    Returns:
        Rendered prompt text with all {{VAR_NAME}} substitutions applied

    Raises:
        RuntimeError: If a required variable is missing or unreplaced placeholders remain
    """
    prompt_path = _PROMPT_ROOT / step.prompt_file
    text = prompt_path.read_text(encoding="utf-8")

    # Substitute each template variable
    for var_name in step.template_vars:
        placeholder = "{{" + var_name + "}}"

        # Tolerate MVP/extractor-gtm divergence: if placeholder not in text, skip
        # (some MVP prompts may not have been updated yet)
        if placeholder not in text:
            continue

        # Require the variable to be in context
        value = context.get(var_name)
        if value is None:
            raise RuntimeError(
                f"SP step {step.step_id} requires template variable {var_name} "
                f"but it was not provided in context"
            )

        # Serialize and substitute
        serialized = json.dumps(value, indent=2, sort_keys=True)
        text = text.replace(placeholder, serialized)

    # Defense: verify no unreplaced {{...}} placeholders remain
    remaining = re.findall(r'\{\{[A-Z_]+\}\}', text)
    if remaining:
        raise RuntimeError(
            f"SP step {step.step_id} has unreplaced template variables: {remaining}. "
            f"Check that all required variables are in the context dict."
        )

    return text
