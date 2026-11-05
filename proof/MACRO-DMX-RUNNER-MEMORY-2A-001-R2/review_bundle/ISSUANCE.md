# MACRO-DMX-RUNNER-MEMORY-2A-001-R2 — Issuance Record (revises R1 after W00)

**Issued**: 2026-10-31 by the Control Tower supervisor session that issued and ran R1 (Claude Code desktop, `claude-opus-5-5`, effort `xhigh`).
**Why**: R1's read-only W00 rated W01, W02 and W05 NO_GO and found 16 design changes naming every build workstream, so J01-GATE held them all (`J01_GATE.md`). The operator ruled on the three blocking questions the same day (`OPERATOR_RULINGS_R2.md`).
**Design**: `docs/91-rfc/rfc-2026-10-30-runner-memory-parity-2a.md` **revision 2**, commit `5335a9e7d`, sha256 `c83aea50bb6bbf98160311c6b46a5ef3fc1741a130705cd955163bf4610734ed`, status **draft**. Revision 1 stays at `77b4052f7`.
**Evidence**: R1's `W00_FINDINGS.md`, sha256 `4baa2184923bf0522d2ebb930c09d3e9eb394920c5ac4451f69f2ad0c4d1f117`, fixed input (not re-run).
**R1 is preserved unchanged** and superseded. Its authorization covers R1 only. Base `97b6d5040` (= origin/main). Authority: NONE. **Nothing in R2 has run.**

## Execution gate

```
AUTHORIZE_MACRO_DMX_RUNNER_MEMORY_2A_001_R2_EXECUTION=YES
```

Approves design revision 2 at the sha256 above and authorizes W01-W09 inside this packet.

### Operator gates inside the run (not granted by the line above)

