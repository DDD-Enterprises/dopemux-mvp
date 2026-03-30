import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schema import PRMetadataUpdate


class MetadataHygieneEngine:
    """Lints and suggests improvements for PR titles and commit messages."""

    def __init__(self):
        self.title_rules = [
            (r"(?i)^wip:", "error", "Remove WIP prefix before merging."),
            (r"(?i)^draft:", "error", "Remove Draft prefix before merging."),
            (
                r"^[^:]+$",
                "warning",
                "Conventional title recommended (e.g., feat: ... or fix: ...).",
            ),
        ]
        self.commit_rules = [
            (
                r"^.{1,50}$",
                "warning",
                "Commit subject should be descriptive and concise.",
            ),
            (r"\n\n", "suggestion", "Add a commit body for complex changes."),
        ]

    def lint_metadata(
        self, title: str, body: str, commits: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Classify metadata issues by severity and fixability."""
        issues = []

        # 1. PR Title
        for pattern, severity, reason in self.title_rules:
            if re.search(pattern, title):
                issues.append(
                    {
                        "target": "PR_TITLE",
                        "pattern": pattern,
                        "severity": severity,
                        "reason": reason,
                        "fixable": severity == "error",
                    }
                )

        # 2. PR Description (Body)
        if len(body.strip()) < 20:
            issues.append(
                {
                    "target": "PR_BODY",
                    "severity": "warning",
                    "reason": "PR description is too short. Provide more context.",
                    "fixable": False,
                }
            )

        return {
            "title": title,
            "issues": issues,
            "summary": {
                "errors": len([i for i in issues if i["severity"] == "error"]),
                "warnings": len([i for i in issues if i["severity"] == "warning"]),
            },
        }

    def emit_report(self, lint_results: Dict[str, Any], out_dir: Path):
        """Emit metadata hygiene artifacts."""
        (out_dir / "PR_METADATA_REPORT.json").write_text(
            json.dumps(lint_results, indent=2)
        )

        fix_actions = [i for i in lint_results["issues"] if i["fixable"]]
        (out_dir / "METADATA_FIX_ACTIONS.json").write_text(
            json.dumps(fix_actions, indent=2)
        )
