# GPT-5.5 Investigation Intake

Source path: /Users/hue/Downloads/dev-workfllow--reseearch.md
Source hash sha256: 82c9abc18c09296b38974464cf5552168b94ae175c15a52c86ae0d5b413c5260
Intake status: OBSERVED
Resolution note: Filename is misspelled, but the title and contents identify an evidence-first AI development operating model for Codex, Claude Code, and ChatGPT.

Attach this GPT-5.5 investigation to Thread 00 Intake / Supervisor Ledger before starting the first packet.
Treat it as advisory below live repo truth and uploaded authority files.
Use it to seed operating-model decisions, not to override runtime evidence.

---

# Evidence-First AI Development Operating Model for Codex, Claude Code, and ChatGPT

## Executive verdict

The best current workflow is **not** a permanent three-agent bureaucracy. The best workflow is a **risk-routed operating model** with a default **two-role lane** and a stricter **three-role lane**. For most real software work, you want: **human-led supervision with a bounded task packet, one primary implementer agent, GitHub/CI as the enforcement layer, and a separate auditor only when the change is hard to test, high-risk, large, externally visible, or likely to drift.** Deep Research is strongest when the supervisor needs current sources and a cited memo. Codex is strongest when work should run **in the background, in parallel, and inside a GitHub-centric cloud lane**. Claude Code is strongest when the truth lives in the **local repo, local tools, local tests, SSH/devcontainers, and interactive debugging loops**. citeturn11view0turn37view0turn36view0turn33view1turn35view0

The blunt default split is this. **Usually supervise with ChatGPT Deep Research or ChatGPT Projects** when requirements are ambiguous, current external research matters, or you need a clean acceptance memo with citations. **Usually implement with Claude Code CLI or Desktop** for local work that touches real dependencies, refactors multiple files, or needs iterative debugging and plan-first execution. **Use Codex Web or Codex App instead when the task is well-bounded, parallelizable, PR-oriented, or better delegated to a cloud/background lane.** **Usually audit with a fresh code-capable session plus GitHub PR/CI evidence**, not with the same session that wrote the code. ChatGPT Deep Research is excellent as a **spec, policy, architecture, and evidence auditor**; it is usually **not** the best sole technical diff auditor unless you also feed it the diff, logs, and proof bundle. citeturn35view0turn33view1turn37view0turn9view1turn22view0turn11view0

The Supervisor / Implementer / Auditor pattern is **worth it** when a change affects security, auth, money, CI/CD, deployment, infrastructure policy, public APIs, data migrations, compliance-sensitive logic, or a large refactor that will generate a fat diff faster than humans can sensibly review line by line. It becomes **wasteful theatre** for tiny, reversible fixes with obvious tests and limited blast radius. If you make a typo fix endure a three-agent tribunal, the delay is your fault, not the model’s. Google’s review guidance explicitly favours small changes because they are reviewed faster and more thoroughly, while NIST’s SSDF and Salesforce’s AI-era review writeup both reinforce the value of peer review, recorded issues, and preserving a real second pair of eyes when AI increases code volume. citeturn18search14turn20view1turn26view0

The pattern is **not automatically optimal**. A simpler **Supervisor + Implementer + GitHub/CI** lane gives the best speed-to-correctness ratio for low- and medium-risk work. The **independent Auditor** materially improves outcomes when any of these are true: the acceptance criteria are non-trivial; tests are incomplete; the PR is large; the change crosses layers; the repo is legacy or poorly understood; the code is security-sensitive; or the implementer already showed signs of drift. Spotify’s background-agent work is especially clear: the dangerous failure case is not “no PR,” but “CI passes and behaviour is still wrong,” because that erodes trust and slips through human review when changes are numerous. citeturn29view2turn20view1turn22view0

**Confidence: 0.78.** Confidence is high on tool capabilities because the major claims below are grounded in official OpenAI, Anthropic, and GitHub documentation. Confidence is only moderate on the exact “best” tool split because there is still very little public, controlled, head-to-head evidence comparing Codex and Claude Code on production defect escape, review lift, or long-term maintainability across the same repos. The public evidence is stronger on **capability fit and failure modes** than on universal superiority. citeturn36view0turn33view1turn22view0turn26view0turn29view2

## Capability matrix and blunt tool fit

The matrix below separates **verified product capability** from **recommended role fit**. Capability claims in the “Strengths” and “Weaknesses” columns are grounded in official docs or credible engineering writeups. The role assignments are recommendations derived from those capabilities and from field reports about review load, context engineering, and long-running agent harnesses. citeturn11view0turn37view0turn36view0turn35view0turn26view0turn29view1turn29view2

