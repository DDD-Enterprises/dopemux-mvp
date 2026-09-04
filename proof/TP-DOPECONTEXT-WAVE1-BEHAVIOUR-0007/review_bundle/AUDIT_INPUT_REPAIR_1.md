# Independent embedded audit — PR #1318, ROUND 2 (delta)

Repository mounted read-only at: `/Users/hue/code/dopemux-mvp/.worktrees/dope-context-wave-reconciliation-001`. Verify against the files; do not trust this prompt.

## What round 1 established

Round 1 audited head `1f6af050aca60a21c10c280756f22358fc3596ec` and returned **PASS with zero
findings**, verifying nine claims (C1–C9) and correctly returning the record's finding R-6 as
NOT_VERIFIABLE because it concerns a checkout outside the mounted worktree. Round 1's full record
is in `proof/TP-DOPECONTEXT-WAVE1-BEHAVIOUR-0007/AUDITOR_REPORT.md` and
`.../review_bundle/AGY_AUDIT.md`.

## What changed since

One commit, `fecb5f3a35ec9b28cf849c2f8e29a5fcdb09f19a`, responding to four Copilot review threads
that all made the same point: bare `index_profile.py:<line>` citations should carry the repo-root
path. The complete diff is in `proof/TP-DOPECONTEXT-WAVE1-BEHAVIOUR-0007/review_bundle/REPAIR_1_DIFF.patch`
and you can also reproduce it with `git -C "/Users/hue/code/dopemux-mvp/.worktrees/dope-context-wave-reconciliation-001" diff 1f6af050a..fecb5f3a3 -- claudedocs/ docs/ task-packets/`.

The author's claim is that this change is **presentation only**: ten bare citations expanded to
`services/dope-context/src/index_profile.py:<line>`, plus line re-wrapping, with no claim, line
number, ruling, scope decision or regex altered.

The author also asserts, contradicting Copilot's stated premise, that the repository contains
**exactly one** `index_profile.py`. Check that.

## What to audit

**D1.** Is the diff genuinely presentation-only? Specifically: does any assertion, cited line
number, verdict, file list, scope ruling, count, or regex differ between the two heads other than
by the path prefix and line wrapping? Any semantic change is a finding.

**D2.** Are the expanded paths **correct**? For each expanded citation, confirm that
`services/dope-context/src/index_profile.py` at the cited line actually contains what the
surrounding prose says it does — specifically `CODE_CHUNKER_VERSION` at :35, `DOCS_CHUNKER_VERSION`
at :36, and `VectorProfile.fingerprint_payload()` spanning :77-89. A citation made *more* precise
while being *wrong* is worse than the ambiguous original.

**D3.** Were any bare `index_profile.py:` citations missed? The author claims all ten were fixed,
not only the four Copilot flagged. Verify none remain in the three documents.

**D4.** Is the repo-has-exactly-one-`index_profile.py` claim true?

**D5.** Does round 1's PASS still hold at head `fecb5f3a35ec9b28cf849c2f8e29a5fcdb09f19a`? In
particular re-confirm the two hard requirements: `src/dopemux/dcp/red_lane_rules.py` is still
unmodified by this PR, and nothing under `services/dope-context/` is modified by it.

## Required output

Return only a single JSON object, no prose around it:

```json
{
  "verdict": "PASS | PASS_WITH_RISKS | FAIL | NEEDS_SUPERVISOR",
  "round_1_still_holds": true,
  "blocking_count": 0,
  "checks": [{"id": "D1", "result": "VERIFIED | REFUTED | PARTIAL | NOT_VERIFIABLE", "details": ""}],
  "findings": [{"id": "F-001", "severity": "BLOCKER | HIGH | MEDIUM | LOW | INFO", "title": "", "body": ""}],
  "remaining_risks": [""],
  "summary": ""
}
```
