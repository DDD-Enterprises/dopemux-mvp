# Signing disclosure — PR #1242 local attestation

This disclosure and the `PROOF.json` beside it satisfy the trusted, signed
local-attestation fallback (`scripts/audit/local_audit_acceptance.py`) for
PR #1242 (`docs(second-brain): publish accepted ADR authority`).

## What this PR is

PR #1242 publishes an already-completed and independently audited Second
Brain ADR acceptance/persistence to `main` from local branch
`tp/DMX-SB-ADR-ACCEPTANCE-002` (packet
`TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PUBLICATION-001`). It makes no new ADR
election, changes no accepted decision, and authorizes no implementation,
runtime, or production mutation.

## Why the trusted CI auditor can't run here

The trusted embedded-audit workflow's own PAL clink / provider-credentialed
path reported `NEEDS_SUPERVISOR` on this PR — the same fail-closed behavior
documented for this gate generally (see `docs/ops/embedded-audit-proof.md`,
"Independent Workflow Output": PR CI does not expose
`EMBEDDED_AUDIT_TOKEN` to PR-head code, so that path emits `SKIPPED`/
`NEEDS_SUPERVISOR` unless a trusted-ref caller supplies both token authority
and PAL output). This is the gate working as designed, not a bypass target —
the accepted alternative is exactly this signed local-attestation path.

## Independent audit performed

`grok` CLI, `grok-4.5` (explicit `-m` flag), `--always-approve --max-turns 80
--output-format plain`, run read-only against the exact frozen commit `C_PUB`
via SHA-addressed `git show`/`git diff`/`git log`/`git merge-base` (content-
addressed operations, valid independent of working-tree checkout state — see
`proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PUBLICATION-001/AUDIT_PROMPT.md`
for the full ten-point verification brief given to the auditor). Verdict
**PASS_ADR_ACCEPTANCE_PUBLICATION_INTEGRITY**, `BLOCKERS=0`, `MUST_FIX=0`:
independently reconstructed and verified all ten `ADR-SB-*` dispositions and
sha256 hashes, ancestry of the prior audited head, per-commit classification
of everything after that head, the fresh main-drift re-derivation, the
merge's clean tree, the reasoning-correction's append-only byte-identity, and
`NOT_RUN`/`NOT_IMPLEMENTED`/`ABSENT` implementation-gate preservation. Full
report: `proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PUBLICATION-001/AUDITOR_REPORT.md`
(raw output, prompt, and full custody — including 3 failed attempts on the
preferred AGY/gemini-3.1-pro-high route before this run — alongside it in
that same directory).

## Bridge topology, named not conflated

| Term | Meaning | SHA |
|---|---|---|
| `AUDITED_TREE` (`C_PUB`) | commit examined by the independent grok-4.5 audit | `9e819f38c5f8c9da44cd396abe740d378f035d1a` |
| `AUDIT_EVIDENCE_HEAD` | proof-only + packet-metadata successor: the audit's own report/custody/prompt/command-log evidence, one schema-conformance fix to that same packet's own `PROOF.json` (added the required `embedded_audit` field), and the `task-packets/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PUBLICATION-001.json` record added in response to a PR review finding (see amendment below) | `804147bfb269303c0ee7d307766e34a2de41e5ce` |
| this bridge commit | adds only `proof/pr_merge/embedded-audit/pr-1242/**` on top of `AUDIT_EVIDENCE_HEAD` | (this commit) |

Verified via `git diff --name-only 9e819f38c5 804147bfb2`: every changed path
is confined to `proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PUBLICATION-001/**`,
`proof/pr_merge/embedded-audit/pr-1242/**`, or the single new
`task-packets/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PUBLICATION-001.json` file —
no code, schema, ADR, or accepted-authority file touched between
`AUDITED_TREE` and `AUDIT_EVIDENCE_HEAD`. `AUDITED_TREE` is an ancestor of
`AUDIT_EVIDENCE_HEAD`. This bridge commit is itself a second proof-only
delta, not a re-audit — the same pattern already disclosed identically for
PR #1235, #1226, and #1224.

## Amendment: re-signed against a later AUDIT_EVIDENCE_HEAD

The first signed attestation for this PR named `head_sha =
2d4e679b02c996ab8dbea1cec01b3a27b998edb6`. Between that commit and the push
of this bridge, a PR review (Codex/Copilot automated reviewers) found this
packet's own `PROOF.json` referenced a `tp_id` with no corresponding
`task-packets/*.json` file — a real gap, fixed in
`804147bfb269303c0ee7d307766e34a2de41e5ce` by adding that record (validated
against `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`). That
fix is not part of the audited code or accepted ADR authority, so the
underlying `grok-4.5` audit evidence is unchanged and still applies; this
`PROOF.json` is re-signed with `head_sha` advanced to the new tip, following
the same acceptance-fails-closed / re-sign-on-legitimate-advance pattern
already used and disclosed for PR #1235.

## Trust model, stated plainly

This signature is a **producer/operator self-attestation**, not a
third-party audit. The independent evidence is the grok-4.5 run itself
(different model family and runtime from this session, run read-only against
the exact audited commit). The signature only lets the trusted CI workflow
accept that already-independent evidence when its own auditor cannot
execute.

Authorized under a fresh, narrowly-scoped operator decision specific to PR
#1242 ("Yes, authorize it for PR #1242") — not inferred from the broader
publication packet's authorization, which did not itself name this CI gate
or this signing mechanism.

## What this proof authorizes

Only readiness-check progression (`independent embedded audit` and `PR
Steward / final readiness` going green) for PR #1242's actual head at the
time this attestation is added. It authorizes no merge — merge remains
`OPERATOR_ONLY` per the publication packet, performed separately after
confirming all required checks report green through the normal (non-bypass)
path.
