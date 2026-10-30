# MACRO-DMX-RUNNER-MEMORY-2A-001 — Issuance Record

**Issued**: 2026-10-30 by the Control Tower supervisor session (Claude Code desktop, `claude-opus-5-5`, effort `xhigh` from `$CLAUDE_EFFORT`).
**Design**: `docs/91-rfc/rfc-2026-10-30-runner-memory-parity-2a.md`, sha256 `1fea60130d55d151dfbc70eb24571efb90c8ecee9e9183a05f3beb0915970cd3`, status **draft**. This packet does not edit it.
**Base**: `97b6d5040496e2271c41d24c339d039303bbe6b1` (= origin/main = merge-base). Branch `feat/runner-memory-2a`, worktree `.worktrees/runner-memory-2a`. Authority: NONE. **Nothing in this packet has run.**

## Execution gate

```
AUTHORIZE_MACRO_DMX_RUNNER_MEMORY_2A_001_EXECUTION=YES
```

One line approves the design at the sha256 above **and** authorizes W00-W08 inside this packet. W00 is read-only. W01-W08 are dispatched only after J01-GATE, and only for workstreams W00 rates GO or GO_REDUCED with no design change against them. A design change W00 finds becomes a revision (R2) that needs its own authorization.

### Not granted here (each stays a separate operator step)

Push or PR · signing · the final audit route · `dopemux auth issue/rotate/revoke --apply` (keychain and `~/.config/dopemux/auth/` writes) · the dope-memory and ConPort migrations on real databases · switching any server from `log` to `enforce` · the orchestrator cutover (`--apply`, `--rollback`) · accepting the ADR-MCPINT-002 amendment · the live Codex acceptance run · merge. Merge order: after #1482, #1483, #1485 and #1484 (design section 8).

## Workstreams

| ID | Work (design ref) | Lane | Runs after | Route | Caps (elapsed / tokens / tool uses) |
|---|---|---|---|---|---|
| W00 | Read-only investigation, go/no-go GATE_TABLE (W0) | L2 | — | Sonnet | 150 min / 1.8M / 350 |
| W01 | dope-memory: required ids, binding check, auth modes, principal column (W1) | L3 | W00 | Sonnet | 120 min / 1.5M / 300 |
| W02 | ConPort: required `instance_id` + `shared`, auth on every surface, transport per W00, migration (W2) | L3 | W00, W01 | Sonnet | 120 min / 1.5M / 300 |
| W03 | `dopemux auth` + shared keychain/hash helper (W3) | L2 | W00 | Sonnet | 90 min / 1.0M / 200 |
| W04 | Stdio bridge: envrc discovery, bearer token, handshake, fail-closed (W4) | L2 | W00, W03 | Sonnet | 90 min / 1.0M / 200 |
| W05 | Orchestrator 4.0.0 built not activated, cutover command, hooks (W5) | L3 | W00, W03 | Sonnet | 120 min / 1.5M / 300 |
| W08 | Internal callers send `internal:*` tokens (W8) | L3 | W00-W03, W05 | Sonnet | 90 min / 1.0M / 200 |
| W06 | Generator gate + Codex/Claude stdio-route config (W6) | L3 | W00-W05 | Sonnet | 120 min / 1.5M / 300 |
| W07 | How-to, agent docs, ADR amendment draft (W7) | L2 | all others | Sonnet | 60 min / 0.6M / 150 |

Serialized: `max_mutating_workstreams` 1, overlap fail-closed. Joins: J01-GATE (W00) → J02-SERVERS (W01-W04) → J03-INTEGRATION (W05, W08, W06) → J04-FREEZE (all; `make test`, docs hooks, preflight, then the single final L3 audit).

## Package members (the macro pins each child and the binding by sha256)

