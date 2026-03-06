#!/usr/bin/env python3
import subprocess
from pathlib import Path
from validate_patch import validate_patch

def sh(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)

def main():
    repo_root = Path(__file__).resolve().parents[2]
    harness_dir = repo_root / "tools/prompt_rewrite_v4"
    bench_dir = harness_dir / "benchmark"
    
    patch_path = bench_dir / "response_opus.patch"
    if not patch_path.exists():
        raise SystemExit(f"Missing patch file: {patch_path}")

    sample_prompt_name = "PROMPT_B0_BOUNDARY_INVENTORY___PARTITION_PLAN.md"
    prompt_rel = f"tools/prompt_rewrite_v4/benchmark/prompts/{sample_prompt_name}"
    prompt_path = repo_root / prompt_rel
    
    if not prompt_path.exists():
        raise SystemExit(f"Missing isolated prompt file: {prompt_path}")

    diff_text = patch_path.read_text(encoding="utf-8")
    original_text = prompt_path.read_text(encoding="utf-8")

    res = validate_patch(
        diff_text=diff_text,
        expected_relpath=prompt_rel,
        original_prompt_text=original_text,
        max_patch_lines=350,
    )
    
    if not res.ok:
        raise SystemExit(f"PATCH VALIDATION FAILED: {res.reason}")

    print("Patch validation passed. Applying patch...")
    proc = sh(["git", "apply", "--whitespace=nowarn", str(patch_path)], cwd=repo_root)
    if proc.returncode != 0:
        raise SystemExit(f"git apply failed:\n{proc.stderr}")

    print(f"APPLIED PATCH SUCCESSFULLY to {prompt_rel}")

if __name__ == "__main__":
    main()
