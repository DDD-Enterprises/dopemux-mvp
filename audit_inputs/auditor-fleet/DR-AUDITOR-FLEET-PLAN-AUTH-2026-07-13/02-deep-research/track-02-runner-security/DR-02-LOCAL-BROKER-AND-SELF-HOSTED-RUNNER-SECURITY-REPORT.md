# DR-02 Local Broker and Self-Hosted Runner Security Report

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Track:** `DR-02-LOCAL-BROKER-AND-SELF-HOSTED-RUNNER-SECURITY`  
**Research date:** `2026-07-13`  
**Status:** `COMPLETE_WITH_UNKNOWNS`

## 1. Scope and evidence posture

**OBSERVED:** The accepted local capability probe is static-only. No audit broker or custom runner was implemented, every model-capable live probe was `NOT_RUN`, and plan-backed authentication and complete containment remain unproven. Mechanical validation is the only currently observed executable lane. `[LOCAL-01][LOCAL-02][LOCAL-03]`

**OBSERVED:** Importing the aggregate Dopemux CLI attempted a network-backed LiteLLM metadata fetch. The observed aggregate import path is therefore unsuitable for a trusted no-network broker preflight. `[LOCAL-03]`

**BOUNDARY:** This report compares security architectures and proposes track-level recommendations. It does not implement the broker, register a runner, test accounts, create credentials, execute candidate code, or perform final cross-track architecture synthesis.

## 2. Executive assessment

**CLAIMED:** GitHub warns that self-hosted runners do not provide the same fresh-environment guarantees as GitHub-hosted runners and may be persistently compromised by untrusted workflow code. GitHub strongly discourages using self-hosted runners for public repositories and advises caution for private repositories as well. `[GH-01][GH-02][GH-03]`

**INFERRED:** A persistent generic self-hosted runner that can execute PR-controlled workflows while holding persistent provider credentials is the worst candidate in this track. It combines hostile execution, durable credentials, reusable local state, and GitHub-controlled scheduling in one blast radius. Runner groups and labels reduce reachability but do not fix that collision.

**PROPOSED, first release:** Use an operator-triggered local broker that verifies the exact repository, PR, base SHA, and head SHA; keep any candidate-code execution in credential-free disposable workers; invoke plan-authenticated tools only through per-tool isolated, data-only adapters after DR-01 and DR-03 prove vendor permission and complete containment; publish results manually. Unsupported adapters remain disabled.

**PROPOSED, later automation:** Use a GitHub-hosted trusted-main workflow to create an exact-head request; authenticate direct submission with GitHub OIDC or verify pull-mode artifacts through GitHub APIs; dispatch through a local broker into disposable workers; publish through a separate least-privilege GitHub App bound to the exact head SHA.

**UNKNOWN:** This track does not establish that any personal plan credential can be converted into a short-lived per-run credential for a disposable VM or container. Copying cached login state is not assumed to be permitted, supported, or secure.

## 3. Questions answered

| ID | Question | Disposition |
|---|---|---|
| Q-GITHUB-WARNINGS | Current GitHub warnings for self-hosted runners | `ANSWERED` |
| Q-GITHUB-CONTROLS | Runner groups, labels, repository restrictions, approvals, environments | `ANSWERED` |
| Q-WORKFLOW-RISKS | `pull_request_target`, injection, reusable workflows, artifacts, caches, secrets | `ANSWERED` |
| Q-INERT-DIFF | Trusted-main retrieval of a diff without checkout or execution | `ANSWERED` |
| Q-EPHEMERAL | Ephemeral and autoscaled runner mechanisms | `ANSWERED` |
| Q-PROVENANCE | Repository, PR, SHA, workflow, freshness, and replay verification | `ANSWERED` |
| Q-SIGNING | OIDC, attestations, signed manifests, API verification | `PARTIAL` |
| Q-CREDENTIAL-ISOLATION | OS user, home, VM, container, and keychain isolation | `PARTIAL` |
| Q-MACOS | macOS account/keychain suitability | `PARTIAL` |
| Q-NETWORK | Per-tool network controls | `PARTIAL` |
| Q-OUTPUT | Safe result return without model write credentials | `ANSWERED` |
| Q-OPERATIONS | One-at-a-time execution, cleanup, revocation, logging, visibility | `ANSWERED` |
| Q-ARCH-SELECTION | First-release and later architecture candidates | `ANSWERED` |

Partial answers are explicit because tool-specific plan credential portability, complete disablement, and stable provider endpoint allowlists are owned by other tracks or require authorized local validation.

## 4. Threat model

### 4.1 Adversaries and hostile inputs

**PROPOSED threat model:** Treat these as attacker-controlled unless independently verified:

- PR code, build scripts, package manifests, tests, and repository instructions;
- PR title, body, comments, review text, branch names, commit messages, and filenames;
- artifacts, caches, generated reports, and reusable workflow outputs;
- any text supplied to an agentic model, including content that attempts to override the audit contract or trigger tools.