| Member | SHA-256 |
|---|---|
| `MACRO_PACKET.json` | `04d1615942d47a9f9890f9a34313b7caf3ba0337660ea1f709b8b049afcaeb08` |
| `EXECUTION_BINDING.json` (issuer) | `850798fca0c343ffd8508fbe5d050f769f9a658eb442b6989b8ad425b440ed4b` |
| `WORKSTREAMS/W00/TASK_PACKET.json` | `6ff8a9751a843fad8a3b14eaaf39fdd82857b405e39a05f4f66fa36ddf0deac8` |
| `WORKSTREAMS/W01/TASK_PACKET.json` | `c4b37d1688f74172348e4b594894e4fd217187a00984728602e0670557c86017` |
| `WORKSTREAMS/W02/TASK_PACKET.json` | `8d4a1d412468ce479fdb01e6ea56db67c5bff2d86475107c3a2eb4c17e1bbd56` |
| `WORKSTREAMS/W03/TASK_PACKET.json` | `61abf5e6d0af980177328ae9751edcd3d29d92817134bf70b4906d644f9c8fce` |
| `WORKSTREAMS/W04/TASK_PACKET.json` | `9bf153949c93eb848d1f30a29044eebd41099c599f9e3225cf92698e29ef583d` |
| `WORKSTREAMS/W05/TASK_PACKET.json` | `a8f10b32df650a408c617d4e05d2e15c658b9c1955c12d8083fe6fed34d83032` |
| `WORKSTREAMS/W06/TASK_PACKET.json` | `fde92b5b91bd1cc3e6f5333370e9a022e1071a251d7862539b23b541a65eede8` |
| `WORKSTREAMS/W07/TASK_PACKET.json` | `05c91a07e07821f476de2145d2bb02c10db7e148c546e5a9567e14d2ebb3e496` |
| `WORKSTREAMS/W08/TASK_PACKET.json` | `c00b56c05b7da06a14da9e1a6b3d243ef374b4a300d1f864cf5077dd46c0e02d` |
| `PRE_ISSUANCE_CONPORT_PARITY.json` (evidence) | `cf7bbeed7634c67533beed9e58b6d954d082463826c2a0aa24cff26460c1fc91` |
| `conport_parity_probe.py` (evidence) | `8f70cdc7958c9f1c3242b4aab281dd438243e450c5cf31181506f0857b4b3e05` |

## Pre-issuance evidence: ConPort transport (design 5.4)

A read-only probe (handshake and `tools/list` only, no tool call) on 2026-10-30 against this worktree's ConPort (REST host `:3019` = container 3004, SSE host `:3007` = container 3005):

| | REST JSON-RPC `POST /mcp` | SSE |
|---|---|---|
| `initialize` | `-32601 Method not found` | answered (`conport 1.30.0`) |
| Tools | 13, all prefixed `conport_` | 17, unprefixed |
| SSE only | — | `fork_instance`, `promote`, `promote_all`, `workspace_summary` |

`src/dopemux/mcp/http_stdio_bridge.py` forwards every message, `initialize` included, unchanged. So design 5.4's condition ("if `:3004` exposes the same tools, the bridge targets it") is **not met** on this evidence: the indicated branch is W2 adding a streamable-HTTP app. Three of the SSE-only tools write, so auth must cover them (W02 B01). This is the supervisor's observation, recorded as W00 input (R06), **not** W00's result; W00 confirms or refutes it in source.

## Calls made at issuance (supervisor's, within the design)

1. **W04 runs after W03.** The design lists W1-W4 as independent after W0; the bridge reuses W03's keychain helper (W03 B04: no other module reads the keychain), so W04 depends on W03.
2. **W02 after W01, W08 after W05.** They share `compose.yml` and `native_hooks.py`; `ct validate-macro` rejected them as parallel until ordered.
3. **The cockpit client is outside W08's allowlist.** Its path is unknown; W00 Q10 finds it and a revision adds it. Fails closed.
4. **The ADR amendment is a new file** (status proposed); the accepted ADR file is not edited.
5. **The cutover command** lives at `src/dopemux/commands/orchestrator_cutover_commands.py` with `--dry-run` as the default.
6. **W00 never pulls the 4.0.0 image** (a download); it reads upstream source on GitHub and marks image-level facts NOT_RUN. **W00 never touches the keychain**; it writes the operator procedure for the prompt test.
7. **W07 routes to Sonnet, not Haiku** (precedent used Haiku for docs): it drafts the ADR amendment text, which is judgment, not transcription.

