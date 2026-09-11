# Errata — amendment-030 evidence bundle

**Corrected from** `bc4249eecf4f428528488a7a3d4eeb3420aebfbc` · **on** 2026-09-11
**Authority** operator instruction to execute the repair sequence from the PR #1341 review
**Route record** [`ROUTE_RECORD.json`](ROUTE_RECORD.json)

---

## The rule this repair followed

**Claims were corrected in place. Records were not touched.**

- A **record** is an artifact of what actually ran: everything under `route_d/`, every module and
  contract under `shared_contracts/`, and the measured `usage` / `RESULTS` blocks of
  `evidence/*.json`. Editing one would make this bundle misrepresent the runs it exists to
  evidence. Defects found in records are written down here **unapplied**.
- A **claim** is an assertion *about* those records: `SUPERVISOR_RETURN.json`,
  `SUPERVISOR_HANDOFF.md`, `README.md`, and the narrative fields of `evidence/*.json`. A wrong
  claim is simply wrong, and was corrected.

Every pre-repair byte remains retrievable at `bc4249ee`. **No measured value was altered anywhere.**

---

## Corrections applied

### E1 — Spend ledger was internally inconsistent *(P1; review thread `…hQ8yd`)*

The bundle carried three mutually incompatible totals: per-attempt figures summing to **$7.91**,
a `token_totals` block computing to **$8.02**, and a headline of **$8.28**.

Reconciled against the primary records:

| Item | Input | Output | USD | Source |
|---|---:|---:|---:|---|
| D attempt 1 | 224,907 | 1,595 | **2.33** | `evidence/D_DISPATCH_RESULT.json` → `SPEND.totals` |
| D attempt 2 | 58,065 | 392 | 0.60 | `…_ATTEMPT_02.json` |
| D attempt 3 | 489,388 | 3,937 | 5.09 | `…_ATTEMPT_03.json` |
| **D subtotal** | **772,360** | **5,924** | **8.02** | = the published `token_totals`, exactly |
| API-route probe | 10,902 | 21 | 0.11 | `evidence/D_APIROUTE_PROBE.json` → `usage` |
| **Total** | **783,262** | **5,945** | **8.13** | |

- `ROUTE_OUTCOMES.D.attempts[0].usd`: **2.22 → 2.33**. The reviewer was right and the return
  disagreed with its own source record: 224,907 × $10/M + 1,595 × $50/M = **$2.3288**. The $2.22
  figure matches no artifact in the bundle.
- `SPEND.total_usd_estimated`: **8.28 → 8.13**, with `route_d_attempts_usd: 8.02` and
  `probe_usd: 0.11` itemised separately. The probe was real spend but sits **outside**
  `token_totals`, which is exactly the three D attempts and nothing else.
- `SPEND.remaining_usd`: **1.72 → 1.87**.
- Attempt 1's turn 3 wrote **no receipt** (it failed arity before the receipt write). Its
  85,082 / 558 is **OBSERVED** in `D_DISPATCH_RESULT.json` → `SPEND.turn_03`, not inferred.
- **Residual UNKNOWN, recorded not guessed:** an earlier ~8,235-token no-output-schema cost-floor
  probe (~$0.08) has no evidence file in this bundle and may be uncounted. **Treat $8.13 as a
  floor.**

### E2 — Catalogue presence does not prove absence of fallback *(P1; threads `…hQ8yq`, `…hQ8y-`)*

Both the return and the probe stated `served_model` is not attestable, then concluded that
`gpt-6-astra` appearing in `/v1/models` proved no silent fallback occurred. It proves no such
thing: `/v1/models` attests **account entitlement**, not which backend served a given request, and
cannot exclude provider-side aliasing.

The inference is **withdrawn**. Both files now record four separate facts:
`requested_model = gpt-6-astra` · `catalog_availability = OBSERVED_PRESENT` ·
`served_model = UNKNOWN` · `provider_fallback = UNKNOWN`.

### E3 — Handoff contradicted the machine return on mutations *(P1; thread `…hQ8yP`)*

`SUPERVISOR_HANDOFF.md` asserted "Repository mutations: 0. GitHub mutations: 0" while
`SUPERVISOR_RETURN.json` recorded `repository_mutations_made: 1` and `github_mutations_made: 1` for
the very act of publishing this bundle. The "start here" document cannot contradict the machine
return. The handoff now separates the two categories:

- **Benchmark / audited-original mutations: 0.** The 028 surface was never edited and re-verified
  clean after every dispatch. Both packet gates honoured.
- **Operator-authorized evidence-publication mutations: 1 repository, 1 GitHub.** One commit on a
  new branch off `mvp/main` in an isolated worktree, pushed, opening PR #1341 — under an explicit
  operator instruction that superseded `GITHUB_MUTATION_AUTHORIZED=NO`.

### E4 — Disclosure count wrong; originals now gone *(P1 security/privacy; thread `…hQ8xy`)*

The count of artifacts embedding the raw `/v1/models` body was stated as **11**; it is **nine**,
all turn receipts, each carrying **136** model ids. `D_APIROUTE_PROBE.stderr_summary.txt` is
truncated at 227 bytes and carries none.

