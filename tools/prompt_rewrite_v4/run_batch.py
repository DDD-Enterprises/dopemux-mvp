from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from render_request import load_config, render_request
from validate_patch import section_bounds, validate_patch


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of file content."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sh(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)


def load_state(state_path: Path) -> dict:
    return json.loads(state_path.read_text(encoding="utf-8"))


def save_state(state_path: Path, state: dict) -> None:
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def list_prompt_files(repo_root: Path, glob_pat: str) -> List[Path]:
    # glob is relative to repo root
    return sorted(repo_root.glob(glob_pat))


def ensure_out_dir(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)


def lint_gate(repo_root: Path, lint_cmd: str) -> None:
    # Split the command string into a list to avoid shell=True injection risk.
    proc = subprocess.run(shlex.split(lint_cmd), cwd=str(repo_root), text=True)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def section_text(prompt_text: str, section_name: str) -> Optional[str]:
    bounds = section_bounds(prompt_text, section_name)
    if bounds is None:
        return None
    start, end = bounds
    lines = prompt_text.splitlines()
    if start > end:
        return ""
    return "\n".join(lines[start - 1 : end])


def has_heading(prompt_text: str, heading_name: str) -> bool:
    target = heading_name.strip().lower()
    for line in prompt_text.splitlines():
        if not line.startswith("#"):
            continue
        current = line.lstrip("#").strip().lower()
        if current == target or current.startswith(f"{target} ") or current.startswith(f"{target}("):
            return True
    return False


def is_inventory_partition_prompt(path: Path) -> bool:
    return "_INVENTORY___PARTITION_PLAN" in path.name


def pending_reasons_for_prompt(prompt_path: Path, prompt_text: str) -> List[str]:
    reasons: List[str] = []

    required_headings = ["Schema", "Extraction Procedure", "Failure Modes", "Legacy Context"]
    for heading in required_headings:
        if not has_heading(prompt_text, heading):
            reasons.append(f"missing_heading:{heading}")

    if "ItemList" not in prompt_text:
        reasons.append("missing_itemlist_envelope")
    if "line_range" not in prompt_text:
        reasons.append("missing_line_range_contract")

    ep_text = section_text(prompt_text, "Extraction Procedure")
    if ep_text is None:
        reasons.append("missing_extraction_procedure")
    else:
        numbered_steps = sum(
            1
            for line in ep_text.splitlines()
            if line.strip().startswith(tuple(f"{n}." for n in range(1, 10)))
        )
        if numbered_steps < 5:
            reasons.append("extraction_procedure_too_short")

    # Inventory/partition prompts should include explicit scan/classify/build phases.
    if is_inventory_partition_prompt(prompt_path) and ep_text is not None:
        ep_lower = ep_text.lower()
        if "scan" not in ep_lower:
            reasons.append("inventory_missing_scan_step")
        if "classif" not in ep_lower:
            reasons.append("inventory_missing_classify_step")
        if "build" not in ep_lower:
            reasons.append("inventory_missing_build_step")

    return sorted(set(reasons))


def build_pending_report(repo_root: Path, files: List[Path]) -> Tuple[List[Path], List[Dict[str, Any]]]:
    pending_files: List[Path] = []
    report_rows: List[Dict[str, Any]] = []

    for file_path in files:
        prompt_text = file_path.read_text(encoding="utf-8")
        reasons = pending_reasons_for_prompt(file_path, prompt_text)
        row: Dict[str, Any] = {
            "path": str(file_path.relative_to(repo_root)),
            "status": "pending" if reasons else "upgraded",
            "pending_reasons": reasons,
        }
        report_rows.append(row)
        if reasons:
            pending_files.append(file_path)

    report_rows.sort(key=lambda row: str(row["path"]))
    return pending_files, report_rows


def resolve_targets(repo_root: Path, cfg, pending_only: bool) -> Tuple[List[Path], Optional[List[Dict[str, Any]]]]:
    files = list_prompt_files(repo_root, cfg.prompt_glob)
    if not pending_only:
        return files, None
    pending_files, report_rows = build_pending_report(repo_root, files)
    return pending_files, report_rows


