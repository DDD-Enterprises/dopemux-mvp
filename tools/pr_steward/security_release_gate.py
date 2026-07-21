"""Security/release-sensitive path classifier for the live PR Steward path.

This module answers one question: does a PR's changed-file set touch a path
category that requires an explicit security/release approval before READY?

It is deliberately distinct from ``dopemux.dcp.red_lane_scanner`` /
``red_lane_rules.FORBIDDEN_PATHS``, which encode "DCP Core must never touch
this" (a hard block for DCP Core specifically, not a general PR-approval
signal). ``FORBIDDEN_PATHS`` is reused here, read-only, as one input
category (``dcp_boundary``) alongside PR-Steward-local categories for
surfaces DCP Core's list doesn't cover (CODEOWNERS, schema/contract files,
secrets-like paths). Matching a category here means "needs approval", not
"forbidden outright" — editing ``.github/workflows/pr-steward.yml`` (this
packet's own scope) correctly triggers ``ci_workflow``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from dopemux.dcp.red_lane_rules import FORBIDDEN_PATHS

_CI_WORKFLOW = re.compile(r"^\.github/workflows/.*$")
_CI_ACTION = re.compile(r"^\.github/actions/.*$")
_CODEOWNERS = re.compile(r"^(\.github/)?CODEOWNERS$")
# DCP-RED-PROOF-CONTRACT-SCHEMA-MUTATION (schemas/dcp/dcp_red_lane_taxonomy.instance.json)
_SCHEMA_CONTRACT = re.compile(r"^(schemas|contracts)/.*\.(schema\.json|json|proto|graphql)$")
_SECRETS_LIKE = re.compile(
    r"(^|/)secrets?(/|$)|\.env(\.|$)", re.IGNORECASE
)
# This gate's own implementation and config are a trust root: anything here
# controls who can approve future security/release-sensitive changes,
# including changes to this very list. It must protect itself.
_PR_STEWARD_TRUST_ROOT = re.compile(r"^tools/pr_steward/.*$")

_LOCAL_CATEGORY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ci_workflow", _CI_WORKFLOW),
    ("ci_workflow", _CI_ACTION),
    ("codeowners", _CODEOWNERS),
    ("schema_contract", _SCHEMA_CONTRACT),
    ("secrets", _SECRETS_LIKE),
    ("pr_steward_trust_root", _PR_STEWARD_TRUST_ROOT),
)


@dataclass(frozen=True)
class SecurityReleaseClassification:
    """Result of classifying a PR's changed files for security/release sensitivity."""

    required: bool
    categories: tuple[str, ...] = field(default_factory=tuple)
    matched_paths: tuple[tuple[str, str], ...] = field(default_factory=tuple)


def classify_security_release_paths(
    changed_files: list[str],
) -> SecurityReleaseClassification:
    """Classify *changed_files* into security/release-sensitive categories.

    Pure function: no I/O, no filesystem access, no mutation of input.
    """
    matches: list[tuple[str, str]] = []
    for path in changed_files:
        local_match = False
        for category, pattern in _LOCAL_CATEGORY_PATTERNS:
            if pattern.search(path):
                matches.append((path, category))
                local_match = True
        # Only check FORBIDDEN_PATHS if no local pattern matched
        if not local_match:
            for forbidden in FORBIDDEN_PATHS:
                if forbidden.match(path):
                    matches.append((path, "dcp_boundary"))
                    break

    categories = tuple(sorted({category for _, category in matches}))
    return SecurityReleaseClassification(
        required=bool(matches),
        categories=categories,
        matched_paths=tuple(matches),
    )
