# Disclosure re-confirmation request — public `/v1/models` catalogue in nine receipts

**Status: OPEN — operator decision required. Nothing has been redacted.**

## What is published

Nine committed turn receipts carry the child process's raw `stderr` in a `stderr` string field
(~21.9 KB each). That stderr contains a benign `codex_models_manager` decode warning **followed by
the full `/v1/models` response body** — **136 model ids**, each with `owned_by` and `shutdown_date`.
This is the account's visible model catalogue.

| File | Catalogue entries |
|---|---|
| `route_d/attempt_01/turn_01_receipt.json` | 136 |
| `route_d/attempt_01/turn_02_receipt.json` | 136 |
| `route_d/attempt_02/turn_01_receipt.json` | 136 |
| `route_d/attempt_03/turn_01_receipt.json` | 136 |
| `route_d/attempt_03/turn_02_receipt.json` | 136 |
| `route_d/attempt_03/turn_03_receipt.json` | 136 |
| `route_d/attempt_03/turn_04_receipt.json` | 136 |
| `route_d/attempt_03/turn_05_receipt.json` | 136 |
| `route_d/attempt_03/turn_06_receipt.json` | 136 |

`evidence/D_APIROUTE_PROBE.stderr_summary.txt` is **truncated at 227 bytes** and does **not** carry
the catalogue. The earlier figure of "11 receipts" was wrong; the correct count is **nine**, and
they are all turn receipts.

**No credential value is present.** Two independent scans found zero live credentials, and that
finding is unchanged.

## Why this is being raised again

Three things have changed since the operator approved publication on 2026-09-10:

1. **A reviewer objected on policy grounds.** Review thread `PRRT_kwDOPyIw986hQ8xy` cites
   `.claude/PROJECT_INSTRUCTIONS.md` and argues provider output samples and account metadata are
   sensitive unless redacted, and that a zero-credential scan does not settle it.
2. **The repository is public**, so this is disclosure to everyone, not to reviewers.
3. **The originals are gone.** `/private/tmp/DMX-DR04-EXEC-012-AMEND-030` has been reaped. When
   publication was approved, redaction would have meant "publish a sanitised copy, keep the
   byte-exact original privately". **That option no longer exists.** These committed receipts are
   now the only surviving copy of this evidence.

That third point inverts the trade-off the operator originally decided under, which is why this is
put again rather than treated as settled.

## Options

| # | Option | Consequence |
|---|---|---|
| **1** | **Re-confirm publication unmodified** *(status quo — no action needed)* | Receipts stay byte-exact and hash-covered. 136 model ids stay public. |
| **2** | Redact the `stderr` field in all nine receipts, keeping a SHA-256 of the original string | **Irreversible.** The original bytes cannot be recovered from anywhere — but they remain reachable at `bc4249ee`, so redaction alone does **not** un-publish them. |
| **3** | Option 2 **plus** a history rewrite of the branch | **Does NOT guarantee removal** — see below. Breaks every existing reference to `bc4249ee`, including this bundle's own errata provenance. |
| **4** | Close PR #1341 | **Stops advancement only. It does NOT make anything private** — see below. |

## Correction: options 3 and 4 previously overstated removal

The first version of this file described option 3 as "genuinely removes the content" and option 4
as "keep the evidence private". **Both were wrong**, and the error mattered, because it made two
options look more protective than they are.

Verified directly against the remote on 2026-09-11:

```
$ gh repo view DDD-Enterprises/dopemux-mvp --json visibility
visibility=PUBLIC

$ git ls-remote mvp 'refs/pull/1341/*'
26bfc93b3e6213587e82d3ad2bea5b389c38d8d4  refs/pull/1341/head
b53f419549c8501f5504a9c3b92eadeb5e96c765  refs/pull/1341/merge
```

`refs/pull/1341/head` is an **independent ref**, not an alias of the branch. So:

- **Closing the PR (option 4) publishes nothing less.** The branch ref and the pull ref both
  persist, in a public repository. Closing stops the PR advancing; it is not a privacy measure and
  must never be described as one.
