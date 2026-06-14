# DR-DCP-015 DCP Tooling Layer Research

> Operator-provided deep-research result, ingested 2026-06-11 as a Phase 2/3 design input for the DX Overhaul initiative. Stored verbatim (citation markers are artifacts of the research tool). Recommendation: **BUILD_AFTER_CORE_CONTRACTS**.

## 1. Executive Recommendation

**BUILD_AFTER_CORE_CONTRACTS**

Build the DCP tooling layer, but only **after** you lock five core contracts: a red-lane taxonomy, a proof/receipt schema, mutation classes, approval artifacts, and project path/resource maps. That is the difference between "helpful packaging" and "hidden authority in a trench coat." Official Claude Code docs make the packaging story attractive: plugins can bundle skills, agents, hooks, MCP servers, LSP servers, and monitors; hooks can block tool calls deterministically; skills are prompt-loaded procedures; and slash commands are explicit operator entrypoints. But those same docs also show the footguns: `allowed-tools` in skills can pre-approve tools, `PreToolUse` hooks can skip prompts or rewrite inputs, plugin `settings.json` can switch the default agent, `channels` can inject messages into the conversation, and monitors auto-start and run unsandboxed at the same trust level as hooks. That is exactly how helper automation turns into hidden authority if contracts come later.

The right move is a staged build. **V1** should package only read-mostly skills, deterministic hooks, prompt renderers, schema/proof validators, and receipt emitters. **Not** live writers, not auto-merge, not auto-approve, not "smart" hidden fixers. NIST's AI RMF is explicitly voluntary and governance-heavy, emphasizing documented oversight, roles, monitoring, and response/recovery controls. In DCP terms: **LLMs reason, hooks enforce, CLI helpers standardize, proof records, supervisor decides.**

## 2. Tooling Surface Matrix

| Surface | What It Is | Best DCP Use | Must Not Do |
|---|---|---|---|
| Claude plugin | A shareable Claude Code package that can bundle skills, agents, hooks, MCP servers, LSP servers, monitors, `bin/`, and default settings, with namespacing and versioning. | Package the DCP layer as an installable unit with versioned skills, deterministic hooks, narrow MCP helpers, and shared validators. Make it **opt-in** and preferably disabled by default if it adds scope or cost. | Must not bundle broad live writers, auto-start risky monitors, or a surprise default-agent override that silently changes session authority. |
| Claude skill | A `SKILL.md`-based reusable workflow/instruction set; custom commands are now merged into skills and can be invoked with `/name` or, unless disabled, by Claude automatically. | Teach DCP procedures: packet authoring, audit review, architecture analysis, PR reading, cockpit operation, research intake. | Must not be the enforcement layer. Must not carry hidden mutation. Side-effectful skills should use `disable-model-invocation: true`. |
| Claude hook | Lifecycle handlers for session, prompt, tool, task, config, compaction, subagent, worktree, and stop events; `PreToolUse` can allow, deny, ask, or defer. | Deterministic guards, forbidden-path checks, explicit receipt emission, config/audit notifications, and post-edit verification. | Must not mutate silently, broadly auto-allow risky tools, or use prompt/agent hooks as the only hard control for red lanes. |
| slash command | Anything in the `/` menu: built-ins, bundled and user-authored skills, and commands contributed by plugins and MCP servers. | Explicit operator entrypoints such as `/dcp-audit` or `/dcp-proof-review` where the user knowingly invokes a workflow. | Must not be treated as a complete gate by itself; direct `/skill` invocation has its own `UserPromptExpansion` path and can bypass naïve `PreToolUse` assumptions. |
| subagent | A specialized assistant with its own context window, system prompt, tool set, and permissions; best for context isolation and parallel focused work. | Research, PR reading, architecture audit, evidence summarization, read-only exploration. | Must not own live write authority or become a laundering path for risky actions. Also, subagents should not themselves spawn subagents. |
| MCP helper | Narrow external tools/services exposed via MCP; Claude plugins can ship `.mcp.json`, and plugin MCP servers start automatically when enabled. | Read-only inspection helpers, auditable lookups, bounded one-purpose brokers behind server-side auth and logging. | Must not expose broad admin APIs or large mutation surfaces directly to the model. |
| Git hook | Native Git client/server hooks like `pre-commit`, `commit-msg`, `pre-push`, `pre-receive`. Some client hooks are bypassable with `--no-verify`. | Local commit/push gating for proof presence, commit-message structure, staged-file validation, and branch update validation. | Must not be the *only* enforcement layer, because client-side hooks are not cloned automatically and can be bypassed. |
| pre-commit hook | A multi-language framework for managing hook installation/execution across stages like `pre-commit`, `pre-push`, and `commit-msg`. | Share cross-project validators for schemas, formatting, proof checks, staged file policies, and CI parity. | Must not hide side effects or replace server-side/CI enforcement for critical policy. |
| Codex wrapper | A noninteractive `codex exec` workflow with explicit sandbox/approval modes, JSONL output, and optional rules evaluation. | Reproducible read-only audits, CI proof generation, bounded refactors in isolated runners, secondary-model review. | Must not inherit uncontrolled local config in automation, run with `danger-full-access`, or become a backdoor live writer. |
| `dopemux dcp` CLI helper | **Recommended DCP surface**, not an official existing product: a deterministic project CLI that standardizes checks, prompt rendering, evidence packing, and acceptance records. | Own the boring-but-critical stuff: preflight, status, red-line evaluation, proof verification, evidence bundling, and explicit supervisor acceptance recording. | Must not impersonate approval, silently call live writers, or collapse "helper" into "governor." |

