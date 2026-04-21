from __future__ import annotations

from dopemux_pr_merge_specialist.schema import (
    ReviewThread,
    ThreadComment,
)
from dopemux_pr_merge_specialist.thread_resolution import decide_thread_disposition


def _policy() -> dict:
    return {
        "thread_rules": {
            "enable_agentic_fix": True,
            "auto_resolve_outdated": True,
            "auto_resolve_resolution_signals": True,
            "resolution_markers": ["addressed", "acknowledged"],
            "objection_markers": ["not fixed", "still"],
            "implementable_patterns": ["```suggestion", "change <code>", "conflict marker", "<<<<<<< head"],
        },
        "conflict_rules": {
            "strict": True,
        },
        "timeouts": {"subprocess_seconds": 5, "gh_seconds": 5},
    }


def _thread(*, body: str, author: str = "human-dev") -> ReviewThread:
    return ReviewThread(
        id="T1",
        is_resolved=False,
        is_outdated=False,
        viewer_can_resolve=True,
        path="src/example.py",
        comments=[
            ThreadComment(
                id="C1",
                author=author,
                body=body,
                created_at="2026-03-12T00:00:00Z",
            )
        ],
    )


def test_agentic_fix_disposition_for_complex_comment():
    thread = _thread(body="Please refactor this method to use a more efficient algorithm.")
    disposition = decide_thread_disposition(thread, validation_green=True, policy=_policy())
    assert disposition.disposition == "agentic_fix"
    assert "human feedback actionable by AI" in disposition.reason


def test_implement_still_takes_precedence_over_agentic_fix():
    thread = _thread(body="```suggestion\nprint('hello')\n```")
    disposition = decide_thread_disposition(thread, validation_green=True, policy=_policy())
    assert disposition.disposition == "implement"


def test_bot_comments_are_not_agentic_fix():
    # github-code-quality is in BOT_AUTHORS
    thread = _thread(body="Complexity is too high.", author="github-code-quality")
    disposition = decide_thread_disposition(thread, validation_green=True, policy=_policy())
    # Should fall through to decline_with_rationale or something else, but not agentic_fix
    assert disposition.disposition == "decline_with_rationale"


def test_short_comments_are_not_agentic_fix():
    thread = _thread(body="Fixed?")
    disposition = decide_thread_disposition(thread, validation_green=True, policy=_policy())
    assert disposition.disposition == "decline_with_rationale"


def test_agentic_fix_requires_explicit_policy_opt_in():
    thread = _thread(body="Please refactor this method to use a more efficient algorithm.")
    policy = _policy()
    policy["thread_rules"]["enable_agentic_fix"] = False
    disposition = decide_thread_disposition(thread, validation_green=True, policy=policy)
    assert disposition.disposition == "decline_with_rationale"
