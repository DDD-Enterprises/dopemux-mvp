"""Truth-harness capture + normalization for RTE characterization goldens (P0).

RTE-TRUTH program, task P0. Provides:

- ``normalize_text``: strips machine/run-specific noise (absolute paths,
  timestamps, git/file SHAs, run ids, durations, PIDs) and masks
  env-dependent fields (``api_key_present``, webhook/live-ok echoes) so a
  golden never encodes the local environment or key presence.
- ``CAPTURES``: the declarative list of introspection-only commands whose
  normalized output is snapshotted under ``tests/goldens/``.
- ``run_capture``: executes one capture in a sanitized subprocess env
  (provider API keys and ``DPMX_*`` consent vars removed - defense in depth
  against accidental live spend) and returns normalized text.
- ``python -m``-style regeneration: ``python tests/goldens/_normalize.py``
  rewrites all goldens plus ``MANIFEST.sha256``.

SAFETY: every capture is dry-run/introspection only. ``--execute`` and
``DPMX_LIVE_OK`` are never used. Captures that would hit provider networks
(``rte doctor`` / ``rte preflight`` live runs, ``rte validate-live``) are
deliberately captured at ``--help`` level only: ``run_doctor_full`` and
``run_provider_preflight`` in ``run_extraction_v5.py`` invoke
``run_provider_doctor_probe`` -> ``call_llm`` (real provider HTTP calls).

Cost previews are captured as the trailing JSON document only, with all
numeric leaves masked (token/cost estimates depend on repo content); the
stable characterization payload is the per-phase route/model identity.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

GOLDENS_DIR = Path(__file__).resolve().parent
SERVICE_ROOT = GOLDENS_DIR.parents[1]
REPO_ROOT = GOLDENS_DIR.parents[3]
RUNNER_V5 = SERVICE_ROOT / "run_extraction_v5.py"
MANIFEST_NAME = "MANIFEST.sha256"

# All 11 operator-facing cost profiles (run_extraction_v5.py COST_PROFILES).
COST_PROFILES: Tuple[str, ...] = (
    "economy",
    "value-default",
    "quality",
    "experimental",
    "gemini-value",
    "grok-fast",
    "openrouter-resilient",
    "openai-heavy",
    "balanced-mix",
    "quality-mix",
    "budget-mix",
)

# Cost preview is captured for the default profile only. Measured wall time
# for one --print-cost-preview invocation from the repo root is ~259s: the
# preview requires a full dry-run phase execution, which walks and sha256-
# hashes every file under the phase's scan roots BEFORE the preview JSON is
# emitted (finding: cost preview is not a cheap introspection surface).
# Route identity for ALL 11 profiles is asserted by the print-config goldens.
COST_PREVIEW_PROFILES: Tuple[str, ...] = ("value-default",)

# Captures whose regeneration is too slow for the default test path. The
# characterization test skips these unless RTE_TRUTH_SLOW_GOLDENS=1.
SLOW_CAPTURE_NAMES: Tuple[str, ...] = ("cost_preview_value_default",)

_SECRET_ENV_PREFIXES = ("DPMX_",)
_SECRET_ENV_VARS = (
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "XAI_API_KEY",
    "OPENROUTER_API_KEY",
    "ANTHROPIC_API_KEY",
)

# --- Normalization rules (order matters) -----------------------------------

_RULES: Tuple[Tuple[re.Pattern[str], str], ...] = (
    # 64-hex (runner_sha256, prompt SHAs) and 40-hex (git SHAs).
    (re.compile(r"\b[0-9a-f]{64}\b"), "<SHA256>"),
    (re.compile(r"\b[0-9a-f]{40}\b"), "<GITSHA>"),
    # ISO-8601 timestamps.
    (
        re.compile(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?"
        ),
        "<TIMESTAMP>",
    ),
    # Generated run ids (run_YYYYMMDDTHHMMSSZ).
    (re.compile(r"\brun_\d{8}T\d{6}Z\b"), "<RUN_ID>"),
    # Leading wall-clock log prefixes (e.g. "14:38:37 [INFO] ...").
    (re.compile(r"(?m)^\d{2}:\d{2}:\d{2} "), "<TIME> "),
    # Durations / throughput / payload sizes / PIDs.
    (
        re.compile(r"\b(elapsed_ms|elapsed_seconds|duration_ms|duration_seconds)=\d+(?:\.\d+)?"),
        r"\1=<NUM>",
    ),
    (
        re.compile(r"\"(elapsed_ms|elapsed_seconds|duration_ms|duration_seconds|pid)\":\s*\d+(?:\.\d+)?"),
        r'"\1": "<NUM>"',
    ),
    (re.compile(r"\bthroughput_partitions_per_min=[\d.]+"), "throughput_partitions_per_min=<NUM>"),
    (re.compile(r"\b(\w*_bytes)=\d+"), r"\1=<NUM>"),
    (re.compile(r"\bpid=\d+"), "pid=<NUM>"),
    # Env-dependent / key-presence fields: never encode the local env in a
    # golden. Covers doctor/preflight payloads should they ever be captured,
    # and print-config webhook echoes.
    (re.compile(r"\"api_key_present\":\s*(?:true|false)"), '"api_key_present": "<MASKED>"'),
    (
        re.compile(r"\"api_key_env_resolved\":\s*(?:\"[^\"]*\"|null)"),
        '"api_key_env_resolved": "<MASKED>"',
    ),
    (re.compile(r"\"secret_set\":\s*(?:true|false)"), '"secret_set": "<MASKED>"'),
    (re.compile(r"\"live_ok\":\s*(?:true|false)"), '"live_ok": "<MASKED>"'),
    (
        re.compile(r"\"(dpmx_webhook_[a-z_]+|dpmx_live_ok)\":\s*(?:\"[^\"]*\"|true|false|\d+)"),
        r'"\1": "<MASKED>"',
    ),
    # Interpreter identity.
    (re.compile(r"\"python_executable\":\s*\"[^\"]+\""), '"python_executable": "<PYTHON_EXECUTABLE>"'),
    (re.compile(r"\"python_version\":\s*\"[^\"]+\""), '"python_version": "<PYTHON_VERSION>"'),
)


def normalize_text(text: str) -> str:
    """Strip machine/run/env-specific noise from captured output."""
    out = text.replace("\r\n", "\n")
    # Path masking first: worktree root, then service root remnants, then home.
    out = out.replace(str(REPO_ROOT), "$REPO")
    out = out.replace(str(Path.home()), "$HOME")
    for pattern, replacement in _RULES:
        out = pattern.sub(replacement, out)
    if not out.endswith("\n"):
        out += "\n"
    return out


def _mask_json_numbers(value):
    """Recursively replace numeric leaves; normalize string leaves."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return "<NUM>"
    if isinstance(value, str):
        return normalize_text(value).rstrip("\n")
    if isinstance(value, list):
        return [_mask_json_numbers(item) for item in value]
    if isinstance(value, dict):
        return {key: _mask_json_numbers(item) for key, item in value.items()}
    return value