## 3. Deterministic vs LLM-Driven Split

| Function | Deterministic Hook/CLI | LLM Skill/Prompt | Why |
|---|---|---|---|
| Forbidden path detection | Yes | No | Path classes, globs, and explicit deny lists are rule logic, not judgment. `PreToolUse` can block before `Write`/`Edit` run. |
| Destructive or out-of-scope shell detection | Yes | No | Command prefix checks and network/destructive command rules should be deterministic, like Claude `PreToolUse` and Codex rules. |
| Schema validation | Yes | No | Validators are repeatable and machine-checkable; do not ask an LLM whether JSON conforms when a schema tool can answer. |
| Proof completeness check | Yes | Yes, advisory | Deterministic layer checks required fields/artifacts/hashes; an LLM can review whether the proof is intelligible or persuasive, but not whether the mandatory pieces exist. |
| Receipt generation and hashing | Yes | No | Receipts are audit records. IDs, timestamps, hashes, exit codes, paths, and parent-child linkage should be emitted by tooling, not narrated by a model. |
| Red-lane classification | Yes, for known lanes | Yes, for gray-area recommendation only | Obvious lanes should be blocked by rules. An LLM can help classify ambiguous intent, but only to recommend `ask`/`warn`, never to override a deterministic deny. |
| Task-packet drafting | No | Yes | This is synthesis, scope framing, and instruction compilation—classic skill territory. |
| PR / issue / architecture synthesis | No | Yes | Judgment-heavy reading and summarization; fits skills and subagents, especially when context isolation matters. |
| Post-edit test execution | Yes | No | Running tests is deterministic. If long-running, use async hooks or CLI, but async hooks cannot block the action that already happened. |
| Final approval decision | No | No | Supervisor-only. Humans decide. |
| Prompt rendering | Yes | Yes, content source | The render itself should be deterministic templating in CLI; the substance can come from an LLM-authored skill or packet. |
| Live external writes | Yes, but only through explicit dedicated wrappers | No direct live writes from skills | External mutations need narrow, auditable command paths with explicit approval artifacts—never open-ended model freedom. |

## 4. Recommended DCP Plugin Package

The DCP plugin should be **source-first** and **runtime-compiled**. The authoring layout below is a good human authoring layout, but it is **not** the literal Claude runtime layout. Official Claude runtime expects `.claude-plugin/plugin.json`, `hooks/hooks.json`, and `.mcp.json`; `commands/` is legacy, and new command-like workflows should be authored as skills. So use the requested tree as the **source package**, then compile it into the official plugin layout at build/install time.

```text
dcp-control-plane-plugin/
  plugin.json
  skills/
  hooks/
  commands/
  agents/
  mcp/
```

**Recommended source-to-runtime mapping**

