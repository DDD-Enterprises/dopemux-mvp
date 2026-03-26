import json
from typing import Any, Dict, List, Optional

from .arbitration_runtime import ArbitrationLLMClient
from .schema import FeedbackItem, PRMergeReport


class SuggestionImplementer:
    """Synthesizes code changes from review suggestions using LLM arbitration."""

    def __init__(self, client: Optional[ArbitrationLLMClient] = None):
        self.client = client or ArbitrationLLMClient(mode="MOCK")

    def synthesize_patch(
        self, item: FeedbackItem, context_files: List[str]
    ) -> Dict[str, Any]:
        """Generate a patch plan for a specific feedback item."""
        prompt = f"""
        Role: Senior Software Engineer
        Task: Implement a review suggestion.

        Feedback from {item.author}:
        "{item.text}"

        File: {item.file}
        Line: {item.line}

        Target Files for Context: {', '.join(context_files)}

        Requirements:
        1. Provide a minimal, surgical code change to address the feedback.
        2. Identify the exact code block to be replaced (search) and the new version (replace).
        3. Output in JSON format:
           {
             "explanation": "why this change addresses the feedback",
             "file": "path/to/file",
             "search": "the exact existing code block to find",
             "replace": "the new code block to insert",
             "confidence": "HIGH|MEDIUM|LOW"
           }
        """

        response = self.client.call_role("analyzer", prompt)

        try:
            data = json.loads(response)
            # Support both old 'patch' and new 'search/replace' for compatibility during transition
            if "patch" in data and "replace" not in data:
                data["replace"] = data["patch"]
                data["search"] = None  # Fallback to append/manual
            return data
        except Exception:
            return {
                "explanation": f"Synthesized fix for feedback from {item.author}",
                "file": item.file or "UNKNOWN",
                "search": None,
                "replace": "# No patch synthesized (Schema failure)",
                "confidence": "LOW",
            }

    def plan_all_suggestions(self, report: PRMergeReport) -> List[Dict[str, Any]]:
        """Process all unresolved feedback items to find actionable patches."""
        patches = []
        if not report.feedback_items:
            return []

        for item in report.feedback_items:
            if item.is_resolved or item.is_outdated or item.id == "PR_BODY":
                continue

            # Attempt synthesis for ANY unresolved comment
            target_files = [item.file] if item.file else []
            patch = self.synthesize_patch(item, target_files)
            patch["source_item_id"] = item.id
            replacement = patch.get("replace") or patch.get("patch") or ""

            # Present to user if the model was able to identify a file and patch
            if (
                patch.get("file")
                and patch["file"] != "UNKNOWN"
                and isinstance(replacement, str)
                and "No patch synthesized" not in replacement
            ):
                patches.append(patch)

        return patches
