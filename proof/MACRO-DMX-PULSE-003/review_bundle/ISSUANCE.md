# MACRO-DMX-PULSE-003 — Issuance Record (PR #1472 update and re-audit)

**Issued**: 2026-10-30 by the Control Tower supervisor side session (Claude Code desktop, `claude-sonnet-5-5`, effort `high`, observed via `$CLAUDE_EFFORT`).
**Requested by**: the operator ("Yes, issue it", answering the follow-up offered after the Pulse R2 delivery). The route itself, "update and re-audit" instead of an admin merge, is the operator's 2026-10-29 choice.
**Authority**: NONE. Nothing in this package was executed, committed, pushed, signed or merged. This is issuance only.

## The two lines the operator must send

```
AUTHORIZE_MACRO_DMX_PULSE_003_EXECUTION=YES
```

Runs W01 and W02 and stops at the proof-only commit P3. It does **not** run the audit.

```
AUTHORIZE_MACRO_DMX_PULSE_003_AUDIT_ROUTE=grok-cli:grok-4.5:ONE_ATTEMPT
```

A separate gate that releases the held W03, the one audit attempt. Sending it without the first line does nothing.

## When to send the first line (read this before authorizing)

Every merge into `main` makes every other signed PR BEHIND again (strict up-to-date, `strict: true`, observed today). This package is **pinned** to `origin/main` = `93050d135ffc2592000c1d0edef82b2912935525` and `origin/feat/pulse-001` = `ee00d36552c6f7a8ef2b83dc0165b8de97481e5a`. If either has moved when the line arrives, the macro stops at its first precondition and spends nothing; the package is then re-issued with new pins (the generator script is saved in the shared notes folder as `build_pulse_003.py`; a few minutes' work), not adapted at run time.

Practical consequence: your merge-train plan was to land #1482 (Route Ledger) first and then re-audit Pulse against the new main. **If #1482 will merge before #1472, do not authorize this yet**: it would be stale the moment #1482 lands. Tell me when main has its final tip and I will re-pin. Right now #1482, #1483 and #1484 are all draft and BLOCKED, so main is stable and this package is valid today.

## What it does, in one paragraph

PR #1472 (`feat/pulse-001`, open, signed head `ee00d3655`) is one commit behind `main` (#1447: 63 paths, none of them Pulse paths). The signed proof is bound to the old head and a merge of `main` fails proof-only closure (`proof_only_escaped_path`), so the merged head needs its own proof and one new independent audit. This macro creates that merged head by a **non-force merge commit, no rebase, no rewritten history, no edited Pulse file**, proves the eight Pulse content files and the cumulative diff are byte-identical, builds the audit input, and (once you send the second line) runs the audit.

Dry-run evidence taken at issuance (all PASS):

| Check | Result |
|---|---|
| `git merge-tree` of `main` into `ee00d3655` | exit 0, conflict-free, tree `5667dfbfe006df07e6239f0fcabef69927b8b541` |
| Paths the merge changes vs `ee00d3655` | exactly the 63 paths `main` brought, pinned in the W01 packet |
| Eight Pulse content files in the merged tree | byte-identical to `ee00d3655` (empty diff) |
| Cumulative diff `main..ee00d3655` over the eight files | sha256 `ba5c6c92974ba3a273759c7790d159cf069446ae76b6cbd2d9430b823f35f5a8`, equal to the one the R2 audit recorded |
| Audit prompt rendered at the current head | 63,792 bytes (limit 150,000) |

## Preserved, never relabelled

| Record | Value |
|---|---|
| Audit 1 (PR #1472 at `1d2219e8c894c5929ceba6ac5f2650dfe7ba2147`) | `PASS_WITH_RISKS`, Q3 FAIL on F1; F1 accepted by the operator |
| Audit 2 (content head `b5dc04dd7d9560ed31a2dc0fd2192218c727ea01`) | `PASS_WITH_RISKS`, Q1–Q10 PASS; N1–N5 OPEN |
| Files that must be byte-identical at the merged head | the 8 proof, attestation and signature files of `proof/MACRO-DMX-PULSE-001/`, `proof/MACRO-DMX-PULSE-002-R2/` and `proof/pr_merge/embedded-audit/pr-1472/` (W02 closure check 6) |

The new audit's verdict is its own record on the merged head. The earlier verdicts are context for the auditor as claims to re-test, not conclusions.

## Exact custody

| Item | Value |
|---|---|
| Worktree | `/Users/hue/code/dopemux-mvp/.worktrees/pulse-003` (fresh; this issuing worktree is not used for execution) |
| Branch | `feat/pulse-003-update`, local only, cut from `origin/feat/pulse-001` = `ee00d3655` |
| Writer | the team lead only, local-shell, **no model** |
| W01 writes | one merge commit **M** (parents `ee00d3655`, then `main`); write surface = the 63 pinned paths |
| W02 writes | 16 flat files under `proof/MACRO-DMX-PULSE-003/review_bundle/`, as one proof-only commit **P3** |
| W03 writes (held) | 13 flat audit files plus `PROOF.json` and `AUDITOR_REPORT.md`, in two commits (custody, then verdict) |
| Rollback | `git revert -m 1 <M>` and revert of the proof commits in reverse order; no reset, no rebase, no force-push; removing the worktree or branch is an operator gate |
| Delivery (not in this macro) | a non-force fast-forward push of `feat/pulse-003-update` to `feat/pulse-001`, after the audit and your confirmation |

The coordinator binding is recorded in the *issuing* worktree's local state; W01 re-records it in the new worktree.

## Workstreams and TP_ROUTE

| WS | Scope | Deps | Route |
|---|---|---|---|
| W01 | Dry-run, then the merge commit M, byte-identity proof, gates at M, negative control (the proof-only closure is expected to fail; that is why a re-audit is needed) | — | `local-shell`, model `NONE` |
| W02 | 7 closure checks, gates, lineage record, frozen cumulative diff, audit prompt from the pinned template, `SHA256SUMS`, proof-only commit P3; then STOP | W01 | `local-shell`, model `NONE` |
| W03 | **HELD**: two content-free containment probes, the one tool-less audit, custody commit before reading, adjudication against source, unsigned `PROOF.json` and `AUDITOR_REPORT.md`, independence left unattested | W02 | `local-shell`; the audit call is `grok-cli` / `grok-4.5` |

```
TP_ROUTE   (coordinator / issuing supervisor)
runner=claude-code-desktop
model=claude-sonnet-5-5
effort=high
skills=task-packet
why=Session model and effort observed (get_session, $CLAUDE_EFFORT); Opus is escalation-only under AGENTS.md section 5 and nothing has failed.
```

```
TP_ROUTE   (W01 and W02, team lead)
runner=local-shell
model=NONE
effort=NONE
skills=NONE
why=A merge, hashes, file-set comparisons, gates and diff assembly are deterministic; a child model call would add cost and no evidence, and the previous macro showed the shell work is quick.
```

```
TP_ROUTE   (W03 audit stage, PROPOSED, held)
runner=grok-cli
model=grok-4.5
effort=high
skills=independent-audit
why=The route that produced the R2 verdict with machine-evidenced containment (init.tools == [], 0 tool_use) and is available now; different family from the Anthropic implementers; one attempt, no fallback.
```

**Model calls in the whole macro: 0 children, 1 audit** (plus two content-free containment probes that are not audit attempts).

## The one proposed audit route (propose, do not run)

`AUDITOR_BINDING_PROPOSED.json` (validated with `ct validate-binding`, not recorded, not run). Same route and recipe as the R2 audit, whose artifacts are now preserved byte-for-byte in `proof/MACRO-DMX-PULSE-002-R2/review_bundle/`: sealed empty directory with only the prompt, no repository mount, no secrets, `--disallowed-tools` built from the probe's own `init.tools` (38 ids), no-skills system prompt. Hard conditions: probe 2 must show `init.tools == []`; the raw stream is committed before it is read, and a missing stream voids the audit; one attempt, zero retries, no fallback route. The audit prompt is `AUDIT_PROMPT_TEMPLATE.txt` (pinned), asking Q1–Q12 and a `predecessor_findings` table for F1–F7 and N1–N5, with per-question verdicts restricted to PASS/FAIL/UNKNOWN (the R2 auditor put `PASS_WITH_RISKS` in Q11, which the contract did not allow).

Alternative the operator may prefer: `agy gemini-4-argon-high`, a second family independent of both earlier auditors. Its availability is UNKNOWN today (429 on 2026-10-22/23). Choosing it means a new auditor binding and a different route line.

## Finite limits and numeric allowances (all PROPOSED, one batch)

Full detail in `ALLOWANCES_PROPOSED.json`. Nothing exists until a line ratifies it (the execution line ratifies W01/W02, the route line ratifies W03 and the audit). Coordinator-enforced from timestamps and counted calls, not by `ct`. **First measured basis now exists**: the R2 macro took about 10 minutes of wall clock for both model children and about 143.6 s / USD 0.0712 for the audit stage including two probes. This macro has no model children.

| Scope | Active (min) | Elapsed (min) | Attempts | Repairs | Det. reruns | Review rounds | Model calls |
|---|---:|---:|---:|---:|---:|---:|---:|
| W01 | 15 | 30 | 1 | 0 | 1 | 1 | 0 |
| W02 | 25 | 45 | 1 | 0 | 1 | 1 | 0 |
| W03 (held) | 30 | 90 | 1 | 0 | 1 | 1 | 1 (the audit) |
| **Macro** | **70** | **165** | child dispatches 0 | 0 | — | 3 | **1** |
| Audit | 20 | 60 | 1 attempt | 0 retries | — | — | prompt ≤150,000 bytes, cost ≤USD 1.00 if reported, ≤2 probes |

Operator-gate waits are excluded from the times. Exceeding any figure, or any FAIL: STOP and `NEEDS_SUPERVISOR`; no self-extension, no repair loop. After an audit FAIL there is no automatic repair.

## Pinned package members (SHA-256)

| Member | SHA-256 |
|---|---|
| `MACRO_PACKET.json` | `94a2988b1c805c5405c5abc3f807cdf17af578f637ab9a280a28c6614f4908a8` |
| `EXECUTION_BINDING.json` (coordinator) | `c940f9a60915b454cf8dfc1dc183b5bcef43a2c328f9d3d2f86db8fffe2eaa81` |
| `WORKSTREAMS/W01/TASK_PACKET.json` | `a1cc80a0b9d4f9244517c9e7b0b8a86788bdb77950e1527608ae10052be360ca` |
| `WORKSTREAMS/W02/TASK_PACKET.json` | `8d72a3b8e639afa98895b77c12c744ab8c720a58443e39fb13aa7fb09f739cc8` |
| `WORKSTREAMS/W03/TASK_PACKET.json` | `f637ba2138e2cf8fc8e1fc443d20d4308d707601679d8f09f6ee329fd14c247c` |
| `AUDIT_PROMPT_TEMPLATE.txt` (pinned inside the W02 packet) | `9f8fddeddba1e66d7033024b14a905212a2e7f7bda13f5ffae6d9f92ebd7dbef` |
| `AUDITOR_BINDING_PROPOSED.json` (proposal, not pinned by the macro) | `04d60e5220a708375065dc7d3cbf1f6064a1bb4881d005e6eea555afc056c2e3` |
| `ALLOWANCES_PROPOSED.json` (proposal, not pinned by the macro) | `247e3b485460f698b729b14ca63d6b86c80523651e807e73c47fc61a6e126d2b` |

Earlier packages are untouched: R1 `MACRO_PACKET.json` `35aaf353…`, R2 `MACRO_PACKET.json` `b85ab8ec…` (re-verified after this build). This file is not referenced by the macro and is not part of the pinned subject. The package stays untracked; W02 flattens a copy into the bundle.

## Validation at issuance

| Check | Result |
|---|---|
| `ct bind-record` coordinator binding | PASS (state file `MACRO-DMX-PULSE-003.json`, local, noncanonical) |
| `ct validate-binding`, coordinator (package and state file) and `AUDITOR_BINDING_PROPOSED.json` (validated only) | PASS ×3 |
| `ct validate-macro --file MACRO_PACKET.json` | PASS, `STATIC_VALID`, 0 errors |
| `task_packet.v2` schema W01, W02, W03 | PASS ×3 |
| Dry-run merge, path set, byte-identity, cumulative-diff hash, prompt size | PASS (table above) |
| Child bindings | not applicable: no child is dispatched |
| DCP route, Task Orchestrator, Universal Router, Audit Broker | NOT_RUN |
| Live Pulse runtime check (engine on `127.0.0.1:3025` plus `claude --plugin-dir plugins/dopemux-pulse`) | NOT_RUN; the operator's step; N1/F2 stay open |

## Remaining uncertainty

- **Whether the PR Steward and the CI audit gate accept this chain is UNKNOWN.** The per-PR attestation `proof/pr_merge/embedded-audit/pr-1472/` is bound to `ee00d3655`; the merged head needs a new attestation, built by your sign flow (outside this macro; `sign_proof` is forbidden here).
- **A cheaper route may exist and is yours to ask for, not mine to assume**: because the Pulse files and the cumulative diff are provably byte-identical, a deterministic equivalence waiver (no model audit) might satisfy the gate if the Steward allows it. Nothing in the repository rules I read says it does, so this package follows your chosen route: a real re-audit.
- **Staleness**: any push to `main` before the delivery push makes the PR BEHIND again and costs another cycle. Land this last among the signed PRs, and deliver right after the audit.
- The F1 fix still cannot cancel an abandoned request (N2), the mod has never run live (N1), and these stay OPEN findings until you accept or repair them.
- Time and token figures are estimates with only one macro of history.

## Execution outline (after the first line)

1. Pins re-verified (`origin/main`, `origin/feat/pulse-001`, PR #1472 OPEN and BEHIND). Fresh worktree `.worktrees/pulse-003`, branch `feat/pulse-003-update`. Copy the package in, re-verify hashes, re-record the coordinator binding.
2. W01: dry-run merge → merge commit **M** → gates → negative control. STOP on any conflict, name-set difference or content change.
3. W02: closure checks, gates, pack, prompt → proof-only commit **P3**; whitespace check on the commit; copy to the notes folder. **STOP. The audit is not run.**
4. After the route line: W03 preflight, probes, the one audit attempt, custody commit, adjudication, unsigned proof. **STOP.**
5. Yours: attest independence, accept or reject N2 (and carried F2/F7), run the sign flow, then the fast-forward push of `feat/pulse-003-update` to `feat/pulse-001`, then the merge decision.

## Out of scope

Any edit to a Pulse file, repair of any finding (a repair changes the audited subject), the other PRs (#1482, #1483, #1484), `--admin` or auto merge, rebase or force-push, and the live runtime check.
