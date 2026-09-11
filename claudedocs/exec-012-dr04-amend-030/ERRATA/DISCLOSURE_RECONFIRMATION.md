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
| **2** | Redact the `stderr` field in all nine receipts, keeping a SHA-256 of the original string | **Irreversible.** The original bytes cannot be recovered from anywhere — but they do remain in git history at `bc4249ee` unless history is rewritten, so redaction alone does **not** actually un-publish them. |
| **3** | Option 2 **plus** a history rewrite of the branch | Genuinely removes the content. Breaks every existing reference to `bc4249ee`, including this bundle's own errata provenance. |
| **4** | Close PR #1341 and keep the evidence private | No public disclosure; no public evidence trail either. |

## Recommendation

**Option 1, re-confirmed explicitly and recorded.** Reasoning, stated plainly so it can be
overruled:

- The disclosed material is a **model catalogue**, not a credential, a customer identifier, or a
  quota/billing figure. Most entries are public OpenAI model ids.
- Redaction now destroys evidence rather than protecting a secret, and **Option 2 does not even
  achieve removal** — the bytes remain reachable at `bc4249ee`. It buys the appearance of
  remediation, not remediation.
- The one option that genuinely removes the content (3) breaks the provenance chain this bundle
  depends on to be auditable at all.

This recommendation is **not** a dismissal of the reviewer's point: the policy citation is
legitimate, and if the operator judges a 136-entry entitlement listing to be account metadata that
should not be public, **Option 3 is the only honest way to act on that** — and the cost of the
broken provenance chain must be accepted with it.

**Whichever option is chosen, record it here and in `SUPERVISOR_RETURN.json` →
`GATES_AND_MUTATIONS.github_mutation_detail.disclosure_decision`.** As of this commit the decision
is recorded as an **explicit operator risk acceptance from 2026-09-10, pending re-confirmation** —
not as an oversight, and not as a credential leak.