- `plugin.json` → generate `.claude-plugin/plugin.json`
- `skills/` → ship directly
- `hooks/` → compile to `hooks/hooks.json` plus any hook scripts under plugin root
- `commands/` → compatibility only; mirror or shim to `skills/`
- `agents/` → ship directly
- `mcp/` → compile into `.mcp.json` plus any bundled server assets

**v1 manifest principles**

- `defaultEnabled: false` if the package adds external scope or any risky helper, so opt-in is explicit.
- No `settings.json` agent override in v1. Plugin settings can activate a custom agent as the main thread; that is too much silent authority too early.
- No `monitors/` in v1. Monitors auto-start, run unsandboxed at hook trust level, and keep running until session end.
- No `channels` in v1. Channels inject message content into the conversation.
- `commands/` exists only as migration glue for old slash workflows; all new DCP authoring should live in `skills/`.

## 5. Recommended DCP Skills

Skills are where DCP should put **teaching, synthesis, and procedure**, not hard enforcement. Anything side-effectful should be **user-invocable only** or hidden from model auto-invocation with `disable-model-invocation: true`. Be stingy with `allowed-tools`, because skill-level pre-approval is a real authority grant.

| Skill | Purpose | Inputs | Outputs | Risk |
|---|---|---|---|---|
| `dcp-task-packet-author` | Turn issue/goal/context into a bounded task packet with scope, expected artifacts, non-goals, and proof checklist. | Goal text, repo refs, changed files, policies, ticket/PR refs. | `task-packet.json` or markdown packet draft. | **Medium** — can smuggle bad assumptions into downstream work if packet templates are sloppy. |
| `dcp-proof-reviewer` | Review evidence against the packet and flag missing or weak proof. | Packet, receipts, diffs, test results, artifacts. | Proof gap report, pass/fail recommendation, questions for supervisor. | **Low-Medium** — synthesis only if kept read-only. |
| `dcp-red-lane-classifier` | Explain why an action appears red-lane, amber, or green when deterministic rules are ambiguous. | Proposed action, paths, command text, policy snippets, prior receipts. | Advisory classification with rationale and requested escalation path. | **High** if mistaken for an authority source; it must never authorize by itself. |
| `dcp-pr-steward-reader` | Read PR diffs, comments, checks, and threads and summarize state without mutating GitHub. | PR number/URL, diff, review threads, CI status. | Human-readable PR brief, unresolved-thread summary, proof gaps. | **Low** if read-only. |
| `dcp-action-plan-compiler` | Convert research or findings into a stepwise action plan with explicit checkpoints and proof hooks. | Research notes, packet, architecture constraints, branch state. | Ordered action plan and local checklist. | **Medium** — can overfit to current context and hallucinate dependencies if not grounded. |
| `dcp-cockpit-operator` | Interpret cockpit state, queue health, and task posture for a human operator. | Cockpit state, queue/task lists, receipts, policy signals. | Suggested next action, watch items, escalation flags. | **Medium** — useful, but dangerous if allowed to act instead of advise. |
| `dcp-dr-intake` | Convert a research prompt into a research intake brief, hypotheses, evidence plan, and output contract. | Research request, repo/module refs, time/risk bounds. | DR intake packet and evidence plan. | **Low** — planning only. |
| `dcp-architecture-auditor` | Review architecture and changes against contracts, boundaries, and layering expectations. | Diffs, architecture docs, schemas, packets, receipts. | Architecture findings, contract violations, required follow-ups. | **Medium** — judgment-heavy, but appropriate for a read-only subagent or skill. |

**v1 authoring rule:** all eight should be authored as skills, but in v1 only `dcp-pr-steward-reader`, `dcp-dr-intake`, and `dcp-architecture-auditor` are good candidates for model invocation. The rest should default to explicit human invocation via `disable-model-invocation: true`.

## 6. Recommended DCP Hooks