def normalize_cost_preview(stdout: str) -> str:
    """Extract the trailing cost-preview JSON document and mask numerics.

    The runner interleaves dry-run narration with the final preview JSON on
    stdout. Narration numerics (inventory counts, payload bytes) are repo-
    content dependent, so only the JSON document is snapshotted, with all
    numeric leaves masked. Route/model identity (dict keys such as
    ``openai/gpt-5.3-codex``) is preserved - that is the characterization.
    """
    payload = None
    for match in re.finditer(r"(?m)^\{", stdout):
        candidate = stdout[match.start():]
        try:
            payload = json.loads(candidate)
            break
        except json.JSONDecodeError:
            continue
    if payload is None:
        raise AssertionError(
            "No JSON document found in --print-cost-preview stdout; "
            "first 500 chars: " + stdout[:500]
        )
    masked = _mask_json_numbers(payload)
    return json.dumps(masked, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


# --- Capture specs ----------------------------------------------------------


@dataclass(frozen=True)
class CaptureSpec:
    name: str
    argv: Tuple[str, ...]  # appended after the python executable
    kind: str  # "text" | "cost_preview"
    timeout: int = 120
    notes: str = ""

    @property
    def golden_filename(self) -> str:
        return f"{self.name}.golden.txt"


def _cli(*args: str) -> Tuple[str, ...]:
    return ("-m", "dopemux", "rte", *args)


def _runner(*args: str) -> Tuple[str, ...]:
    return (str(RUNNER_V5), *args)


_HELP_SUBCOMMANDS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("help_rte", ()),
    ("help_rte_run", ("run",)),
    ("help_rte_list", ("list",)),
    ("help_rte_doctor", ("doctor",)),
    ("help_rte_status", ("status",)),
    ("help_rte_preflight", ("preflight",)),
    ("help_rte_validate_live", ("validate-live",)),
    ("help_rte_trace", ("trace",)),
    ("help_rte_scan", ("scan",)),
    ("help_rte_wizard", ("wizard",)),
    ("help_rte_promptset", ("promptset",)),
)


