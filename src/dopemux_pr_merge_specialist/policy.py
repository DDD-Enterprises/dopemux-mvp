from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple

import yaml

from .runtime import fingerprint_payload
from .schema import ARTIFACT_VERSION, POLICY_SCHEMA_VERSION, TOOL_VERSION


class PolicyError(RuntimeError):
    """Raised when the effective policy cannot be loaded safely."""


BUNDLED_POLICY_PATH = Path(__file__).resolve().parent / "config" / "policy.example.yaml"
REPO_POLICY_CANDIDATES = (
    Path("config/pr_merge_specialist/policy.yaml"),
    Path("config/pr_merge_specialist/policy.yml"),
)
SUPPORTED_PLATFORMS = {"darwin", "linux"}
REQUIRED_TOP_LEVEL_KEYS = (
    "version",
    "platform",
    "timeouts",
    "validation",
    "gates",
    "thread_rules",
    "check_rules",
    "conflict_rules",
    "safety",
    "retry",
    "merge",
)

DEFAULT_POLICY: Dict[str, Any] = {
    "version": POLICY_SCHEMA_VERSION,
    "platform": {
        "supported": ["darwin", "linux"],
        "unsupported": ["windows"],
        "shell": "posix",
    },
    "timeouts": {
        "subprocess_seconds": 600,
        "gh_seconds": 120,
        "phase_seconds": 1800,
    },
    "validation": {
        "require_local_validation_for_merge_ready": True,
        "steps": [
            {
                "name": "pre-commit",
                "command": ["pre-commit", "run", "--all-files"],
                "run_in_dry_run": False,
            },
            {
                "name": "docs-frontmatter-fix",
                "command": ["python", "scripts/docs_frontmatter_guard.py", "--fix"],
                "run_in_dry_run": False,
            },
            {
                "name": "docs-validator",
                "command": ["python", "scripts/docs_validator.py"],
                "run_in_dry_run": False,
            },
            {
                "name": "docs-hygiene",
                "command": [
                    "python",
                    "scripts/check_docs_hygiene.py",
                    "--check",
                    "--all-files",
                ],
                "run_in_dry_run": False,
            },
            {
                "name": "docs-filename-hygiene",
                "command": [
                    "python",
                    "scripts/check_docs_filename_hygiene.py",
                    "--check",
                    "--all-files",
                ],
                "run_in_dry_run": False,
            },
            {
                "name": "root-hygiene",
                "command": ["python", "scripts/check_root_hygiene.py"],
                "run_in_dry_run": False,
            },
        ],
    },
    "gates": {
        "require_clean_worktree": True,
        "allow_dirty_override": True,
        "block_on_active_threads": True,
        "block_on_pending_required_checks": True,
        "block_on_missing_approvals": True,
        "block_on_changes_requested": True,
    },
    "thread_rules": {
        "auto_resolve_outdated": True,
        "auto_resolve_resolution_signals": True,
        "resolution_markers": [
            "addressed",
            "fixed",
            "resolved",
            "acknowledged",
            "done in latest push",
            "updated in latest push",
            "landed in latest push",
        ],
        "objection_markers": [
            "not fixed",
            "still",
            "needs changes",
            "please address",
            "didn't",
            "fails",
            "not resolved",
        ],
        "implementable_patterns": [
            "```suggestion",
            "change <code>",
            "delete <code>",
            "remove <code>",
            "conflict marker",
            "<<<<<<< head",
        ],
    },
    "check_rules": {
        "wait_for_healthy_pending": True,
        "wait_seconds": 900,
        "poll_seconds": 30,
        "fail_closed_on_incomplete_data": True,
    },
    "conflict_rules": {
        "strict": True,
        "scan_changed_files_for_markers": True,
        "allow_blanket_strategies": False,
        "canonical_head_markers": [
            "keep the current main version",
            "keep the current version",
            "keep the deterministic head side",
            "keep the wrapper implementation already in head",
        ],
        "auto_recovery": {
            "require_opt_in_label": True,
            "opt_in_labels": ["conflict:mechanical"],
            "blocked_labels": ["conflict:semantic"],
            "max_conflict_files": 5,
            "prefer_side": "theirs",
            "safe_path_prefixes": ["docs/", "tests/"],
            "safe_filenames": [
                "package.json",
                "package-lock.json",
                "yarn.lock",
                "pnpm-lock.yaml",
                "poetry.lock",
                "uv.lock",
                "requirements.txt",
                "requirements-dev.txt",
                "requirements-test.txt",
            ],
        },
    },
    "safety": {
        "negative_allowlist": [
            "migrations",
            "auth",
            "permissions",
            "deploy",
            "infra",
            "schema",
            "contract",
            "secrets",
            "destructive",
        ]
    },
    "retry": {
        "max_attempts": 3,
        "backoff_seconds": 2,
        "max_backoff_seconds": 10,
        "retryable_gh_errors": [
            "rate limit",
            "502",
            "503",
            "504",
            "connection reset",
            "timeout",
            "temporary failure",
        ],
    },
    "merge": {
        "allow_auto_fallback_only_for": [
            "merge_queue_required",
        ],
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_yaml(path: Path) -> Dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise PolicyError(f"Invalid YAML in policy {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PolicyError(f"Policy {path} must be a mapping at the top level.")
    return payload


def discover_policy_path(
    repo_root: Path, explicit_path: Optional[str] = None
) -> Tuple[Path, str]:
    if explicit_path:
        path = Path(explicit_path)
        if not path.is_absolute():
            path = repo_root / path
        return path.resolve(), "explicit"
    for candidate in REPO_POLICY_CANDIDATES:
        path = repo_root / candidate
        if path.exists():
            return path.resolve(), "repo"
    return BUNDLED_POLICY_PATH.resolve(), "bundled"


def _validate_command_steps(steps: Iterable[Dict[str, Any]], *, section: str) -> None:
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            raise PolicyError(f"{section}.steps[{index}] must be a mapping.")
        if not step.get("name"):
            raise PolicyError(f"{section}.steps[{index}] is missing 'name'.")
        command = step.get("command")
        if (
            not isinstance(command, list)
            or not command
            or not all(isinstance(x, str) and x for x in command)
        ):
            raise PolicyError(
                f"{section}.steps[{index}] must define a non-empty string command list."
            )


def validate_policy(policy: Dict[str, Any]) -> None:
    missing = [key for key in REQUIRED_TOP_LEVEL_KEYS if key not in policy]
    if missing:
        raise PolicyError(
            f"Policy is missing required top-level keys: {', '.join(missing)}"
        )
    version = policy.get("version")
    if version != POLICY_SCHEMA_VERSION:
        raise PolicyError(
            f"Unsupported policy schema version {version!r}; expected {POLICY_SCHEMA_VERSION}."
        )
    platform = policy.get("platform")
    if not isinstance(platform, dict):
        raise PolicyError("platform must be a mapping.")
    supported = platform.get("supported")
    if not isinstance(supported, list) or not supported:
        raise PolicyError("platform.supported must be a non-empty list.")
    validation = policy.get("validation")
    if not isinstance(validation, dict):
        raise PolicyError("validation must be a mapping.")
    _validate_command_steps(validation.get("steps", []), section="validation")
    for section_name in (
        "gates",
        "thread_rules",
        "check_rules",
        "conflict_rules",
        "safety",
        "retry",
        "merge",
    ):
        if not isinstance(policy.get(section_name), dict):
            raise PolicyError(f"{section_name} must be a mapping.")
    negative_allowlist = policy["safety"].get("negative_allowlist")
    if not isinstance(negative_allowlist, list):
        raise PolicyError("safety.negative_allowlist must be a list.")


def load_effective_policy(
    repo_root: Path,
    *,
    explicit_path: Optional[str] = None,
) -> Dict[str, Any]:
    policy_path, source = discover_policy_path(repo_root, explicit_path)
    if not policy_path.exists():
        raise PolicyError(f"Policy file does not exist: {policy_path}")
    loaded = _load_yaml(policy_path)
    effective = _deep_merge(DEFAULT_POLICY, loaded)
    validate_policy(effective)
    effective["_meta"] = {
        "source": source,
        "path": str(policy_path),
        "fingerprint": fingerprint_payload(effective),
    }
    return effective


def policy_artifact_payload(policy: Dict[str, Any]) -> Dict[str, Any]:
    meta = dict(policy.get("_meta", {}))
    payload = deepcopy(policy)
    payload.pop("_meta", None)
    payload.update(
        {
            "artifact_version": ARTIFACT_VERSION,
            "policy_schema_version": POLICY_SCHEMA_VERSION,
            "tool_version": TOOL_VERSION,
            "policy_source": meta.get("source", "unknown"),
            "policy_path": meta.get("path", ""),
            "policy_fingerprint": meta.get("fingerprint", fingerprint_payload(payload)),
        }
    )
    return payload


def policy_fingerprint(policy: Dict[str, Any]) -> str:
    meta = policy.get("_meta", {})
    return str(meta.get("fingerprint", fingerprint_payload(policy)))