**INFERRED:** Agentic auditors widen the classic CI threat model. Prompt injection can turn inert-looking text into attempted shell, filesystem, browser, MCP, plugin, or network actions. A prompt saying “read only” is policy text, not a sandbox. `[GH-01][GHSL-02][AWI-01]`

### 4.2 Protected assets

- provider plan credentials, OAuth sessions, refresh state, and account tokens;
- GitHub App keys, installation tokens, PATs, and repository write authority;
- SSH keys, package-registry credentials, local keychains, developer home directories, and browser sessions;
- trusted workflow definitions, worker images, broker policy, replay state, and result-signing keys;
- private repository data and client-sensitive diffs;
- proof artifacts and exact-head provenance.

### 4.3 Primary attack paths

| Attack path | Risk | Required response |
|---|---|---|
| PR workflow scheduled onto credential-bearing runner | Credential exfiltration and persistence | Reject generic runner architecture |
| `pull_request_target` checks out PR head | Privileged execution of hostile code | Never check out or execute candidate code in trusted context |
| Untrusted metadata embedded in shell script | Workflow injection | Pass through environment or structured input; avoid direct interpolation |
| Privileged workflow consumes low-trust artifact | Artifact poisoning | Treat artifact as hostile data; verify origin and digest; never execute |
| Privileged workflow restores poisoned cache | Code execution | Do not share executable caches across trust levels |
| Agent reads hostile instructions with tools enabled | Agentic workflow injection | Disable tools externally or keep adapter blocked |
| Result publisher shares process or credential with model | GitHub write credential theft | Separate publisher component and identity |
| Request is replayed or PR head changed | Wrong-code approval | Freshness, nonce, durable replay store, exact-head recheck |

## 5. GitHub security controls and their limits

### 5.1 Self-hosted runner warnings

**CLAIMED:** GitHub-hosted runners normally provide fresh job environments, while self-hosted runners retain operator-managed state and may be persistently compromised. `[GH-01][GH-02][GH-03]`

**INFERRED:** “Dedicated” does not mean “safe.” A machine can be dedicated to auditing and still be a generic runner reachable by unsafe workflow code. The deciding question is which trusted workflow definitions can schedule it and whether candidate-controlled content can execute there.

### 5.2 Runner groups and labels

**CLAIMED:** Runner groups can restrict access by organization, repository, and selected workflow. Exact selected-workflow restrictions are materially stronger than labels. `[GH-05][GH-06]`

**CLAIMED:** Labels route jobs but are not attested platform identity. They should not be used as proof that a runner has a particular security posture.

**PROPOSED:** If self-hosted workers are ever introduced, place them in a dedicated group restricted to a trusted workflow path pinned to a protected ref or full commit SHA. This remains defense in depth, not permission to install persistent plan credentials.

### 5.3 Fork approvals and repository Actions policy

**CLAIMED:** GitHub allows repositories and organizations to control which actions and reusable workflows may run, whether fork PR workflows require approval, and whether actions must be pinned to immutable full SHAs. `[GH-07][GH-01]`

**INFERRED:** Approval of a fork workflow is not equivalent to review of every command that candidate code can cause to execute. Approval reduces accidental execution; it does not make candidate code trusted.

### 5.4 Environments and workflow execution protections

**CLAIMED:** Environments can require reviewers and restrict access to environment secrets. Workflow execution protections can restrict actors and event types before workflows run. `[GH-08][GH-09]`

**LIMIT:** These are scheduling and secret-release controls. They do not provide kernel, filesystem, process, or network containment after a hostile workload starts.

### 5.5 Branch protection and required checks

**CLAIMED:** Branch protection can require checks and can bind a required status/check to an expected GitHub App source. `[GH-19]`

**PROPOSED:** Use branch protection to trust only the dedicated audit publisher. Do not let the model or worker publish directly.

## 6. Workflow, artifact, and cache risks

### 6.1 `pull_request_target`

**CLAIMED:** `pull_request_target` runs in the trusted base-repository context. The dangerous pattern is fetching or checking out the untrusted head and then executing it with elevated token or secret access. `[GH-04][GHSL-01]`

**PROPOSED:** A trusted-main request workflow may inspect metadata and retrieve a diff as data, but must not:

- use `actions/checkout` on the PR head;
- execute scripts, actions, package hooks, tests, or generated binaries from the PR;
- import candidate-controlled modules;
- source candidate environment files;
- consume candidate-controlled reusable workflows.

### 6.2 Reusable workflows

**INFERRED:** A reusable workflow is part of the trusted computing base only when the caller and called workflow are both pinned and protected. Passing attacker-controlled values into privileged reusable workflows can still create injection or confused-deputy paths.

### 6.3 Artifacts

**CLAIMED:** GitHub artifacts have transfer digests, but a valid digest proves that the downloaded bytes match the uploaded bytes, not that the producer was trusted or the content is safe to execute. `[GH-14]`

**PROPOSED:** A request artifact may contain a canonical JSON manifest and a diff blob, but the broker treats both as hostile data. It verifies run identity, producer workflow, repository, SHAs, digest, size limits, and schema before use. It never extracts into a shared writable directory or executes content from the artifact.

### 6.4 Caches