| Surface | Best role | Strengths | Weaknesses | Best task types | Bad task types | Required guardrails | Evidence requirements | Recommended usage frequency |
|---|---|---|---|---|---|---|---|---|
| **ChatGPT Web / Deep Research** | **Supervisor, researcher, acceptance writer** | Deep Research can search the public web, uploaded files, and enabled apps, lets you review the research plan before execution, and returns structured cited reports; Projects keep files, instructions, chats, and memory together for long-running work; Deep Research uses **read** actions only for connected apps. citeturn11view0turn11view3 | Standard ChatGPT is not a direct repo execution surface; GitHub app visibility varies by plan/experience; Deep Research is research-oriented, not a code mutation workflow. citeturn11view1turn11view0 | Architecture research, supervisor packets, acceptance memos, source-grounded comparisons, policy review, cross-tool orchestration | Local debugging, environment-specific fixes, unattended repo mutation | Require explicit proof from implementers; never accept “tests passed” without logs; keep scopes bounded; use Projects to avoid context scatter | Packet, diff, command log, test/CI evidence, acceptance memo | **Often** for medium/high ambiguity; **rarely** for trivial fixes |
| **Codex Web** | **Background implementer** | Runs tasks in the background, including in parallel, in its own cloud environment; works against GitHub repos and can create PRs; supports configurable cloud environments and internet controls. citeturn37view0turn36view0 | Requires GitHub connection; cloud environment can diverge from the developer’s local truth; agent phase is offline by default unless internet access is enabled, so setup matters. citeturn37view0turn36view0 | PR-oriented work, bounded backlog items, overnight maintenance, multi-lane throughput | Deep local debugging, hardware-/secret-dependent flows, anything that depends on undocumented local state | Pin setup steps, repo, branch, test commands, and allowed internet; prefer draft PRs first; keep packets narrow | PR link, environment setup, changed file list, commands run, local/CI validation | **Frequent** for bounded cloud delegation |
| **Codex CLI** | **Implementer or read-only auditor** | Local sandbox/approval controls, AGENTS.md instruction loading, skills, plugins, MCP, and optional subagents; network is off by default and workspace writes are sandboxed by default. citeturn9view3turn36view0turn8search14turn9view4 | Permission/network config can be mis-set; container and Windows semantics need care; instruction files are guidance, not magic. citeturn36view0turn9view3 | Local implementation with OpenAI stack, read-only audits, scripted tasks, repo exploration | Unbounded autonomous work in unsafe configs; giant, ambiguous rewrites without a packet | Default to workspace-write + on-request approvals; keep network off unless justified; use read-only for audits | Proof JSON, command log, test output, changed-file inventory | **Situational**; strongest if you already want the Codex stack locally |
| **Codex App** | **Parallel implementer manager** | Desktop command centre with parallel threads, built-in worktrees, automations, Git functions, and shared skills; automations can run in dedicated background worktrees. citeturn9view0turn9view1turn9view2 | More moving parts than plain CLI; poor worktree hygiene creates collisions; local-vs-worktree handoffs need discipline. citeturn9view1turn9view2 | Multi-agent backlog execution, repeated maintenance workflows, parallel experiments, throughput-heavy solo ops | Tiny one-off edits; tasks where a full app surface is overhead | One task per worktree; explicit branch naming; no shared mutable files across lanes; draft PR by default | Thread link, worktree/branch mapping, PR/CI status, proof package | **Frequent** if you manage many concurrent tasks |
| **Codex Skills** | **Workflow packaging** | Packages instructions, resources, and optional scripts for reusable workflows; follows the open Agent Skills standard; app/CLI/IDE all support skills. citeturn8search14turn9view0 | Not a standalone agent; stale skills fossilize bad process; hidden script side effects can become foot-guns | Proof capture, PR preparation, repo bootstrap, standard audits, recurring migrations | Novel design work, emergency debugging, first-time architecture choices | Version skills; keep them small; log skill version in proofs; review scripts like code | Skill version, inputs, outputs, artifacts produced | **Only** for repeated work |
| **Claude Code CLI** | **Default local implementer** | Reads/edits/runs locally, supports plan mode, permission modes, CLAUDE.md, auto memory, hooks, MCP, skills, subagents, worktrees, non-interactive mode, and devcontainers; official guidance strongly emphasizes verification and “explore, then plan, then code.” citeturn13view0turn13view2turn13view3turn13view4turn35view0turn15view3 | Local environment dependency; context window fills fast and performance degrades; CLAUDE.md and auto memory guide behaviour but do not hard-enforce it; dangerous permission bypass is unsafe. citeturn13view2turn35view0turn15view0 | Medium features, refactors, debugging, multi-file edits, test-driven changes, local validation | Mass parallel backlog across many repos without extra orchestration; cross-repo blast-radius audits without better search tooling | Verify-own-work loop; use plan mode when scope is non-trivial; reset context aggressively; use worktrees for parallelism; devcontainer for consistency | Commands run, tests run, diffs, screenshots where needed, proof JSON | **Default** for most local complex work |
| **Claude Code Desktop/App** | **GUI implementer and interactive auditor** | Multiple side-by-side sessions, visual diff review, preview/browser verification, local/remote/SSH execution, CI monitoring with auto-fix/auto-merge, scheduled tasks, and PR tracking. citeturn33view0turn33view1 | Desktop-specific workflow overhead; remote sessions have different permission semantics; computer use changes the trust boundary and should be treated as high-risk. citeturn33view1turn13view9 | Guided implementation, UI/debug sessions, visual review, remote or SSH work, supervised parallel work | Blind unattended risk-heavy changes; anything where a human shouldn’t trust UI automation | Start in Ask permissions or Plan mode; keep computer use off unless necessary; use Remote only for bounded work | Annotated diff, preview evidence, CI status, proof bundle | **Frequent** if you prefer GUI workflows |
| **GitHub PR / CI layer** | **Enforcement and audit trail** | Protected branches can require reviews, CODEOWNERS, status checks, stale-review dismissal, latest-push approval, signed commits, and conversation resolution; Actions artifacts persist logs and outputs. citeturn22view0turn22view1turn22view2turn22view3turn22view4turn22view5turn22view6 | CI gates are necessary but not sufficient; skipped jobs can still report success; PR review alone cannot reconstruct intent if diffs are huge. citeturn22view3turn26view0 | Merge gating, audit trail, artifact storage, CODEOWNERS enforcement, final acceptance path | Architecture planning, local debugging, semantic behaviour validation by itself | Protected branches, required checks, draft PRs, CODEOWNERS, artifact uploads, no direct pushes to protected branches | CI logs, artifacts, PR discussion, code-owner approvals, merge record | **Always** for executable changes to protected branches |

Two blunt corrections matter here. First, **ChatGPT is usually the best supervisor, not the best wrench**. Use it to narrow scope, compare options, catch weak reasoning, and write the acceptance memo. Do not make it blindly bless unverifiable implementation claims. Deep Research is read-oriented by design; that is a feature, not a defect, for supervision. citeturn11view0turn11view2

Second, **do not dual-wield Codex and Claude on every task just because you can**. That is expensive cosplay. Pick one primary implementer for a lane and keep the other as a conditional second opinion. Anthropic’s own best-practices page explicitly warns that context is the critical constraint and promotes managing context aggressively, while OpenAI’s Codex docs make it clear that subagents and cloud delegation add token and operational overhead. The fastest reliable system is the one that minimizes needless handoff friction. citeturn35view0turn9view4

## Scenario assignments and decision tree

These assignments assume three things. **Small changes review better than big ones**; **peer review remains important when AI increases code volume**; and **review must preserve human judgment instead of collapsing into approval theatre**. That is consistent with Google’s review guidance, NIST SSDF’s peer-review and issue-recording practices, Spotify’s warning about “CI passes but still wrong,” and Salesforce’s observation that AI-generated PR size and reviewer load can break the old file-by-file review model. citeturn18search14turn20view1turn29view2turn26view0

