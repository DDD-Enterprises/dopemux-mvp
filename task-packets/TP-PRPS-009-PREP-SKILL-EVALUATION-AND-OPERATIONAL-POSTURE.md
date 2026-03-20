---
id: TP-PRPS-009-PREP-SKILL-EVALUATION-AND-OPERATIONAL-POSTURE
title: Tp Prps 009 Prep Skill Evaluation And Operational Posture
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-16'
last_review: '2026-03-16'
next_review: '2026-06-14'
prelude: Tp Prps 009 Prep Skill Evaluation And Operational Posture (explanation) for
  dopemux documentation and developer workflows.
---
TP-PRPS-009-PREP-SKILL-EVALUATION-AND-OPERATIONAL-POSTURE

Summary

Perform a formal post-pilot evaluation of pr-prep-specialist and decide its next operational posture. This packet turns the live-pilot evidence from 008 into a governance decision about whether the prep skill should remain:
    •    package-only
    •    draft-first
    •    supervised final-creation capable
    •    restricted
    •    or rolled back to human-only prep

This is the “did the prep skill actually earn trust?” packet.

⸻

Why now

After 008, the prep skill has been exercised on real branches with:
    •    real branch truth detection
    •    real adjacent-work ambiguity
    •    real docs/changelog obligations
    •    real PR draft generation
    •    real layered validation
    •    real handoff to pr-merge-specialist

At that point, the next step should not be more invention. It should be a formal answer to:
    •    how accurate was it?
    •    how useful was it?
    •    where did it overreach?
    •    what posture is justified now?

⸻

Goals
    •    evaluate the prep skill as a whole operational subsystem
    •    assess pilot outcomes across accuracy, usefulness, and safety
    •    analyze operator acceptance and overrides
    •    analyze incidents and weak spots
    •    analyze handoff usefulness to pr-merge-specialist
    •    recommend the correct next operational posture
    •    define any required restrictions or expansion preconditions

⸻

Non-goals
    •    adding new prep features
    •    broad rollout
    •    automatic posture changes
    •    merge-specialist evaluation
    •    hiding pilot defects behind averages or vibes

⸻

Deliverables
    1.    docs/pr_prep/evaluation-model.md
    2.    docs/pr_prep/post-pilot-go-no-go-criteria.md
    3.    docs/pr_prep/operational-posture-options.md
    4.    proof/pr_prep/eval/PREP_SKILL_EVALUATION_REPORT.json
    5.    proof/pr_prep/eval/PILOT_ACCEPTANCE_SUMMARY.json
    6.    proof/pr_prep/eval/OVERRIDE_ANALYSIS.json
    7.    proof/pr_prep/eval/INCIDENT_ANALYSIS.json
    8.    proof/pr_prep/eval/OBLIGATION_ACCURACY_SUMMARY.json
    9.    proof/pr_prep/eval/PR_DRAFT_QUALITY_SUMMARY.json
    10.    proof/pr_prep/eval/HANDOFF_USEFULNESS_SUMMARY.json
    11.    proof/pr_prep/eval/GO_NO_GO_DECISION.json
    12.    proof/pr_prep/eval/GOVERNANCE_RECOMMENDATION.json
    13.    proof/pr_prep/eval/EVALUATION_MANIFEST.json

⸻

Allowed final decisions

Use exactly one of these:
    •    GO_PACKAGE_ONLY
    •    GO_DRAFT_FIRST
    •    GO_SUPERVISED_FINAL_CREATION
    •    NO_GO_LIMIT_TO_ARTIFACTS_ONLY
    •    ROLLBACK_TO_HUMAN_PREP

Confidence levels
    •    HIGH
    •    MEDIUM
    •    LOW
    •    INSUFFICIENT_EVIDENCE

⸻

Scope

In scope

Evaluate these domains:

1. Branch truth quality

Did 001 reliably determine:
    •    base branch
    •    merge base
    •    worktree truth
    •    change profile
    •    risk/prep posture

2. Adjacent-work detection quality

Did 002:
    •    catch meaningful sibling/stash overlap
    •    avoid panic on incidental overlap
    •    produce useful ambiguity decisions

