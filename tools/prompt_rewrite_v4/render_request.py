from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    repo_root: str
    prompt_glob: str
    heuristics_path: str
    system_prompt_path: str
    patch_prompt_path: str
    out_dir: str
    max_patch_lines: int
    batch_size: int
    lint_cmd: str
    commit_every: int
    commit_prefix: str


def load_config(path: Path) -> Config:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return Config(**raw)


def render_request(
    heuristics_text: str,
    prompt_relpath: str,
    prompt_text: str,
    max_patch_lines: int,
) -> str:
    # Keep the request deterministic and compact.
    # The system prompt is separate; this is the user payload.
    return "\n".join(
        [
            "Task: Produce a minimal unified diff patch for the provided prompt file.",
            "",
            f"Output cap: If unified diff would exceed {max_patch_lines} lines, output exactly: OUTPUT_LIMIT_REACHED",
            "",
            "Inputs:",
            "- Heuristics Library v1",
            "- Prompt file content",
            "",
            "Heuristics Library v1:",
            "---BEGIN HEURISTICS---",
            heuristics_text.rstrip("\n"),
            "---END HEURISTICS---",
            "",
            f"FILE: {prompt_relpath}",
            "---BEGIN FILE---",
            prompt_text.rstrip("\n"),
            "---END FILE---",
            "",
            "Return unified diff only. No prose.",
            "",
        ]
    )


def main() -> None:
    # This module is imported by run_batch.py; not intended as a CLI.
    raise SystemExit("render_request.py is not a CLI. Use run_batch.py.")


if __name__ == "__main__":
    main()