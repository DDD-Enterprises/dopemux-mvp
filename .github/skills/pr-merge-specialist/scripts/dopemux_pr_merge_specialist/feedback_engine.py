import re
from typing import Any, Dict, List, Optional

from .schema import FeedbackIntent, FeedbackItem, RemediationPlan


class FeedbackClassifier:
    """Classifies feedback text into deterministic intents using policy-backed rules."""

    def __init__(self):
        # Ordered by precedence: MUST_FIX > OPTIONAL
        self.rules = [
            (
                r"(?i)\b(fix|bug|error|broken|incorrect|wrong|resolve)\b",
                "MUST_FIX_CODE",
            ),
            (r"(?i)\b(test|coverage|pytest|unit test|verification)\b", "MUST_FIX_TEST"),
            (r"(?i)\b(doc|readme|document|documentation|comment)\b", "MUST_FIX_DOC"),
            (r"(?i)\b(verify|ensure|check if|validate)\b", "MUST_VERIFY"),
            (
                r"(?i)\b(overview|suggestion|review|summary|should)\b",
                "OPTIONAL_SUGGESTION",
            ),
            (r"\?", "QUESTION"),
        ]

    def classify(self, text: str) -> FeedbackIntent:
        """Classify text based on first matching rule."""
        for pattern, intent in self.rules:
            if re.search(pattern, text):
                return intent
        return "HUMAN_DECISION_REQUIRED"


class FeedbackIntake:
    """Ingests and normalizes all PR feedback surfaces into a unified schema."""

    def __init__(self, classifier: FeedbackClassifier):
        self.classifier = classifier

    def normalize(self, pr_node: Dict[str, Any]) -> List[FeedbackItem]:
        items = []

        # 1. PR Body
        if pr_node.get("body"):
            items.append(
                FeedbackItem(
                    id="PR_BODY",
                    author=pr_node["author"]["login"],
                    text=pr_node["body"],
                    source_type="BODY",
                    intent="HUMAN_DECISION_REQUIRED",  # Body is context, not usually a single "fix"
                )
            )

        # 2. Issue Comments
        for c in pr_node.get("comments", {}).get("nodes", []):
            items.append(
                FeedbackItem(
                    id=c["id"],
                    author=c["author"]["login"],
                    text=c["body"],
                    source_type="PR_COMMENT",
                    intent=self.classifier.classify(c["body"]),
                    timestamp=c["createdAt"],
                )
            )

        # 3. Reviews (Summaries)
        for r in pr_node.get("reviews", {}).get("nodes", []):
            if r["body"].strip():
                items.append(
                    FeedbackItem(
                        id=r["id"],
                        author=r["author"]["login"],
                        text=r["body"],
                        source_type="PR_COMMENT",
                        intent=self.classifier.classify(r["body"]),
                        timestamp=r["createdAt"],
                    )
                )

        # 4. Review Threads (Inline)
        for t in pr_node.get("reviewThreads", {}).get("nodes", []):
            # We take the root comment context + all replies
            thread_comments = t.get("comments", {}).get("nodes", [])
            if not thread_comments:
                continue

            root = thread_comments[0]
            # Combined text for classification context
            combined_text = "\n".join([c["body"] for c in thread_comments])

            items.append(
                FeedbackItem(
                    id=root["id"],
                    author=root["author"]["login"],
                    text=combined_text,
                    source_type="THREAD",
                    intent=self.classifier.classify(combined_text),
                    file=root.get("path"),
                    line=root.get("line"),
                    timestamp=root["createdAt"],
                    is_resolved=t["isResolved"],
                    is_outdated=t["isOutdated"],
                    thread_id=t["id"],
                )
            )

        return items


class RemediationPlanner:
    """Builds a deterministic action plan from classified feedback items."""

    def plan(self, items: List[FeedbackItem]) -> RemediationPlan:
        plan = {
            "code_changes": [],
            "test_work": [],
            "docs_changes": [],
            "metadata_hygiene": [],
            "thread_replies": [],
            "escalations": [],
        }

        for item in items:
            if item.is_resolved or item.is_outdated:
                continue  # Skip non-actionable

            intent = item.intent
            if intent == "MUST_FIX_CODE":
                plan["code_changes"].append(item)
            elif intent == "MUST_FIX_TEST":
                plan["test_work"].append(item)
            elif intent == "MUST_FIX_DOC":
                plan["docs_changes"].append(item)
            elif intent in ["QUESTION", "MUST_VERIFY"]:
                plan["thread_replies"].append(item)
            elif intent == "HUMAN_DECISION_REQUIRED":
                plan["escalations"].append(item)
            elif intent == "CONFLICTING_FEEDBACK":
                plan["escalations"].append(item)
            # OPTIONAL_SUGGESTION is logged but not explicitly put in "must-fix" groups for now

        return RemediationPlan(
            code_changes=plan["code_changes"],
            test_work=plan["test_work"],
            docs_changes=plan["docs_changes"],
            metadata_hygiene=plan["metadata_hygiene"],
            thread_replies=plan["thread_replies"],
            escalations=plan["escalations"],
        )
