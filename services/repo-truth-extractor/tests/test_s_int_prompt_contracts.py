from __future__ import annotations

import json
from pathlib import Path


def test_s_int_prompt_files_and_schemas_exist() -> None:
    root = Path(__file__).resolve().parents[3]
    prompt_root = root / "services" / "repo-truth-extractor" / "prompts" / "phase_s_int"
    schema_root = prompt_root / "schemas"
    for stem in ["S16", "S17", "S18", "S19", "S20"]:
        prompt_path = next(prompt_root.glob(f"{stem}_*.md"))
        schema_path = schema_root / f"{stem}.json"
        assert prompt_path.exists()
        assert "{{S_INT_INPUT_JSON}}" in prompt_path.read_text(encoding="utf-8")
        json.loads(schema_path.read_text(encoding="utf-8"))