For DCP, the lifecycle events that matter most are `SessionStart`, `UserPromptExpansion`, `PreToolUse`, `PostToolUse`, `PostToolBatch`, `TaskCreated`, `TaskCompleted`, `Stop`, `ConfigChange`, `InstructionsLoaded`, `SubagentStart/Stop`, and `WorktreeCreate/Remove`. In practice, **v1 should anchor hard controls in `UserPromptExpansion`, `PreToolUse`, Git/pre-commit hooks, and explicit CLI validation**. `PostToolUse` and `Stop` are for receipts and feedback, not for secret second brains.

| Hook | Event | Blocks? | Inputs | Outputs | Risk |
|---|---|---|---|---|---|
| session-start context hook | `SessionStart` plus optionally `InstructionsLoaded`/`ConfigChange` | No in DCP design | Repo root, branch, packet pointer, policy version, last receipts, session mode. | Injected context, active packet selection, stale-state warning, local receipt stub. | **Low** if read-only. |
| pre-tool red-line guard | `PreToolUse` | Yes | `tool_name`, `tool_input`, path/classification maps, approval artifact presence. | `allow` / `ask` / `deny` / `defer`, reason, optional normalized input, receipt entry. | **High** — this is real authority; keep logic deterministic and reviewable. |
| pre-edit forbidden-path guard | `PreToolUse` with matcher `Write|Edit` | Yes | Absolute file path, target path class, packet scope, allowlist/denylist. | Deny or ask, plus reason tied to policy/rule ID. | **High** — edit authority is where "oops" becomes "postmortem." |
| post-edit schema/check hook | `PostToolUse` or `PostToolBatch` after `Write|Edit` | No hard block here; fail later at commit/accept | Changed files, diff stats, validator registry, schema commands. | Check results, `additionalContext`, receipt updates, maybe async task IDs. | **Medium** — async is fine for speed, but async hooks cannot block. |
| pre-commit proof guard | `git pre-commit`, `commit-msg`, and optionally `pre-push` via Git or pre-commit framework | Yes | Staged diff, packet ID, receipt manifest, proof bundle, branch/push target. | Commit/push allow or block, message normalization, missing-proof diagnosis. | **Medium** — strong for local discipline, weak if treated as the only enforcement. |
| stop/summary receipt hook | `Stop` and optionally `SessionEnd` | No for v1 | Last assistant message, task status, background tasks, current receipt graph. | Turn receipt, summary stub, unresolved-risk note, proof to-do list. | **Medium** — Stop hooks *can* continue work, but DCP should not use them to coerce looping; use them for receipts only. |

**Important design rule:** do **not** use prompt-based or agent-based hooks for hard blocks in v1. The moment the guard itself becomes probabilistic, your "control plane" becomes a vibe plane. Use prompt/agent hooks only as advisories or secondary reviewers.

## 7. Recommended CLI Helpers

CLI is where DCP should standardize reality. Skills are prompts. Hooks intercept lifecycle. Git/pre-commit catch SCM boundaries. But the durable, scriptable, testable, cross-project layer should be `dopemux dcp ...`.

```bash
dopemux dcp preflight
dopemux dcp status
dopemux dcp next
dopemux dcp evidence-pack
dopemux dcp prompt implement
dopemux dcp prompt audit
dopemux dcp verify-proof
dopemux dcp red-lines
dopemux dcp render-to --dry-run
dopemux dcp accept
```

| Command | Purpose | Mutation Policy |
|---|---|---|
| `dopemux dcp preflight` | Validate repo trust, branch posture, packet presence, policy version, missing receipts, and forbidden pending state. | **Read-only**. |
| `dopemux dcp status` | Show current packet, branch, staged changes, receipts, unresolved risk flags, and next required proof. | **Read-only**. |
| `dopemux dcp next` | Compute the next safe step from packet + repo + receipts. | **Read-only**. |
| `dopemux dcp evidence-pack` | Assemble receipts, diffs, logs, validator outputs, and artifact hashes into a proof bundle. | **Local write only** under dedicated evidence path. |
| `dopemux dcp prompt implement` | Render a bounded implementation prompt from packet + policy + current repo state. | **Read-only**. |
| `dopemux dcp prompt audit` | Render an audit/review prompt focused on proof, architecture, and red lanes. | **Read-only**. |
| `dopemux dcp verify-proof` | Validate proof schema, required fields, referenced artifacts, and hashes. | **Read-only**. |
| `dopemux dcp red-lines` | Evaluate a proposed action, diff, command, or target path against red-lane policy. | **Read-only**. |
| `dopemux dcp render-to --dry-run` | Preview rendering a task packet or action plan into downstream formats without executing it. | **Dry-run by default**; no live mutation. |
| `dopemux dcp accept` | Record explicit supervisor acceptance of a packet, proof bundle, or next-step mutation gate. | **Local metadata write only**; does **not** perform the mutation itself. |