1. **Accept ADR-227** after W09 drafts it (J01-CARVEOUT). Until then nothing under a red-lane path is edited.
2. **If W09 reports the carve-out is not effective for edits in this worktree** (the Claude Code guard may load the rules from the checkout the session started in), approve a small carve-out PR to `main` first, as ADR-224 did (#1193). W09 finds out; nobody tests it by attempting a red-lane edit.
3. **Run the keychain ACL procedure** (W00 findings section 6) before W03; the team lead records the result in `KEYCHAIN_ACL_RESULT.md`.

Still separate afterwards: push or PR, signing, the audit route, token issuance, the ConPort migration, switching servers to `enforce`, accepting the ADR-MCPINT-002 amendment, the live Codex acceptance run, merge.

## What changed from R1

| R1 | R2 |
|---|---|
| Three servers incl. task orchestrator 4.0.0 | dope-memory and ConPort only; the orchestrator moves to Wave 2C (upstream 4.0.0 unreleased; 4.0 drops every 3.x tool this repo calls) |
| No red-lane handling | **W09** first: ADR-227 and file-exact exemptions for exactly 20 files under `services/working-memory-assistant/`, `docker/mcp-servers-source/conport/` and `services/dopecon-bridge/` |
| G2 "every call" | G2 on HTTP writes; local ledger/Redis writers record self-asserted principals (**W06**) |
| W08: 4 internal callers | **W05**: 11 HTTP writers incl. the two dopecon-bridge files; the Python task-orchestrator service and `pm/adapters/conport.py` are listed as known unverified writers before enforce |
| `compose.yml` env | `src/dopemux/mcp/docker_runtime.py` (the generated sidecar override) |
| ConPort transport open | streamable-HTTP app beside `sse_app()` (W00 confirmed) |
| `migration_runner.py` | ledger migration `chronicle/migrations/v1_3_0_add_write_principal.sql` (auto-applies); ConPort `008_write_principal.sql` + `008_rollback.sql` (operator-run) |
| Generator gate had an orchestrator check | two checks (memory servers in enforce, keychain token); Claude Code rendered by `mcp init`/`ensure` |
| W00 investigation | done; pinned as evidence |

## Workstreams and order

| ID | Work | Lane | Runs after | Caps (min / tokens / tool uses) |
|---|---|---|---|---|
| W09 | Red-lane carve-out: ADR-227, `red_lane_rules.py`, guard tests; reports whether the exemption is effective in this worktree | L3 | — | 90 / 1.0M / 200 |
| W03 | `dopemux auth` + keychain/hash helper (after the keychain procedure) | L2 | — | 90 / 1.0M / 200 |
| W01 | dope-memory identity, auth modes, principal migration, health fields, CI test, `eventbus_consumer.py` | L3 | W09 + ADR accepted | 120 / 1.5M / 300 |
| W04 | Stdio bridge: envrc ports, token, streamable handshake, fail closed | L2 | W03 | 90 / 1.0M / 200 |
| W02 | ConPort identity, auth on three surfaces, streamable app, migration, proxies forward tokens | L3 | W09 + ADR accepted, W01 | 150 / 1.8M / 350 |
| W06 | Local writers record self-asserted principals | L3 | W01 | 60 / 0.6M / 150 |
| W05 | HTTP internal callers send their principal's token | L3 | W09, W01, W02, W03 | 120 / 1.5M / 300 |
| W07 | Generator gate, Codex + Claude Code rendering, catalog | L3 | W01-W04 | 120 / 1.5M / 300 |
| W08 | How-to (every operator step with rollback), agent docs, ADR-MCPINT-002 amendment draft | L2 | all others | 60 / 0.6M / 150 |

Serialized (`max_mutating_workstreams` 1, overlap fail-closed). W03 and W09 touch no red-lane path, so they can run while ADR-227 waits for acceptance. Joins: J01-CARVEOUT (W09 + operator) → J02-SERVERS (W01-W04) → J03-CALLERS (W05-W07) → J04-FREEZE (all, then the single final L3 audit).

## Package members (the macro pins each child and the binding)

| Member | SHA-256 |
|---|---|
| `MACRO_PACKET.json` | `b7ffb0833774728a0e59d1f6a54f0a44c6a726ab9c943b029d339562696fd491` |
| `EXECUTION_BINDING.json` (issuer) | `b30ddedde5ae34480ed5a3abc826519bd6b6fdc1a1a6233410215427fddb7988` |
| `WORKSTREAMS/W01/TASK_PACKET.json` | `13df3077d375f9025bba412ca74c0a781091a11bc5982f6a94f2b528f175299f` |
| `WORKSTREAMS/W02/TASK_PACKET.json` | `32ceb92486f43138b779a492df6125f0b60c4184c20c209eaa2fdef119f83920` |
| `WORKSTREAMS/W03/TASK_PACKET.json` | `3ec7088f63cc95a12374c982d27dc747c7168506ad102ab2b41874af1142c1fb` |
| `WORKSTREAMS/W04/TASK_PACKET.json` | `eab7da27177386ac320fa5ddecef14ce0c399bf352d57f2df389ed05b49db659` |
| `WORKSTREAMS/W05/TASK_PACKET.json` | `d2c795d69e83b186f5736c8fc536e4718a16e40667ec0d0bf58bd690af4e6751` |
| `WORKSTREAMS/W06/TASK_PACKET.json` | `9cc54dfee22dd671af7d8d4d01b967f221b06b46478a54889d37b127a88efe7f` |
| `WORKSTREAMS/W07/TASK_PACKET.json` | `3ff53b854e78aa3e97646033bd8d4e7f7236e523faf98bd896726e1ab457ba11` |
| `WORKSTREAMS/W08/TASK_PACKET.json` | `db7573ca277428a5bebb5df05012cad721ee95f2ec5952cca997b631a27a463e` |
| `WORKSTREAMS/W09/TASK_PACKET.json` | `f574532bc485ba3859b7ccdf3032cf2ae51c611a8bba5b13c4b5134e37e167f5` |

## PROPOSED allowances

Macro: 18 h to a frozen head (operator gates and the audit excluded); 12,000,000 subagent tokens; 12 dispatches (9 + at most 3 retries); 4 correction rounds; intermediate model audits 0; `advisor` 0 for every child and the coordinator; one final independent audit outside this budget. Basis: R1's W00 used 411,169 tokens, 120 tool uses and 18.6 min for a 12-question investigation, well inside its cap; build caps follow the Memory Bridge R2 precedent scaled by file count. Caps, not forecasts. As before, `macro_packet.v2` has no allowance fields, so the team lead enforces them.

## TP_ROUTE

```
TP_ROUTE   (issuer)
runner=claude-code-desktop
model=claude-opus-5-5
effort=xhigh
skills=task-packet
why=revising an L3 macro after a no-go investigation; red-lane and identity-scope judgment stays with the supervisor

TP_ROUTE   (W01-W09)
runner=claude-code-agent
model=claude-sonnet-5-5
effort=UNKNOWN
skills=NONE   (TDD required by invariant)
why=bounded implementation against explicit B-rules and pinned W00 evidence; Sonnet ran W00 at about a quarter of its token cap

TP_ROUTE   (final audit, held until J04-FREEZE)
runner=UNKNOWN   (operator picks per run)
model=UNKNOWN
effort=UNKNOWN
skills=independent-audit
why=one independent L3 audit, different family from the Claude implementers
```

## Validation at issuance

| Check | Result |
|---|---|
| `task_packet.v2` schema, W01-W09 | PASS ×9 |
| `ct validate-macro` | PASS, STATIC_VALID |
| `ct bind-record` + `ct validate-binding` (issuer) | PASS |
| Macro pins | MATCH |
| Design rev 2 docs hooks | PASS (markdownlint NOT_RUN: its Node install fails on a `27.0.0-alpha` version) |
| Child bindings | NOT_RUN: created per child at dispatch |
| Live behaviour of any service | NOT_RUN |

## Decision for the operator

Approve design revision 2 and authorize R2 with the line above, or say what to change first.
