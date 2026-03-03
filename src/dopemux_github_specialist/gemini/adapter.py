from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional
from .runner import run_gemini
from .validate import parse_and_validate_report
from ..prompts import CHEAP_MODEL_SYSTEM_PROMPT
from ..redaction import RedactionPolicy
from ..schema import Report


def run_extraction_adapter(
    input_bundle: Dict[str, Any],
    run_id: str,
    out_dir: Path,
    gemini_command: Optional[str] = None
) -> Report:
    """
    Main entry point for Gemini-based extraction.
    Takes the input bundle, calls Gemini, validates the result, and writes proof artifacts.
    """
    input_text = json.dumps(input_bundle, ensure_ascii=False, indent=2)
    
    # Redaction check on input
    policy = RedactionPolicy()
    policy.assert_safe_text(input_text)
    
    # Store proof inputs
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "INPUTS.json").write_text(input_text, encoding="utf-8")
    (out_dir / "PROMPT.txt").write_text(CHEAP_MODEL_SYSTEM_PROMPT, encoding="utf-8")

    # Run Gemini
    raw_output = run_gemini(CHEAP_MODEL_SYSTEM_PROMPT, input_text, command=gemini_command)
    (out_dir / "RAW_STDOUT.txt").write_text(raw_output, encoding="utf-8")
    
    # Validate and build report
    report = parse_and_validate_report(raw_output, run_id)
    
    # Final redaction check on report
    report_json = json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True, indent=2)
    policy.assert_safe_text(report_json)
    
    return report