3. Obligation accuracy

Did 003 correctly classify:
    •    docs requirements
    •    changelog/release-note requirements
    •    migration/config notes
    •    linked context needs

4. PR draft quality

Did 004 produce:
    •    good titles
    •    complete summaries
    •    honest verification sections
    •    strong risks/rollback/reviewer notes
    •    correct high-risk notes
    •    non-embarrassing checklist state

5. Validation correctness

Did 005:
    •    keep deterministic checks first
    •    invoke consensus only when justified
    •    produce the correct prep decisions
    •    preserve not-run states honestly

6. Creation/handoff quality

Did 006:
    •    use the correct creation mode
    •    preserve warnings and blockers
    •    hand off enough truth to pr-merge-specialist

7. Operational pilot quality

Did 008 show:
    •    operator trust
    •    usable outputs
    •    acceptable override rate
    •    acceptable incident rate
    •    acceptable pilot posture for continued use

Out of scope
    •    downstream merge outcomes beyond handoff usefulness
    •    org-wide rollout
    •    event-driven automation
    •    new skill capabilities

⸻

Preconditions
    •    TP-PRPS-001 through TP-PRPS-008 complete
    •    pilot artifacts available
    •    operator acceptance/override/incident data available
    •    handoff usefulness data available

⸻

Inputs
    •    all proof artifacts from 001–008
    •    pilot case index
    •    pilot run reports
    •    acceptance/override reports
    •    incident reports
    •    obligation accuracy report
    •    PR draft quality report
    •    handoff usefulness report
    •    pilot health summary

⸻

Outputs
    •    whole-skill evaluation report
    •    per-domain quality summaries
    •    go/no-go decision
    •    governance recommendation
    •    evaluation manifest

⸻

Ordered steps

1. Define go/no-go criteria

Create explicit decision criteria for:
    •    package-only approval
    •    draft-first approval
    •    supervised final-creation approval
    •    no-go / rollback

Criteria must include:
    •    truthfulness
    •    usefulness
    •    operator acceptance
    •    override severity/rate
    •    incident severity/rate
    •    obligation accuracy
    •    handoff usefulness
    •    sample-size caveats

2. Aggregate evidence across 001–008

Separate:
    •    structural validation
    •    pilot behavior
    •    thin-sample areas
    •    known weak spots

Do not blur those together.

3. Evaluate branch truth quality

Assess whether wrong base-branch selection, dirty-state handling, or change-profile misclassification happened often enough to limit trust.

4. Evaluate adjacent-work quality

Assess whether overlap detection:
    •    caught real issues
    •    overblocked harmless ones
    •    missed meaningful missing work

5. Evaluate obligation accuracy

Assess whether docs/changelog/migration/context obligations were:
    •    correct
    •    conservative but useful
    •    false-positive noisy
    •    false-negative dangerous

6. Evaluate PR draft quality

Assess:
    •    title usefulness
    •    summary correctness
    •    verification honesty
    •    risk/rollback quality
    •    reviewer note usefulness
    •    checklist correctness
    •    overall reviewer readability

7. Evaluate validation correctness

Assess whether 005:
    •    blocked what should be blocked
    •    drafted what should be draft-only
    •    avoided consensus overuse
    •    preserved visible uncertainty correctly

8. Evaluate handoff quality

Assess whether handoff bundles were:
    •    complete
    •    truthful
    •    useful downstream
    •    too noisy
    •    missing key context

9. Evaluate pilot behavior

Assess:
    •    operator acceptance rate
    •    partial acceptance rate
    •    rejection rate
    •    override severity/rate
    •    incident severity/rate
    •    usefulness trend
    •    whether current posture should continue

10. Produce formal decision and governance recommendation

Emit:
    •    one final decision
    •    rationale
    •    confidence
    •    required restrictions or next-step preconditions
    •    whether expansion is justified or not

⸻