def cursor_key(pending_only: bool) -> str:
    return "pending_cursor" if pending_only else "cursor"


def mode_prefix(pending_only: bool) -> str:
    return "pending_" if pending_only else ""


def render_one(repo_root: Path, cfg_path: Path, state_path: Path, pending_only: bool = False) -> None:
    cfg = load_config(cfg_path)
    out_dir = repo_root / cfg.out_dir
    ensure_out_dir(out_dir)

    state = load_state(state_path)
    key = cursor_key(pending_only)
    cursor = int(state.get(key, 0))

    files, pending_report = resolve_targets(repo_root, cfg, pending_only)
    if not files:
        if pending_only:
            print("DONE: no pending prompts found")
            return
        raise SystemExit(f"No prompt files matched glob: {cfg.prompt_glob}")

    if cursor >= len(files):
        print(f"DONE: {key} at end of file list")
        return

    prompt_path = files[cursor]
    prompt_rel = str(prompt_path.relative_to(repo_root))

    # Pre-render validation: ensure target file has required sections.
    prompt_text = prompt_path.read_text(encoding="utf-8")
    ep_bounds = section_bounds(prompt_text, "Extraction Procedure")
    fm_bounds = section_bounds(prompt_text, "Failure Modes")

    if ep_bounds is None or fm_bounds is None:
        state.setdefault("failed", []).append(
            {
                "cursor": cursor,
                "cursor_key": key,
                "path": prompt_rel,
                "reason": (
                    "Missing required sections. "
                    f"Extraction Procedure: {ep_bounds is not None}, Failure Modes: {fm_bounds is not None}"
                ),
            }
        )
        # Advance to avoid getting stuck on the same bad file forever.
        state[key] = cursor + 1
        save_state(state_path, state)
        raise SystemExit(f"SKIP: {prompt_rel} missing required section headings")

    sha256_before = calculate_sha256(prompt_path)

    heur_path = cfg_path.parent / cfg.heuristics_path
    heur_text = heur_path.read_text(encoding="utf-8")

    request_text = render_request(
        heuristics_text=heur_text,
        prompt_relpath=prompt_rel,
        prompt_text=prompt_text,
        max_patch_lines=cfg.max_patch_lines,
    )

    req_file = out_dir / f"request_{mode_prefix(pending_only)}{cursor}.txt"
    req_file.write_text(request_text, encoding="utf-8")

    state.setdefault("in_progress", []).append(
        {
            "cursor": cursor,
            "cursor_key": key,
            "mode": "pending_only" if pending_only else "all",
            "path": prompt_rel,
            "sha256_before": sha256_before,
            "request_path": str(req_file.relative_to(repo_root)),
            "response_path": str(
                (out_dir / f"response_{mode_prefix(pending_only)}{cursor}.patch").relative_to(repo_root)
            ),
            "started_at": now_utc_iso(),
        }
    )
    if pending_only and pending_report is not None:
        state["pending_report"] = pending_report
    save_state(state_path, state)

    print(f"WROTE: {req_file}")
    print(f"SHA256: {sha256_before}")
    print(f"NEXT: run Opus in Claude Code using {repo_root / cfg.system_prompt_path} + {req_file}")
    print(f"SAVE PATCH AS: {out_dir / f'response_{mode_prefix(pending_only)}{cursor}.patch'}")


