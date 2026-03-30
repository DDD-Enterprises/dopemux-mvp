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
    "remote_check_repro",

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
                "command": ["pre-commit", "run"],
                "scope": "changed_files",
                "run_in_dry_run": False,
            },
            {
                "name": "docs-frontmatter-fix",
                "command": ["python", "scripts/docs_frontmatter_guard.py", "--fix"],
                "scope": "docs_frontmatter_files",
                "run_in_dry_run": False,
            },
            {
                "name": "docs-hygiene",
                "command": [
                    "python",
                    "scripts/check_docs_hygiene.py",
                    "--check",
                ],
                "scope": "docs_validator_files",
                "run_in_dry_run": False,
            },
            {
                "name": "docs-filename-hygiene",
                "command": [
                    "python",
                    "scripts/check_docs_filename_hygiene.py",
                    "--check",
                ],
                "scope": "docs_validator_files",
                "run_in_dry_run": False,
            },
            {
                "name": "root-hygiene",
                "command": ["python", "scripts/check_root_hygiene.py"],
                "run_in_dry_run": False,
            },
        ],
    },
    "remote_check_repro": {
        "steps": [
            {
                "check_name": "🧪 Unit Tests",
                "command": [
                    "pytest",
                    "tests/",
                    "--maxfail=1",
                    "--disable-warnings",
                    "--cov=src/dopemux",
                    "--cov-report=term-missing",
                    "--cov-report=xml:coverage.xml",
                    "--cov-report=html:htmlcov",
                ],
                "scope": "repo",
            }
        ],
    },
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
        scope = step.get("scope", "repo")
        if not isinstance(scope, str) or scope not in VALID_VALIDATION_SCOPES:
            raise PolicyError(
                f"{section}.steps[{index}] has invalid scope {scope!r}; "
                f"expected one of {sorted(VALID_VALIDATION_SCOPES)}."
            )
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