**CLAIMED:** GitHub documents cache-poisoning risk and warns against storing sensitive data in caches. `[GH-15][CODEQL-01]`

**PROPOSED:** Do not use Actions caches as a trust bridge between low-trust PR jobs and privileged request or publication jobs. Disposable audit workers should start without inherited build caches unless a separately trusted, content-addressed cache policy is proven.

## 7. Trusted-main diff retrieval as inert data

**CLAIMED:** GitHub REST endpoints can return PR metadata, changed files, and diff or patch media types without checking out the branch. `[GH-16]`

**PROPOSED retrieval rule:**

1. Resolve the repository by immutable `repository_id` and expected owner/name.
2. Read PR metadata and record `pr_number`, `base.ref`, event `base.sha`, `head.ref`, and `head.sha`.
3. Fetch the diff or selected file contents using API endpoints, never by executing candidate Git operations on the credential-bearing host.
4. Store `diff_sha256`, byte count, file count, and retrieval timestamp.
5. Re-query the PR immediately before dispatch. Reject if the head SHA changed.
6. Re-query again before publication. Mark the result stale rather than publishing against a different head.

**INFERRED:** The diff itself remains hostile. A parser, renderer, model, or wrapper must not interpret diff text as a command channel.

## 8. Comparative architecture matrix

| Candidate | Exact-head provenance | Persistent credential exposure | Hostile execution isolation | Operational burden | Track verdict |
|---|---:|---:|---:|---:|---|
| 1. Operator-triggered local audit broker | High with API cross-checks | Low if broker is data-only | Good when execution is delegated | Moderate | **PROPOSED for first release** |
| 2. Persistent dedicated self-hosted runner | Medium | **High** | **Poor** | Moderate | **REJECTED** |
| 3. Ephemeral self-hosted runner | High potential | High if credentials are injected | Better persistence hygiene, same-run exfiltration remains | High | **REJECTED for credential-bearing hostile work; usable for credential-free mechanical jobs** |
| 4. Broker plus isolated per-tool worker accounts | High | Medium | Same-kernel boundary only | Moderate | **PROPOSED as defense in depth, not sole sandbox** |
| 5. Broker plus disposable VM/container workers | High | Low if workers are credential-free | Strongest local isolation; VM preferred | High | **PROPOSED for candidate execution** |
| 6. GitHub-hosted workflow emits verified local request | Very high | Low on local ingress | Strong ingress separation | Moderate | **PROPOSED for later automation** |
| 7. Manual local audit with artifact upload | High when SHAs are recorded | Low | Strong; no automatic PR execution | Low to moderate | **PROPOSED immediate fallback** |

### Matrix interpretation

**REJECTED:** Candidate 2 collapses GitHub scheduling, hostile execution, persistent credentials, local state, and logs into one trust zone.

**LIMITED:** Candidate 3 improves cleanup but cannot prevent a malicious job from exfiltrating credentials during its only run. Ephemerality is a broom, not a force field.

**PROPOSED:** Candidate 4 is valuable for per-tool configuration and keychain separation, but same-host code execution remains too close to persistent credentials.

**PROPOSED:** Candidate 5 is the correct execution boundary for mechanical validators or any operation that must run candidate code. Containers are acceptable only for lower-risk isolation where shared-kernel risk is explicitly accepted; disposable VMs are preferred for hostile code.

## 9. Signed request and provenance requirements

### 9.1 Canonical request envelope

**PROPOSED:** A request envelope should contain at least:

```json
{
  "schema_version": "1.0.0",
  "request_id": "uuid",
  "repository": "owner/name",
  "repository_id": 123,
  "repository_owner_id": 456,
  "pr_number": 42,
  "base_ref": "main",
  "event_base_sha": "...",
  "head_ref": "feature",
  "head_sha": "...",
  "workflow_repository": "owner/name",
  "workflow_path": ".github/workflows/audit-request.yml",
  "workflow_ref": "owner/name/.github/workflows/audit-request.yml@<trusted-ref-or-sha>",
  "run_id": 123456,
  "run_attempt": 1,
  "actor": "login",
  "actor_id": 789,
  "event_name": "pull_request_target-or-approved-event",
  "created_at": "2026-07-13T00:00:00Z",
  "expires_at": "2026-07-13T00:10:00Z",
  "nonce": "random-128-bit-or-more",
  "payload_sha256": "...",
  "diff_sha256": "...",
  "requested_route": "mechanical-or-specific-adapter"
}
```

**PROPOSED validation order:**

1. Parse with a strict schema and reject unknown fields where practical.
2. Verify transport identity: OIDC in direct push mode, or GitHub API identity in pull mode.
3. Verify issuer, audience, signature, repository, workflow, ref/SHA, actor, run, and event claims.
4. Verify the workflow run and PR through GitHub APIs.
5. Confirm the PR still has the same `head_sha` and expected base relationship.
6. Verify artifact and diff digests.
7. Enforce expiry and a durable single-use replay record keyed by `request_id`, `run_id`, `run_attempt`, and nonce.
8. Record an immutable broker receipt before worker launch.