**What belongs here**: deterministic red-line checks, proof validation, prompt rendering from explicit templates, evidence bundling and hashing, recording supervisor acceptance, thin wrappers around Git/pre-commit/Codex invocations with explicit sandbox settings.

**What does not belong here**: hidden deployment, auto-approve logic, PR merge/approve, CRM/client/runtime writes disguised as "helpers."

## 8. Proof / Receipt Requirements For Helpers

Every helper run should emit a receipt. Receipts must be machine-verifiable, human-readable, and chainable across helper surfaces.

**Required fields**: `receipt_id`, `parent_receipt_id`, `packet_id`, `helper_surface` (skill/hook/git-hook/pre-commit/cli/codex-wrapper/mcp/subagent), `helper_name`, `helper_version`, `policy_version`, `started_at`/`ended_at`/`duration_ms`, `actor`, `model`, `repo` (root/branch/head before-after/worktree/cwd), `invocation` (normalized args, prompt hash, no raw secrets), `inputs`, `decision` (allow/warn/block/defer/advisory/accepted/failed), `decision_reason` (+ rule IDs), `mutations`, `checks` (with exit codes), `artifacts` (paths + SHA-256), `approvals`, `errors`, `sensitivity`, `signature`.

**Minimal schema example**:

```json
{
  "receipt_id": "rcpt_01J...",
  "parent_receipt_id": "rcpt_01H...",
  "packet_id": "pkt_2026_06_03_001",
  "helper_surface": "cli",
  "helper_name": "dopemux dcp verify-proof",
  "helper_version": "0.1.0+abc1234",
  "policy_version": "dcp-policy-2026-06-03",
  "started_at": "2026-06-03T18:42:10Z",
  "ended_at": "2026-06-03T18:42:11Z",
  "duration_ms": 842,
  "actor": {"type": "human", "id": "supervisor:local", "session_id": "sess_..."},
  "repo": {"root": "/repo", "branch": "feature/x", "head_before": "abc...", "head_after": "abc..."},
  "invocation": {"args": ["verify-proof", "--bundle", ".dcp/proof/run-17"], "prompt_sha256": null},
  "decision": "allow",
  "decision_reason": "All required proof artifacts present",
  "checks": [
    {"id": "proof-schema", "status": "pass", "exit_code": 0},
    {"id": "artifact-hash", "status": "pass", "exit_code": 0}
  ],
  "artifacts": [{"path": ".dcp/proof/run-17/manifest.json", "sha256": "..."}],
  "approvals": [],
  "errors": [],
  "sensitivity": {"redacted": true},
  "signature": {"alg": "sha256", "value": "..."}
}
```

**Non-negotiables**: hash prompts and artifacts; record **attempted** blocked mutations too; never store raw secrets in receipts; separate local evidence paths from business data paths; chain receipts so a final proof bundle can reconstruct who did what, with which policy, on which repo state.

## 9. Red-Lane Automation Policy

One rule: **the more external, irreversible, identity-affecting, or policy-changing an action is, the less it belongs to skills and the more it belongs to explicit human-supervised wrappers.**

