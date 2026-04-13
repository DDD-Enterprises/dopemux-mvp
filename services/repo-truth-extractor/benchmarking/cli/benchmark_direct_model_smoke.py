from __future__ import annotations

import argparse
import getpass
import os
import sys
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve()
SERVICE_ROOT = HERE.parents[2]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.direct_model.runner import DirectModelRunner
from output_safety import sanitized_json_text


@contextmanager
def _temporary_credentials(overrides: dict[str, str]):
    original = {key: os.environ.get(key) for key in overrides}
    try:
        for key, value in overrides.items():
            os.environ[key] = value
        yield
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _resolve_prompted_credentials(
    *,
    openrouter_api_key: str | None,
    xai_api_key: str | None,
    prompt_for_keys: bool,
) -> dict[str, str]:
    resolved = {
        "OPENROUTER_API_KEY": str(openrouter_api_key or "").strip(),
        "XAI_API_KEY": str(xai_api_key or "").strip(),
    }
    missing = [key for key, value in resolved.items() if not value]
    if missing and not prompt_for_keys:
        missing_csv = ", ".join(sorted(missing))
        raise RuntimeError(
            f"Missing required active benchmark credentials: {missing_csv}. "
            "Provide them explicitly with CLI flags or rerun with prompting enabled."
        )
    if missing and not sys.stdin.isatty():
        missing_csv = ", ".join(sorted(missing))
        raise RuntimeError(
            f"Cannot prompt for missing credentials in non-interactive mode: {missing_csv}. "
            "Pass --openrouter-api-key and --xai-api-key explicitly."
        )
    for key in missing:
        provider_label = "OpenRouter" if key == "OPENROUTER_API_KEY" else "xAI"
        resolved[key] = getpass.getpass(f"Enter active {provider_label} API key for this run: ").strip()
        if not resolved[key]:
            raise RuntimeError(f"{provider_label} API key was not provided.")
    return resolved


def run_direct_model_smoke(
    root: Path | None = None,
    proof_dir: Path | None = None,
    *,
    openrouter_api_key: str | None = None,
    xai_api_key: str | None = None,
    prompt_for_keys: bool = True,
) -> dict[str, object]:
    runner = DirectModelRunner(root)
    overrides = _resolve_prompted_credentials(
        openrouter_api_key=openrouter_api_key,
        xai_api_key=xai_api_key,
        prompt_for_keys=prompt_for_keys,
    )
    with _temporary_credentials(overrides):
        return runner.run(proof_dir=proof_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Direct-model benchmark MVP smoke runner.")
    parser.add_argument("--benchmark-root", type=Path, default=None)
    parser.add_argument("--proof-dir", type=Path, default=None)
    parser.add_argument("--openrouter-api-key", default=None)
    parser.add_argument("--xai-api-key", default=None)
    parser.add_argument(
        "--no-prompt-for-keys",
        action="store_true",
        help="Fail closed instead of prompting for active keys.",
    )
    args = parser.parse_args(argv)
    payload = run_direct_model_smoke(
        root=args.benchmark_root,
        proof_dir=args.proof_dir,
        openrouter_api_key=args.openrouter_api_key,
        xai_api_key=args.xai_api_key,
        prompt_for_keys=not args.no_prompt_for_keys,
    )
    print(sanitized_json_text(payload, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