### 9.2 OIDC direct push mode

**CLAIMED:** GitHub Actions can request a signed OIDC JWT with repository and workflow identity claims. `[GH-10][GH-11]`

**PROPOSED:** The workflow sends the manifest and OIDC token directly to the broker over authenticated TLS. The broker must enforce a broker-specific audience and narrow claim policy. GitHub’s own gateway example warns that a valid GitHub OIDC token proves only that some Actions workflow obtained it unless application-specific claims are checked. `[GH-12]`

### 9.3 Pull pickup mode

**PROPOSED:** If the broker polls GitHub rather than accepting inbound requests, the workflow uploads the manifest and diff as artifacts. The broker uses a read-only GitHub App or other approved API credential to verify repository, run, workflow, actor, SHAs, artifact digest, and freshness.

**PROPOSED:** Do not place the raw OIDC bearer token in the artifact. It is short-lived and reusable by whoever obtains it during validity. OIDC is an online identity proof, not a durable signed manifest file.

### 9.4 Artifact attestations

**CLAIMED:** GitHub artifact attestations provide Sigstore-backed provenance evidence and can be verified. `[GH-13]`

**UNKNOWN:** Their best-supported use is build provenance, and plan availability or suitability for frequent audit-request manifests is not established here. Use them only as supporting evidence. They do not replace API cross-checks, freshness, replay prevention, or policy authorization.

## 10. Result envelope and safe output channels

### 10.1 Result envelope

**PROPOSED:** The worker or adapter emits a result envelope containing:

- request ID and request-envelope digest;
- repository ID, PR number, event base SHA, and exact head SHA;
- audit route, tool, requested model, observed model if available, provider, and identity confidence;
- worker image/template digest and isolation mode;
- start/end timestamps, exit code, timeout state, and typed failure class;
- findings payload digest and any evidence-file digests;
- network policy identifier and whether fallback occurred;
- explicit `stale_head`, `environment_failure`, and `model_quality_failure` fields;
- broker signature or MAC over the canonical result.

### 10.2 Publication

**PROPOSED, first release:** Human operator uploads or pastes the result after verifying the exact head SHA.

**CLAIMED:** GitHub Checks write access is designed for GitHub Apps, and protected branches can require expected check sources. `[GH-18][GH-19]`

**PROPOSED, later:** A separate publisher service or GitHub App reads only the sealed result spool, verifies the broker signature and exact head SHA, then creates the check or status. The model and candidate-processing worker never receive GitHub write credentials.

## 11. Credential isolation requirements

### 11.1 Non-negotiable requirements

**PROPOSED:**

- No persistent provider credential in a generic self-hosted runner.
- No GitHub write credential in the model process or candidate-processing worker.
- Separate OS user, home directory, configuration root, logs, temp directory, and keychain/secret store per provider tool.
- No shared writable plugin, MCP, hook, cache, extension, or instruction directories across tool profiles.
- Broker runs as a dedicated non-admin user and does not execute candidate code.
- Candidate execution workers receive no persistent provider or GitHub credentials.
- Credentials are never copied from a human workstation profile merely because the files are technically portable.
- An adapter is disabled when vendor permission, credential lifecycle, or complete containment is `UNKNOWN`, `CLAIMED`, or `CONFLICTING`.

### 11.2 Plan-authenticated model invocation

**UNKNOWN:** This track cannot prove that providers issue short-lived disposable-worker credentials for plan usage.

**PROPOSED fail-closed posture:** Where a provider only supports a persistent local login, the model adapter may run only as a data-only process in its isolated account, with shell/filesystem/tools/plugins/MCP/hooks/memory/subagents disabled by enforceable controls proven in DR-03. If those controls are not fully proven, use manual app/CLI review or disable the route.

### 11.3 OS user versus VM/container

| Boundary | Strength | Approved use |
|---|---|---|
| Separate process only | Weak | Not sufficient for credential isolation |
| Separate home/config | Moderate against accidents | Required per tool, not sufficient alone |
| Separate macOS user/keychain | Moderate defense in depth | Credential-bearing data-only adapter |
| Container | Moderate, shared kernel | Credential-free lower-risk worker; explicit risk acceptance |
| Disposable VM | Stronger kernel boundary | Preferred for hostile candidate execution |
| Separate physical/remote host | Strongest operational separation | Later option where cost and maintenance justify it |

## 12. macOS account and keychain assessment

**CLAIMED:** macOS supports separate users and keychain access controls. `[APPLE-01][APPLE-02]`

**INFERRED:** This supports per-tool credential segregation and reduces accidental cross-profile reads. It does not make hostile code safe on the same host. A local privilege escalation, kernel exploit, misconfigured shared group, writable shared directory, launch agent, or privileged helper can cross the intended boundary.

**PROPOSED:**

- create dedicated non-admin users for broker and each credential-bearing tool;
- disable remote login and unnecessary sharing for those users;
- prohibit shared writable config, cache, plugin, and temp locations;
- keep broker and tool users out of administrator groups;
- use separate keychains and lock/unlock policy appropriate to supervised operation;
- never execute candidate code under those users;
- prefer a VM for any worker that executes candidate code.

