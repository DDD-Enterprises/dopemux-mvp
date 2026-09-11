# Independent L2 audit — PR #1341, dopemux-mvp

You are the **sole final independent auditor** for this pull request. You are not the
implementer. Your verdict is binding evidence. You have **one** call; there is no second pass.

## 0. Custody — do this first, before reading anything else

The workspace mounted for you is a git worktree. Run:

```
git rev-parse HEAD
```

It **must** print exactly:

```
d39d06bcb75fa2dcb5fac3de779e45c1cf0b502f
```

If it prints anything else, **stop immediately** and return `NEEDS_SUPERVISOR` with
`CUSTODY_MISMATCH` as your sole finding. Do not audit a different commit.

The base to diff against is `640f0a2b56d795442455b0ecd98cef7c7d22703e`. The prior, already-
reviewed head is `bc4249eecf4f428528488a7a3d4eeb3420aebfbc`.

If you have file-reading and shell tools, independently recompute and confirm these SHA-256
hashes under `claudedocs/exec-012-dr04-amend-030/`. If you cannot run tools, say so plainly and
set `HASH_RECOMPUTATION=NOT_RUN` — do **not** claim verification you did not perform.

```
53e24df158979555674087f9c9b304b73a373f64a60f6437ca8bb3e2356803b1  SUPERVISOR_RETURN.json
b896c9ba676f65c3380f33d30bcdf1d9fc4e141c06725d9af120bb780d7802e2  SUPERVISOR_HANDOFF.md
547ea8f0df195dfb5fe575576c3d448be992895657611ba4c799acfc013eee3a  README.md
5b7503eaab9debe5346895b3e3b816c6f90c8959b198ab89c2f20fe758bf66d9  CHECKPOINT.md
61e22c381a424e756c8ba54ee5ba042f5cab995e891e8898f6a4a28614afadd6  evidence/D_APIROUTE_PROBE.json
7fe74e8607c70aed7fc4a25227e53001d2060c3573140581df2d69b043b11aa7  ERRATA/DEFECT-001-narration-preface-count.json
7a8819b88bf8fd2c8b107d857366871d5e2d8b1d7c95d2f4ea4fccc031fb4ee8  ERRATA/DEFECT-002-unknown-tool-event-contract.json
34c044c9848c1a9467e2b87ee67075ea77aafb86b2625e1af01cae55bd7ccbcb  ERRATA/PATH_MAP.json
723c1ab071d806b17929ab62abdbc459f18631a0db5c47fc27d7ffe50d25c4e1  ERRATA/ROUTE_RECORD.json
b92cccd80a415c6a7d66dff1810580c08b8b24da6f0fdc6a847fb62e5590f360  ERRATA/DISCLOSURE_RECONFIRMATION.md
33343737428a7cc6c50786e99cf3b47def1b5b6b87a56e7122f99af3b7917807  ERRATA/ERRATA.md
```

## 1. What this PR is

It is an **evidence-only** PR. It publishes the execution evidence of a model-routing benchmark
(EXEC-012 / DR04, amendment 030) under `claudedocs/exec-012-dr04-amend-030/`. It contains no
product code, no configuration and no workflow changes. **It does not claim the benchmark
succeeded** — Route D produced no research report across three live attempts and Route A never
reached a provider.

Since `bc4249ee` it has been repaired in response to a review. The repair followed one rule:

> **Claims were corrected in place. Records were never touched.**
> A *record* is an artifact of what actually ran (`route_d/**`, `shared_contracts/**`, and the
> measured `usage`/`RESULTS` blocks of `evidence/*.json`). A *claim* is an assertion about those
> records (`SUPERVISOR_RETURN.json`, `SUPERVISOR_HANDOFF.md`, `README.md`, narrative fields).

Start at `ERRATA/ERRATA.md`, which indexes every correction.

## 2. Your job

Challenge all fifteen points below. For each, state **UPHELD**, **DISPUTED** or **UNVERIFIABLE**,
with the evidence you relied on. Be adversarial: you are looking for claims the artifacts do not
support. Do not accept a summary's word for anything you can check against a primary file.