| Scenario | Supervisor tool | Implementer tool | Auditor tool | Required evidence | Packet needed | Independent audit | Is PR review enough | Human acceptance mandatory |
|---|---|---|---|---|---|---|---|---|
| Small bug fix | Claude Plan mode or lightweight ChatGPT thread | Claude Code CLI/Desktop | GitHub PR/CI; fresh read-only audit only if low confidence | Repro case, failing→passing test or command, changed files | Usually no | Usually no | Usually yes | Yes for merge |
| Medium feature | ChatGPT Web/Project; Deep Research if requirements are ambiguous | Claude Code CLI/Desktop | Fresh Claude read-only session + GitHub CI | Task packet, tests, lint, changed-file inventory, proof JSON | Yes | Conditional | No | Yes |
| Large refactor | ChatGPT Deep Research or Project | Claude Code CLI/Desktop in worktrees | Fresh Claude read-only + ChatGPT acceptance audit | Packet, phased plan, before/after validation, proof JSON, command log | Yes | Yes | No | Yes |
| Security-sensitive change | ChatGPT Deep Research + human owner | Claude Code CLI in devcontainer or SSH | Separate security-review Claude session + human security reviewer + GitHub rules | Threat note, tests, SAST/linters, changed-file map, rollback notes | Yes | Yes | No | Yes |
| Architecture/design decision | ChatGPT Deep Research | Claude read-only exploration or small spike branch | Human + ChatGPT counter-analysis | ADR, alternatives, repo references, optional spike proof | Yes | Usually yes | No | Yes |
| Documentation-only change | Lightweight ChatGPT or none | Codex Web/App or Claude Desktop | GitHub PR review | Render/preview or doc lint, file list | Usually no | No | Usually yes | Yes |
| CI/build/dev-experience change | ChatGPT Web or Deep Research if standards/security matter | Claude Code CLI/Desktop in devcontainer; Codex if env is mirrored | Fresh Claude read-only + GitHub CI | Pipeline diff, logs/artifacts, rerun success, rollback notes | Yes | Usually yes | No | Yes |
| Multi-agent parallel backlog | ChatGPT Project as authority layer | Codex Web/App across worktrees or background tasks | GitHub CI on every lane; sampled fresh Claude audits on riskier lanes | One packet per lane, branch map, proof per lane, queue ledger | Yes | Conditional by risk | No | Yes |
| Legacy codebase exploration | ChatGPT Deep Research for synthesis | Claude Code CLI/Desktop exploration and subagents | Human spot-check or fresh ChatGPT summary audit | Architecture memo, file map, open questions, no code claims without evidence | Yes | Usually no | No | Yes if it becomes a change |
| Recovery from failed/drifting implementation | Fresh ChatGPT or fresh Claude plan | Prefer the *other* code agent or a fresh worktree | GitHub CI + fresh auditor | Failure summary, reset diff, new packet, untouched-file list | Yes | Yes | No | Yes |

The routing tree below is the practical version. It is built from verified surface differences: Deep Research is source-grounded and read-oriented; Codex Web is cloud/background/parallel and PR-native; Claude Code is strongest in local, permission-gated, plan-first repo work; GitHub enforces the merge contract. citeturn11view0turn37view0turn33view1turn22view0

```text
Start
│
├─ Is this under ~5 minutes, reversible, and obvious?
│  ├─ Yes → No AI or one local agent only. Human reviews diff. No separate auditor.
│  └─ No
│
├─ Do you need fresh external research, standards, vendor docs, or policy comparison?
│  ├─ Yes → ChatGPT Deep Research supervises.
│  └─ No
│
├─ Does the task depend on local truth?
│   Examples: real toolchain, SSH host, devcontainer, flaky tests, debugger,
│   multi-file refactor, interactive preview, local secrets, GUI validation.
│  ├─ Yes → Claude Code implements.
│  └─ No
│
├─ Is the task bounded enough to delegate to cloud/background lanes?
│   Examples: PR-oriented backlog item, repetitive maintenance, parallel throughput,
│   overnight work, GitHub-first repo.
│  ├─ Yes → Codex Web/App implements.
│  └─ No → Claude Code implements.
│
├─ Is risk high?
│   Security/auth/payments/data/CI-public API/infra-policy/low testability/large diff
│  ├─ Yes → Full Supervisor / Implementer / Auditor workflow.
│  └─ No
│
├─ Is the diff likely > ~3 files, > ~150 LOC, or acceptance non-obvious?
│  ├─ Yes → Add independent auditor in fresh context.
│  └─ No → Supervisor + Implementer + GitHub/CI is enough.
│
└─ If the first implementation drifts or stalls
   ├─ Reset to a fresh packet
   ├─ Shrink scope
   ├─ Switch worktree
   └─ Prefer the other implementation agent for the retry
```

Tool disagreements need a boring, deterministic protocol, not a philosophy seminar. The rule is simple: **evidence beats eloquence**. If Codex says the change is fine and Claude says it is dangerous, or vice versa, the supervisor does **not** pick the prettier paragraph. The supervisor narrows the dispute to a replayable question: which file, which behaviour, which command, which failing or missing test, which spec clause. If neither tool can produce decisive evidence, the packet is too broad or the test harness is too weak; stop, shrink, and re-run. For high-risk work, the human owner resolves the tie and records the rationale in the acceptance ledger. citeturn20view1turn22view0turn29view2

What should remain human-only? Final acceptance on high-risk changes; policy or scope changes mid-task; approval to weaken sandboxing or permissions; production rollbacks; secrets and identity management; and any merge where the proof bundle and auditor verdict do not cleanly agree. AI can accelerate judgment. It should not counterfeit it. citeturn15view0turn36view0turn26view0

## Operating model

### Default lifecycle

This is the recommended **full lifecycle** for serious work. The key design choice is not “more agents.” It is **better packets, stronger proof, and cleaner handoffs**.