| Surface / Action | Default Policy | Block vs Warn | Allowed Execution Path | Required Proof |
|---|---|---|---|---|
| Ordinary repo code/docs edits in approved paths | Allow with checks | Warn if missing packet/proof; block if outside scope | Claude edit tools + validators | Packet ID + post-edit checks + receipt |
| Forbidden-path file edits | Block | **Block** | Only via explicit supervisor-approved workflow | Approval record + targeted receipt + path justification |
| Shell commands that only inspect local repo | Allow | Warn if noisy | Direct tool/CLI | Receipt |
| Destructive/networked shell, package installs, deploy | Deny by default | **Block** unless explicit approved wrapper path | Dedicated wrapper only, bounded environment | Approval + sandbox receipt + command digest |
| Commits without proof linkage | Deny | **Block** | `git commit` only after local proof guard passes | Packet ID + proof manifest + validated message |
| Pushes with unresolved red-lane flags | Deny | **Block** | `git push` after pre-push/CI checks | Proof manifest + policy pass |
| GitHub read actions | Allow | Warn if outside packet scope | Read-only CLI/MCP | Receipt |
| GitHub mutation (PR create/update, comments, threads, labels) | Deny in v1 | **Block** | Separate dedicated wrapper, only if explicitly approved per repo | Approval + mutation receipt + target refs |
| PR approve / merge | Deny | **Block** | Human-only in v1 | Human approval outside helper automation |
| Branch protection / CODEOWNERS changes | Deny | **Block** | Human-only / change-control path | Change ticket + approval + audit receipt |
| Task Orchestrator live writes | Deny | **Block** | Dedicated orchestrator wrapper after explicit accept | Target entity ID + approval + immutable receipt |
| Dopetask execution | Deny by default | **Block** in v1 except explicit dry-run | Dedicated exec wrapper after dry-run + accept | Dry-run result + approval + execution receipt |
| Client sends | Deny | **Block** | Draft-only in v1; human presses send | Draft proof + human send |
| CRM writes | Deny | **Block** | Narrow CRM wrapper with explicit entity targeting | Approval + before/after values + receipt |
| Identity merges | Deny | **Block** | Human-only in v1 | Manual approval + independent review |
| Approval-policy changes | Deny | **Block** | Manual change control only | Signed change record |
| Runtime DB / event-store writes | Deny | **Block** | Separate operational tooling | Change ticket + environment + rollback proof |
| Secret access | Deny raw model access | **Block** unless through narrow broker | Secret broker returns scoped credential to tool, not transcript | Access log + purpose + expiry |

**Policy logic per action**: classify target → apply deterministic rule map → green: allow + receipt → amber: ask/warn through explicit human path → red: block, receipt, point to escalation path.

**Key implementation detail**: use `UserPromptExpansion` to block direct `/deploy`-style commands before expansion; `PreToolUse` to block `Write`/`Edit`/`Bash`/side-effecting MCP tools; Git/pre-commit hooks to block commit/push without proof; duplicate critical checks in CI/server-side gates because local hooks are bypassable.

## 10. Cross-Project Packaging Strategy

Split into **core**, **profile**, and **repo evidence**:

- **`dcp-core`**: receipt schema, red-lane taxonomy, helper CLI engine, generic skills, generic hook scripts, proof validators, common prompt templates.
- **`dcp-profile-dopemux`**: dopemux path classes, entity/resource rules, proof extras, red-lane extensions.
- **`dcp-profile-dnh-crm`**: CRM-sensitive entity rules, identity merge blocks, client-send policy, CRM proof extras.
- **Repo-local evidence layer**: actual path maps, CODEOWNERS, schema registries, current CLI/task/orchestrator commands, environment names, existing proof artifact locations.

**Extension model**: core defines **base denies** and **minimum proof requirements**; profiles may **add** denies/warnings/validators; repo-local config may tune read-only conveniences but must **not weaken core denies** without an explicit, versioned exception mechanism tied to supervisor approval.

**Packaging**: core as repo package + private plugin artifact; profiles as adjacent packages; build outputs target Claude plugin artifact, `.pre-commit-config.yaml` fragment, git hook scripts, Codex wrapper profiles/rules, `dopemux dcp` executable.

**Do not** fork skill prompts per project as the main extension point. Extend through **rules, schemas, and path/resource maps**.

## 11. Security / Prompt Injection / Tool Abuse Risks

