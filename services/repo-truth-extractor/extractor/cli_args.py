"""Argparse construction seam for the Repo Truth Extractor v5 runner."""

from __future__ import annotations

import argparse
import textwrap
from dataclasses import dataclass
from typing import Any, Mapping, Sequence


DEFAULT_MAX_FILES_DOCS = 35
DEFAULT_MAX_FILES_CODE = 20
DEFAULT_MAX_CHARS = 650000
DEFAULT_FILE_TRUNCATE_CHARS = 70000


@dataclass(frozen=True)
class ParserContext:
    """Contract values owned by the v5 runner and injected into its CLI seam."""

    phases: Sequence[str]
    dpmx_live_ok_env: str
    first_live_preset_name: str
    staged_safe_preset_name: str
    default_gemini_model_id: str
    cost_profiles: Mapping[str, Any]
    cost_profile_aliases: Mapping[str, str]
    cost_profile_alias_metadata: Mapping[str, Any]
    default_cost_profile: str
    routing_policy_choices: Sequence[str]
    routing_ladders: Mapping[str, Any]
    default_routing_policy: str
    s_prompts_modes: Sequence[str]
    interactive_safe_batch_wait_seconds: int
    verify_phase_choices: Sequence[str]
    promptgen_default_max_files: int
    promptgen_default_max_bytes: int
    promptgen_default_excerpt_bytes: int
    promptgen_default_output_dir: str


class OperatorArgumentParser(argparse.ArgumentParser):
    """Argument parser with operator guidance that preserves the v5 CLI contract."""

    def __init__(self, *args: Any, context: ParserContext, **kwargs: Any) -> None:
        self._context = context
        super().__init__(*args, **kwargs)

    def format_help(self) -> str:
        quick_reference = textwrap.dedent(
            f"""
            Operator Quick Reference
              Common:
                --preset {self._context.first_live_preset_name} --dry-run --run-id local_probe
                --print-cost-preview --phase A --dry-run
                --print-routing-guide
              Advanced:
                --routing-policy balanced_openrouter
                --output-root /abs/path/to/sandboxed-artifacts
              Diagnostics:
                --list-phases
                --print-config --phase A --dry-run
                --preflight-providers --phase D
              Recovery / Resume:
                --resume --phase D --run-id <RUN_ID>
                --status --run-id <RUN_ID>

            Examples
              Validator-first staged first live:
                python services/repo-truth-extractor/run_extraction_v5.py --preset {self._context.first_live_preset_name} --dry-run --run-id first_live_probe
              Explicit cost preview:
                python services/repo-truth-extractor/run_extraction_v5.py --print-cost-preview --phase A --dry-run --run-id cost_probe
              Isolated artifact root:
                python services/repo-truth-extractor/run_extraction_v5.py --phase A --dry-run --output-root /tmp/rte-v5-sandbox
            """
        ).strip()
        return quick_reference + "\n\n" + super().format_help()

    def error(self, message: str) -> None:
        detail = str(message or "")
        guidance: list[str] = []
        if "argument --routing-policy: invalid choice" in detail:
            guidance.extend(
                [
                    f"Valid routing policies: {', '.join(sorted(self._context.routing_ladders.keys()))}.",
                    f"Example: --routing-policy {self._context.default_routing_policy}",
                ]
            )
        elif "argument --phase: invalid choice" in detail:
            guidance.extend(
                [
                    f"Valid phases: {', '.join(self._context.phases)} plus S_INT or ALL.",
                    "Example: --phase A --dry-run",
                ]
            )
        elif "DPMX_LIVE_OK" in detail or "explicit consent" in detail:
            guidance.extend(
                [
                    "Use --dry-run first to inspect inputs, routes, and estimated cost.",
                    f"Only rerun live with --execute and {self._context.dpmx_live_ok_env}=1 after approval.",
                ]
            )
        elif "--phase is required" in detail:
            guidance.extend(
                [
                    "Use --phase <PHASE> for execution, or one of the introspection modes such as --list-phases, --print-config, or --print-cost-preview.",
                    f"Example: --phase A --dry-run or --preset {self._context.first_live_preset_name} --dry-run",
                ]
            )
        if guidance:
            detail = detail.rstrip() + "\n\n" + "\n".join(guidance)
        super().error(detail)