| Stage | Responsible role | Best tool | Input | Output | Common failure mode | Stop condition | Artifacts produced |
|---|---|---|---|---|---|---|---|
| Intake | Human operator | ChatGPT Web/Project | Issue, bug report, spec, PR comment, incident note | One-sentence objective, risk class, constraints | Ambiguous objective | Missing owner or success condition | Intake note |
| Supervisor scoping | Supervisor | ChatGPT Deep Research if current research matters; otherwise ChatGPT Web or Claude Plan | Intake note, repo context, standards/docs | Scoped problem statement; assumptions; dependencies; acceptance logic | Over-broad scope | More than one mergeable unit | Scope memo |
| Task packet creation | Supervisor | ChatGPT Web/Deep Research | Scoped objective | Strict packet with allowed files, forbidden files, commands/tests, proof requirements, rollback notes | Packet too broad or vague | No clear “done” or no validation command | `TASK-###.md` |
| Implementer handoff | Supervisor | Same surface | Packet + repo/branch/worktree target | Branch/worktree assignment and authority order | Multiple agents share the same files | File overlap unresolved | ACTIVE pointer |
| Implementation | Implementer | Claude Code CLI/Desktop **or** Codex Web/App | Packet, repo instructions, local/cloud environment | Minimal diff, local notes, blockers | Scope creep, unrelated edits, invented repo state | Blocked, drift detected, or validation impossible | Working diff |
| Proof generation | Implementer | Same as implementer + scripts/CI | Working diff | Structured proof bundle | Claimed tests not run; missing command history | Validation incomplete | `proof.json`, command log, file inventory, logs/screenshots |
| Implementation intake | Supervisor | ChatGPT Web or same repo-aware tool in read-only mode | Packet + proof bundle + diff | Intake summary: ready for audit / rejected as incomplete | Supervisor trusts prose instead of evidence | Proof missing required fields | Intake memo |
| Auditor review | Auditor / red team | Fresh Claude read-only session for technical audit; ChatGPT DR for spec/policy audit | Diff, proof bundle, packet, CI outputs | Accept / reject / conditional accept with concrete follow-ups | Auditor reviews summary but not diff | Unreplayable proof or suspicious scope drift | Audit report |
| Supervisor acceptance | Supervisor + human owner | ChatGPT Web/Deep Research | Packet + proof + audit report + CI | Merge decision and required follow-up packets | Vibes-based acceptance | Evidence conflict unresolved | Acceptance memo |
| Commit / PR / merge path | Implementer + GitHub | GitHub PR/CI layer | Accepted change | Draft PR → ready for review → merge | Direct push, stale reviews, missing code-owner approval | Required checks/reviews incomplete | PR, CI artifacts, merge record |
| Ledger / changelog update | Supervisor or script | GitHub + local ledger script | Merge result | Durable trace of what shipped and why | Ledger becomes optional fiction | Acceptance not recorded | Acceptance ledger entry |
| Next-packet selection | Supervisor | ChatGPT Project or backlog tool | Follow-up items from audit/merge | Next bounded packet | Backlog re-inflates into giant epics | No next smallest safe slice | Follow-up packet list |

### Minimal workflow

The lightweight lane exists to keep the process from becoming a strangulation device. Use it for low-risk work where the change is **small, reversible, testable, and boring**.

| Item | Can be skipped | Skip only when all of this is true | What must still happen |
|---|---|---|---|
| Separate task packet | Yes | Single-file or near-single-file change; no public API change; no schema/auth/infra/pipeline impact; acceptance fits in one sentence | Explicit scope in the prompt or PR body |
| Separate auditor | Yes | Objective validation exists and was run; diff is small; blast radius is low; human author actually reviews the diff | Independent human eyes on the diff before merge |
| Formal proof bundle | Yes | Docs-only, comments-only, or behaviour-preserving housekeeping | At minimum: changed-file list, commands run, and honest status |
| Ledger update | Yes | Trivial low-risk change already captured by issue + PR + merge history | Merge record in GitHub |
| Multiple model review | Yes | No ambiguity, no disagreement, no security/data implications | CI and diff review |
| Formal acceptance memo | Yes | The merge decision is obvious from PR + tests + diff | Human acceptance still occurs |

What must **never** be skipped is less negotiable. The change must still have a bounded objective. The implementer must not invent repo state. Tests, linters, or validation commands must only be reported if they were actually run. The diff must be reviewed by a human before merging to a protected branch. And if the change touches auth, money, secrets, CI/CD, infra policy, data migrations, or externally visible behaviour, you are **not** in the lightweight lane anymore. Google’s small-change guidance and Anthropic’s “planning adds overhead, so skip it when the fix is truly small” both support this lighter fast path. citeturn18search14turn35view0

### High-rigor workflow

When governance, safety, determinism, and auditability matter, you want a stricter lane that treats AI like a powerful but untrustworthy contractor. NIST SSDF recommends peer review, recording issues in workflow systems, and collecting/protecting provenance data for releases; GitHub gives you enforceable merge gates and artifact storage; OWASP treats CI/CD itself as a critical security target, not just a convenience. citeturn20view1turn20view3turn22view0turn22view4turn18search5

Recommended required artifacts in the high-rigor lane:

| Artifact | Purpose | Producer | Minimum content |
|---|---|---|---|
| **Task packet** | Defines authority, scope, validation, proof, rollback | Supervisor | Objective, risk class, allowed/forbidden files, commands, acceptance criteria |
| **ACTIVE packet pointer** | Prevents thread confusion | Supervisor/script | Task ID, branch, worktree, packet path, owner |
| **Implementation summary** | Honest handoff from implementer | Implementer | What changed, what did not, blockers, known gaps |
| **Proof JSON** | Replayable evidence | Implementer/script | Commits, files, commands, test results, artifacts, risks |
| **Command log** | Verifies actual execution | Implementer/script | Timestamped commands and exit codes |
| **Changed-file inventory** | Scope check | Implementer/script | Paths changed, added, removed, intentionally untouched |
| **Validation output** | Replayable checks | Implementer/script + CI | Local test/lint/build logs and CI links |
| **Audit report** | Independent verdict | Auditor | Scope check, diff review, replay summary, risks, recommendation |
| **Acceptance ledger** | Durable governance trace | Supervisor/human | Final decision, approver, date, follow-up items |
| **Follow-up packet list** | Keeps next work bounded | Supervisor | Deferred issues and next smallest packets |

