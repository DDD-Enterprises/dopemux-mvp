from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .io import write_json

REQUIRED_ROOT_KEYS = {
    "profile_id",
    "version",
    "priority",
    "description",
    "selection_threshold",
    "match_weights",
    "phase_policy",
    "prompt_overlays",
    "v2_rules",
}
REQUIRED_PHASE_POLICY_KEYS = {"targets_by_phase", "budgets_by_phase", "prompt_variants_by_phase_step"}
REQUIRED_BUDGET_KEYS = {"max_files", "max_chars", "file_truncate_chars"}


def _validate_profile(path: Path, payload: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    missing = REQUIRED_ROOT_KEYS - set(payload.keys())
    if missing:
        errors.append(f"missing_root_keys={sorted(missing)}")

    profile_id = payload.get("profile_id")
    if not isinstance(profile_id, str) or not profile_id.startswith("P"):
        errors.append("invalid_profile_id")

    phase_policy = payload.get("phase_policy")
    if not isinstance(phase_policy, dict):
        errors.append("phase_policy_not_object")
        return errors

    missing_phase_policy = REQUIRED_PHASE_POLICY_KEYS - set(phase_policy.keys())
    if missing_phase_policy:
        errors.append(f"missing_phase_policy_keys={sorted(missing_phase_policy)}")

    budgets = phase_policy.get("budgets_by_phase")
    if isinstance(budgets, dict):
        for phase, row in sorted(budgets.items()):
            if not isinstance(row, dict):
                errors.append(f"budget_not_object:{phase}")
                continue
            miss_budget = REQUIRED_BUDGET_KEYS - set(row.keys())
            if miss_budget:
                errors.append(f"budget_missing_keys:{phase}:{sorted(miss_budget)}")
            for key in REQUIRED_BUDGET_KEYS:
                value = row.get(key)
                if not isinstance(value, int) or value <= 0:
                    errors.append(f"budget_invalid:{phase}:{key}")

    match_weights = payload.get("match_weights")
    if not isinstance(match_weights, dict):
        errors.append("match_weights_not_object")
    else:
        for key, value in sorted(match_weights.items()):
            if not isinstance(key, str):
                errors.append("match_weight_key_not_string")
            if not isinstance(value, (int, float)):
                errors.append(f"match_weight_not_numeric:{key}")

    v2_rules = payload.get("v2_rules")
    if not isinstance(v2_rules, dict):
        errors.append("v2_rules_not_object")

    return errors


def validate_profiles(profiles_dir: Path) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    all_ok = True
    for path in sorted(profiles_dir.glob("P*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            rows.append({"file": str(path), "valid": False, "errors": [f"json_decode_error:{type(exc).__name__}"]})
            all_ok = False
            continue
        if not isinstance(payload, dict):
            rows.append({"file": str(path), "valid": False, "errors": ["not_object"]})
            all_ok = False
            continue

        errors = _validate_profile(path, payload)
        valid = not errors
        if not valid:
            all_ok = False
        rows.append(
            {
                "file": str(path),
                "profile_id": payload.get("profile_id"),
                "valid": valid,
                "errors": sorted(set(errors)),
            }
        )

    rows.sort(key=lambda row: str(row.get("profile_id") or row.get("file")))
    return {
        "version": "PROFILE_VALIDATE_REPORT_V1",
        "profiles_total": len(rows),
        "profiles_valid": sum(1 for row in rows if row.get("valid")),
        "status": "PASS" if all_ok else "FAIL",
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser("Validate promptgen profile JSON files")
    parser.add_argument("--all", action="store_true", help="Validate all profiles in default directory.")
    parser.add_argument("--profiles-dir", default="services/repo-truth-extractor/lib/promptgen/profiles")
    parser.add_argument(
        "--report-out",
        default="reports/repo-truth-extractor/promptgen_outputs/PROFILE_VALIDATE.report.json",
    )
    args = parser.parse_args()

    if not args.all:
        parser.error("--all is required")

    profiles_dir = Path(args.profiles_dir)
    report = validate_profiles(profiles_dir)
    write_json(Path(args.report_out), report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
