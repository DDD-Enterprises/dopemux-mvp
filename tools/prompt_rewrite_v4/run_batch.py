from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import List

from render_request import load_config, render_request
from validate_patch import validate_patch


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
    # Run via shell for convenience; command is controlled by config.
    proc = subprocess.run(lint_cmd, cwd=str(repo_root), shell=True, text=True)
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

    # Resolve heuristics path relative to cfg_path directory
    heur_path = cfg_path.parent / cfg.heuristics_path
    heur_text = heur_path.read_text(encoding="utf-8")
    prompt_text = prompt_path.read_text(encoding="utf-8")

    request_text = render_request(
        heuristics_text=heur_text,
        prompt_relpath=prompt_rel,
        prompt_text=prompt_text,
        max_patch_lines=cfg.max_patch_lines,
    )

    req_file = out_dir / f"request_{cursor}.txt"
    req_file.write_text(request_text, encoding="utf-8")

    print(f"WROTE: {req_file}")
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

    # Mark done + advance
    state.setdefault("done", []).append({"cursor": cursor, "path": prompt_rel})
    state["cursor"] = cursor + 1
    save_state(state_path, state)

    print(f"APPLIED + LINT PASS: {prompt_rel}")
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