## 13. Network controls

**CLAIMED:** Apple’s built-in firewall is focused on incoming connections, and Apple states that Packet Filter is not a supported product API. `[APPLE-03][APPLE-04]`

**CLAIMED:** Docker provides explicit network modes, including isolated and user-defined bridge networks, but containers share the host kernel. `[DOCKER-01][DOCKER-02]`

**PROPOSED network classes:**

| Worker class | Network posture |
|---|---|
| Mechanical validation | `NONE` by default; allow only explicitly required local services |
| Candidate-code execution | `NONE` by default; use a controlled dependency mirror only when justified |
| Plan-authenticated model adapter | Provider-only egress plus required auth refresh; no inbound access; exact endpoints remain tool-specific `UNKNOWN` |
| GitHub request verifier | GitHub API/OIDC endpoints only |
| Result publisher | GitHub API only |

**UNKNOWN:** Stable provider endpoint allowlists for each CLI are not established. CDN, update, telemetry, browser-login, and refresh behavior can make hostname-only policy brittle. Until DR-03 and authorized observation resolve this, network restriction is an architectural requirement, not a proven per-tool configuration.

## 14. Recommended first-release architecture

**PROPOSED:**

```text
Human operator
  -> requests audit for repo + PR

Local broker user (no candidate execution)
  -> resolves repository_id and PR through GitHub API
  -> records base SHA, head SHA, diff digest, freshness
  -> selects only an eligible route
  -> acquires durable single-audit lease

Mechanical route
  -> disposable credential-free VM/container
  -> no network by default
  -> sealed result envelope

Plan-auth model route, only when DR-01 + DR-03 permit
  -> dedicated per-tool non-admin account
  -> data-only input, no repository checkout
  -> enforceable no-shell/no-write/no-MCP/no-plugin posture
  -> sealed result envelope

Human operator
  -> verifies exact head still matches
  -> uploads or posts result manually
```

### Why this is the first release

- It does not require exposing a local host to arbitrary GitHub job scheduling.
- It keeps GitHub write authority outside the model.
- It gives the operator visibility into every request and result.
- It supports the already observed mechanical lane immediately.
- It keeps unproven model adapters disabled instead of laundering CLI installation into permission.
- It can later evolve into automated ingress and publication without changing the core trust boundaries.

## 15. Recommended later automated architecture

**PROPOSED:**

```text
GitHub-hosted trusted-main request workflow
  -> no PR-head checkout or execution
  -> canonical request manifest + diff digest
  -> OIDC-authenticated POST to broker
     OR artifact upload for API-verified pickup

Local broker
  -> verifies OIDC/API identity, workflow, run, actor, repo, PR, SHAs
  -> freshness + replay checks
  -> durable lease and audit receipt
  -> launches disposable credential-free execution worker
  -> invokes only eligible isolated model adapter
  -> seals result envelope

Dedicated publisher GitHub App
  -> verifies broker seal and exact head SHA
  -> creates check/status for that head only

Branch protection / PR Steward
  -> consumes result as evidence
  -> retains human approval authority
```

**PROPOSED:** GitHub-hosted ingress is preferred because request creation occurs in a fresh hosted environment and the local machine receives a narrowly defined data object rather than arbitrary workflow execution.

## 16. Trust-boundary diagram

```text
[UNTRUSTED CONTRIBUTOR]
  controls PR code, metadata, comments, artifacts, caches
        |
        v
[GITHUB REPOSITORY / PR]
        |
        | trusted-main workflow reads metadata + diff as DATA ONLY
        v
[GITHUB-HOSTED REQUEST JOB]
  no candidate checkout, no provider credential
        |
        | OIDC-authenticated request or API-verifiable artifact
        v
[LOCAL BROKER]
  verifies identity, SHAs, freshness, replay
  holds routing policy, not approval authority
  never executes candidate code
        |
        +------------------------------+
        |                              |
        v                              v
[CREDENTIAL-FREE DISPOSABLE WORKER]  [ISOLATED TOOL ADAPTER]
  mechanical/candidate execution      persistent plan credential only if proven
  no GitHub write credential          data-only, no candidate execution
        |                              |
        +--------------+---------------+
                       v
               [SEALED RESULT SPOOL]
                       |
                       v
            [HUMAN OR GITHUB APP PUBLISHER]
              exact-head bound, least privilege
                       |
                       v
              [PR STEWARD / HUMAN GATE]
```

## 17. One-audit-at-a-time, logging, revocation, and visibility

**CLAIMED:** GitHub concurrency can serialize workflows or jobs. `[GH-22]`

**PROPOSED:** Use both GitHub concurrency and a broker-side durable lease. GitHub concurrency does not protect against manual or duplicate broker submissions, while a local mutex alone does not serialize upstream requests.

**CLAIMED:** GitHub recommends forwarding ephemeral runner logs externally. `[GH-23]`

**PROPOSED:** Stream broker and worker logs to append-only external storage before worker destruction. Log:

