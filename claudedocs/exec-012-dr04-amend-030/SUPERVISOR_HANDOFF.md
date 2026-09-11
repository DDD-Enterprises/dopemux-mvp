# Supervisor Handoff — MACRO-DMX-DR04-EXEC-012-LIVE-DISPATCH-029

**Amendment 030** (A/D → API-metered) + **operator option "b"** (arity repair, second D attempt, Route A)
**Returned** 2026-09-10T20:15Z · **Status** `PARTIAL_RETURN_TO_SUPERVISOR`
**Corrected** 2026-09-11 from `bc4249ee` — claims only, records untouched. See [`ERRATA/ERRATA.md`](ERRATA/ERRATA.md).

---

## Headline

Route D executed live **three times** on the amended API-metered path and never produced a
research report. Attempt 3 established **why**, and the cause is not the model, not the
amendment and not the harness's arity assumption — it is a **structural defect in the frozen
retrieval budget** that would fail any model on any provider path.

Route A **never reached a provider**. It requires a macOS Terminal.app process ancestry that no
agent session can supply. Its attempt is unconsumed and everything else about it is ready.

Routes B and C are unchanged from 029.

---

## Spend: **$8.13 of the $10 ceiling** · remaining **$1.87**

772,360 input / 5,924 output tokens across Route D's three attempts = **$8.02**, plus the
API-route probe (10,902 / 21) = **$0.11**. Parallel **$0.00**, Voyage **$0.00**.

| Item | Input | Output | USD |
|---|---:|---:|---:|
| D attempt 1 | 224,907 | 1,595 | 2.33 |
| D attempt 2 | 58,065 | 392 | 0.60 |
| D attempt 3 | 489,388 | 3,937 | 5.09 |
| API-route probe | 10,902 | 21 | 0.11 |
| **Total** | **783,262** | **5,945** | **8.13** |

*The $8.28 published at `bc4249ee` was unreconciled and is withdrawn — see `ERRATA/ERRATA.md`.
One residual unknown: an earlier ~8,235-token no-schema cost-floor probe (~$0.08) has no
evidence file here and may be uncounted, so treat this as a floor.*
Token counts are exact; the $10/$50-per-million rate is **assumed, not verified**.
There is **no dollar cap in either route's code** — only turn counts. The ceiling is honoured
contractually, by the lead.

---

## The primary finding

> `limits.codex = 6` and `web_search 3 + web_fetch 3` = **6 retrieval slots**.
> In `research_loop.execute()` each turn either emits `final` **or** retrieves.
> A model that spends its full retrieval allowance consumes all six turns and has
> **zero turns left to write the report**.

**Root cause:** `request_payload()` passes the model its `retrieval_budget` but **never passes
the codex turn ceiling**; `mechanics` says only "Return final report when complete." The model
is shown one budget and judged against a second, undisclosed one.

Attempt 3 ran search/fetch/search/fetch/search/fetch — exactly 3 and 3, both ceilings hit
precisely, six schema-valid actions, **zero unapproved tool events** — and was then cut off.

**Remedy** (either, both are method amendments, **not applied**):
`limits.codex ≥ retrieval_slots + 1`, or disclose the turn ceiling in the payload.

---

## Route outcomes

| Route | Outcome | Attempt | Spend |
|---|---|---|---|
| **A** | `TOP_LEVEL_TERMINAL_REQUIRED` — never reached a provider | **UNCONSUMED** | $0.00 |
| **B** | Reused unchanged (`B_RESEARCH_RERUN=FORBIDDEN` honoured) | unconsumed | $0.00 |
| **C** | Unchanged from 029; still blocked | unconsumed | $0.00 |
| **D** | 3 attempts, all consumed, no report | consumed ×3 | $8.02 |

**Route D attempts:** 1 — arity (`CODEX_COMPLETION_AMBIGUOUS`, $2.33) · 2 — **my error**, an
incomplete archive ($0.60) · 3 — the budget defect above ($5.09).

**Route A's blocker** is `adapter/policy.py:72 top_level()`, which walks the ancestry to pid 1
and demands an executable path ending `/Terminal`. **iTerm2 fails it too** — this is not
agent-specific. Circumvention (patching the gate, faking `ps`, re-parenting) was **refused**:
each would defeat a deliberate integrity control and invalidate A as evidence.

---

## What the amendment did prove

The `openai-api` provider path works end to end — credential resolved from the child
environment via `env_key` with **no `codex login`**, `--output-schema` round-trips, tool
isolation holds, and **ten live turns** completed across three attempts (nine of them
receipted) with `UNAPPROVED_NATIVE_TOOL_EVENT_COUNT = 0` throughout.

Two further findings:

- **Prompt caching writes but never hits.** `cached_input_tokens = 0` with `cache_write ≈ input`
  on all nine receipted turns, spanning attempts 1, 2 and 3 — each turn is a fresh
  `--ephemeral` thread, so the cache key is
  almost certainly thread-scoped. ~60% of D's cost was re-sending an unchanged 233 KB prefix.
- **The served model is not attestable** from the event stream. `served_model='UNKNOWN'` is
  honest. What *is* established is narrower than previously claimed: the request pins
  `gpt-6-astra` and that id is present in the account catalogue. Catalogue presence does **not**
  attest which backend served a request and does **not** rule out provider-side aliasing or
  fallback, so `provider_fallback` stays **UNKNOWN**. The earlier "no silent fallback occurred"
  is withdrawn (`ERRATA` item E2).

---

## The arity repair — honest status

`W01/message_arity.py` — published here as `shared_contracts/message_arity.py`; see
`ERRATA/PATH_MAP.json` — imported by absolute path by **both** routes, so parity is by
construction. Regression-proven against attempt 1's real turn-3 fixture (2 messages →
`narration_preface_count=1` + a valid action) and 13 unit/route cases.

**It never fired in attempt 3.** All six turns had zero narration. Attempt 3 passed turn 3
because the model didn't narrate, not because the repair worked. That run is evidence the
repair did no harm — not evidence it works in production.

It also **relaxes a completion criterion**. If "exactly one `agent_message` per turn" was an
intended compliance criterion rather than an implementation assumption, this changes what is
being measured. That needs ratification or rejection.

---

## Lead errors — disclosed

Three, costing **$0.60** total; none consumed benchmark work.

1. **D attempt 2** — archived three directories, missed `evidence/`.
2. **A attempt 1** — authorization lacked `voyage_service_label`, a key the *consumer* reads
   that **no validator checks**.
3. **A attempt 2** — missed the `top_level()` runtime precondition.

**Common root:** each time I validated one layer and treated it as sufficient. A passing gate is
evidence the gate is satisfied, not evidence the run will proceed.

**Corrective rule now in force:** before any dispatch that writes a one-shot claim, enumerate
**from the source**, on the path *after* the claim — (1) every `O_EXCL` write target and bare
`mkdir()`, (2) every input key the consumer reads, (3) every runtime precondition. All three
checks are free.

---

## Integrity

- **Audited original 028 UNCHANGED** — 138 entries, `UNEXPECTED_FILES=1` (Route C's
  pre-existing marker only), `MISSING_FILES=0`, `HASH_MISMATCHES=0`.
- **No `__pycache__`** in either tree. All work on a revertible copy.
- **Secret scan:** **zero live credential values**. Two scans with different scopes: **245 files**
  = the full amend-030 working tree (now reaped); **75 files** = the pre-publication scan of the
  published subset, which is 76 files today because this return was written after that scan ran.
  Ten regex hits, all verified benign — four are the harnesses' own detector patterns, six are a
  synthetic fixture W07's own report annotates "Not a live credential."
- **Mutations — corrected.** *Benchmark / audited-original mutations:* **0** — the 028 surface was
  never edited and re-verified clean after every dispatch, and both packet gates were honoured for
  it. *Operator-authorized evidence-publication mutations:* **1 repository** (one commit on a new
  branch off `mvp/main` in an isolated worktree) and **1 GitHub** (branch push + this PR #1341),
  performed under an explicit operator instruction that superseded `GITHUB_MUTATION_AUTHORIZED=NO`.
  The flat "0 / 0" published at `bc4249ee` contradicted the machine return and is withdrawn
  (`ERRATA` item E3).
- **Public-repo disclosure:** nine turn receipts embed the raw `/v1/models` body (136 model ids
  each). The originals in `/private/tmp` have since been reaped, so these are the only copies and
  redaction would now destroy evidence rather than sanitise it —
  **operator re-confirmation requested**, `ERRATA/DISCLOSURE_RECONFIRMATION.md`.

---

## Decisions needed

1. **Authorize the D budget amendment** (`codex ≥ 7`, or disclose the ceiling) — *blocking;*
   without it Route D cannot produce a report.
2. **Run Route A from Terminal.app**: `RUN_ROUTE_A_FROM_TERMINAL.command` — *blocking.*
3. **Raise or confirm the $10 ceiling** — $1.87 remains and A has not run — *blocking.*
4. Consider settling (1) before spending A's single attempt: A shares `codex: 6` + 3+3 and may
   hit the same wall. Unverified.
5. Ratify or reject the arity repair as a method amendment.
6. Route C's diagnostic keychain read — carried over from 029, still open.

**Four-route comparison: NO.** A never ran, C is blocked, D produced no report. Only B has a
completed research artifact.