A high-rigor merge should typically require: protected branch, required CI checks, code-owner review if applicable, stale review dismissal or “latest reviewable push” approval, and an explicit human acceptance decision. GitHub supports all of those controls directly. citeturn22view0turn22view1turn22view2turn22view6

## Prompt templates

These templates are designed around the practices the official docs consistently recommend: give the agent a way to verify its own work; separate exploration from implementation when the task is non-trivial; keep context clean; use explicit permissions and sandbox boundaries; and avoid accepting unverifiable output. citeturn35view0turn36view0turn33view1

### Supervisor task packet prompt

```text
You are the Supervisor for TASK_ID={{TASK_ID}}.

Your job is to produce a bounded execution packet for a software change.
You are not implementing the change.

Authority order:
1. System / managed policy / branch protection / repo policy
2. Human owner instructions
3. This task packet
4. Repo-local agent instructions (AGENTS.md / CLAUDE.md) unless they conflict with higher authority
5. Agent inference

Output a packet with exactly these sections:

# Task
One-sentence objective.

# Risk class
Low / Medium / High, with a short justification.

# In scope
Concrete files, modules, behaviours, and acceptance boundaries.

# Out of scope
Explicitly forbidden expansions.

# Allowed files
Exact paths or globs.

# Forbidden files
Exact paths or globs.

# Acceptance criteria
Observable behaviours, not vibes.

# Required validation
Exact commands to run, in order.
Mark each as:
- mandatory
- optional
- not possible without human access

# Proof requirements
Require:
- changed-file inventory
- commands run with exit codes
- test/lint/build results
- known gaps
- files intentionally untouched
- rollback note

# Commit policy
Default: no commit unless packet says commit is allowed.
No direct push to protected branches.
Draft PR first if risk is Medium or High.

# Stop conditions
List exact reasons the implementer must stop and report instead of guessing.

# Open questions
Only include questions that materially block correctness.

Constraints:
- Do not assume repo state you have not been shown.
- Do not require impossible validation.
- Keep packet small enough for one mergeable unit.
- If the work should be split, split it now into Packet A / Packet B / Packet C.
```

### Codex implementer prompt

```text
You are the Implementer for TASK_ID={{TASK_ID}} using Codex.

Authority order:
1. System / managed policy / sandbox / approval policy
2. Human owner instructions
3. Task packet
4. Repository instructions from AGENTS.md
5. Your own inference

You must obey these hard rules:
- Do not invent repo state.
- Do not claim tests passed unless you actually ran them.
- Do not modify files outside ALLOWED FILES.
- Do not touch FORBIDDEN FILES.
- Do not expand scope.
- If validation cannot be completed, stop and report.
- If a repository instruction conflicts with the task packet, stop and report the conflict.

Task packet:
{{TASK_PACKET}}

Execution requirements:
- First, inspect the repo and confirm whether the packet is feasible.
- If the task is ambiguous, stop before editing.
- Make the minimum set of changes required.
- Keep network use disabled unless explicitly authorized.
- Prefer working on a dedicated branch/worktree.
- Keep changes patch-like and easy to review.
- Run the REQUIRED VALIDATION commands exactly as specified.
- Produce a structured handoff with:
  - summary of changes
  - changed files
  - commands run + exit codes
  - test/lint/build results
  - known gaps
  - files intentionally untouched
  - rollback note

Output format:
## Status
done / blocked / partial

## Summary
...

## Changed files
...

## Commands run
...

## Validation
...

## Known gaps
...

## Untouched by design
...

## Recommended next step
...
```

### Claude Code implementer prompt

```text
You are the Implementer for TASK_ID={{TASK_ID}} using Claude Code.

Authority order:
1. System / managed policy / permission mode / sandbox
2. Human owner instructions
3. Task packet
4. CLAUDE.md and project rules
5. Your own inference

Hard rules:
- Do not invent repo state.
- Do not claim tests passed unless actually run.
- Do not modify files outside ALLOWED FILES.
- Do not touch FORBIDDEN FILES.
- Do not silently “clean up” unrelated code.
- Stop and report if blocked.
- If this is a non-trivial change, begin in Plan mode before editing.
- If packet and CLAUDE.md conflict, stop and report.

Task packet:
{{TASK_PACKET}}

Operating procedure:
1. Explore only what is needed.
2. If task is medium/high complexity, produce a short execution plan first.
3. Implement the smallest correct diff.
4. Run required validation commands.
5. If UI behaviour is involved, produce visual or preview evidence where possible.
6. Create a structured handoff.

Required handoff format:
## Status
done / blocked / partial

## Plan delta
Any deviation from the approved plan, or “none”.

## Summary of implementation
...

## Changed files
...

## Commands actually run
...

## Validation results
...

## Risks / known gaps
...

## Files intentionally untouched
...

## Rollback note
...
```

### Implementation intake prompt

```text
You are performing implementation intake for TASK_ID={{TASK_ID}}.

Inputs:
- task packet
- implementation summary
- proof bundle
- diff or PR link
- CI outputs if available

Your job:
- verify completeness before audit
- reject incomplete or non-replayable submissions
- do not approve correctness

Checklist:
1. Does the implementation claim stay within scope?
2. Are all changed files listed?
3. Are commands and exit codes present?
4. Are test results supported by actual outputs?
5. Are known gaps honestly stated?
6. Is there a rollback note?
7. Is any required evidence missing?

Output:
## Intake result
ready-for-audit / incomplete / scope-drift / unverifiable

## Missing evidence
...

## Suspected drift
...

## Notes for auditor
...
```

### Auditor red-team prompt

```text
You are the independent Auditor / Red Team for TASK_ID={{TASK_ID}}.

You did not implement this change.
Assume the implementation summary may be incomplete, optimistic, or wrong.

Authority order:
1. System / managed policy / repo policy
2. Human owner instructions
3. Task packet
4. Proof bundle
5. Implementation summary

Audit charter:
- Verify scope
- Inspect the diff
- Replay validation where possible
- Look for regression risk, security issues, hallucinated repo claims, and overclaiming
- Recommend accept / reject / conditional accept

You must:
- Review the actual diff, not just the summary
- Treat “tests passed” as untrusted unless supported by logs
- Flag any file changed outside allowed scope
- Call out missing evidence
- Distinguish between verified findings and concerns that need human confirmation

Output exactly:
## Verdict
accept / conditional-accept / reject

## Verified findings
...

## Scope check
in-scope / out-of-scope elements

## Validation replay
what was replayed, what was not replayed, why

## Security / regression concerns
...

## Proof quality
strong / adequate / weak

## Required follow-up packets
...

## Merge recommendation
...
```