| Risk | How It Fails | Mitigation |
|---|---|---|
| Model-only guardrails | The model "knows" a lane is risky but still gets clever or inconsistent. | Hard blocks in deterministic hooks/CLI only; LLM advisory at most. |
| Skill-level hidden authority | `allowed-tools` quietly grants tool access without normal prompts. | Mutating skills manual-only; minimize `allowed-tools`; deny risky tools in permission rules. |
| Hook-level hidden authority | `PreToolUse` can `allow` or rewrite `updatedInput`, skipping user review. | Never auto-allow red-lane tools; treat `updatedInput` as a code-review surface; rule IDs in receipts. |
| Plugin default-agent takeover | Plugin `settings.json` can activate a plugin agent as the main thread. | Ban default-agent overrides in v1. |
| Automatic unsandboxed background activity | Plugin monitors auto-start, run unsandboxed at hook trust level. | No monitors in v1; if ever used: read-only telemetry, explicit opt-in, receipt every event. |
| Prompt injection via dynamic skill context | `!` commands inline live command output into skill prompts. | Don't inline untrusted content; read-only fetch + sanitize + separate review; isolate via subagents. |
| Channel/message injection | Plugin `channels` inject external messages into the conversation. | No channels in DCP v1. |
| MCP overreach | Broad MCP server exposes live mutation tools directly to the model. | Narrow, typed, mostly read-only MCP helpers; sensitive writes via explicit wrappers with approvals/logging. |
| Client hook bypass | `--no-verify` or missing local hook installation defeats local policy. | Mirror critical checks in CI/pre-receive/branch protection. |
| Codex automation drift | CI/wrappers inherit user config/rules and behave differently than intended. | Explicit sandbox/approval settings; `--ignore-user-config` / `--ignore-rules` in controlled automation; JSONL receipts. |
| Secret leakage into proofs | Receipts/prompts capture raw tokens or sensitive values. | Never store raw secrets in receipts; secret brokers; secure storage for sensitive plugin config. |
| Subagent laundering | Parent delegates "research," then quietly uses results to justify a risky step. | Subagents read-only; separate advisory from mutation paths; explicit approval artifacts for all external writes. |
| Cockpit authority collapse | A UI button turns "review" into "approve and mutate." | Every cockpit action must show risk class, target, side effects, and proof/approval prerequisites before execution. |

## 12. V1 / V2 / Never Build

| Item | Stage | Why |
|---|---|---|
| Receipt schema and proof manifest | V1 | Foundational. |
| Deterministic red-lane engine | V1 | Core authority boundary belongs in hooks/CLI, not skills. |
| `dopemux dcp preflight/status/verify-proof/red-lines/evidence-pack` | V1 | High value, low hidden authority. |
| Read-only skills: DR intake, PR reading, architecture audit | V1 | Prompt-based reuse without live mutation. |
| `UserPromptExpansion` + `PreToolUse` guards | V1 | Covers direct slash invocation and tool execution. |
| Git / pre-commit / pre-push proof guards | V1 | Cheap local discipline and CI reuse. |
| Read-only MCP helpers | V1 | Safe-ish if narrow and auditable. |
| Supervisor `accept` record | V1 | Preserves "supervisor decides." |
| Project profile packages (dopemux, dNh-CRM) | V1 | Avoid hardcoding project specifics into core prompts. |
| Codex noninteractive read-only wrapper profiles | V1 | Reproducible audits and CI evidence. |
| Automatic PR draft comment generation | V2 | Only after receipts/proof are solid. |
| Background subagent orchestration for large audits | V2 | After the authority model is locked. |
| Narrow write-broker MCP servers with mandatory approval artifacts | V2 | Only after core contracts + repo evidence exist. |
| Plugin marketplace distribution / dependency graphing | V2 | Operational convenience. |
| Monitors for read-only telemetry | V2 | Too much implicit runtime in v1. |
| Plugin `channels` | **Never** | No external message injection into authority-bearing sessions. |
| Plugin default-agent override | **Never** | Silent authority collapse. |
| Auto-approve / auto-merge / auto-resolve PR actions | **Never** | Violates the supervisor principle. |
| CRM/client send automation from skills/hooks | **Never** | Hidden irreversible external mutation. |
| Broad live-writer plugin | **Never** | A plugin is a package, not a secret government. |

## 13. Anti-Patterns