1. **Record-tier immutability.** Verify `git diff --name-only bc4249ee d39d06bcb -- claudedocs/exec-012-dr04-amend-030/route_d claudedocs/exec-012-dr04-amend-030/shared_contracts` is empty. Is the claims/records separation real and consistently applied, or is it a rhetorical device that conceals edits to evidence?
2. **The corrected spend ledger.** `SUPERVISOR_RETURN.json` -> `SPEND`. Verify 224,907+58,065+489,388 = 772,360 and 1,595+392+3,937 = 5,924; that the D subtotal is $8.02 at $10/$50 per million; that the probe's $0.11 is correctly held *outside* `token_totals`; and that the total is $8.13 with $1.87 remaining. Confirm attempt 1 is $2.33 and that the previously published $2.22 and $8.28 were unsupported. Check the residual UNKNOWN (the ~8,235-token probe) is honestly flagged rather than silently absorbed.
3. **Model identity separation.** `requested_model` / `catalog_availability` / `served_model` / `provider_fallback`. Is the withdrawal of the earlier "no silent fallback occurred" inference complete and correct in **both** `SUPERVISOR_RETURN.json` and `evidence/D_APIROUTE_PROBE.json`? Does any residual text still imply serving identity is known?
4. **Mutation accounting.** Does the handoff's corrected split (benchmark mutations 0 vs operator-authorized publication mutations 1 repo + 1 GitHub) now agree with `SUPERVISOR_RETURN.json` -> `GATES_AND_MUTATIONS`? Is the supersession of `GITHUB_MUTATION_AUTHORIZED=NO` disclosed rather than buried?
5. **Turn accounting.** Ten live codex turns (3+1+6) across three attempts, nine receipted. Verify against `route_d/attempt_*/loop_state/` and the receipt files. Is the unreceipted turn (attempt 1 turn 3) honestly sourced to `D_DISPATCH_RESULT.json` -> `SPEND.turn_03` rather than inferred?
6. **Scan-scope correction.** 245 files (working tree) vs 75 (pre-publication subset) vs 76 present. Is the explanation coherent and non-evasive?
7. **Provenance / path map.** Records cite `W01/...`; artifacts are published under `shared_contracts/`. Is leaving the records unrewritten and supplying `ERRATA/PATH_MAP.json` the right call, or does it obstruct verification?
8. **DEFECT-001** (`ERRATA/DEFECT-001-narration-preface-count.json`). The `narration_preface_count` defect in `shared_contracts/message_arity.py`. Is the reasoning for **not** fixing it in place sound? Critically: verify the claim that **no committed receipt carries a wrong value** — check attempt 3's receipts for narration and attempt 1 turn 3's shape. If any receipt *is* mislabelled, that materially changes the finding.
9. **DEFECT-002** (`ERRATA/DEFECT-002-unknown-tool-event-contract.json`). The unknown-event gap in `shared_contracts/W01_TOOL_EVENT_CLASSIFIER.json` versus its declared `FAIL_CLOSED_ALLOWLIST`. Is recording it unapplied appropriate for a frozen contract? Is the admission that implementation behaviour is UNKNOWN from these artifacts honest?
10. **Public disclosure.** Nine turn receipts embed a raw `/v1/models` body (136 model ids each) in a **public** repository. Verify the count of nine and that no live credential value is present.
11. **Operator risk acceptance.** `ERRATA/DISCLOSURE_RECONFIRMATION.md`. The operator granted an explicit, bounded exception. Is it properly scoped, dated, attributed and reversible-in-record? Is the corrected claim — that neither closing the PR nor rewriting history reliably removes already-published bytes — accurate?
12. **`POLICY_COMPLIANT=NO` must remain truthful.** The disclosure item is an accepted **policy exception**, not compliance. You **may accept** that bounded exception. You **may not** rewrite it into compliance. An audit that reports this PR as policy-compliant on the disclosure question is wrong on the facts. Confirm the artifacts themselves never claim compliance.
13. **The primary Route-D finding.** `limits.codex = 6` with 3 web_search + 3 web_fetch = 6 retrieval slots leaves no turn to emit `final`. Is the structural-defect conclusion supported by attempt 3's six turns, and is it correctly scoped as route-level rather than model-level?
14. **Does the PR represent its evidence accurately** without overclaiming? Specifically: does it anywhere imply the benchmark is complete, that a four-route comparison exists, or that Route A ran? It should assert the opposite.
15. **Authority.** Confirm the bundle claims no adoption, activation or merge authority, and that nothing in it purports to grant any.

## 3. Reporting rules

- Quote file paths and identifiers for every load-bearing claim.
- Distinguish **Observed** (you verified it), **Inferred** (plausible, unproven) and **Unknown**
  (missing evidence). Never backfill an Unknown.
- If you cannot verify something, say `UNVERIFIABLE` and why. That is a valid, valuable answer.
- Report any **novel** security or governance risk that is not already operator-accepted.

## 4. Required output format

End your response with exactly this block, filled in, and nothing after it:

```
MODEL_REQUESTED=gemini-3.8-flash-high
MODEL_RESPONSE_CLAIMED=<the model identifier you believe you are, from your own self-knowledge>
MODEL_PROVIDER_ATTESTED=UNKNOWN
EFFORT_REQUESTED=high
EFFORT_OBSERVED=<your best honest statement, or UNKNOWN>
HASH_RECOMPUTATION=<PASS|FAIL|NOT_RUN>
CUSTODY_HEAD_CONFIRMED=<yes|no>
POINTS_UPHELD=<n of 15>
POINTS_DISPUTED=<n>
POINTS_UNVERIFIABLE=<n>
NOVEL_UNACCEPTED_RISKS=<none, or a list>
VERDICT=<PASS|PASS_WITH_RISKS|FAIL|NEEDS_SUPERVISOR>
```

`MODEL_PROVIDER_ATTESTED` stays `UNKNOWN` unless you have a verifiable provider-side source; do
not infer it from configuration. Choose `VERDICT` from those four tokens only. `PASS_WITH_RISKS`
requires you to enumerate each risk and say whether it is already operator-accepted.
