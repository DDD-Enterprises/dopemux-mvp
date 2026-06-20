import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schema import ChecklistItem, FeedbackItem, PRMetadataUpdate, VerificationResult


class PRBodyEnforcer:
    """Parses and enforces PR body structure, checklists, and evidence."""

    def __init__(self, policy: Optional[Dict[str, Any]] = None):
        self.required_sections = policy or [
            "summary",
            "verification",
            "risks",
            "rollback",
        ]

    def parse_structure(self, body: str) -> Dict[str, Any]:
        """Detect sections and task lists."""
        sections = {}
        # Simple heading detection
        current_section = "intro"
        lines = body.split("\n")

        for line in lines:
            heading_match = re.match(r"^#+\s+(.+)$", line)
            if heading_match:
                current_section = heading_match.group(1).lower()
                sections[current_section] = []
            else:
                if current_section not in sections:
                    sections[current_section] = []
                sections[current_section].append(line)

        return {
            "sections": {k: "\n".join(v).strip() for k, v in sections.items()},
            "gaps": [
                s
                for s in self.required_sections
                if not any(s in k for k in sections.keys())
            ],
        }

    def plan_mutations(
        self,
        body: str,
        checklists: List[ChecklistItem],
        results: List[VerificationResult],
        remediation_items: List[FeedbackItem],
    ) -> Dict[str, Any]:
        """Build a deterministic mutation plan for the PR body."""
        structure = self.parse_structure(body)
        actions = []
        new_body = body

        # 1. Section Gaps
        for gap in structure["gaps"]:
            actions.append(
                {
                    "type": "INSERT_SECTION",
                    "target": gap,
                    "reason": "Required section missing",
                }
            )
            # Active injection: append the missing section with a spacer
            heading = (
                f"\n\n# 🚀 {gap.capitalize()}"
                if gap == "summary"
                else f"\n\n--- \n\n# 🧪 {gap.capitalize()}"
            )
            if gap == "risks":
                heading = f"\n\n--- \n\n# ⚠️ {gap.capitalize()}"
            if gap == "rollback":
                heading = f"\n\n--- \n\n# ↩️ {gap.capitalize()}"

            new_body += f"{heading}\n- [ ] Pending detail..."

        # 2. Checklist Updates (Evidence-backed)
        for item in checklists:
            if not item.is_checked and item.intent_link:
                # Evidence rule: does a passing verification result exist?
                passing = any(
                    r.exit_code == 0
                    for r in results
                    if item.intent_link in r.command.lower()
                )
                if passing:
                    actions.append(
                        {
                            "type": "CHECK_ITEM",
                            "target": item.text,
                            "evidence": "Verification passed",
                            "prior_state": "unchecked",
                        }
                    )
                    old_line = f"[{' '}] {item.text}"
                    new_line = f"[x] {item.text}"
                    new_body = new_body.replace(old_line, new_line)

        # 3. Stale Detection (Optional enhancement)

        return {
            "prior_body": body,
            "new_body": new_body,
            "actions": actions,
            "gaps": structure["gaps"],
            "is_mutated": new_body != body,
        }

    def emit_report(self, plan: Dict[str, Any], out_dir: Path):
        """Emit auditable enforcement artifacts."""
        (out_dir / "PR_BODY_MUTATION_PLAN.json").write_text(json.dumps(plan, indent=2))
        (out_dir / "PR_SECTION_GAPS.json").write_text(
            json.dumps(plan["gaps"], indent=2)
        )

        summary = {
            "mutations_planned": len(plan["actions"]),
            "sections_missing": len(plan["gaps"]),
            "status": "ADVISORY",
        }
        (out_dir / "PR_BODY_ENFORCEMENT_SUMMARY.json").write_text(
            json.dumps(summary, indent=2)
        )