- request and result digests;
- verified GitHub identities and SHAs;
- selected route and eligibility evidence;
- worker image/template digest;
- network policy;
- process exit, timeout, and cleanup state;
- publication receipt or manual-upload acknowledgement.

**PROPOSED revocation:** Disabling a tool adapter, removing a GitHub App installation, revoking a provider session, or marking a worker image untrusted must prevent new dispatch immediately. Existing jobs should be terminated unless an operator explicitly preserves them for forensic review.

## 18. Failure and recovery model

| Failure | Required state transition |
|---|---|
| OIDC signature, audience, or claim failure | `REJECTED_IDENTITY`; no worker launch |
| API repository/PR/SHA mismatch | `REJECTED_PROVENANCE` or `STALE_HEAD` |
| Expired request or replay | `REJECTED_FRESHNESS`; alert and retain receipt |
| Unsupported or unknown adapter state | `BLOCKED_TOOL_INELIGIBLE`; no fallback |
| Worker timeout/crash | `ENVIRONMENT_FAILURE`; destroy worker; preserve external logs |
| Candidate tries network or forbidden write | `CONTAINMENT_VIOLATION`; terminate and quarantine worker template |
| Model output malformed | `MODEL_OUTPUT_INVALID`; do not publish; no automatic stronger-model promotion |
| Result publisher failure | `PUBLICATION_PENDING`; keep sealed result for operator review |
| Head changes before publication | `STALE_HEAD`; never publish as current |
| Broker crash with lease held | recover from durable lease expiry; never attach blindly to old worker |
| Suspected credential exposure | disable adapter, revoke session where possible, preserve evidence, require operator clearance |

**PROPOSED:** Environment failure, policy failure, and model-quality failure remain separate. A broken runner must not silently trigger a more expensive or less private model route.

## 19. Security controls mapped to enforcement source

| Control | Prompt | CLI | Wrapper | OS | VM/container | GitHub | Operator |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Treat candidate content as hostile | ✓ |  | ✓ |  |  |  | ✓ |
| No PR-head checkout in trusted context |  |  | ✓ |  |  | ✓ | ✓ |
| Strict request/result schema |  |  | ✓ |  |  |  |  |
| Repository/PR/SHA/API verification |  |  | ✓ |  |  | ✓ |  |
| OIDC audience/claim verification |  |  | ✓ |  |  | ✓ |  |
| Freshness and replay prevention |  |  | ✓ |  |  |  |  |
| Disable shell, write, MCP, hooks, plugins | ✓ | ✓ | ✓ | ✓ | ✓ |  |  |
| Per-tool user/home/keychain isolation |  |  | ✓ | ✓ |  |  | ✓ |
| No persistent credentials in hostile worker |  |  | ✓ | ✓ | ✓ |  |  |
| Network egress restriction |  |  | ✓ | ✓ | ✓ |  |  |
| Restrict runner group and workflow |  |  |  |  |  | ✓ | ✓ |
| Pin actions and reusable workflows |  |  |  |  |  | ✓ | ✓ |
| One active audit |  |  | ✓ |  |  | ✓ |  |
| Destroy disposable worker |  |  | ✓ |  | ✓ |  |  |
| Separate GitHub App publisher |  |  | ✓ | ✓ |  | ✓ | ✓ |
| Final approval authority |  |  |  |  |  |  | ✓ |

**INFERRED:** Prompt and CLI controls are useful but insufficient by themselves. The most important controls belong to wrappers, operating-system accounts, VM/container boundaries, GitHub policy, and the human approval gate.

## 20. Contradictions and resolution

### C-001: Ephemeral runner recommendation versus same-run exfiltration

**CONFLICTING:** GitHub recommends ephemeral runners for autoscaling and cleanup. That does not mean a credential-bearing ephemeral job is safe while it is running.

**RESOLVED:** Treat ephemerality as persistence hygiene. Require the hostile worker to be credential-free or keep candidate execution out of the credential-bearing domain.

### C-002: Artifact attestation provenance versus request authorization

**CONFLICTING:** Attestations prove provenance properties but do not by themselves authorize an audit request or prove it is fresh and unreplayed.

**CARRIED:** Use OIDC/API verification as mandatory. Attestations remain optional supporting evidence until intended use and plan availability are confirmed.

### C-003: macOS keychain isolation versus host isolation

**CONFLICTING:** Separate users/keychains are real boundaries for normal applications but are not equivalent to a separate kernel.

**RESOLVED:** Use them for per-tool credential separation only; use a disposable VM for hostile execution.

## 21. Unknowns

1. **UNKNOWN:** Which plan-backed tools officially permit dedicated-user, VM, or disposable-worker deployment without unsupported credential copying.
2. **UNKNOWN:** Which tools can prove complete disablement of shell, writes, MCP, plugins, hooks, skills, memory, subagents, repository instructions, and web access.
3. **UNKNOWN:** Stable per-tool provider endpoint allowlists and telemetry/update behavior.
4. **UNKNOWN:** Whether artifact attestations are available and intended for frequent request manifests on the actual GitHub plan.
5. **UNKNOWN:** The final worker technology for the actual macOS host.

