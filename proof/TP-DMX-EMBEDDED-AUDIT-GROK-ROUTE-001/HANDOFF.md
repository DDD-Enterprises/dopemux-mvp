# HANDOFF — TP-DMX-EMBEDDED-AUDIT-GROK-ROUTE-001

## What this packet does

It gives the trusted embedded-audit contract a word for the Grok runner.

Before this, `schemas/proof/embedded_audit.schema.json` enumerated seven auditor tools
and six auditor models, none of them Grok, with `additionalProperties: false` and a
conditional forbidding `auditor_tool: "none"` or `auditor_model: "unknown"` for any
non-`SKIPPED` status. A completed, passing Grok audit therefore had exactly two
representable encodings, and both were lies:

```text
status: SKIPPED  + none/unknown   -> asserts no audit happened
status: PASS     + a tool from the enum -> fabricates an auditor identity
```

That is not a defect in any particular audit. It is a missing word in a vocabulary,
and the correct repair is to add the word.

## What it admits, and what it refuses to admit

```text
ADMITTED     auditor_tool  += grok-cli
             auditor_model += grok-4.5

             bound fail-closed in BOTH directions:
               auditor_model == grok-4.5  =>  auditor_tool  == grok-cli
               auditor_tool  == grok-cli  =>  auditor_model == grok-4.5

NOT ADMITTED grok-4.5-build   usage/telemetry label, not a requestable model id
             grok-4.6         the runner's current default, but outside the
                              authorization -- admitting it is an operator decision
```

The bidirectional binding matters because a one-directional rule lets half a pair be
borrowed. The pre-existing `gemini-3.1-pro-high -> agy` conditional is one-directional;
this packet does not repeat that gap for the new pair, and does not alter the old one.

Each conditional carries its own `then.required`. JSON Schema `properties` is vacuous
for an absent key, so without it, deleting `auditor_tool` would *satisfy* the rule
rather than fail it.

## Why the coverage claim is worth believing

Four things, none of which is "the producer says so":

1. **The differential is against the real pre-change contract**, read from git, not a
   paraphrase of its rules. Old and new schema must return the same verdict for every
   pre-change tool/model pair across all five statuses. A hand-written reference
   predicate would only prove the producer's *understanding* was preserved.
2. **The whole existing corpus revalidates**: 74/74 PASS. This is the same check CI
   runs as `🔍 Audit Proof Validator (--all)`.
3. **The tests are proven to fail.** One conditional was deleted from a copy of the
   schema; three tests went red, including the specific semantic one. A suite that
   passes against a schema with the feature removed is not testing the feature.
4. **The intended #1227 block was validated both ways** — PASS under the new contract,
   FAIL under the old one for exactly the two enum reasons.

## Scope, and the honest account of what was left alone

`CONSUMER_INVENTORY.json` is the deliverable that justifies the boundary, including the
non-changes. The operator conditioned `run_embedded_audit.py` on inspection proving a
recognition table; there is none, so it is untouched. `local_audit_acceptance.py` is
tool-agnostic and inherits both conditionals through Draft7.

Two named exclusions worth attacking rather than trusting:

- **`schemas/proof/auditor_route.schema.json`** also has a tool enum without
  `grok-cli`. It governs the router's route-selection record, a different lane, and its
  model field is an unconstrained string. Representing a completed audit does not write
  it. If Grok is ever added to the automated router, that packet must extend this enum.
- **`docs/**`** carries no machine-read enum listing. The original gap note sketched a
  docs update as indicative scope; the operator narrowed the packet and forbade
  broadening without proof of necessity, so it is deliberately deferred rather than
  smuggled in.

The one consumer the grep missed was caught by the test suite: the parity corpus in
`test_local_audit_acceptance.py` pins the `allOf` count and demands a violating fixture
per conditional, precisely so a new conditional cannot become unenforced. It failed as
designed and named what it wanted.

## Things that changed under the packet while it was being written

**The runner drifted.** When the gap was first recorded, the grok CLI exposed exactly
one model — `grok-4.5`, also the default. It is now version 1.0.3, exposes two, and
**the default is `grok-4.6`**.

Two consequences:

1. **Future Grok audits must pin `-m grok-4.5`.** An unpinned invocation will run on
   `grok-4.6` and be unrepresentable under this contract — the same wall this packet
   just removed, hit again from the other side. Whether to admit `grok-4.6` is an
   operator decision, not a producer convenience.
2. A claim in `GROK_SCHEMA_REPRESENTATION_GAP.md` is now stale: it argues that because
   the runner exposes exactly one model, `fallback_enabled: false` and
   `model_switching: false` are *structurally* guaranteed. That guarantee no longer
   holds. The historical document is left unedited; `CONSUMER_INVENTORY.json`
   supersedes that one claim.

**#1227's auditor model was recoverable.** That packet recorded
`model: UNKNOWN_TO_PRODUCER` — honest, and fatal to the follow-on step that must *name*
the model. Naming `grok-4.5` on an assumption would be exactly the fabrication this
work exists to prevent. The runner's own session metadata settles it from bytes: both
the killed attempt and the run that produced the verdict record `grok-4.5`. Evidence
and its limits are in `review_bundle/pr1227_r2_session_model_evidence/`.

## What is still NOT true after this merges

```text
PR #1227 merged                     NO   -- separate lane, separate decision
any ADR accepted                    NO
Grok admitted to the auto router    NO
grok-4.6 representable              NO
runtime behaviour changed           NO
docs updated to list grok           NO   -- deliberately deferred
```

This packet changes a vocabulary. It does not audit, accept, or merge anything else.

## The next step, and the trap in it

Once this is on `main`, PR #1227 can encode its round-2 audit truthfully. The trusted
schema is read from the **trusted ref**, never from the PR branch — which is why this
had to land on `main` first, and why adding these values on #1227's own branch would
have done nothing.

The trap: #1227's proof update must change **proof/evidence metadata only**. The 36
R2-audited files must remain byte-identical to `6e1b4472ba`, or the audit that the
metadata attests to is no longer the audit that ran. Verify by hashing, not by reading
a diff — a same-path change arriving from `main` does not show up as a diff against the
branch.

Merging #1227 still accepts no ADR and authorizes no implementation.
