import json
import re
from typing import Any, Dict, List, Optional

from .schema import (
    ChecklistItem,
    PRMetadataUpdate,
    VerificationRequest,
    VerificationResult,
)


class BodyParser:
    """Parses GFM checklists and metadata from PR body text."""

    def parse_checklists(self, body: str) -> List[ChecklistItem]:
        items = []
        # Match GFM checklists: - [ ] text or - [x] text
        matches = re.finditer(r"^\s*[-*]\s+\[([ xX])\]\s+(.+)$", body, re.MULTILINE)
        for i, m in enumerate(matches):
            state = m.group(1).lower() == "x"
            text = m.group(2).strip()

            # Simple heuristic for intent link
            intent_link = None
            if "pytest" in text.lower() or "test" in text.lower():
                intent_link = "pytest"
            elif "lint" in text.lower():
                intent_link = "lint"
            elif "typecheck" in text.lower() or "mypy" in text.lower():
                intent_link = "typecheck"

            items.append(
                ChecklistItem(
                    id=f"CHECK_{i}",
                    text=text,
                    is_checked=state,
                    intent_link=intent_link,
                )
            )
        return items


class BodyEnforcer:
    """Generates updated body text with evidence and checked items."""

    def enforce(
        self,
        body: str,
        checklists: List[ChecklistItem],
        results: List[VerificationResult],
    ) -> str:
        new_body = body

        # 1. Update Checkboxes based on results
        for item in checklists:
            if not item.is_checked and item.intent_link:
                # Check if we have a passing result for this intent
                # Note: This is simplified; real mapping would use the intent_link
                passing = any(
                    r.exit_code == 0
                    for r in results
                    if item.intent_link in r.command.lower()
                )
                if passing:
                    # Precise replace of the specific line
                    old_line = f"[{' '}] {item.text}"
                    new_line = f"[x] {item.text}"
                    new_body = new_body.replace(old_line, new_line)

        # 2. Append Evidence Block (Idempotent)
        if results and "<!-- dopemux:evidence -->" not in new_body:
            evidence_md = "\n\n---\n### 🔬 Verification Evidence (Auto-generated)\n"
            for r in results:
                status = "✅" if r.exit_code == 0 else "❌"
                evidence_md += f"- {status} `{r.command}` (Exit {r.exit_code})\n"
            evidence_md += "<!-- dopemux:evidence -->\n"
            new_body += evidence_md

        return new_body


class MetadataCleaner:
    """Applies hygiene rules to PR titles and descriptions."""

    def __init__(self):
        self.rules = [
            (r"(?i)^wip:\s*", ""),  # Remove WIP:
            (r"(?i)^draft:\s*", ""),  # Remove Draft:
            (r"\s*\[wip\]\s*", ""),  # Remove [WIP]
        ]

    def clean(self, title: str, body: str) -> PRMetadataUpdate:
        new_title = title
        hygiene_applied = []

        # 1. Clean Title
        for pattern, replacement in self.rules:
            if re.search(pattern, new_title):
                new_title = re.sub(pattern, replacement, new_title).strip()
                hygiene_applied.append(f"Removed prefix matching {pattern}")

        # 2. Ensure Conventional Title (simplified)
        if ":" not in new_title:
            # If no type, we might prepend a generic one if we were being aggressive
            # For now, let's just note it
            pass

        return PRMetadataUpdate(
            old_title=title,
            new_title=new_title,
            old_body=body,
            new_body=body,  # Body cleaning separate from enforcement
            hygiene_applied=hygiene_applied,
        )