### Supervisor acceptance prompt

```text
You are the Supervisor deciding acceptance for TASK_ID={{TASK_ID}}.

Inputs:
- task packet
- implementation handoff
- proof bundle
- audit report
- PR / CI state

Rules:
- Do not accept from vibes.
- Do not accept if required evidence is missing.
- Do not accept if scope drift is unresolved.
- Do not accept “partial” work unless the packet explicitly allows partial acceptance.
- If audit and proof conflict, reject or send back for clarification.
- Human approval is still required for final acceptance.

Output exactly:
## Acceptance state
accepted / accepted-with-follow-ups / rejected / needs-human-decision

## Why
...

## Evidence relied on
...

## Deferred issues
...

## Merge conditions
...

## Ledger entry
one concise paragraph suitable for the acceptance ledger
```

### Failed implementation recovery prompt

```text
You are recovering TASK_ID={{TASK_ID}} after a failed or drifting implementation.

Inputs:
- original packet
- failed implementation summary
- failing proof or missing proof
- current diff status

Your goals:
- identify why the first attempt failed
- shrink scope if needed
- preserve any valid work
- produce a clean retry packet
- recommend whether to switch tools or worktrees

Hard rules:
- Do not continue from a dirty, ambiguous state.
- Do not reuse claims that were not verified.
- If necessary, recommend reverting to the base commit and restarting in a fresh branch/worktree.

Output:
## Failure mode
...

## Keep / discard decision
...

## Minimal salvageable changes
...

## Retry strategy
same tool / switch tool / switch environment / split packet

## New packet
...
```

### Parallel-agent coordination prompt

```text
You are coordinating parallel agents for EPIC={{EPIC_ID}}.

Your job is not to code.
Your job is to partition work so agents do not collide.

Rules:
- One packet per branch/worktree
- No overlapping write scope unless explicitly serialized
- Shared files must either be assigned to one lane or moved to a final integration packet
- Every lane needs its own success criteria and proof bundle
- High-risk lanes get mandatory independent audit

Output format:
## Lane map
Lane A:
- task id
- goal
- allowed files
- forbidden files
- dependencies
- merge order

Lane B:
...

## Collision risks
...

## Serialized integration packet
...

## Audit requirements by lane
...
```

### PR review prompt

```text
You are reviewing a pull request for correctness, scope, and merge readiness.

Inputs:
- packet
- PR diff
- proof bundle
- CI state
- audit notes if any

Review priorities:
1. Scope compliance
2. Definite logic or behavioural issues
3. Missing validation
4. Security and data-handling risks
5. Rollback clarity
6. Noise or unrelated edits

Do not focus on style unless it affects correctness or maintainability.
Do not re-summarize the PR unless needed.
Be concrete.

Output:
## Merge readiness
ready / not-ready / risky

## Blocking issues
...

## Non-blocking issues
...

## Missing evidence
...

## Suggested next packet
...
```

### Post-merge cleanup prompt

```text
You are performing post-merge cleanup for TASK_ID={{TASK_ID}}.

You are not re-implementing the feature.

Your tasks:
- verify the merge landed as intended
- update the ledger / changelog / packet status
- list any residual follow-up work
- make sure temporary branches, worktrees, or draft notes are cleaned up
- confirm whether proof artifacts were stored correctly

Output:
## Merge verification
...

## Cleanup actions
...

## Stored artifacts
...

## Follow-up packets
...

## Process improvement note
one sentence on what slowed this task down or improved it
```

## Proof, validation, and metrics

A strong proof design should satisfy three different goals at once: **technical replayability**, **governance traceability**, and **release provenance**. NIST SSDF explicitly calls for recording and triaging issues in workflow systems and collecting/safeguarding provenance data for releases. GitHub Actions artifacts are a natural storage layer for logs, test outputs, and intermediate evidence. On the platform side, OpenAI exposes Codex usage through the Compliance API for supported clients, while Claude Code offers enterprise compliance controls and OpenTelemetry-based logging/metrics. citeturn20view1turn20view3turn22view4turn22view5turn11view4turn15view4turn15view5

Recommended standard proof schema:

```json
{
  "task_id": "TASK-042",
  "packet_version": "2026-05-17T14:22:00Z",
  "repo": "org/repo",
  "branch": "task/TASK-042-oauth-callback-fix",
  "base_commit": "abc123",
  "head_commit": "def456",
  "implementer": {
    "tool": "claude-code-cli",
    "surface": "local-devcontainer",
    "session_id": "optional-session-id",
    "skill_versions": ["proof-bundle@1.2.0"],
    "instruction_sources": ["CLAUDE.md", ".claude/skills/proof/SKILL.md"]
  },
  "auditor": {
    "tool": "claude-code-cli-read-only",
    "surface": "fresh-worktree",
    "session_id": "optional-audit-session-id",
    "verdict": "conditional-accept"
  },
  "supervisor": {
    "tool": "chatgpt-deep-research",
    "project": "checkout-hardening",
    "acceptance_state": "accepted-with-follow-ups"
  },
  "scope": {
    "allowed_files": ["src/auth/**", "tests/auth/**"],
    "forbidden_files": ["infra/**", "package-lock.json"],
    "files_changed": [
      "src/auth/callback.ts",
      "tests/auth/callback.test.ts"
    ],
    "files_intentionally_untouched": [
      "src/auth/session.ts"
    ]
  },
  "commands_run": [
    {
      "cmd": "pnpm test -- callback",
      "exit_code": 0,
      "timestamp": "2026-05-17T14:31:09Z"
    },
    {
      "cmd": "pnpm lint",
      "exit_code": 0,
      "timestamp": "2026-05-17T14:32:41Z"
    }
  ],
  "validation": {
    "local": [
      {
        "name": "unit-tests",
        "status": "passed",
        "evidence_path": "artifacts/unit-tests.txt"
      },
      {
        "name": "lint",
        "status": "passed",
        "evidence_path": "artifacts/lint.txt"
      }
    ],
    "ci": [
      {
        "provider": "github-actions",
        "run_id": "123456789",
        "status": "passed",
        "artifact_paths": [
          "artifacts/ci-summary.txt"
        ]
      }
    ],
    "manual": [
      {
        "name": "oauth-callback-preview",
        "status": "reviewed",
        "evidence_path": "artifacts/preview-screenshot.png"
      }
    ]
  },
  "artifacts_produced": [
    "proof.json",
    "command-log.txt",
    "changed-files.txt",
    "preview-screenshot.png"
  ],
  "risks": [
    "OAuth edge cases still depend on provider-side redirect behaviour"
  ],
  "known_gaps": [
    "No live provider integration test in local environment"
  ],
  "rollback_notes": "Revert commit def456 and redeploy previous auth callback package.",
  "follow_up_packets": [
    "TASK-043 add provider-integration-smoke-test"
  ],
  "attestations": {
    "repo_state_not_invented": true,
    "tests_only_claimed_if_run": true,
    "scope_drift_detected": false,
    "human_acceptance_required": true
  }
}
```