- **Model-only red-line enforcement** — if the model is the only guard, there is no guard.
- **Hidden auto-fix** — post-edit silent rewrites turn the audit trail into mush.
- **Hooks that mutate silently** — command hooks run with full user permissions; state changes need explicit receipts and operator awareness.
- **Plugins that bundle broad live writers** — plugin MCP servers and monitors auto-start when enabled.
- **Skills that execute commands** — a skill may *instruct* Claude to use tools, but skills are not the command authority layer.
- **Helper commands that skip proof** — a mutating command without proof is not a helper; it is a liability.
- **Cockpit buttons that hide risk** — if "Sync" really means "rewrite client identity mappings," you built an incident generator.
- **Default-enabled risky plugins** — use `defaultEnabled: false`.
- **Relying on client hooks as the sole policy** — client hooks are not cloned and `--no-verify` exists.
- **Authoritative policy in prompt prose instead of rule data** — prompts drift; schemas and rules are harder to "reinterpret."
- **Secrets in receipts or prompts** — including "just for debugging once." No.

## 14. Questions For Repo Evidence

| Question | Repo Evidence Needed |
|---|---|
| Which exact paths are red-lane in Dopemux and dNh-CRM? | CODEOWNERS, policy directories, infra/runtime config paths, identity/CRM schema locations. |
| What is a "Task Orchestrator write" in this repo? | Source modules, API specs, CLI entrypoints, mutation methods, dry-run support. |
| What exactly is "Dopetask execution"? | Task runner code, execution commands, environment dependencies, state targets. |
| Which commands currently mutate CRM/client/identity/runtime state? | Internal CLIs, MCP servers, service clients, admin scripts, API wrappers. |
| What proof artifacts already exist today? | Existing packet templates, logs, transcripts, CI artifacts, audit records, receipt-like files. |
| Which schemas should post-edit hooks validate? | Schema directories, validator commands, generation pipelines, mandatory checks. |
| What is the current approval artifact? | Labels, files, commit trailers, signed JSON records, issue states, manual forms. |
| What cockpit commands already exist? | UI/CLI modules, dashboards, operator docs, existing command surfaces. |
| Are there current Claude/Codex wrappers already in repo? | Scripts, profile files, `.claude/`, `.codex/`, CI workflows, wrapper binaries. |
| Which external systems are allowed at all? | Policy docs, allowlists, managed settings, environment segregation rules. |
| What is the repo's branch protection / PR authority model? | Branch rules, PR workflow docs, CODEOWNERS, required checks, merge/approve roles. |
| Do receipts need cryptographic signing or is hashing enough? | Compliance requirements, threat model, existing signing infrastructure, audit expectations. |

## 15. Inputs For GPT-5.5 Synthesis

- Recommendation: **BUILD_AFTER_CORE_CONTRACTS**.
- Lock five contracts first: red-lane taxonomy, receipt schema, mutation classes, approval artifact, project path/resource maps.
- V1 packages **read-only skills + deterministic hooks + CLI validators + evidence/receipt helpers**.
- Hard blocks belong in `UserPromptExpansion`, `PreToolUse`, Git/pre-commit/pre-push, and CI/server-side duplicates.
- Skills teach/compile/summarize; hooks enforce; CLI standardizes; humans approve.
- Plugin v1 excludes `monitors`, `channels`, and default-agent override.
- Side-effectful skills default to `disable-model-invocation: true`; be stingy with `allowed-tools`.
- `dopemux dcp` owns preflight, status, next, prompt rendering, verify-proof, evidence-pack, red-lines, accept.
- External writes only through narrow dedicated wrappers after explicit supervisor acceptance.
- Codex wrappers use explicit sandbox/approval settings and controlled config/rules in automation.
- Client-side hooks are useful but not authoritative; duplicate critical gates in CI/server controls.
- Repo evidence still needed for exact red-lane paths, orchestrator semantics, Dopetask behavior, proof artifacts, and permitted write surfaces.

## 16. Sources

Anthropic official docs (plugins, plugins reference, plugin dependency versions, skills, hooks + hooks reference, subagents + SDK subagents, interactive mode, security, MCP, Agent SDK slash commands/features/overview) · OpenAI Codex docs (non-interactive mode, CLI command reference, sandbox, approvals & security, config basics + reference, rules/execpolicy, slash commands, agent skills) · Git SCM githooks + Pro Git hooks · pre-commit framework docs · NIST AI RMF 1.0.