def build_parser(context: ParserContext) -> OperatorArgumentParser:
    parser = OperatorArgumentParser(
        "Master Extraction Runner",
        description=(
            "Repo Truth Extractor v5 runtime. Use --dry-run for preview. "
            f"Live execution requires explicit consent via {context.dpmx_live_ok_env}=1."
        ),
        epilog=(
            "Quick start: python services/repo-truth-extractor/run_extraction_v5.py "
            "--phase A --dry-run --run-id local_preview. "
            f"For live execution, rerun with --execute and {context.dpmx_live_ok_env}=1."
        ),
        context=context,
    )
    parser.add_argument("--skip-prescan", action="store_true", help="Skip the integrated Stage 0 prescan.")
    parser.add_argument("--prescan-import-dir", type=str, help="Import precomputed prescan from external directory.")
    parser.add_argument("--prescan-online", action="store_true", help="Authorize online LLM passes during integrated prescan.")
    parser.add_argument(
        "--prescan-allow-scope-reduction",
        action="store_true",
        help=(
            "Allow prescan skip hints to remove files from execution scope. Disabled by default "
            "so prescan remains non-authoritative for first baseline runs."
        ),
    )
    parser.add_argument("--allow-online-llm", action="store_true", help="Authorize online LLM spend for the whole run.")
    parser.add_argument(
        "--preset",
        choices=[context.first_live_preset_name, context.staged_safe_preset_name],
        default=None,
        help="Apply a staged operator-safe rollout preset.",
    )
    parser.add_argument(
        "--preset-stage",
        choices=["initial", "post-review", "full"],
        default="initial",
        help="Preset stage to execute. 'initial' runs A/H/D/C, 'post-review' runs R/X/T/Z/S/SP.",
    )
    parser.add_argument(
        "--skip-pre-live-validator",
        action="store_true",
        help="Skip the validator-first gate for live preset execution.",
    )
    parser.add_argument(
        "--output-root",
        type=str,
        default=None,
        help="Override the v5 artifact root for this run (for isolated experiments or CI sandboxes).",
    )
    parser.add_argument("--sync", action="store_true", help="Synchronize prompt source scopes with modern architecture.")
    parser.add_argument("--phase", choices=context.phases + ["S_INT", "ALL"], required=False)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--execute",
        action="store_true",
        help=(
            "Explicitly permit live provider execution. Requires "
            f"{context.dpmx_live_ok_env}=1."
        ),
    )
    parser.add_argument("--max-files-docs", type=int, default=DEFAULT_MAX_FILES_DOCS)
    parser.add_argument("--max-files-code", type=int, default=DEFAULT_MAX_FILES_CODE)
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    parser.add_argument("--max-request-bytes", type=int, default=200000)
    parser.add_argument("--file-truncate-chars", type=int, default=DEFAULT_FILE_TRUNCATE_CHARS)
    parser.add_argument("--home-scan-mode", choices=["safe", "full"], default="safe")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--fail-fast-auth", dest="fail_fast_auth", action="store_true", default=True
    )
    parser.add_argument(
        "--no-fail-fast-auth", dest="fail_fast_auth", action="store_false"
    )
    parser.add_argument(
        "--gemini-auth-mode",
        choices=["api_key", "bearer", "both", "query_key", "auto"],
        default="auto",
    )
    parser.add_argument(
        "--gemini-model-id",
        type=str,
        default=context.default_gemini_model_id,
        help="Override Gemini model ID for all Gemini-routed phases.",
    )
    parser.add_argument(
        "--routing-policy",
        choices=context.routing_policy_choices,
        default=None,
        help=(
            "DEPRECATED: legacy routing policy. Prefer --cost-profile. "
            "When set, this value is mapped to a cost profile via "
            "LEGACY_ROUTING_POLICY_TO_COST_PROFILE and a deprecation warning is emitted."
        ),
    )
    parser.add_argument(
        "--cost-profile",
        choices=sorted(list(context.cost_profiles.keys()) + list(context.cost_profile_aliases.keys())),
        default=None,
        metavar="PROFILE",
        help=(
            f"Cost profile selecting model tier + service_tier + cached-input + "
            f"batch behavior. Default: {context.default_cost_profile}. "
            f"Known profiles: {', '.join(sorted(context.cost_profiles.keys()))}. "
            "Workload aliases: "
            f"{', '.join(sorted(context.cost_profile_alias_metadata.keys()))}. "
            "Additional rte-cost-* aliases are normalized through the cost-profile "
            "resolver. Replaces --routing-policy. See "
            "claudedocs/research/routing-design-2026-05.md."
        ),
    )
    parser.add_argument(
        "--disable-provider",
        action="append",
        default=[],
        metavar="PROVIDER",
        help=(
            "Manual kill-switch: disable a provider for this run (skips any route "
            "with this provider). Repeatable. Valid values: openai, anthropic, "
            "gemini, xai, openrouter. Per Phase D consensus this replaces the "
            "rejected app-level circuit breaker."
        ),
    )
    parser.add_argument(
        "--model-alias",
        action="append",
        default=[],
        metavar="ALIAS=MODEL_ID",
        help=(
            "Override a cell-level model alias (e.g., "
            "--model-alias SYNTH_MODEL=openrouter/anthropic/claude-opus-4.7). "
            "Value is 'provider/model'; anthropic only via openrouter/. "
            "Repeatable. Canonical cell keys: BULK_DOCS_MODEL, BULK_CODE_MODEL, "
            "CE_MODEL, SYNTH_MODEL (CE/SYNTH must stay on openai|openrouter)."
        ),
    )
    parser.add_argument(
        "--s-prompts",
        choices=sorted(context.s_prompts_modes),
        default=None,
        help="Compatibility flag retained for older invocations. Phase S now always uses legacy prompts; use phase SP for registry-backed pipeline prompts.",
    )
    parser.add_argument(
        "--s-steps",
        type=str,
        default=None,
        help="Comma-separated subset of Phase S base steps (S0-S12) to execute.",
    )
    parser.add_argument("--disable-escalation", action="store_true")
    parser.add_argument("--escalation-max-hops", type=int, default=2)
    parser.add_argument(
        "--batch-mode",
        dest="batch_mode",
        action="store_true",
        default=False,
        help="Use Batch API for LLM calls (default: False).",
    )
    parser.add_argument(
        "--no-batch",
        dest="batch_mode",
        action="store_false",
        help="Disable Batch API and use synchronous calls.",
    )
    parser.add_argument(
        "--batch-submit-only",
        action="store_true",
        help="Submit batch jobs and persist metadata without inline polling/fetch.",
    )
    parser.add_argument(
        "--batch-watch",
        action="store_true",
        help="Poll submitted batch jobs, fetch results, and emit webhook notifications.",
    )
    parser.add_argument(
        "--batch-provider",
        choices=["auto", "openai", "gemini", "xai"],
        default="auto",
    )
    parser.add_argument("--batch-poll-seconds", type=int, default=30)
    parser.add_argument(
        "--batch-wait-timeout-seconds",
        type=int,
        default=86400,
        help=(
            "Batch polling timeout in seconds. 86400 is the legacy default and can leave long-running waits behind; "
            f"{context.interactive_safe_batch_wait_seconds} is the safer interactive value."
        ),
    )
    parser.add_argument("--batch-max-requests-per-job", type=int, default=2000)
    parser.add_argument(
        "--batch-retrieve",
        action="store_true",
        help="Retrieve OpenAI batch results and integrate with webhook system.",
    )
    parser.add_argument(
        "--batch-ids",
        type=str,
        nargs="+",
        help="List of batch IDs to retrieve.",
    )
    parser.add_argument(
        "--retrieve-provider",
        choices=["openai", "gemini"],
        default="openai",
        help="Batch provider for retrieval (openai or gemini).",
    )
    parser.add_argument(
        "--gemini-transport",
        choices=["sdk", "openai_compat_http"],
        default="sdk",
    )
    parser.add_argument(
        "--openai-transport",
        choices=["openai_sdk"],
        default="openai_sdk",
    )
    parser.add_argument(
        "--xai-transport",
        choices=["openai_sdk"],
        default="openai_sdk",
    )
    # TP-RTX-V5-GROK-DOC-COMPARISON-STEP-0001: comparison lane CLI args
    parser.add_argument(
        "--compare-mode",
        choices=["additional"],
        default=None,
        help=(
            "Enable comparison lane. 'additional' runs a secondary model alongside "
            "canonical without affecting pass/fail. Disabled by default."
        ),
    )
    parser.add_argument(
        "--compare-model",
        type=str,
        default=None,
        help="Model ID to use for the comparison lane (e.g. grok-4.20-beta).",
    )
    parser.add_argument(
        "--compare-provider",
        type=str,
        default=None,
        help="Provider slug for the comparison model (e.g. xai). Inferred from registry if omitted.",
    )
    parser.add_argument(
        "--compare-steps",
        type=str,
        default=None,
        help=(
            "Comma-separated list of step IDs to run comparison on "
            "(e.g. H9,A9). Defaults to COMPARISON_ELIGIBLE_STEPS allowlist."
        ),
    )
    parser.add_argument(
        "--retry-policy", choices=["none", "default"], default="default"
    )
    parser.add_argument("--retry-max-attempts", type=int, default=4)
    parser.add_argument("--retry-base-seconds", type=float, default=2.0)
    parser.add_argument("--retry-max-seconds", type=float, default=30.0)
    parser.add_argument("--phase-auth-fail-threshold", type=int, default=5)
    parser.add_argument("--partition-workers", type=int, default=1)
    parser.add_argument(
        "--executor",
        choices=["thread", "process"],
        default="thread",
        help="Executor type: thread (default) or process",
    )
    parser.add_argument("--debug-phase-inputs", action="store_true")
    parser.add_argument("--fail-fast-missing-inputs", action="store_true")
    parser.add_argument("--run-id", type=str)
    parser.add_argument(
        "--max-cost-usd",
        type=float,
        default=None,
        help=(
            "Hard per-run live spend cap in USD. When unset, the active "
            "cost profile's default cap is auto-applied at runtime (see "
            "--cost-profile) -- this flag is the only operator-facing hint "
            "that a cap is always in effect, not just when set explicitly. "
            "Requires pricing coverage and partition_workers=1."
        ),
    )
    parser.add_argument(
        "--llm-temperature",
        type=float,
        default=0.1,
        help=(
            "Sampling temperature forwarded to provider chat/completion calls "
            "(range 0.0-2.0, default 0.1). Ignored for OpenAI gpt-5* models, "
            "which reject the temperature parameter entirely (resolve_temperature "
            "omission rule) -- TP-RTE-TRUTH-R2-003."
        ),
    )
    parser.add_argument("--no-write-latest", action="store_true")
    parser.add_argument("--write-latest-even-on-dry-run", action="store_true")
    parser.add_argument(
        "--audit-sample-rate",
        type=float,
        default=0.15,
        help="Fraction of phase outputs to audit with judge model (0 to disable).",
    )
    parser.add_argument(
        "--doctor",
        action="store_true",
        help=(
            "Write shared doctor diagnostic artifacts. These are advisory only and do not "
            "satisfy launch or certification authority."
        ),
    )
    parser.add_argument(
        "--doctor-auth",
        action="store_true",
        help=(
            "Write shared authentication doctor diagnostics. These are advisory only and do not "
            "satisfy launch or certification authority."
        ),
    )
    parser.add_argument(
        "--preflight-providers",
        action="store_true",
        help=(
            "Run provider preflight for the current invocation and write a shared diagnostic copy. "
            "Launch authority uses the run-scoped PROVIDER_PREFLIGHT.json under runs/<run_id>/."
        ),
    )
    parser.add_argument("--coverage-report", action="store_true")
    parser.add_argument("--ui", choices=["auto", "rich", "plain"], default="auto")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--status-json", action="store_true")
    parser.add_argument("--watch", type=float)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--jsonl-events", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--print-promptpack", action="store_true")
    parser.add_argument(
        "--print-routing-guide",
        action="store_true",
        help="Print routing policy intent, cost tendency, and override caveats.",
    )
    parser.add_argument(
        "--print-prescan-guide",
        action="store_true",
        help="Print prescan usage guidance, including when it helps and when it is safe to skip.",
    )
    parser.add_argument(
        "--print-cost-preview",
        action="store_true",
        help="During dry-run, emit the per-phase cost preview derived from the resolved inventory and routes.",
    )
    parser.add_argument(
        "--list-phases",
        action="store_true",
        help="Print phase code, name, purpose, dependencies, and default route summary as JSON.",
    )
    parser.add_argument("--print-run-order", action="store_true")
    parser.add_argument("--print-phase-routing", action="store_true")
    parser.add_argument("--tail-run-log", action="store_true")
    parser.add_argument("--tail-lines", type=int, default=200)
    parser.add_argument("--since", type=str, default="")
    parser.add_argument("--step", type=str)
    parser.add_argument("--d0-max-files", type=int)
    parser.add_argument("--d1-max-files", type=int)
    parser.add_argument("--show-provider-usage", action="store_true")
    parser.add_argument(
        "--print-phase-prompts",
        nargs="?",
        const="ALL",
        type=str,
        help="Print prompt files and declared outputs for PHASE or ALL.",
    )
    parser.add_argument("--verify-phase-output", choices=context.verify_phase_choices)
    parser.add_argument("--print-config", action="store_true")
    parser.add_argument("--gemini-list-models", action="store_true")
    # TP-WEBHOOKS-0002: async pilot flags
    parser.add_argument(
        "--async-provider",
        choices=["openai"],
        default=None,
        help="Submit Phase R partitions asynchronously via the given provider's API.",
    )
    parser.add_argument(
        "--finalize",
        action="store_true",
        help="Finalize Phase R by reading webhook completions from the ledger.",
    )
    promptgen_group = parser.add_argument_group("promptgen")
    promptgen_group.add_argument("--promptgen-scan", action="store_true")
    promptgen_group.add_argument(
        "--promptgen-max-files", type=int, default=context.promptgen_default_max_files
    )
    promptgen_group.add_argument(
        "--promptgen-max-bytes", type=int, default=context.promptgen_default_max_bytes
    )
    promptgen_group.add_argument(
        "--promptgen-excerpt-bytes", type=int, default=context.promptgen_default_excerpt_bytes
    )
    promptgen_group.add_argument("--promptgen-include-globs", action="append")
    promptgen_group.add_argument("--promptgen-exclude-globs", action="append")
    promptgen_group.add_argument(
        "--promptgen-output-dir", type=str, default=context.promptgen_default_output_dir
    )
    parser.add_argument(
        "--promptset-root",
        type=str,
        default=None,
        help=(
            "Override prompt root directory. Points to a generated promptset "
            "directory (from `dopemux extractor init`) or any directory containing "
            "prompt files. Equivalent to setting REPO_TRUTH_EXTRACTOR_PROMPT_ROOT."
        ),
    )
    parser.add_argument(
        "--prescan-dir",
        type=str,
        default=None,
        help="Path to prescan output dir for intelligence-informed extraction.",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        help="Extraction profile name (e.g., P09_INTEGRATION_SURFACE_V1). Filters phases and overrides budgets.",
    )
    return parser