**Nothing was redacted.** Since `/private/tmp/DMX-DR04-EXEC-012-AMEND-030` has been reaped, these
receipts are the only surviving copy, so redaction would now be destruction rather than
sanitisation — and would not even un-publish the bytes, which remain at `bc4249ee`. The 2026-09-10
operator approval is recorded as an **explicit risk acceptance, pending re-confirmation**:
see [`DISCLOSURE_RECONFIRMATION.md`](DISCLOSURE_RECONFIRMATION.md).

### E5 — Live-turn accounting *(P2)*

"Nine live turns across attempts 1 and 3" was wrong twice over. Route D made **ten** live codex
turns — 3 + 1 + 6 across attempts 1, **2** and 3 — of which **nine** were receipted. The
prompt-cache finding is unaffected: `cached_input_tokens = 0` holds on all nine receipted turns and
on the unreceipted one.

Also recorded here: `RUN_ROUTE_A_FROM_TERMINAL.command`, the handover script named in blocking
decision 2, lived in the reaped working tree and is **not** in this bundle. Route A's relaunch
needs it rebuilt.

### E6 — Secret-scan scopes were unlabelled *(P2; thread `…hQ80D`)*

**245 files** = the full amend-030 working tree. **75 files** = the pre-publication scan of the
published subset, which is 76 files today because `SUPERVISOR_RETURN.json` was written after that
scan ran. Neither count is an error in the other; both are now labelled. Zero live credential
values in both.

### E7 — `W01/...` provenance paths

Records cite artifacts as `W01/...` because that is where they were when they ran; they are
published here under `shared_contracts/`. **The records were left as-is** — rewriting them would
make them describe a layout that never executed. [`PATH_MAP.json`](PATH_MAP.json) supplies the
mapping, and also lists the artifacts cited by the records that are *not* in this bundle.

### E8 — My own options table overstated removal *(correcting E4's companion document)*

The first version of `DISCLOSURE_RECONFIRMATION.md` described closing PR #1341 as keeping the
evidence "private", and a branch history rewrite as one that "genuinely removes the content".
**Both were wrong**, and wrongly favourable — they made two options look protective.

Verified against the live remote: the repository is **PUBLIC**, and `refs/pull/1341/head` is an
**independent ref** alongside the branch ref. Closing the PR therefore un-publishes nothing, and a
branch rewrite leaves the pull ref pointing at the old commit; GitHub further documents that old
commits can persist via direct SHA, cached views, forks and clones, with full removal potentially
requiring GitHub Support.

Corrected in that file, with the evidence inline. The recommendation is unchanged and slightly
strengthened: **no option reliably removes the content**, so option 3's certain cost buys an
uncertain benefit.

The disposition is also now stated explicitly, per external supervisor review on 2026-09-11:
`POLICY_COMPLIANT=NO`, `POLICY_EXCEPTION_REQUIRED=YES`, `SECURITY_RISK_OWNER=OPERATOR`. Retaining
the receipts must be reported as a **bounded operator exception, never as compliance**. The
attestation block is staged **unsigned** — an attestation cannot be manufactured by recommending it.

---

## Defects recorded but deliberately NOT applied

Both targets are **records**. Fixing them here would corrupt the evidence; they must be fixed in
the successor working surface under supervisor authority.

| ID | Target | Severity | Observed impact on this bundle |
|---|---|---|---|
| [DEFECT-001](DEFECT-001-narration-preface-count.json) | `shared_contracts/message_arity.py` — `narration_preface_count` returns `len(kept)-1`, mislabelling suffix narration as prefix | LOW / latent | **None.** Attempt 3 had zero narration; attempt 1 turn 3 was prefix-shaped, where the formula is correct. **No committed receipt carries a wrong value.** Reproduced on a scratchpad copy — see the file. |
| [DEFECT-002](DEFECT-002-unknown-tool-event-contract.json) | `shared_contracts/W01_TOOL_EVENT_CLASSIFIER.json` — `verdict_contract` defines outcomes for *forbidden* and *zero-forbidden* events but none for an **unknown** type, despite declaring `FAIL_CLOSED_ALLOWLIST` | MEDIUM / contract completeness | **No observed misclassification** — only allowlisted types ever appeared. Whether the *implementations* fail closed on an unknown type is **UNKNOWN from these artifacts** and must be verified from source before the next dispatch. |

---

## Not done in this repair

- **No embedded audit, no PR Steward run.** Both fail at `bc4249ee`; re-running them belongs after
  this repair is reviewed, against a frozen head.
- **No review threads resolved.** That is the reviewer's or operator's action.
- **`ct route-record` / `ct validate-route`: `NOT_RUN`** — `.control-tower/` is not present on this
  branch, and AGENTS.md forbids borrowing another checkout's installation. Preserved as `NOT_RUN`,
  not simulated. The equivalent fields are captured in [`ROUTE_RECORD.json`](ROUTE_RECORD.json).
- **The disclosure attestation is NOT granted.** Staged unsigned in
  `DISCLOSURE_RECONFIRMATION.md`. **Freeze gate: do not freeze a head, run the L2 audit, or run PR
  Steward until the operator completes it.** The current head's Steward failure is expected.
- **The two blocking supervisor decisions are untouched**: the Route D budget amendment
  (`limits.codex ≥ 7`) and the Route A Terminal.app run. This repair corrects the record of what
  happened; it does not advance the benchmark.