- **A branch history rewrite (option 3) does not by itself remove the objects.** The pull ref still
  points at the old commit, and GitHub additionally documents that old commits can stay reachable
  via direct SHA, cached views, forks and existing clones — full removal can require GitHub Support
  and coordination with anyone holding a copy.

Neither correction changes the recommendation below; it strengthens it. Option 3 must be chosen in
the knowledge that removal is **best-effort and not guaranteed**, and option 4 must not be chosen
for privacy reasons at all.

## Recommendation

**Option 1, re-confirmed explicitly and recorded.** Reasoning, stated plainly so it can be
overruled:

- The disclosed material is a **model catalogue**, not a credential, a customer identifier, or a
  quota/billing figure. Most entries are public OpenAI model ids.
- Redaction now destroys evidence rather than protecting a secret, and **Option 2 does not even
  achieve removal** — the bytes remain reachable at `bc4249ee`. It buys the appearance of
  remediation, not remediation.
- No option reliably removes the content. Option 3 is best-effort at best, and it breaks the
  provenance chain this bundle depends on to be auditable at all — a certain cost for an uncertain
  benefit.

This recommendation is **not** a dismissal of the reviewer's point: the policy citation is
legitimate, and if the operator judges a 136-entry entitlement listing to be account metadata that
should not be public, **Option 3 plus a GitHub Support request is the only route that even attempts
removal** — and the broken provenance chain, plus the possibility that removal still fails, must be
accepted with it.

## Attestation — GRANTED 2026-09-11

An external supervisor review on 2026-09-11 recommended **option 1** and framed the disposition as
`POLICY_COMPLIANT=NO` with `POLICY_EXCEPTION_REQUIRED=YES` and `SECURITY_RISK_OWNER=OPERATOR`. That
framing is adopted: retaining the receipts is **not** policy-compliant and is reported here as a
bounded operator exception, **never as compliance**.

The operator granted the attestation directly on 2026-09-11, having been shown the corrected
options table — including that neither closing the PR nor rewriting history reliably removes the
published bytes.

```text
DISCLOSURE_DECISION=RECONFIRM_PUBLICATION_UNMODIFIED
OPERATOR_RISK_ACCEPTANCE=YES
SCOPE=PR #1341, nine Route D turn receipts containing the raw account-visible /v1/models catalogue
      (136 model ids each, with owned_by and shutdown_date)
ACKNOWLEDGED_REPO_POLICY_EXCEPTION=YES
ACKNOWLEDGED_PUBLIC_DISCLOSURE=YES
ACKNOWLEDGED_NO_LIVE_CREDENTIAL_VALUES_FOUND=YES
REDACTION_AUTHORIZED=NO
HISTORY_REWRITE_AUTHORIZED=NO
CLOSE_PR_AUTHORIZED=NO
GRANTED_BY=OPERATOR (repository owner, DDD-Enterprises)
GRANTED_UTC=2026-09-11
RATIONALE=Preserve the only surviving byte-exact execution evidence. The /private/tmp working roots
          have been reaped, so current-tip redaction would destroy evidence without removing the
          already-published historical bytes, which remain reachable at bc4249ee and via
          refs/pull/1341/head. The disclosed material is accepted as bounded provider/account
          metadata risk -- not treated as policy-compliant, and not a credential leak.
```

`ACKNOWLEDGED_NO_LIVE_CREDENTIAL_VALUES_FOUND` is evidence-backed rather than a judgement: two
independent scans returned zero findings.

**How a downstream auditor must read this.** The correct verdict on this item is *not* `PASS`. It is
an explicit, bounded, operator-owned policy exception with the risk accepted and recorded. An
auditor reporting this PR as policy-compliant on the disclosure question would be reporting it
wrongly.

**Freeze gate: SATISFIED.** The head carrying this attestation may now be frozen, and the single
independent L2 audit may be run against it. PR Steward follows only if that audit returns `PASS` or
a policy-permitted `PASS_WITH_RISKS`. Do not re-run PR Steward before the audit.
