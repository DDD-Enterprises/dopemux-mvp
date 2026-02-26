from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from render_request import load_config, render_request
from validate_patch import validate_patch, section_bounds


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of file content."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


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
    # Split the command string into a list to avoid shell injection risks.
    cmd_list = shlex.split(lint_cmd)
    proc = subprocess.run(cmd_list, cwd=str(repo_root), text=True)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def render_one(repo_root: Path, cfg_path: Path, state_path: Path) -> None:
    cfg = load_config(cfg_path)
    out_dir = repo_root / cfg.out_dir
    ensure_out_dir(out_dir)

    state = load_state(state_path)
    cursor = int(state.get("cursor", 0))

    files = list_prompt_files(repo_root, cfg.prompt_glob)
    if not files:
        raise SystemExit(f"No prompt files matched glob: {cfg.prompt_glob}")

    if cursor >= len(files):
        print("DONE: cursor at end of file list")
        return

    prompt_path = files[cursor]
    prompt_rel = str(prompt_path.relative_to(repo_root))

    # Pre-render validation: ensure target file has required sections
    prompt_text = prompt_path.read_text(encoding="utf-8")
    ep_bounds = section_bounds(prompt_text, "Extraction Procedure")
    fm_bounds = section_bounds(prompt_text, "Failure Modes")
    
    if ep_bounds is None or fm_bounds is None:
        state.setdefault("failed", []).append({
            "cursor": cursor, 
            "path": prompt_rel, 
            "reason": f"Missing required sections. Extraction Procedure: {ep_bounds is not None}, Failure Modes: {fm_bounds is not None}"
        })
        save_state(state_path, state)
        raise SystemExit(f"SKIP: {prompt_rel} missing required section headings")

    # Resolve heuristics path relative to cfg_path directory
    # Calculate file hash for audit trail
    sha256_before = calculate_sha256(prompt_path)

    heur_path = cfg_path.parent / cfg.heuristics_path
    heur_text = heur_path.read_text(encoding="utf-8")

    request_text = render_request(
        heuristics_text=heur_text,
        prompt_relpath=prompt_rel,
        prompt_text=prompt_text,
        max_patch_lines=cfg.max_patch_lines,
    )

    req_file = out_dir / f"request_{cursor}.txt"
    req_file.write_text(request_text, encoding="utf-8")

    # Update state with file hash and request/response paths
    state.setdefault("in_progress", []).append({
        "cursor": cursor,
        "path": prompt_rel,
        "sha256_before": sha256_before,
        "request_path": str(req_file.relative_to(repo_root)),
        "response_path": str((out_dir / f"response_{cursor}.patch").relative_to(repo_root)),
        "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    })
    save_state(state_path, state)

    print(f"WROTE: {req_file}")
    print(f"SHA256: {sha256_before}")
    print(f"NEXT: run Opus in Claude Code using {repo_root / cfg.system_prompt_path} + {req_file}")
    print(f"SAVE PATCH AS: {out_dir / f'response_{cursor}.patch'}")


def apply_one(repo_root: Path, cfg_path: Path, state_path: Path) -> None:
    cfg = load_config(cfg_path)
    out_dir = cfg_path.parent / cfg.out_dir
    ensure_out_dir(out_dir)

    state = load_state(state_path)
    cursor = int(state.get("cursor", 0))

    files = list_prompt_files(repo_root, cfg.prompt_glob)
    if cursor >= len(files):
        print("DONE: cursor at end of file list")
        return

    prompt_path = files[cursor]
    prompt_rel = str(prompt_path.relative_to(repo_root))

    # Use repo_root for out_dir to match render_one behavior
    out_dir = repo_root / cfg.out_dir
    patch_path = out_dir / f"response_{cursor}.patch"
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
        state.setdefault("failed", []).append({"cursor": cursor, "path": prompt_rel, "reason": res.reason})
        save_state(state_path, state)
        raise SystemExit(f"PATCH VALIDATION FAILED: {res.reason}")

    # Apply patch
    proc = sh(["git", "apply", "--whitespace=nowarn", str(patch_path)], cwd=repo_root)
    if proc.returncode != 0:
        state.setdefault("failed", []).append(
            {"cursor": cursor, "path": prompt_rel, "reason": f"git apply failed: {proc.stderr.strip()}"}
        )
        save_state(state_path, state)
        raise SystemExit(f"git apply failed:\n{proc.stderr}")

    # Lint gate (hard)
    lint_gate(repo_root, cfg.lint_cmd)

    # Calculate after hash and update audit trail
    sha256_after = calculate_sha256(prompt_path)
    
    # Find and update the in_progress entry
    in_progress = state.get("in_progress", [])
    updated_in_progress = []
    completed_entry = None
    for entry in in_progress:
        if entry.get("cursor") == cursor and entry.get("path") == prompt_rel:
            entry["sha256_after"] = sha256_after
            entry["completed_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            completed_entry = entry
            state.setdefault("completed", []).append(entry)
        else:
            updated_in_progress.append(entry)
    state["in_progress"] = updated_in_progress

    # Mark done + advance
    state.setdefault("done", []).append({"cursor": cursor, "path": prompt_rel})
    state["cursor"] = cursor + 1
    save_state(state_path, state)

    print(f"APPLIED + LINT PASS: {prompt_rel}")
    print(f"SHA256: {sha256_after}")
    print(f"ADVANCED CURSOR -> {state['cursor']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", action="store_true", help="Render next request_<n>.txt for current cursor")
    ap.add_argument("--apply", action="store_true", help="Validate + apply response_<n>.patch and advance cursor")
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

    if args.render == args.apply:
        raise SystemExit("Choose exactly one: --render OR --apply")

    if args.render:
        render_one(repo_root, cfg_path, state_path)
    else:
        apply_one(repo_root, cfg_path, state_path)


if __name__ == "__main__":
    main()