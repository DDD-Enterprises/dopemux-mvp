#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROMPTSET_PATH = ROOT / "services" / "repo-truth-extractor" / "promptsets" / "v4" / "promptset.yaml"
OUTPUT_PATH = ROOT / "reports" / "repo_truth_map.json"

RUNNER_MINIMUM_REQUIRED_KEYS = ("id", "path", "line_range")


def _read_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must decode to an object")
    return data


def _required_item_keys_for_outputs(outputs: Iterable[str]) -> list[str]:
    has_json = any(str(value).strip().lower().endswith(".json") for value in outputs)
    if not has_json:
        return []
    return [str(value).strip() for value in RUNNER_MINIMUM_REQUIRED_KEYS]


def _collect_steps(promptset: dict) -> list[dict]:
    steps: list[dict] = []
    for phase, payload in (promptset.get("phases") or {}).items():
        if not isinstance(payload, dict):
            continue
        for row in payload.get("steps", []):
            if not isinstance(row, dict):
                continue
            step_id = str(row.get("step_id") or "").strip()
            if not step_id:
                continue
            outputs = [
                str(value).strip()
                for value in row.get("outputs", [])
                if str(value).strip()
            ]
            prompt_declared = {
                "expected_artifacts": outputs,
            }
            required_keys = _required_item_keys_for_outputs(outputs)
            if required_keys:
                prompt_declared["required_item_keys"] = required_keys
            steps.append(
                {
                    "phase": str(phase).strip().upper(),
                    "step": step_id,
                    "step_id": step_id,
                    "prompt_declared": prompt_declared,
                }
            )
    return steps


def main() -> int:
    promptset = _read_yaml(PROMPTSET_PATH)
    steps = _collect_steps(promptset)
    payload = {"steps": steps}
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