These unknowns block automatic plan-authenticated execution or implementation choices, not the security conclusion that a credential-bearing generic runner must be rejected.

## 22. Activities not run

- No self-hosted runner was registered or executed.
- No GitHub workflow, repository setting, environment, runner group, or App was created or modified.
- No provider login, token inspection, credential copy, or account test occurred.
- No candidate code, artifact, cache, or reusable workflow was executed.
- No OIDC token was requested and no broker endpoint was tested.
- No live per-tool network allowlist was measured.

## 23. Recommendations

1. **REJECTED:** Persistent generic self-hosted runner with plan credentials.
2. **PROPOSED:** Operator-triggered broker plus manual publication for first release.
3. **PROPOSED:** Credential-free disposable worker for mechanical validation and any candidate execution.
4. **BLOCKED:** Plan-authenticated adapters until DR-01 and DR-03 evidence clears each tool.
5. **PROPOSED:** GitHub-hosted trusted-main request job, OIDC/API verification, disposable workers, and separate GitHub App publisher for later automation.
6. **PROPOSED:** macOS users/keychains as per-tool defense in depth, never as the sole hostile-code sandbox.
7. **PROPOSED:** Fail closed on identity, provenance, freshness, containment, adapter eligibility, network, timeout, and cleanup failures.

## 24. Synthesis implications

- Preserve Dopemux as operator control and route recommendation. The broker is an adapter/executor, not approval authority.
- Keep mechanical validation as a first-class credential-free route.
- Exclude the persistent generic self-hosted runner from the preferred architecture.
- Bind requests and results to exact repository identity, PR number, event base SHA, head SHA, workflow identity, payload digest, freshness, and replay state.
- Use OIDC for online workflow identity verification, not as an artifact-stored bearer token.
- Keep provider credentials, hostile execution, and GitHub write authority in separate trust domains.
- Carry all vendor-auth and per-tool containment unknowns into synthesis as fail-closed adapter eligibility gates.
- Avoid the observed aggregate Dopemux CLI import path in the offline broker.

## 25. Source ledger