## PROPOSED allowances (accepted only by authorizing the macro)

- **Macro**: 18 h wall time from authorization to a frozen head (operator gates and the audit excluded); 12,000,000 subagent tokens; 12 dispatches (9 + at most 3 retries); 4 correction rounds; intermediate model audits 0; `advisor` 0 for every child and the coordinator; final independent audit 1, outside this budget.
- **Per workstream**: the table above; 1 attempt + 1 retry; 1 diff re-read + at most 1 correction round.
- **Basis (judgment, cost UNKNOWN)**: Memory Bridge W01 (12 questions) used about 336k tokens and 816 s; W00 has 12 broader questions plus GitHub reads, so about 5× tokens. Builds scale from the Memory Bridge R2 caps (1.2M, 90 min) by size: the three L3 server/orchestrator/generator workstreams get 1.5M and 120 min. Caps, not forecasts.
- **Enforcement gap** (as in the precedent): `macro_packet.v2` has no allowance fields, so the numbers live in each child's A01-A03, the macro `base_policy` and `final_audit_policy`. `ct validate-macro` does not check them; the team lead does.

## TP_ROUTE

```
TP_ROUTE   (issuer)
runner=claude-code-desktop
model=claude-opus-5-5
effort=xhigh
skills=task-packet
why=L3 macro with security-sensitive identity and a cross-repo cutover; issuance keeps that judgment with the supervisor

TP_ROUTE   (W00)
runner=claude-code-agent
model=claude-sonnet-5-5
effort=UNKNOWN
skills=NONE
why=read-only investigation needing source tracing and go/no-go judgment; Sonnet completed the Memory Bridge W01 equivalent within budget; Haiku too weak for verdicts

TP_ROUTE   (W01-W06, W08)
runner=claude-code-agent
model=claude-sonnet-5-5
effort=UNKNOWN
skills=NONE   (TDD required by invariant, not by skill preload)
why=bounded TDD implementation against explicit B-rules and W00 evidence; security judgment stays in the packet and the final audit

TP_ROUTE   (W07)
runner=claude-code-agent
model=claude-sonnet-5-5
effort=UNKNOWN
skills=NONE
why=docs derived from committed files plus an ADR amendment draft that needs precise wording

TP_ROUTE   (final audit, held until J04-FREEZE)
runner=UNKNOWN   (operator picks AGY gemini or the contained Grok CLI recipe per run)
model=UNKNOWN
effort=UNKNOWN
skills=independent-audit
why=one independent L3 audit, different family from the Claude implementers
```

Requested vs observed: every child `model_observed` is UNKNOWN until a runtime receipt exists. `effort=UNKNOWN` because the agent runner sets no per-child effort.

## Validation at issuance

| Check | Result |
|---|---|
| `task_packet.v2` schema, W00-W08 | PASS ×9 |
| `ct validate-macro` | PASS, STATIC_VALID (first run FAIL: W01/W02 and W05/W08 write overlap; fixed by ordering) |
| `ct bind-record` + `ct validate-binding` (issuer) | PASS (record in the main checkout's gitignored `.control-tower/state/bindings/`) |
| Macro pins (9 task packets + binding) | MATCH |
| Base = origin/main = merge-base | PASS (`97b6d5040`) |
| ConPort parity probe | ran; result above |
| Child bindings | NOT_RUN: created per child at dispatch |
| Live behaviour of any service | NOT_RUN |

## State of the checkout

`task-packets/MACRO-DMX-RUNNER-MEMORY-2A-001/` is the working package and is **not committed** (preflight rejects GEC v2 packets there). The flat copy in `proof/MACRO-DMX-RUNNER-MEMORY-2A-001/review_bundle/` (this record, the macro, the binding, `W00`-`W08_TASK_PACKET.json`, the probe evidence and `SHA256SUMS.txt`) is committed on `feat/runner-memory-2a`, local only.

## Decision for the operator

Approve the design and authorize the macro with the execution-gate line above, or say what to change first.