Proof should be **generated as close to execution as possible**, preferably by a wrapper script or skill, not by asking the model to remember what it ran after the fact. Local validation logs should be written to files as commands execute. CI logs and reports should be uploaded as artifacts. The proof JSON should be committed only for high-rigor internal workflows or stored as a PR/CI artifact for regular workflows. If you have enterprise controls, also capture Codex or Claude session telemetry separately rather than stuffing everything into the proof JSON. citeturn22view4turn22view5turn11view4turn15view4

Proof becomes **invalid** when any of the following happens: the base commit changes and overlaps affected files; the task packet changes; validation commands change; required secrets, configs, or environments change; the branch is rebased and the diff meaningfully differs; or the auditor finds undocumented changed files. In other words, proof is tied to a **specific scope, environment, and commit graph**, not to a vague sense that “it was fine at some point.” NIST’s provenance guidance is the right mental model here. citeturn20view3

Recommended metrics:

| Metric | Definition | Manual or automatic | Best collection source |
|---|---|---|---|
| Cycle time from packet to implementation | Packet created → implementer handoff complete | Automatic | Task timestamps, PR timestamps |
| Implementation pass rate | % of packets that reach proof-complete status on first attempt | Automatic | Packet tracker + proof status |
| Audit fail rate | % of audited packets rejected or conditionally rejected | Automatic | Audit reports |
| Rework rate | % of merged changes needing follow-up fix packets | Mixed | PR links + follow-up packet list |
| Escaped defect rate | % of merges that later trigger incident/bugfix/hotfix | Mixed | Issue tracker + incident tracker |
| Proof completeness rate | % of required proof fields/artifacts present | Automatic | Proof schema validation |
| Scope drift rate | % of packets with changed files outside allowed scope | Automatic | Changed-file inventory vs packet |
| CI failure rate | % of implementer branches that fail required checks | Automatic | GitHub checks |
| Context refresh cost | Time spent rebuilding context after drift or long gaps | Manual estimate | Supervisor note |
| Token / tool cost | Usage cost per packet or per merged PR | Automatic | Vendor billing/usage telemetry |
| Human interruption count | Number of approval prompts, clarifications, or rescue interventions | Mixed | Tool logs + manual notes |
| Merge readiness time | Proof-complete → merge-ready | Automatic | Proof timestamp + PR ready timestamp |

For software delivery outcomes, track DORA-style lead time and change failure rate at the repo or team level, because “the agent was fast” is useless if production gets worse. DORA’s current guidance still centres change failure rate and related operational outcomes. citeturn18search3turn18search7

## Failure modes and anti-patterns

The dangerous failure modes are not subtle. They are boring, repeated, and expensive: self-approval, stale context, unreviewable diffs, fake proof, and merge decisions made from vibes because the volume of AI-generated code outpaced judgment. Salesforce’s review-system writeup, Spotify’s background-agent series, Anthropic’s harness notes, and NIST SSDF all point in roughly the same direction: **if you do not redesign the review and evidence layer, AI simply moves the bottleneck and hides defects behind velocity.** citeturn26view0turn29view2turn13view10turn13view12turn20view1

| Failure mode | How it happens | Why it matters | Early warning signs | Prevention | Recovery protocol |
|---|---|---|---|---|---|
| Implementer self-approval | Same session writes and “reviews” its own change | Confirmation bias dressed as audit | Review comments are vague or absent | Fresh-context auditor; protected-branch review gates | Re-audit in read-only mode; do not merge from same-session review |
| Supervisor hallucinating repo state | ChatGPT or any planner infers files, commands, or architecture it never saw | Bad packets poison the whole lane | Packet references missing files or wrong commands | Require repo evidence before packet finalization | Reject packet; regenerate from actual repo context |
| Auditor trusting summaries instead of diffs | Auditor reads handoff prose, not the change | Scope drift and logic bugs slip through | Audit report mentions no file paths or exact findings | Auditor must inspect diff and changed-file inventory | Re-run audit from diff + proof only |
| Stale context | Long sessions accumulate dead branches, failed ideas, unrelated files | Model behaviour degrades as context fills | Repeated confusion; forgotten constraints | Use `/clear`, rewinds, fresh sessions, smaller packets | Start fresh from packet and latest clean state |
| Duplicate agents editing same files | Parallel work without write-scope partitioning | Merge conflicts and silent overwrites | Same files appear in multiple lanes | One task per worktree; lane map; serialize shared files | Rebase or reset conflicting lanes; create integration packet |
| Parallel worktree collision | Worktrees share assumptions but not branch discipline | Confusing branch history, bad diffs | Wrong branch names; surprise untracked files | Strict branch naming and ACTIVE pointer | Stop all lanes; reconcile branch map; reassign work |
| Excessive ceremony on trivial tasks | Full process applied to tiny changes | Throughput dies for no gain | Packet overhead exceeds change time | Use fast-lane thresholds | Collapse to lightweight path and record why |
| Packets too broad | “Implement OAuth” instead of one mergeable unit | Drift is guaranteed | Allowed files cover half the repo | Force packet splitting | Reject packet; split by behaviour or layer |
| Proof that cannot be replayed | Handwritten proof, missing logs, vague commands | Audit becomes fiction | “Ran tests successfully” with no outputs | Auto-generate proof from scripts | Mark unverifiable; rerun validation |
| CI passes but behaviour is still wrong | Weak tests or wrong acceptance criteria | Highest trust-destroying failure | PR looks clean; bugs arrive after merge | Stronger acceptance criteria; visual/manual proof where needed | Hotfix packet + acceptance test packet |
| Local/cloud environment mismatch | Codex cloud or remote lane differs from local truth | Passing cloud run, failing real repo | “Works in cloud” but fails locally | Pin env setup; use devcontainers/SSH/local when truth matters | Reproduce locally; switch tools or elevate lane |
| Agent fixing outside scope | Model “helpfully” edits unrelated files | Review noise and hidden regressions | Extra files, formatting changes, dependency churn | Allowed-files list; changed-file inventory; auditor scope check | Revert unrelated edits; re-open smaller packet |
| Model disagreement with no resolution protocol | Competing agent opinions, no evidence standard | Decisions become subjective | Endless debate, no new test or replay | Evidence-first tie-break; supervisor narrows dispute | Create decisive micro-test or spike; human resolves |
| Acceptance from vibes | Pressure to merge because work “looks good” | Governance failure | Thin proof, weak audit, strong confidence language | Acceptance memo with evidence relied on | Reject and require missing proof |

