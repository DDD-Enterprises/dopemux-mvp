from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict

from .models import SPStep

_PROMPT_ROOT = Path(__file__).resolve().parents[1] / "prompts" / "phase_s"


def render_sp_prompt(step: SPStep, context: Dict[str, Any]) -> str:
    """Render an SP prompt by substituting template variables."""
    prompt_path = _PROMPT_ROOT / step.prompt_file
    text = prompt_path.read_text(encoding="utf-8")

    for var_name in step.template_vars:
        placeholder = "{{" + var_name + "}}"
        if placeholder not in text:
            # MVP prompts may not include placeholders yet.
            continue
        value = context.get(var_name)
        if value is None:
            raise RuntimeError(
                f"SP step {step.step_id} requires {var_name} but it was not provided in context"
            )
        serialized = json.dumps(value, indent=2, sort_keys=True)
        text = text.replace(placeholder, serialized)

    remaining = re.findall(r"\{\{[A-Z_]+\}\}", text)
    if remaining:
        raise RuntimeError(
            f"SP step {step.step_id} has unreplaced template variables: {remaining}"
        )
    return text
