#!/usr/bin/env python3
"""Prepare an isolated benchmark prompt + request payload for Opus patch testing."""

from __future__ import annotations

import shutil
from pathlib import Path

from render_request import render_request


SAMPLE_PROMPT_REL = (
    "services/repo-truth-extractor/promptsets/v4/prompts/"
    "PROMPT_B0_BOUNDARY_INVENTORY___PARTITION_PLAN.md"
)


def _resolve_heuristics_path(harness_dir: Path) -> Path:
    md_path = harness_dir / "HEURISTICS_LIBRARY_v1.md"
    txt_path = harness_dir / "HEURISTICS_LIBRARY_v1.txt"
    if md_path.exists():
        return md_path
    if txt_path.exists():
        return txt_path
    raise FileNotFoundError("Missing heuristics library (.md or .txt)")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    harness_dir = repo_root / "tools" / "prompt_rewrite_v4"
    bench_dir = harness_dir / "benchmark"
    bench_prompts = bench_dir / "prompts"
    bench_prompts.mkdir(parents=True, exist_ok=True)

    src_prompt = repo_root / SAMPLE_PROMPT_REL
    if not src_prompt.exists():
        raise SystemExit(f"Sample prompt does not exist: {src_prompt}")

    dst_prompt = bench_prompts / src_prompt.name
    shutil.copy2(src_prompt, dst_prompt)

    heur_path = _resolve_heuristics_path(harness_dir)
    heur_text = heur_path.read_text(encoding="utf-8")
    prompt_text = dst_prompt.read_text(encoding="utf-8")

    request_text = render_request(
        heuristics_text=heur_text,
        prompt_relpath=f"tools/prompt_rewrite_v4/benchmark/prompts/{dst_prompt.name}",
        prompt_text=prompt_text,
        max_patch_lines=350,
    )

    req_file = bench_dir / "request_benchmark.txt"
    req_file.write_text(request_text, encoding="utf-8")

    sys_prompt = harness_dir / "OPUS_SYSTEM_PROMPT.txt"
    if sys_prompt.exists():
        shutil.copy2(sys_prompt, bench_dir / "OPUS_SYSTEM_PROMPT.txt")

    print(f"WROTE: {req_file.relative_to(repo_root)}")
    print("READY FOR OPUS:")
    print("1. Use tools/prompt_rewrite_v4/benchmark/OPUS_SYSTEM_PROMPT.txt as System Instructions")
    print("2. Feed tools/prompt_rewrite_v4/benchmark/request_benchmark.txt to Opus")
    print("3. Save diff output as tools/prompt_rewrite_v4/benchmark/response_opus.patch")


if __name__ == "__main__":
    main()
