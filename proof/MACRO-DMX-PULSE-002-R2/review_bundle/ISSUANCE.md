# MACRO-DMX-PULSE-002-R2 — Issuance Record (revision 2, amends MACRO-DMX-PULSE-002)

**Issued**: 2026-10-23T20:50Z by the Control Tower supervisor side session (Claude Code desktop, `claude-sonnet-5-5`, effort `high`, observed via `get_session` and `$CLAUDE_EFFORT`).
**Requested by**: supervisor session `local_901ed6d9`, relaying the operator and the merge owner (instruction quoted in the macro's `operator_refs`).
**Authority**: NONE. Nothing in this package was executed, committed, pushed, signed or merged. The R1 authorization covers the R1 revision only and does not satisfy this revision.

## The two lines the operator must send

```
AUTHORIZE_MACRO_DMX_PULSE_002_R2_EXECUTION=YES
```

Runs W01, W02 and W03 up to a frozen, gate-green head and a proof-only commit, and stops. It does **not** run the audit.

```
AUTHORIZE_MACRO_DMX_PULSE_002_R2_AUDIT_ROUTE=grok-cli:grok-4.5:ONE_ATTEMPT
```

A separate gate for the one audit route proposed below. Sending only the first line leaves the audit unrun. Sending the second line without the first does nothing. The line names the route on purpose: if the operator wants a different route, it needs a new line and a new auditor binding.

## What changed from R1 and why

The merge owner found that R1 created a new stacked repair PR and explicitly excluded #1472, so running it would add a PR without clearing #1472's finalization gate. R2 is built to qualify the **successor of #1472**.

| Topic | R1 (issued, preserved, not authorized to run) | R2 (this revision) |
|---|---|---|
| Relationship to #1472 | "optional hardening", stacked PR | The audited successor head of the whole Pulse feature; predecessor record kept as data |
| Audit subject | the delta only | the **cumulative** feature at the frozen head: `merge-base(origin/main, C)..C`, restricted to the eight content files |
| Workstreams | W01 code, W02 docs | W01 code, W02 docs, **W03 successor qualification** (deterministic closure checks, gates, lineage record, audit input; no model) |
| Custody | `feat/pulse-002-hardening` in `.worktrees/pulse-002` | the dispatching worktree and its branch, named exactly below |
| Limits | prose only | finite per-workstream and per-macro limits, all marked PROPOSED, ratified by the first line |
| Audit | route "operator-gated", unnamed | exactly one route proposed, one attempt, zero retries, raw stream custody mandatory |
| Delivery | stacked PR only | operator chooses fast-forward of `feat/pulse-001` (so PR #1472 carries the successor head) or a stacked draft PR |

R1 is untouched in `task-packets/MACRO-DMX-PULSE-002/` (hashes unchanged, listed below) and a copy sits in the shared notes folder. R1 is superseded; do not authorize it.

## Predecessor record (preserved, never relabelled)

| Fact | Value |
|---|---|
| PR | #1472 `feat/pulse-001` → `main`, OPEN, unmerged |
| Audited head | `1d2219e8c894c5929ceba6ac5f2650dfe7ba2147` |
| Signed proof head (base of R2) | `f4115046484ed0dc580cc4337bb8c7cf55d39af7` (= `origin/feat/pulse-001`) |
| Verdict | `PASS_WITH_RISKS`, **Q3 = FAIL on F1** (Grok `grok-4.5`, tool-less, operator-approved route) |
| F1 | accepted by the operator as a disclosed residual risk on 2026-10-22; that record stays |
| Files that must be byte-identical at R2's frozen head | `proof/MACRO-DMX-PULSE-001/{PROOF.json,PROOF.json.sig,AUDITOR_REPORT.md,review_bundle/GROK_ADJUDICATION.md,review_bundle/GROK_AUDIT_RESPONSE.txt}` and `proof/pr_merge/embedded-audit/pr-1472/{PROOF.json,PROOF.json.sig}` (W03 closure checks 4 and 5) |

The existing signed proofs and the attestation for #1472 do **not** cover R2. The new audit's verdict is its own record; the old verdict is not edited, combined with "superseded", or upgraded. If the new audit finds F1 repaired, it says so in `predecessor_findings`; that is a new fact beside the old one.

## Exact custody

| Item | Value |
|---|---|
| Worktree | `/Users/hue/code/dopemux-mvp/.claude/worktrees/pulse-f1-001-5a321f` (the dispatching worktree, as the supervisor directed) |
| Branch | `claude/pulse-f1-001-5a321f`, local only |
| Base / HEAD at start | `f4115046484ed0dc580cc4337bb8c7cf55d39af7`, porcelain shows only the two untracked `task-packets/` directories |
| W01 writer | Sonnet child: `plugins/dopemux-pulse/hooks/register.tsx`, `plugins/dopemux-pulse/hooks/register.test.ts` |
| W02 writer | Haiku child: `plugins/dopemux-pulse/README.md`, `docs/02-how-to/pulse-status-line.md` |
| W03 writer | team lead, local-shell, no model: 18 flat files under `proof/MACRO-DMX-PULSE-002-R2/review_bundle/` |
| Commits | team lead only, explicit pathspec: **C1** (W01), **C2** (W02) = the content head **C** the audit freezes, **P** (W03) a proof-only successor |
| Rollback | `git revert` in reverse order (P, C2, C1). No reset, no force-push. Deleting branch or worktree is an operator gate |
| Out of bounds | `services/adhd_engine`, `src/`, `.claude/`, `proof/MACRO-DMX-PULSE-001/`, `proof/pr_merge/embedded-audit/pr-1472/`, the R1 package |

The package stays untracked until W03 flattens a copy into the bundle (the preflight rejects GEC v2 packets under `task-packets/` in a PR).

**What ran under R1 (recorded, not hidden)**: W01 (`claude-sonnet-5-5`, via the Agent tool) was dispatched twice and stopped twice by the supervisor before it returned anything; `git diff` was empty both times (patch sha256 `e3b0c442…b855`, the empty-file hash). Observed model identity: `UNKNOWN`. Child bindings for the R1 ids were recorded in the local state and are not reused. Nothing else ran: no W02 dispatch, no commit, no gate.

## Workstreams and TP_ROUTE

| WS | Scope | Deps | Route |
|---|---|---|---|
| W01 | **Guard-lifetime/race fix (F1, audit Q3)**: hold the in-flight guard until `$.http.fetch` settles; `unreachable` still shown after 2 s; late answer discarded; no unhandled rejection; no timer leak; five non-vacuous tests with the existing slow-fetch mock plus mutation checks. Bounded F6 (toast a refused `command.register`) | — | `claude-sonnet-5-5` pinned, no fallback |
| W02 | F3 (`/done` also resets the continuous-focus count), F4 (drop the commit SHA), as-built notes | W01 | `claude-haiku-5-5`; `claude-sonnet-5-5` only as the one repair, on a supervisor-accepted evidence-backed STOP |
| W03 | Successor qualification: 5 closure checks, gates at C, lineage record (verdict preserved verbatim), cumulative + delta frozen diffs, audit prompt from the pinned template, `SHA256SUMS`, one proof-only commit | W02 | `local-shell`, model `NONE` |

```
TP_ROUTE   (coordinator / issuing supervisor)
runner=claude-code-desktop
model=claude-sonnet-5-5
effort=high
skills=task-packet,plugin-authoring
why=Session model and effort observed (get_session, $CLAUDE_EFFORT); coordination of a bounded successor macro; Opus is escalation-only under AGENTS.md section 5 and nothing has failed.
```

```
TP_ROUTE   (W01 implementer)
runner=claude-code-agent
model=claude-sonnet-5-5
effort=UNKNOWN
skills=plugin-authoring
why=Promise-lifetime and race logic in an early-access hook API is not a Haiku-tier slice; Sonnet is the cheapest adequate candidate, no fallback; effort is not settable per child from this runner.
```

```
TP_ROUTE   (W02 implementer)
runner=claude-code-agent
model=claude-haiku-5-5
effort=UNKNOWN
skills=NONE
why=Docs wording derived from committed code with deterministic checks (docs hooks, no-hash grep, line cap) is the cheapest adequate slice; the Sonnet fallback is named, single-use and supervisor-gated.
```

```
TP_ROUTE   (W03, team lead)
runner=local-shell
model=NONE
effort=NONE
skills=NONE
why=Ancestry, file-set, hash, gate and diff work is deterministic; a model call would add cost and no evidence.
```

```
TP_ROUTE   (final audit, PROPOSED only, held)
runner=grok-cli
model=grok-4.5
effort=high
skills=independent-audit
why=The route that already produced an independent verdict for #1472, available without waiting for the Gemini quota; different family from the Anthropic implementers; tool-less recipe; one attempt, no fallback.
```

## The one proposed audit route (propose, do not run)

`AUDITOR_BINDING_PROPOSED.json` (validated with `ct validate-binding`, **not** recorded, not selected, not run).

- **Route**: `grok-cli`, `grok-4.5`, effort `high`, the tool-less recipe (`reference_grok_cli_contained_audit_recipe`): sealed empty directory holding only `AUDIT_PROMPT.txt`, no repository mount, no secrets, 45 disallowed tool ids, no-skills system prompt. Independence class `DIFFERENT_FAMILY` (Anthropic implementers). Provider-attested identity `UNKNOWN`; the previous run self-reported `grok-4`.
- **One attempt, zero retries, no fallback route.** A launch or quota failure stops and reports; any other route needs a new operator line and a new binding.
- **Subject**: the cumulative diff of the eight content files at the frozen head C, plus the lineage context. The prompt is `AUDIT_PROMPT_TEMPLATE.txt` (pinned below) filled by W03; the operator can read the template before approving. It asks Q1–Q11 (the old Q1–Q10 re-asked on the whole feature, Q3 and Q5 extended to the guard, Q10 per-finding closure) and a `predecessor_findings` table. The earlier findings are given as claims to re-test, not as conclusions.
- **Custody (the lesson from #1472)**: prompt, raw event stream, `init.tools`, response, run record and hashes are copied into `proof/MACRO-DMX-PULSE-002-R2/review_bundle/` in the same hour. If the raw stream is not saved, or `init.tools != []`, the audit is void and no verdict is read.
- **Alternative the operator may prefer**: `agy gemini-4-argon-high` (a second family, independent of the first auditor too), but it returned 429 and resets about 2026-10-24T03:30Z; `gemini-3.1-pro-high` is absent. Choosing it means a new auditor binding and a different route line. This session did not choose for you.
- Dry-run check at issuance: the prompt rendered against the current `f4115046` content is 56,176 bytes (limit 150,000; the PULSE-001 prompt was 52,805).

## Finite limits and numeric allowances (all PROPOSED; one batch)

Full detail in `ALLOWANCES_PROPOSED.json`. Neither the merge owner nor the operator had recorded numeric allowances for these macros, so nothing below exists until the first AUTHORIZE line ratifies it. They are coordinator-enforced from timestamps and counted dispatches, not by `ct`. Basis: judgment only; no measured per-workstream history is in hand (UNKNOWN). The one measured figure is the PULSE-001 audit run, about 200 s and about USD 0.0436.

| Scope | Active (min) | Elapsed (min) | Dispatch attempts | Repair attempts | Review rounds | Model calls | Tokens |
|---|---:|---:|---:|---:|---:|---:|---|
| W01 (Sonnet) | 45 | 90 | 1 | 1 | 2 | ≤2 | ≤500,000 child (if reported) |
| W02 (Haiku) | 20 | 45 | 1 | 1 | 2 | ≤2 | ≤150,000 child (if reported) |
| W03 (local-shell) | 30 | 60 | 1 | 0 (1 deterministic rerun for an environmental failure) | 1 | 0 | n/a |
| **Macro total** | **95** | **240** | **4 dispatches** | **2** | **5** | **4 child + 1 audit** | ≤650,000 child; coordinator tokens UNKNOWN, not enforced |
| Audit | 20 | 60 | 1 attempt | 0 retries | — | 1 | prompt ≤150,000 bytes, cost ≤USD 1.00 (if reported) |

Semantics: "active" is worker or team-lead working time, "elapsed" is wall clock from dispatch to return; both exclude operator-gate waits. Review rounds before freeze: at most 2 per child. After freeze, a semantic change invalidates the audit and needs a new operator line; proof-only commits do not. After an audit FAIL or NEEDS_SUPERVISOR there is no automatic repair loop. Exceeding any figure: STOP and NEEDS_SUPERVISOR with evidence, no self-extension. The two stopped R1 W01 dispatches are proposed **not** to count against R2.

## Pinned package members (SHA-256)

| Member | SHA-256 |
|---|---|
| `MACRO_PACKET.json` | `b85ab8ec4a17c75a967da1daca5f5264f172e035315167775cbde0e5162df28d` |
| `EXECUTION_BINDING.json` (coordinator) | `2949b99edcfe760fa05727ff2913d304bfd5cfd24d2997831a3b6cddc59e0784` |
| `WORKSTREAMS/W01/TASK_PACKET.json` | `9cc3bc5a6b1bc9280585d4c818c3d46fe7281a41ca5876e438935b826552feb1` |
| `WORKSTREAMS/W02/TASK_PACKET.json` | `fae519f6da53926134fe70a6aea405298322ed3f464abc269a1035eb2ca1b6d8` |
| `WORKSTREAMS/W03/TASK_PACKET.json` | `92070ac216069a43e153ef126a92f3f4f95feb3a16f82b0591c91dbfc798b869` |
| `AUDIT_PROMPT_TEMPLATE.txt` (pinned inside the W03 packet) | `7b0ee9d3dde9ba564e73898eccf14e0fd55927b934bc7350a54d09ccab00d30d` |
| `AUDITOR_BINDING_PROPOSED.json` (proposal, not pinned by the macro) | `b07e9b990d87a5b1d33c6f9c5c2c37db5143471f142113468e630f6a98c3979b` |
| `ALLOWANCES_PROPOSED.json` (proposal, not pinned by the macro) | `3d7fedc466723e68f26123b7b085717a7a53841898054b653c637619d99f572d` |

R1, preserved unchanged in `task-packets/MACRO-DMX-PULSE-002/`: `MACRO_PACKET.json` `35aaf353a4dba1bd4b0926052af739dc77679d71f05c4bbb243f0263865fbae2`, `EXECUTION_BINDING.json` `f64a5b10ff9b17a96308b26556047e0e77931f2320d3a3350271f009fedb1ed6`, W01 `465dcf0033da5627e39afeaa5b8a42536938063a6b2ae0274d7903d617373c72`, W02 `ceea9408728d37d9d5db079c9a49fd99b6895399f3a430c0d75cc9a07e4e13fc`, `ISSUANCE.md` `42fdcf1a42da89b9c3d6cb9b320dd132d362a64e73028b0ddd5fc0a3453c5b30`.

This file is not referenced by the macro and is not part of the pinned subject.

## Validation at issuance

| Check | Result |
|---|---|
| `ct bind-record` coordinator binding | PASS (state file `MACRO-DMX-PULSE-002-R2.json`, local, noncanonical) |
| `ct validate-binding`, coordinator (package and state file) | PASS |
| `ct validate-binding`, `AUDITOR_BINDING_PROPOSED.json` (validated only, not recorded) | PASS |
| `ct validate-macro --file MACRO_PACKET.json` | PASS, `STATIC_VALID`, 0 errors |
| `task_packet.v2` schema W01, W02, W03 | PASS ×3 |
| Audit-prompt dry run on the current content | PASS: one placeholder per field, 56,176 bytes |
| Closure check (3) dry run | after finding that #1472 also carries `proof/pr_merge/embedded-audit/pr-1472/**`, the check now allows exactly that path and `proof/MACRO-DMX-PULSE-001/**`, both required unchanged |
| R1 package bytes | unchanged (hashes above re-verified after the build) |
| Child bindings for R2 | NOT_RUN by design: recorded at dispatch |
| DCP route, Task Orchestrator, Universal Router, Audit Broker | NOT_RUN (task-orchestrator unreachable) |
| Live Pulse runtime check (engine on `127.0.0.1:3025` plus `claude --plugin-dir plugins/dopemux-pulse`) | NOT_RUN; the operator's step; F2 stays open and is not claimed repaired |

## Remaining uncertainty (state plainly)

- **Whether this clears #1472's finalization gate is UNKNOWN.** R2 produces the evidence and a successor head; it does not claim readiness. The signed attestation for #1472 sits at `proof/pr_merge/embedded-audit/pr-1472/` bound to the old head; a successor head needs its own attestation and signing, which is outside this macro (`sign_proof` is forbidden here) and must not overwrite the old one. How the PR Steward and the CI audit gate treat two heads under one PR is for the operator and the Steward to decide.
- **Delivery vehicle is open**: fast-forwarding `feat/pulse-001` (PR #1472 then carries C and P, no force-push needed because C descends from the current head) versus a stacked draft PR based on `feat/pulse-001`. Either is a push the macro does only after the audit and the operator's confirmation.
- The F1 fix cannot cancel an abandoned request (no abort option in this build's declaration); if the host never settles one, polling pauses. The host timeout is UNKNOWN. This is disclosed in code, docs and the audit prompt.
- The previous audit's containment is attested, not reproducible; R2 makes raw-stream preservation a hard condition.
- Time and token numbers are PROPOSED estimates without measured history.

## Execution outline (after the first line)

1. Preconditions: HEAD `f4115046…`, porcelain as above, PR #1472 OPEN at that head, R2 hashes verified. Load `plugin-authoring` and keep the `claude-code.d.ts` path for W01.
2. `ct bind-record` and `ct validate-binding` for W01 and W02 (the coordinator binding is already recorded in this worktree's state).
3. Dispatch W01 (Sonnet). Re-read the diff, re-run `claude plugin validate/test` and the mutation checks myself, commit **C1**.
4. Dispatch W02 (Haiku). Re-read the diff, run the docs hooks from the primary checkout's venv and the no-hash grep, commit **C2** = **C**. Freeze.
5. Run W03 myself: closure checks, gates, lineage, diffs, prompt, hashes; commit **P**. Copy the R2 package and the pack to the shared notes folder. **STOP.** The audit is not run.
6. Only after the second line and a fresh preflight: one audit attempt on the named route; preserve every artifact; then an operator-gated closure (new `PROOF.json` with `packet_id`, signing, push) outside this macro.

## Out of scope

`services/adhd_engine` (including `session_minutes`, F5 and F7), F2 (the live runtime check), editing, re-signing or re-labelling anything for #1472, the Memory Bridge and Route Ledger mods, and any merge.