| ID | Title | Publisher | Class | Publication/update | Accessed | URL or local reference |
|---|---|---|---|---|---|---|
| LOCAL-01 | Auditor Fleet Capability Probe Summary | Dopemux local capability probe | OFFICIAL_DOCUMENTATION | 2026-07-13 | 2026-07-13 | local:Auditor Fleet Capability Probe Summary |
| LOCAL-02 | Routing Constraints | Dopemux local capability probe | OFFICIAL_DOCUMENTATION | 2026-07-13 | 2026-07-13 | local:Routing Constraints |
| LOCAL-03 | Network And Containment Observations | Dopemux local capability probe | OFFICIAL_SECURITY | 2026-07-13 | 2026-07-13 | local:Network And Containment Observations |
| GH-01 | Secure use reference | GitHub | OFFICIAL_SECURITY | UNKNOWN | 2026-07-13 | https://docs.github.com/en/actions/reference/security/secure-use |
| GH-02 | Self-hosted runners reference | GitHub | OFFICIAL_DOCUMENTATION | UNKNOWN | 2026-07-13 | https://docs.github.com/en/actions/reference/runners/self-hosted-runners |
| GH-03 | Adding self-hosted runners | GitHub | OFFICIAL_DOCUMENTATION | UNKNOWN | 2026-07-13 | https://docs.github.com/actions/hosting-your-own-runners/adding-self-hosted-runners |
| GH-04 | Securely using pull_request_target | GitHub | OFFICIAL_SECURITY | UNKNOWN | 2026-07-13 | https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target |
| GH-05 | Runner groups | GitHub | OFFICIAL_DOCUMENTATION | UNKNOWN | 2026-07-13 | https://docs.github.com/en/actions/concepts/runners/runner-groups |
| GH-06 | Managing access to self-hosted runners using groups | GitHub | OFFICIAL_DOCUMENTATION | UNKNOWN | 2026-07-13 | https://docs.github.com/enterprise-cloud@latest/actions/hosting-your-own-runners/managing-self-hosted-runners/managing-access-to-self-hosted-runners-using-groups |
| GH-07 | Managing GitHub Actions settings for a repository | GitHub | OFFICIAL_DOCUMENTATION | UNKNOWN | 2026-07-13 | https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository |
| GH-08 | Deployments and environments | GitHub | OFFICIAL_DOCUMENTATION | UNKNOWN | 2026-07-13 | https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments |
| GH-09 | Workflow execution protections | GitHub | OFFICIAL_SECURITY | 2026-06-18 | 2026-07-13 | https://docs.github.com/en/organizations/managing-organization-settings/actions-policies/workflow-execution-protections |
| GH-10 | OpenID Connect | GitHub | OFFICIAL_SECURITY | UNKNOWN | 2026-07-13 | https://docs.github.com/en/actions/concepts/security/openid-connect |
| GH-11 | OpenID Connect reference | GitHub | OFFICIAL_DOCUMENTATION | UNKNOWN | 2026-07-13 | https://docs.github.com/actions/reference/openid-connect-reference |
| GH-12 | actions-oidc-gateway-example | GitHub | OFFICIAL_REPOSITORY | UNKNOWN | 2026-07-13 | https://github.com/github/actions-oidc-gateway-example/blob/main/oidc_gateway.go |
| GH-13 | Artifact attestations | GitHub | OFFICIAL_SECURITY | UNKNOWN | 2026-07-13 | https://docs.github.com/en/actions/concepts/security/artifact-attestations |
| GH-14 | Store and share data with workflow artifacts | GitHub | OFFICIAL_DOCUMENTATION | UNKNOWN | 2026-07-13 | https://docs.github.com/en/actions/tutorials/store-and-share-data |
| GH-15 | Dependency caching reference | GitHub | OFFICIAL_SECURITY | UNKNOWN | 2026-07-13 | https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching |
| GH-16 | REST API endpoints for pull requests | GitHub | OFFICIAL_DOCUMENTATION | UNKNOWN | 2026-07-13 | https://docs.github.com/en/rest/pulls/pulls |
| GH-17 | REST API endpoints for workflow runs | GitHub | OFFICIAL_DOCUMENTATION | UNKNOWN | 2026-07-13 | https://docs.github.com/en/rest/actions/workflow-runs |
| GH-18 | REST API endpoints for check runs | GitHub | OFFICIAL_DOCUMENTATION | UNKNOWN | 2026-07-13 | https://docs.github.com/rest/checks/runs |
| GH-19 | About protected branches | GitHub | OFFICIAL_DOCUMENTATION | UNKNOWN | 2026-07-13 | https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches |
| GH-20 | Actions Runner Controller | GitHub | OFFICIAL_DOCUMENTATION | UNKNOWN | 2026-07-13 | https://docs.github.com/en/actions/concepts/runners/actions-runner-controller |
| GH-21 | REST API endpoints for self-hosted runners | GitHub | OFFICIAL_DOCUMENTATION | UNKNOWN | 2026-07-13 | https://docs.github.com/rest/actions/self-hosted-runners |
| GH-22 | Control the concurrency of workflows and jobs | GitHub | OFFICIAL_DOCUMENTATION | UNKNOWN | 2026-07-13 | https://docs.github.com/actions/writing-workflows/choosing-what-your-workflow-does/control-the-concurrency-of-workflows-and-jobs |
| GH-23 | Monitoring and troubleshooting self-hosted runners | GitHub | OFFICIAL_DOCUMENTATION | UNKNOWN | 2026-07-13 | https://docs.github.com/actions/how-tos/managing-self-hosted-runners/monitoring-and-troubleshooting-self-hosted-runners |
| GHSL-01 | Keeping your GitHub Actions and workflows secure Part 1: Preventing pwn requests | GitHub Security Lab | INDEPENDENT_SECURITY_RESEARCH | 2021-08-03 | 2026-07-13 | https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/ |
| GHSL-02 | Keeping your GitHub Actions and workflows secure Part 2: Untrusted input | GitHub Security Lab | INDEPENDENT_SECURITY_RESEARCH | 2021-08-04 | 2026-07-13 | https://securitylab.github.com/resources/github-actions-untrusted-input/ |
| CODEQL-01 | Cache Poisoning via caching of untrusted files | GitHub CodeQL | OFFICIAL_SECURITY | UNKNOWN | 2026-07-13 | https://codeql.github.com/codeql-query-help/actions/actions-cache-poisoning-direct-cache/ |
| AWI-01 | Demystifying and Detecting Agentic Workflow Injection Vulnerabilities in GitHub Actions | arXiv preprint | INDEPENDENT_SECURITY_RESEARCH | 2026-05-08 | 2026-07-13 | https://arxiv.org/abs/2605.07135 |
| APPLE-01 | Keychain data protection | Apple | OFFICIAL_SECURITY | 2024-12-19 | 2026-07-13 | https://support.apple.com/en-ca/guide/security/secb0694df1a/web |
| APPLE-02 | Add a user or group on Mac | Apple | OFFICIAL_DOCUMENTATION | UNKNOWN | 2026-07-13 | https://support.apple.com/guide/mac-help/add-a-user-or-group-mchl3e281fc9/mac |
| APPLE-03 | Firewall security in macOS | Apple | OFFICIAL_SECURITY | UNKNOWN | 2026-07-13 | https://support.apple.com/en-ca/guide/security/seca0e83763f/web |
| APPLE-04 | TN3165: Packet Filter is not API | Apple | OFFICIAL_DOCUMENTATION | 2024-02-27 | 2026-07-13 | https://developer.apple.com/documentation/technotes/tn3165-packet-filter-is-not-api |
| DOCKER-01 | Networking overview | Docker | OFFICIAL_DOCUMENTATION | UNKNOWN | 2026-07-13 | https://docs.docker.com/engine/network/ |
| DOCKER-02 | Bridge network driver | Docker | OFFICIAL_DOCUMENTATION | UNKNOWN | 2026-07-13 | https://docs.docker.com/engine/network/drivers/bridge/ |
