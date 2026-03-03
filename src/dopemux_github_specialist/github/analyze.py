from __future__ import annotations

from typing import List

from ..schema import ProposedAction


def apply_safety_rules(actions: List[ProposedAction]) -> List[ProposedAction]:
    """
    Conservative defaults:
    - Nothing is safe_to_execute unless it is purely formatting or metadata suggestion.
    - comment_pr is NOT safe by default.
    - suggest_labels is NOT safe by default (wrong labels are annoying and hard to unwind).
    """
    out: List[ProposedAction] = []
    for a in actions:
        out.append(
            ProposedAction(
                kind=a.kind,
                title=a.title,
                body_md=a.body_md,
                suggestions=a.suggestions,
                safe_to_execute=False,
                evidence=a.evidence,
            )
        )
    return out