def apply_one(repo_root: Path, cfg_path: Path, state_path: Path, pending_only: bool = False) -> None:
    cfg = load_config(cfg_path)
    out_dir = repo_root / cfg.out_dir  # consistent with render_one: relative to repo_root
    ensure_out_dir(out_dir)

    state = load_state(state_path)
    key = cursor_key(pending_only)
    cursor = int(state.get(key, 0))

    files, _ = resolve_targets(repo_root, cfg, pending_only)
    if cursor >= len(files):
        print(f"DONE: {key} at end of file list")
        return

    prompt_path = files[cursor]
    prompt_rel = str(prompt_path.relative_to(repo_root))

    patch_path = out_dir / f"response_{mode_prefix(pending_only)}{cursor}.patch"
    if not patch_path.exists():
        raise SystemExit(f"Missing patch file: {patch_path}")

    diff_text = patch_path.read_text(encoding="utf-8")
    original_text = prompt_path.read_text(encoding="utf-8")

    res = validate_patch(
        diff_text=diff_text,
        expected_relpath=prompt_rel,
        original_prompt_text=original_text,
        max_patch_lines=cfg.max_patch_lines,
    )
    if not res.ok:
        state.setdefault("failed", []).append(
            {"cursor": cursor, "cursor_key": key, "path": prompt_rel, "reason": res.reason}
        )
        save_state(state_path, state)
        raise SystemExit(f"PATCH VALIDATION FAILED: {res.reason}")

    proc = sh(["git", "apply", "--whitespace=nowarn", str(patch_path)], cwd=repo_root)
    if proc.returncode != 0:
        state.setdefault("failed", []).append(
            {
                "cursor": cursor,
                "cursor_key": key,
                "path": prompt_rel,
                "reason": f"git apply failed: {proc.stderr.strip()}",
            }
        )
        save_state(state_path, state)
        raise SystemExit(f"git apply failed:\n{proc.stderr}")

    lint_gate(repo_root, cfg.lint_cmd)

    sha256_after = calculate_sha256(prompt_path)

    in_progress = state.get("in_progress", [])
    updated_in_progress = []
    for entry in in_progress:
        if (
            entry.get("cursor") == cursor
            and entry.get("path") == prompt_rel
            and entry.get("cursor_key", "cursor") == key
        ):
            entry["sha256_after"] = sha256_after
            entry["completed_at"] = now_utc_iso()
            state.setdefault("completed", []).append(entry)
        else:
            updated_in_progress.append(entry)
    state["in_progress"] = updated_in_progress

    state.setdefault("done", []).append(
        {
            "cursor": cursor,
            "cursor_key": key,
            "mode": "pending_only" if pending_only else "all",
            "path": prompt_rel,
        }
    )
    state[key] = cursor + 1
    save_state(state_path, state)

    print(f"APPLIED + LINT PASS: {prompt_rel}")
    print(f"SHA256: {sha256_after}")
    print(f"ADVANCED {key} -> {state[key]}")


def print_pending_report(repo_root: Path, cfg_path: Path) -> None:
    cfg = load_config(cfg_path)
    files = list_prompt_files(repo_root, cfg.prompt_glob)
    pending_files, report_rows = build_pending_report(repo_root, files)
    payload = {
        "prompt_glob": cfg.prompt_glob,
        "total_prompts": len(files),
        "pending_count": len(pending_files),
        "upgraded_count": len(files) - len(pending_files),
        "pending_paths": [str(path.relative_to(repo_root)) for path in pending_files],
        "report": report_rows,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", action="store_true", help="Render next request_<n>.txt for current cursor")
    ap.add_argument("--apply", action="store_true", help="Validate + apply response_<n>.patch and advance cursor")
    ap.add_argument(
        "--pending-only",
        action="store_true",
        help="Operate only on prompts that fail upgrade checks.",
    )
    ap.add_argument(
        "--pending-report",
        action="store_true",
        help="Print JSON report of prompts still needing upgrades.",
    )
    ap.add_argument("--config", default="tools/prompt_rewrite_v4/config.json")
    ap.add_argument("--state", default="tools/prompt_rewrite_v4/state.json")
    args = ap.parse_args()

    repo_root = Path(".").resolve()
    cfg_path = repo_root / args.config
    state_path = repo_root / args.state

    if not cfg_path.exists():
        raise SystemExit(f"Missing config: {cfg_path}")
    if not state_path.exists():
        raise SystemExit(f"Missing state: {state_path}")

    if args.pending_report:
        if args.render or args.apply:
            raise SystemExit("Use --pending-report by itself")
        print_pending_report(repo_root, cfg_path)
        return

    if args.render == args.apply:
        raise SystemExit("Choose exactly one: --render OR --apply")

    if args.render:
        render_one(repo_root, cfg_path, state_path, pending_only=args.pending_only)
    else:
        apply_one(repo_root, cfg_path, state_path, pending_only=args.pending_only)


if __name__ == "__main__":
    main()