def _build_captures() -> List[CaptureSpec]:
    captures: List[CaptureSpec] = []
    for name, sub in _HELP_SUBCOMMANDS:
        captures.append(
            CaptureSpec(
                name=name,
                argv=_cli(*sub, "--help"),
                kind="text",
                notes="Click help text (COLUMNS=80).",
            )
        )
    captures.append(
        CaptureSpec(
            name="rte_list_v5",
            argv=_cli("list"),
            kind="text",
            notes="v5 list == readonly --print-config with no phase scope.",
        )
    )
    captures.append(
        CaptureSpec(
            name="rte_status_empty_run",
            argv=_runner("--status", "--run-id", "golden_truth_status"),
            kind="text",
            notes="Status table for a fresh (all NOT_STARTED) fixed run id.",
        )
    )
    for profile in COST_PROFILES:
        captures.append(
            CaptureSpec(
                name=f"print_config_{profile.replace('-', '_')}",
                argv=_runner(
                    "--cost-profile",
                    profile,
                    "--phase",
                    "A",
                    "--dry-run",
                    "--skip-prescan",
                    "--print-config",
                    "--run-id",
                    f"golden_truth_pc_{profile.replace('-', '_')}",
                ),
                kind="text",
                notes="Resolved config incl. cell aliases + route requirements.",
            )
        )
    for profile in COST_PREVIEW_PROFILES:
        captures.append(
            CaptureSpec(
                name=f"cost_preview_{profile.replace('-', '_')}",
                argv=_runner(
                    "--cost-profile",
                    profile,
                    "--phase",
                    "A",
                    "--dry-run",
                    "--skip-prescan",
                    "--print-cost-preview",
                    "--run-id",
                    f"golden_truth_cpv_{profile.replace('-', '_')}",
                ),
                kind="cost_preview",
                timeout=420,
                notes="Trailing preview JSON only; numeric leaves masked.",
            )
        )
    return captures


CAPTURES: List[CaptureSpec] = _build_captures()

# Captures deliberately NOT taken (documented for the audit trail):
SKIPPED_CAPTURES: Dict[str, str] = {
    "rte doctor (live)": (
        "run_doctor_full -> run_provider_doctor_probe -> call_llm makes real "
        "provider HTTP calls; not introspection-safe. Help-only capture."
    ),
    "rte preflight (live)": (
        "run_provider_preflight probes every routed provider via call_llm. "
        "Help-only capture."
    ),
    "rte validate-live (live)": (
        "Fail-closed live validation workflow (paid stages). Help-only capture."
    ),
    "rte wizard (interactive)": "Interactive walkthrough. Help-only capture.",
    "rte scan (execution)": (
        "Blocked by default (legacy v3 consent gate). Help-only capture."
    ),
    "cost previews for remaining 10 profiles": (
        "Time-box: one --print-cost-preview costs ~259s wall time from the "
        "repo root (full dry-run phase execution incl. file walk + hashing "
        "precedes the preview). Only value-default is snapshotted, and its "
        "regeneration is gated behind RTE_TRUTH_SLOW_GOLDENS=1. Route "
        "identity for all 11 profiles is covered by print-config goldens."
    ),
}


def subprocess_env() -> Dict[str, str]:
    """Sanitized env: no provider keys, no DPMX_* consent vars, fixed width."""
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in _SECRET_ENV_VARS
        and not any(key.startswith(prefix) for prefix in _SECRET_ENV_PREFIXES)
    }
    env["COLUMNS"] = "80"
    env["NO_COLOR"] = "1"
    env["TERM"] = "dumb"
    existing = env.get("PYTHONPATH", "")
    src = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src if not existing else f"{src}{os.pathsep}{existing}"
    return env


def run_capture(spec: CaptureSpec) -> str:
    proc = subprocess.run(
        [sys.executable, *spec.argv],
        cwd=str(REPO_ROOT),
        env=subprocess_env(),
        capture_output=True,
        text=True,
        timeout=spec.timeout,
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"capture {spec.name!r} exited {proc.returncode}\n"
            f"argv: {spec.argv}\nstderr tail:\n{proc.stderr[-2000:]}"
        )
    if spec.kind == "cost_preview":
        return normalize_cost_preview(proc.stdout)
    return normalize_text(proc.stdout)


def write_manifest() -> Path:
    lines = []
    for path in sorted(GOLDENS_DIR.glob("*.golden.txt")):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.name}")
    manifest = GOLDENS_DIR / MANIFEST_NAME
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest


def regenerate(names: Sequence[str] | None = None) -> None:
    import time

    for spec in CAPTURES:
        if names and spec.name not in names:
            continue
        started = time.time()
        output = run_capture(spec)
        (GOLDENS_DIR / spec.golden_filename).write_text(output, encoding="utf-8")
        print(f"[golden] {spec.name}: {len(output)} chars in {time.time() - started:.1f}s")
    write_manifest()
    print(f"[golden] wrote {MANIFEST_NAME}")


if __name__ == "__main__":
    regenerate(sys.argv[1:] or None)
