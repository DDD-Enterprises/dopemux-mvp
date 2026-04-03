#!/usr/bin/env python3
"""Unified docs hygiene sweep runner."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


DEFAULT_AUDIT_PATH = "reports/docs-hygiene/sweep_audit.json"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"Unable to import module {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_SCRIPT_DIR = Path(__file__).resolve().parent
_PLACEMENT = _load_module("check_docs_hygiene", _SCRIPT_DIR / "check_docs_hygiene.py")
_FILENAME = _load_module("check_docs_filename_hygiene", _SCRIPT_DIR / "check_docs_filename_hygiene.py")
_FRONTMATTER = _load_module("docs_frontmatter_guard", _SCRIPT_DIR / "docs_frontmatter_guard.py")
_DUPLICATES = _load_module("check_docs_duplicates", _SCRIPT_DIR / "check_docs_duplicates.py")
_VALIDATOR = _load_module("docs_validator", _SCRIPT_DIR / "docs_validator.py")
_ROOT = _load_module("check_root_hygiene", _SCRIPT_DIR / "check_root_hygiene.py")


@dataclass
class StepResult:
    step: str
    exit_code: int
    details: Dict[str, Any]
    resulting_paths: Optional[List[str]] = None


def _iter_docs(repo_root: Path, requested_paths: Optional[List[str]] = None) -> List[Path]:
    if requested_paths is not None:
        docs: List[Path] = []
        for raw in requested_paths:
            path = repo_root / _PLACEMENT._normalize_relpath(raw)
            if path.exists() and path.is_file() and path.suffix == ".md":
                docs.append(path)
        return sorted(docs)
    base = repo_root / "docs"
    if not base.exists():
        return []
    return sorted(base.rglob("*.md"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _build_totals(results: List[StepResult]) -> Dict[str, Any]:
    by_step = {result.step: result for result in results}
    return {
        "filename_violations": by_step.get("filename", StepResult("", 0, {})).details.get("violations", 0),
        "frontmatter_updates_needed": by_step.get("frontmatter", StepResult("", 0, {})).details.get("needs_update", 0),
        "frontmatter_post_placement_updates": by_step.get("frontmatter", StepResult("", 0, {})).details.get("post_placement_updates", 0),
        "duplicate_archives": by_step.get("duplicates", StepResult("", 0, {})).details.get("archive", 0),
        "duplicate_renames": by_step.get("duplicates", StepResult("", 0, {})).details.get("rename", 0),
        "duplicate_manual_review": by_step.get("duplicates", StepResult("", 0, {})).details.get("manual_review", 0),
        "placement_violations": by_step.get("placement", StepResult("", 0, {})).details.get("violations", 0),
        "schema_errors": by_step.get("schema-validation", StepResult("", 0, {})).details.get("errors", 0),
        "schema_warnings": by_step.get("schema-validation", StepResult("", 0, {})).details.get("warnings", 0),
        "root_hygiene_violations": by_step.get("root-hygiene", StepResult("", 0, {})).details.get("violations", 0),
    }


def _run_frontmatter(
    mode: str,
    repo_root: Path,
    requested_paths: Optional[List[str]],
    audit_dir: Path,
) -> StepResult:
    files = _iter_docs(repo_root=repo_root, requested_paths=requested_paths)
    changed_files: List[str] = []
    for path in files:
        if _FRONTMATTER.ensure_frontmatter(path, fix=(mode == "apply")):
            changed_files.append(_PLACEMENT._normalize_relpath(str(path.relative_to(repo_root))))

    if mode == "audit":
        _write_json(
            audit_dir / "frontmatter_audit.json",
            [{"path": path, "status": "needs_update"} for path in changed_files],
        )

    exit_code = 0 if mode == "apply" or not changed_files else 1
    return StepResult(
        step="frontmatter",
        exit_code=exit_code,
        details={"checked": len(files), "needs_update": len(changed_files)},
        resulting_paths=(
            [
                _PLACEMENT._normalize_relpath(str(path.relative_to(repo_root)))
                for path in files
                if path.exists()
            ]
            if requested_paths is not None
            else None
        ),
    )


def _reconcile_frontmatter_after_moves(repo_root: Path, requested_paths: Optional[List[str]]) -> int:
    updated = 0
    for path in _iter_docs(repo_root=repo_root, requested_paths=requested_paths):
        _FRONTMATTER.ensure_frontmatter(path, fix=True)
        text = path.read_text(encoding="utf-8")
        data, body, _ = _FRONTMATTER.parse_frontmatter(text)
        if not isinstance(data, dict):
            continue
        guessed_type = _FRONTMATTER.guess_type(str(path))
        current_type = data.get("type")
        if current_type == guessed_type:
            continue
        title = data.get("title", _FRONTMATTER.default_title(path))
        old_prelude = f"{title} ({current_type}) for dopemux documentation and developer workflows."
        data["type"] = guessed_type
        if data.get("prelude") == old_prelude:
            data["prelude"] = _FRONTMATTER.default_prelude(path, title)
        path.write_text(_FRONTMATTER.build_frontmatter(data) + body.lstrip(), encoding="utf-8")
        updated += 1
    return updated


def _run_schema_validation(
    mode: str,
    repo_root: Path,
    requested_paths: Optional[List[str]],
    audit_dir: Path,
) -> StepResult:
    validator = _VALIDATOR.DocumentValidator()
    validator.project_root = repo_root
    files = _iter_docs(repo_root=repo_root, requested_paths=requested_paths)
    checked = 0
    for path in files:
        checked += 1
        validator.validate_file(str(path), fix=False)

    issues = [asdict(error) for error in validator.errors]
    warnings = [asdict(warning) for warning in validator.warnings]
    if mode == "audit":
        _write_json(audit_dir / "schema_validation_audit.json", {"errors": issues, "warnings": warnings})

    return StepResult(
        step="schema-validation",
        exit_code=0 if not validator.errors else 1,
        details={"checked": checked, "errors": len(issues), "warnings": len(warnings)},
        resulting_paths=(
            [
                _PLACEMENT._normalize_relpath(str(path.relative_to(repo_root)))
                for path in files
                if path.exists()
            ]
            if requested_paths is not None
            else None
        ),
    )


def _run_root_hygiene(
    mode: str,
    repo_root: Path,
    audit_dir: Path,
) -> StepResult:
    policy = _ROOT._load_policy((repo_root / _ROOT.DEFAULT_POLICY_PATH).resolve())
    candidates = sorted(path.name for path in repo_root.glob("*.md"))
    violations = _ROOT._evaluate(candidates, policy)
    if mode == "audit":
        _write_json(audit_dir / "root_hygiene_audit.json", violations)
    return StepResult(
        step="root-hygiene",
        exit_code=0 if not violations else 1,
        details={"checked": len(candidates), "violations": len(violations)},
        resulting_paths=None,
    )


def _predict_resulting_paths(step: str, records: List[Any]) -> List[str]:
    next_paths: List[str] = []
    for record in records:
        current = getattr(record, "path", None)
        if step == "filename":
            next_paths.append(getattr(record, "target_path", None) or current)
            continue
        if step == "duplicates":
            status = getattr(record, "status", "")
            if status == "archive_duplicate":
                next_paths.append(getattr(record, "base_path", None) or current)
            elif status == "rename_orphan":
                next_paths.append(getattr(record, "target_path", None) or current)
            else:
                next_paths.append(current)
            continue
        if step == "placement":
            next_paths.append(getattr(record, "target_path", None) or current)
            continue
        next_paths.append(current)

    normalized: List[str] = []
    seen: set[str] = set()
    for path in next_paths:
        if not path:
            continue
        norm = _PLACEMENT._normalize_relpath(path)
        if norm in seen:
            continue
        seen.add(norm)
        normalized.append(norm)
    return normalized


def _run_module_step(
    step: str,
    mode: str,
    repo_root: Path,
    policy: Dict[str, Any],
    requested_paths: Optional[List[str]],
    audit_path: Path,
    build_records: Callable[..., List[Any]],
    runner: Any,
) -> StepResult:
    if requested_paths is not None and len(requested_paths) == 0:
        return StepResult(step=step, exit_code=0, details={"records": 0}, resulting_paths=[])

    records = build_records(repo_root=repo_root, policy=policy, requested_paths=requested_paths)
    details: Dict[str, Any] = {"records": len(records)}

    if step == "filename":
        details["violations"] = sum(1 for record in records if record.zone == "active" and record.status == "needs_rename")
    elif step == "duplicates":
        details["archive"] = sum(1 for record in records if record.status == "archive_duplicate")
        details["rename"] = sum(1 for record in records if record.status == "rename_orphan")
        details["manual_review"] = sum(1 for record in records if record.status == "manual_review")
    elif step == "placement":
        details["violations"] = sum(1 for record in records if record.zone == "active" and record.status == "needs_relocation")

    resulting_paths = requested_paths
    if requested_paths is not None:
        resulting_paths = _predict_resulting_paths(step=step, records=records)

    if mode == "audit":
        exit_code = runner.run_audit(
            repo_root=repo_root,
            policy=policy,
            audit_path=audit_path,
            requested_paths=requested_paths,
        )
    elif mode == "apply":
        exit_code = runner.run_apply(
            repo_root=repo_root,
            policy=policy,
            audit_path=audit_path,
            requested_paths=requested_paths,
        )
    else:
        exit_code = runner.run_check(repo_root=repo_root, policy=policy, requested_paths=requested_paths)

    return StepResult(step=step, exit_code=exit_code, details=details, resulting_paths=resulting_paths)


def run_sweep(
    mode: str,
    repo_root: Path,
    requested_paths: Optional[List[str]] = None,
    audit_out: str = DEFAULT_AUDIT_PATH,
) -> int:
    policy = _PLACEMENT._load_policy((repo_root / _PLACEMENT.DEFAULT_POLICY_PATH).resolve())
    audit_dir = (repo_root / Path(audit_out)).resolve().parent
    current_paths = requested_paths

    results: List[StepResult] = []

    result = _run_module_step(
            step="filename",
            mode=mode,
            repo_root=repo_root,
            policy=policy,
            requested_paths=current_paths,
            audit_path=audit_dir / "filename_audit.json",
            build_records=_FILENAME.build_records,
            runner=_FILENAME,
        )
    results.append(result)
    current_paths = result.resulting_paths

    result = _run_frontmatter(mode=mode, repo_root=repo_root, requested_paths=current_paths, audit_dir=audit_dir)
    results.append(result)
    current_paths = result.resulting_paths

    result = _run_module_step(
            step="duplicates",
            mode=mode,
            repo_root=repo_root,
            policy=policy,
            requested_paths=current_paths,
            audit_path=audit_dir / "duplicates_audit.json",
            build_records=_DUPLICATES.build_records,
            runner=_DUPLICATES,
        )
    results.append(result)
    current_paths = result.resulting_paths

    result = _run_module_step(
            step="placement",
            mode=mode,
            repo_root=repo_root,
            policy=policy,
            requested_paths=current_paths,
            audit_path=audit_dir / "placement_audit.json",
            build_records=_PLACEMENT.build_records,
            runner=_PLACEMENT,
        )
    results.append(result)
    current_paths = result.resulting_paths

    result = _run_schema_validation(mode=mode, repo_root=repo_root, requested_paths=current_paths, audit_dir=audit_dir)
    results.append(result)
    current_paths = result.resulting_paths

    results.append(_run_root_hygiene(mode=mode, repo_root=repo_root, audit_dir=audit_dir))

    if mode == "apply":
        post_placement_updates = _reconcile_frontmatter_after_moves(repo_root=repo_root, requested_paths=current_paths)
        results[1].details["post_placement_updates"] = post_placement_updates

    report_paths = {
        "combined": str((repo_root / audit_out).resolve()),
        "filename": str((audit_dir / "filename_audit.json").resolve()),
        "frontmatter": str((audit_dir / "frontmatter_audit.json").resolve()),
        "duplicates": str((audit_dir / "duplicates_audit.json").resolve()),
        "placement": str((audit_dir / "placement_audit.json").resolve()),
        "schema_validation": str((audit_dir / "schema_validation_audit.json").resolve()),
        "root_hygiene": str((audit_dir / "root_hygiene_audit.json").resolve()),
    }
    summary = {
        "mode": mode,
        "scope": "all-docs" if requested_paths is None else "explicit-paths",
        "requested_paths": requested_paths or [],
        "totals": _build_totals(results),
        "report_paths": report_paths,
        "steps": [asdict(result) for result in results],
    }
    if mode == "audit":
        _write_json((repo_root / audit_out).resolve(), summary)
        print(f"docs-sweep: wrote audit -> {(repo_root / audit_out).resolve()}")

    print("docs-sweep: summary")
    for result in results:
        detail_summary = " ".join(f"{key}={value}" for key, value in result.details.items())
        print(f" - {result.step}: exit={result.exit_code} {detail_summary}".rstrip())

    exit_code = 0 if all(result.exit_code == 0 for result in results) else 1
    if exit_code == 0:
        print("docs-sweep: OK")
    else:
        print("docs-sweep: FAILED")
    return exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the unified docs hygiene sweep.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Run all docs hygiene checks.")
    mode.add_argument("--apply", action="store_true", help="Apply all supported docs hygiene fixes.")
    mode.add_argument("--audit", action="store_true", help="Write combined docs hygiene audit JSON.")
    parser.add_argument(
        "--audit-out",
        default=DEFAULT_AUDIT_PATH,
        help=f"Combined audit artifact path (default: {DEFAULT_AUDIT_PATH})",
    )
    parser.add_argument(
        "--all-files",
        action="store_true",
        help="Accepted for parity with other docs hygiene commands.",
    )
    parser.add_argument("filenames", nargs="*", help="Optional subset of markdown files to sweep.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = _PLACEMENT._repo_root()
    requested_paths = None if args.all_files or not args.filenames else args.filenames
    mode = "check" if args.check else "apply" if args.apply else "audit"
    return run_sweep(mode=mode, repo_root=repo_root, requested_paths=requested_paths, audit_out=args.audit_out)


if __name__ == "__main__":
    raise SystemExit(main())
