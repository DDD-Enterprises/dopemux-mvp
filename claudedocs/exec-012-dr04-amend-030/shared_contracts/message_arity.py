"""W01 common A/D agent_message arity reconciliation (operator amendment 030).

Route A and Route D both import THIS one module by absolute path -- the same
mechanism W01/profile_argv.py uses for the isolation argv -- so the arity rule
is identical by construction rather than asserted by inspection.

Why this module exists: on 2026-09-10 Route D stopped at turn 3 with
CODEX_COMPLETION_AMBIGUOUS because the turn produced TWO agent_message items,
a natural-language preface followed by a valid schema-conforming object. Both
harnesses assumed exactly one agent_message per turn. That assumption, not the
model and not the tool-isolation contract, is what failed.

Contract and rejected alternatives: W01_ARITY_RECONCILIATION_CONTRACT.json
"""


class Ambiguous(Exception):
    """Neutral failure signal. Each route CATCHES this and re-raises its OWN
    original error code, so this amendment does not change either route's
    failure taxonomy. Route exception classes are deliberately NOT imported
    here -- W01 stays dependency-free and shared."""


def reconcile(texts, accepts=None):
    """Reconcile one turn's agent_message items against the output contract
    in force for that call.

    texts   -- the agent_message texts, in stream order.
    accepts -- callable(str) -> bool deciding whether a single text satisfies
               the output contract in force, or None when NO output contract
               is in force (free-form text).

    Returns (selected, agent_message_count, narration_preface_count).

    Output contract in force:
        Exactly one text must satisfy `accepts`. That text is the output; the
        others are narration and are discarded (but remain in the preserved
        raw event stream). Zero, or two or more, raises Ambiguous -- the same
        genuinely-ambiguous condition the routes rejected before.

    No output contract in force:
        The output is every non-empty text joined in stream order by a blank
        line. This is LOSSLESS; nothing is discarded, so
        narration_preface_count is 0 and agent_message_count reports how many
        items were merged. See the contract file for why JOIN is chosen over
        taking the LAST message.
    """
    kept = [t for t in texts if isinstance(t, str) and t.strip()]
    if not kept:
        raise Ambiguous('NO_NONEMPTY_AGENT_MESSAGE')
    if accepts is None:
        return '\n\n'.join(kept), len(kept), 0
    conforming = []
    for text in kept:
        try:
            satisfied = bool(accepts(text))
        except Exception:
            satisfied = False
        if satisfied:
            conforming.append(text)
    if len(conforming) != 1:
        raise Ambiguous('CONFORMING_MESSAGE_COUNT_%d' % len(conforming))
    return conforming[0], len(kept), len(kept) - 1