Some practices are just stupid in practice. Using both Codex and Claude on every task is usually stupid. Letting memory files or prompt text stand in for policy enforcement is stupid; Anthropic says memory is loaded as context, not enforced config, and Codex instruction loading has precedence and size rules, so policy-critical constraints belong in **managed settings, hooks, rules, CI, and GitHub protections**, not in wishful markdown alone. And accepting giant PRs because “the agent already checked it” is stupid; Salesforce’s whole point is that under AI load, review itself must be re-architected. citeturn13view2turn9view3turn13view1turn13view7turn36view0turn26view0

The most dangerous anti-pattern of all is pretending that faster generation means the old review process is still sufficient. It isn’t. The review layer must get more selective, more evidence-based, and more explicit about where human judgment still sits. citeturn26view0turn29view2

## Adoption plan and final SOP

The practical mistake most teams make is trying to “fully transform” on day one. Don’t. Start by standardizing packets, proof, and routing. Then introduce independent audit only where it clearly earns its keep. OpenAI’s own Codex guidance talks about AI-native planning/scoping, while Anthropic’s long-running-agent material repeatedly emphasizes harness design, test feedback, and environment setup instead of blind autonomy. citeturn24view0turn13view10turn13view11turn13view12

### Recommended 30-day adoption plan

| Week | Goal | What to implement | Success criterion |
|---|---|---|---|
| **Week one** | Baseline workflow and templates | Create packet template, proof schema, fast-lane rules, default branch/worktree naming, one Claude implementer prompt, one auditor prompt | Every non-trivial task uses a bounded packet and honest proof |
| **Week two** | Proof and audit hardening | Add command logging, CI artifact uploads, changed-file inventory, independent audit trigger rules, GitHub branch protections/CODEOWNERS review where needed | Audits reject incomplete proof instead of guessing |
| **Week three** | Parallelization and tool routing | Introduce Codex Web/App for bounded background tasks; define when Claude vs Codex wins; add ACTIVE pointer and per-lane branch map | At least two parallel lanes run without file collision or scope confusion |
| **Week four** | Metrics, cleanup, optimization | Track cycle time, audit fail rate, scope drift, proof completeness, CI failure, interruption count; prune pointless ceremony; package repeated steps into skills | Process becomes faster *and* cleaner, not just bigger |

### Recommended final operating model

| Lane | Use when | Supervisor | Implementer | Auditor | Merge rule |
|---|---|---|---|---|---|
| **Default workflow** | Medium-risk repo work with normal testability | ChatGPT Web/Project | Claude Code CLI/Desktop | Fresh Claude read-only if needed + GitHub CI | Human accepts after proof + review |
| **Fast lane** | Small, reversible, boring changes | Human or lightweight ChatGPT thread | Claude or Codex, whichever is already in hand | GitHub PR/CI only | Human reviews diff and merges |
| **High-risk workflow** | Security, auth, money, CI/CD, public API, schema/data migration, complex refactor | ChatGPT Deep Research + human owner | Claude Code in controlled environment, or Codex only if cloud lane is trustworthy | Independent technical audit + optional ChatGPT policy/spec audit | Human acceptance is mandatory; branch protections required |
| **Emergency recovery workflow** | Failed or drifting implementation | Fresh supervisor session | Fresh worktree, usually with the *other* coding tool | Independent audit before retry merge | No merge from dirty state |
| **Parallel execution workflow** | Backlog fan-out, repeated maintenance, background work | ChatGPT Project as authority layer | Codex Web/App in one branch/worktree per lane | GitHub CI across all lanes; sampled fresh Claude audits on risky lanes | Integrate through serialized packets |
| **Weekly process improvement loop** | Continuous improvement | Human owner + ChatGPT summary | N/A | N/A | Review metrics, top rejects, slowest packets, and unnecessary steps |

The final recommendation is mercilessly simple.

**Default:** ChatGPT supervises when the task needs current research or a clean packet; Claude Code implements in the real repo; GitHub enforces; a separate auditor appears only when risk or ambiguity demands it.
**Cloud throughput lane:** ChatGPT or a human packets the work; Codex runs bounded tasks in the background and in parallel; GitHub holds the line; Claude audits selectively.
**High-risk lane:** human owner + ChatGPT Deep Research for scoping, Claude in a controlled local/SSH/devcontainer truth environment for implementation, independent fresh-context audit, and hard GitHub merge gates.
**Do not** normalize self-approval, giant packets, or proof by storytelling.
**Do** normalize small packets, replayable proof, strict scope, and human acceptance of anything consequential. citeturn11view0turn35view0turn37view0turn33view1turn22view0turn20view1turn26view0turn29view2