Implementation requirements
    •    Be honest about thin samples.
    •    If package generation is good but live creation is underproven, recommend GO_DRAFT_FIRST, not bravado.
    •    If handoff quality is weak, do not recommend broader operational use.
    •    If incidents are low but operator acceptance is weak, say so directly.
    •    No automatic posture change occurs from this packet.
    •    Recommendations must be governance-first, not momentum-first.

⸻

Suggested quality bands

Branch truth
    •    TRUSTWORTHY
    •    USEFUL_WITH_CAVEATS
    •    NOISY
    •    UNSAFE

Adjacent-work detection
    •    HIGH_SIGNAL
    •    CONSERVATIVE_USEFUL
    •    OVERBLOCKING
    •    UNDERDETECTING

Obligation detection
    •    ACCURATE
    •    CONSERVATIVE
    •    NOISY
    •    UNRELIABLE

PR draft quality
    •    HIGHLY_USEFUL
    •    USEFUL_WITH_CAVEATS
    •    LIMITED
    •    MISLEADING

Handoff quality
    •    READY_FOR_DOWNSTREAM_USE
    •    SUFFICIENT_WITH_GAPS
    •    INSUFFICIENT

Pilot usefulness
    •    STRONG
    •    PROMISING
    •    LIMITED
    •    CONCERNING

⸻

Commit plan
    1.    docs(pr-prep): add post pilot evaluation model and go no go criteria
    2.    docs(pr-prep): add operational posture options and governance rules
    3.    feat(pr-prep): aggregate structural and pilot evidence across 001 to 008
    4.    feat(pr-prep): add domain quality summaries for truth obligations drafting validation and handoff
    5.    feat(pr-prep): add pilot acceptance override and incident analysis
    6.    feat(pr-prep): add go no go decision and governance recommendation outputs
    7.    feat(artifacts): emit prep skill post pilot evaluation bundle and manifest
    8.    test(pr-prep): add evaluation classification and decision coverage

⸻

Acceptance checks
    •    Go/no-go criteria are explicit.
    •    Structural and pilot evidence are separated clearly.
    •    Per-domain summaries exist.
    •    Final decision artifact exists.
    •    Governance recommendation exists.
    •    Thin-sample caveats are explicit.
    •    No authority changes occur automatically.

⸻

Proof requirements

Required artifacts:
    •    docs/pr_prep/evaluation-model.md
    •    docs/pr_prep/post-pilot-go-no-go-criteria.md
    •    docs/pr_prep/operational-posture-options.md
    •    proof/pr_prep/eval/PREP_SKILL_EVALUATION_REPORT.json
    •    proof/pr_prep/eval/PILOT_ACCEPTANCE_SUMMARY.json
    •    proof/pr_prep/eval/OVERRIDE_ANALYSIS.json
    •    proof/pr_prep/eval/INCIDENT_ANALYSIS.json
    •    proof/pr_prep/eval/OBLIGATION_ACCURACY_SUMMARY.json
    •    proof/pr_prep/eval/PR_DRAFT_QUALITY_SUMMARY.json
    •    proof/pr_prep/eval/HANDOFF_USEFULNESS_SUMMARY.json
    •    proof/pr_prep/eval/GO_NO_GO_DECISION.json
    •    proof/pr_prep/eval/GOVERNANCE_RECOMMENDATION.json
    •    proof/pr_prep/eval/EVALUATION_MANIFEST.json

Validation must cover at least:
    •    one path supporting package-only
    •    one path supporting draft-first
    •    one case where supervised final creation remains unjustified
    •    one thin-sample caveat case
    •    one case where handoff quality materially affects the recommendation
    •    one case where obligation accuracy materially affects the recommendation

⸻

Rollback notes
    •    Evaluation-only packet, low operational risk.
    •    If pilot evidence is too thin, emit INSUFFICIENT_EVIDENCE rather than forcing a fake decision.
    •    If domain quality is mixed, prefer narrower posture recommendation.
    •    If operator feedback conflicts, surface disagreement explicitly rather than averaging it into mush.

⸻

Exit criteria

This packet is complete when pr-prep-specialist has a formal post-pilot whole-skill evaluation and a clear governance recommendation for its next operational posture.
