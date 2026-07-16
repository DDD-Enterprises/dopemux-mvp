# DR Campaign Independent Acceptance Review

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Review date:** `2026-07-13`  
**Verdict:** `ACCEPT_WITH_CARRIED_UNKNOWNS`  
**GPT-5.6 Pro synthesis authorized:** `true`  
**Authorization scope:** architecture synthesis only, with every carried unknown and contradiction enforced as a fail-closed boundary.

## 1. Executive verdict

`OBSERVED` All five findings JSON files validate against the supplied Draft 2020-12 track schema. All five tracks have a report and findings file, identify every declared research question, and assign each question an allowed disposition: `ANSWERED`, `PARTIAL`, `UNKNOWN`, or `CONFLICTING`.

`INFERRED` The research packet is sufficiently complete and conservative for architecture synthesis. It is not sufficient to authorize unattended execution of any model-capable local adapter. The useful result is a map of supported vendor surfaces, prohibited shortcuts, security boundaries, and explicit gates. The packet does not prove local plan-backed authentication, complete containment, actual model identity, route quality, private-data permission, or deterministic subscription capacity.

`PROPOSED` Synthesis may proceed only if it preserves the following rule: an adapter with `UNKNOWN`, `CLAIMED`, or `CONFLICTING` authentication, containment, identity, privacy, cost, or certification evidence remains non-executable. Mechanical validation is the sole currently observed automatic lane.

No final broker, runner, adapter, or routing architecture is selected in this acceptance review.

## 2. Validation summary

| Check | Result | Acceptance assessment |
|---|---:|---|
| Five findings JSON files parse | PASS | All parse as JSON. |
| Five findings JSON files validate against `TRACK-FINDINGS.schema.json` | PASS | Draft 2020-12 validation with date format checking produced zero errors. |
| Every track question has an allowed disposition | PASS | 66 questions total; none omitted from the findings arrays. |
| Reports preserve `UNKNOWN`, `CONFLICTING`, and `NOT_RUN` | PASS | No model invocation or account test is laundered into observation. |
| Plan auth, API auth, cached sessions, and OpenRouter are distinct | PASS | The distinctions are repeated across DR-01, DR-03, and DR-05. |
| Local static evidence remains authoritative for the inspected host | PASS | External documentation extends policy knowledge but does not overwrite local state. |
| Self-hosted runner threat model is adversarial | PASS | Credential-bearing generic runners are rejected; hostile PR data is treated as attacker-controlled. |
| Grok Build and AGY automatic promotion is prevented | PASS | Grok remains version/auth/containment blocked; AGY remains research-only or operator-supervised. |
| Plan credits are not inferred from tokens | PASS | Subscription capacity remains non-deterministic and per-request debit remains `UNKNOWN`. |
| OpenRouter is not treated as identity, privacy, or release authority | PASS | It is restricted to controlled API fallback transport. |
| Prompt-injection contamination | PASS | No researched page instruction was treated as campaign authority; prompt injection appears only as a threat being analyzed. |
| Synthesis input set is hashable | PASS WITH EXCLUSIONS | Every accepted physical input is SHA-256 hashed in the synthesis manifest. Missing convenience/raw-receipt files are explicitly excluded. |

## 3. Track dispositions

| Track | Track status | JSON schema | Question coverage | Unknowns | Contradictions | Acceptance |
|---|---|---:|---:|---:|---:|---|
| `DR-01-VENDOR-PLAN-AUTH-AND-TERMS` | `COMPLETE_WITH_UNKNOWNS` | PASS | 16 (ANSWERED=6, CONFLICTING=2, PARTIAL=8) | 9 | 5 | ACCEPTED WITH CONDITIONS |
| `DR-02-LOCAL-BROKER-AND-SELF-HOSTED-RUNNER-SECURITY` | `COMPLETE_WITH_UNKNOWNS` | PASS | 13 (ANSWERED=9, PARTIAL=4) | 5 | 3 | ACCEPTED WITH CONDITIONS |
| `DR-03-TOOL-AUTOMATION-AND-CONTAINMENT` | `COMPLETE_WITH_UNKNOWNS` | PASS | 16 (ANSWERED=4, CONFLICTING=2, PARTIAL=9, UNKNOWN=1) | 9 | 4 | ACCEPTED WITH CONDITIONS |
| `DR-04-AUDIT-ROUTING-EVALUATION-AND-INDEPENDENCE` | `COMPLETE_WITH_UNKNOWNS` | PASS | 12 (ANSWERED=11, PARTIAL=1) | 3 | 2 | ACCEPTED WITH CONDITIONS |
| `DR-05-API-FALLBACK-PRIVACY-AND-COST` | `COMPLETE_WITH_UNKNOWNS` | PASS | 9 (ANSWERED=7, PARTIAL=2) | 7 | 4 | ACCEPTED WITH CONDITIONS |

### DR-01

`OBSERVED` DR-01 separates first-party subscription credentials from API credentials and third-party wrapper behavior. Claude Code `setup-token`, Codex access tokens, Gemini consumer deprecation, Antigravity programmatic surfaces, Grok Build headless use, and OpenRouter API authentication are not collapsed into one auth class.

`CONFLICTING` The Codex plan-list discrepancy remains carried. The Claude-through-OpenCode prohibition is sourced most directly to OpenCode's documentation rather than a matching Anthropic legal page. Neither issue is silently repaired.

### DR-02

`OBSERVED` DR-02 treats PR content, metadata, artifacts, caches, and agent instructions as hostile. It rejects a persistent generic self-hosted runner that combines PR execution and provider credentials. It separates ingress identity, candidate execution, provider credentials, and publication authority.

`UNKNOWN` Artifact attestation suitability, tool-specific credential portability, stable egress allowlists, and the final worker technology remain unresolved, but each has a bounded fail-closed effect.

### DR-03

`OBSERVED` DR-03 preserves installed-version evidence and blocks every model-capable CLI from unattended use. It distinguishes headless output from authentication permission and from full containment.

`CONFLICTING` Grok Build current documentation may not match installed `0.2.99`. AGY has a locally observed print surface and an official product family, but no accepted deterministic machine-readable audit receipt or complete containment contract.

### DR-04

`OBSERVED` DR-04 labels its taxonomy, routing ladder, benchmark, numeric thresholds, certification window, and revocation rules as `PROPOSED` rather than observed runtime policy. It explicitly states that no benchmark was run and no tool is certified for a lane.

`UNKNOWN` Dopemux-specific thresholds and route performance remain unknown. The provisional numeric gates are low-confidence policy candidates, not research-established constants.

### DR-05

`OBSERVED` DR-05 keeps subscription price, subscription limits, API usage, OpenRouter cost, local runner cost, and operator burden separate. It stores unavailable measurements as unknown rather than zero.

`CONFLICTING` OpenRouter's ZDR/data tags are useful filters but not definitive third-party policy evidence. Provider-native cost controls are not uniformly synchronous hard stops. These tensions are carried into synthesis.

## 4. Local capability evidence comparison

`OBSERVED` The accepted local artifacts establish:

- all live model probes were `NOT_RUN` or forbidden;
- all model-capable local auth modes remain `UNKNOWN`;
- all observed model identities remain `UNKNOWN`;
- mechanical validation is the only observed executable lane;
- pre-commit is potentially mutating and excluded from the offline lane;
- the aggregate Dopemux CLI attempted a network-backed LiteLLM metadata fetch during import;
- no automatic tool selection was made.

`OBSERVED` No track contradicts those host facts by claiming an observed plan-backed run, observed serving model, observed local API route, or proven live containment. Vendor documentation is consistently presented as `CLAIMED`, `INFERRED`, or `PROPOSED` when it extends the local record.

`CONFLICTING` Vendor documentation proves that some products expose supported non-interactive mechanisms. That does not prove that the currently installed local binaries use those mechanisms, that credentials are portable to the intended worker, or that the intended worker passes containment. Synthesis must preserve these as separate gates.

## 5. Targeted current-source spot checks

Limited web use was confined to load-bearing official claims. Access date: `2026-07-13`.

| Claim checked | Official source | Result |
|---|---|---|
| Claude Code offers a one-year OAuth `setup-token` for CI/scripts | `https://code.claude.com/docs/en/authentication` | CONFIRMED |
| Codex access tokens support trusted non-interactive local workflows and are available for Business/Enterprise | `https://developers.openai.com/codex/enterprise/access-tokens` | CONFIRMED |
| Gemini CLI stopped serving consumer individual, Google AI Pro, and Google AI Ultra login routes on 2026-06-18 | `https://developers.google.com/gemini-code-assist/docs/deprecations/code-assist-individuals` | CONFIRMED |
| Antigravity exposes official CLI and SDK surfaces, including silent/headless-oriented use | `https://antigravity.google/docs/cli-overview` and `https://antigravity.google/docs/sdk/overview` | CONFIRMED AT CAPABILITY LEVEL; unattended audit receipt and lifecycle remain unproven |
| Grok Build documents headless execution, streaming JSON, and API-key auth for non-browser environments | `https://docs.x.ai/build/overview` | CONFIRMED; installed-version containment remains unresolved |
| GitHub warns that self-hosted runners can be persistently compromised by untrusted workflow code | `https://docs.github.com/en/actions/reference/security/secure-use` | CONFIRMED |
| OpenRouter documents provider pinning, fallback disablement, required parameters, data filters, ZDR, and unit-price filters, while disclaiming definitive third-party policy authority | `https://openrouter.ai/docs/guides/routing/provider-selection` | CONFIRMED |
| OpenCode states that Anthropic prohibits Claude Pro/Max plugins and separately documents other subscription integrations | `https://opencode.ai/docs/providers/` | CONFIRMED AS AN OPENCODE CLAIM, not direct Anthropic legal evidence |

No broad replacement research was performed.

## 6. Source quality and traceability limitations

`OBSERVED` The combined JSON source ledgers contain 130 entries. Source-class distribution: `INDEPENDENT_SECURITY_RESEARCH` 3, `OFFICIAL_DOCUMENTATION` 77, `OFFICIAL_PRICING` 10, `OFFICIAL_REPOSITORY` 6, `OFFICIAL_SECURITY` 18, `OFFICIAL_TERMS` 4, `PEER_REVIEWED_RESEARCH` 8, `STANDARD` 4. More than half are current official documentation, terms, security, pricing, or official repositories.

`OBSERVED` 111 of 130 source-ledger entries use `null` for publication/update date. Some official pages do not expose a date, but several research papers and stable documents could have been dated more precisely. This is a traceability weakness, not evidence that the cited claims are false.

`OBSERVED` Additional metadata defects:

- DR-01 questions-supported metadata does not directly map `DR01-Q16`, although deployment conclusions cite multiple findings and sources.
- DR-03 findings use local aliases `L-CAP-MATRIX`, `L-NETWORK`, `L-ROUTING`, and `L-MECHANICAL`. The Markdown report defines them, but the JSON source ledger omits them because its ledger contains only web sources.
- DR-03 questions-supported metadata does not directly map `DR03-Q15` or `DR03-Q16`; those conclusions rely on the local aliases and synthesis across findings.
- DR-04 questions-supported metadata does not directly map `DR04-Q11`, although the relevant finding cites `SRC-02`, `SRC-03`, `SRC-04`, and `SRC-15`.
- DR-01 findings `DR01-F001` and `DR01-F020` have empty `source_refs`; their claims are nevertheless directly supported by the accepted local probe artifacts.
- DR-03 and DR-04 Markdown source ledgers omit direct URLs, reducing independent reproducibility from those reports alone.

`INFERRED` These defects do not require track rejection because the decisive recommendations are conservative, the local evidence is independently hashable, the load-bearing current vendor claims were spot-checked, and synthesis is prohibited from enabling an unknown route. They must remain visible and must not be interpreted as stronger source support than the packet contains.

## 7. Carried contradictions

- `DR-01-VENDOR-PLAN-AUTH-AND-TERMS::DR01-C001`: OpenAI sources present different complete lists of ChatGPT plans that include Codex. **Required posture:** preserve both positions and fail closed.
- `DR-01-VENDOR-PLAN-AUTH-AND-TERMS::DR01-C003`: The strongest explicit statement that Anthropic plan auth is prohibited in OpenCode comes from OpenCode documentation rather than an Anthropic terms page reviewed in this track. **Required posture:** preserve both positions and fail closed.
- `DR-01-VENDOR-PLAN-AUTH-AND-TERMS::DR01-C005`: xAI officially advertises headless Grok Build, but the explicit non-browser authentication path is API-key based and subscription-session runner permission is not documented. **Required posture:** preserve both positions and fail closed.
- `DR-02-LOCAL-BROKER-AND-SELF-HOSTED-RUNNER-SECURITY::C-002`: Artifact attestations provide provenance evidence, but their suitability as the primary authorization mechanism for frequent audit-request manifests is not established. **Required posture:** preserve both positions and fail closed.
- `DR-03-TOOL-AUTOMATION-AND-CONTAINMENT::DR03-C001`: Current Grok Build public documentation may describe a newer product surface than installed grok 0.2.99, whose captured help exposes a specific set of schema and containment flags. **Required posture:** preserve both positions and fail closed.
- `DR-03-TOOL-AUTOMATION-AND-CONTAINMENT::DR03-C002`: AGY 1.1.1 exposes a local print flag, while reviewed official material did not establish a stable unattended machine-readable proof contract. **Required posture:** preserve both positions and fail closed.
- `DR-03-TOOL-AUTOMATION-AND-CONTAINMENT::DR03-C003`: OpenCode can expose a configured provider/model string while actual serving provider, fallback behavior, and model identity remain unverified. **Required posture:** preserve both positions and fail closed.
- `DR-03-TOOL-AUTOMATION-AND-CONTAINMENT::DR03-C004`: Vendor documentation describes sandbox and configuration controls, while the accepted local packet requires installed-version proof that every prohibited inherited and agentic surface is disabled. **Required posture:** preserve both positions and fail closed.
- `DR-05-API-FALLBACK-PRIVACY-AND-COST::C-01`: OpenRouter can filter to endpoints tagged data-deny/ZDR, while its documentation says third-party data-policy tags are not definitive policy sources. **Required posture:** preserve both positions and fail closed.
- `DR-05-API-FALLBACK-PRIVACY-AND-COST::C-03`: Gemini project controls are called spend caps but official documentation permits enforcement latency and long-running-task overage. **Required posture:** preserve both positions and fail closed.
- `DR-05-API-FALLBACK-PRIVACY-AND-COST::C-04`: OpenAI names project spend-limit alerts, but the reviewed documentation describes threshold notification rather than request blocking. **Required posture:** preserve both positions and fail closed.
- `XTRACK-C001`: DR-01 establishes official Antigravity CLI and SDK surfaces, while DR-03 does not establish a stable machine-readable unattended audit receipt or complete containment contract. **Required posture:** Treat first-party programmatic capability as distinct from unattended audit-adapter eligibility. Keep AGY operator-supervised or disabled until the receipt, lifecycle, and containment contract is proven.
- `XTRACK-C002`: DR-01 establishes official Grok Build headless execution and an API-key route, while DR-03 records a version mismatch between current documentation and installed grok 0.2.99 plus incomplete containment. **Required posture:** Do not promote installed Grok Build to automation. Separate current vendor capability from installed-version conformance and plan-session permission.
- `XTRACK-C003`: DR-01 identifies first-party Claude Code and Codex non-interactive plan credentials, while DR-02 and DR-03 block local unattended use until worker trust, exact auth provenance, and installed-version containment are proven. **Required posture:** Vendor permission is necessary but not sufficient. Model adapters remain disabled until both deployment authorization and local security conformance pass.
- `XTRACK-C004`: DR-03 ranks Codex CLI and Claude Code as the strongest adapter candidates, while DR-04 prohibits binding any tool to a route before local evaluation and identity evidence exist. **Required posture:** Candidate priority may guide future conformance work, but it must not become route selection or certification.
- `XTRACK-C005`: DR-05 documents OpenRouter routing and ZDR filters, while DR-03 and DR-05 both state that router metadata and policy tags are not provider attestation or a definitive privacy authority. **Required posture:** Use OpenRouter only as pinned fallback transport. Missing upstream contract, exact route metadata, or provider identity invalidates governed proof.

## 8. Carried unknowns

All track unknowns are carried, not merged away:

- `DR-01-VENDOR-PLAN-AUTH-AND-TERMS::DR01-U001`: How is a Claude Code setup-token explicitly revoked before expiry, and is there an admin inventory for all such tokens? **Blocking scope:** Automated Claude Code deployment requiring immediate centralized revocation.
- `DR-01-VENDOR-PLAN-AUTH-AND-TERMS::DR01-U002`: What exact concurrency and machine-copy limits apply to personal-plan Codex cached authentication? **Blocking scope:** Parallel or shared personal-plan Codex runner pools.
- `DR-01-VENDOR-PLAN-AUTH-AND-TERMS::DR01-U003`: Which Workspace or Gemini Code Assist licenses permit persistent plan-backed Gemini CLI brokers or custom runners? **Blocking scope:** Plan-backed Gemini CLI automation outside a named workstation.
- `DR-01-VENDOR-PLAN-AUTH-AND-TERMS::DR01-U004`: What are Antigravity subscription credential storage, lifetime, refresh, revocation, and runner-class rules? **Blocking scope:** Persistent or ephemeral Antigravity plan-backed workers.
- `DR-01-VENDOR-PLAN-AUTH-AND-TERMS::DR01-U005`: Do OpenAI and GitHub explicitly authorize their subscription credentials inside OpenCode for unattended automation? **Blocking scope:** OpenCode plan-backed Codex or Copilot runner deployment.
- `DR-01-VENDOR-PLAN-AUTH-AND-TERMS::DR01-U006`: What lifecycle, revocation, sharing, and fair-use rules apply to plan-authenticated Grok Build sessions? **Blocking scope:** Unattended plan-backed Grok Build on any runner.
- `DR-01-VENDOR-PLAN-AUTH-AND-TERMS::DR01-U007`: How can each tool produce provider-attested actual model identity and billing-route evidence per run? **Blocking scope:** Independence claims, proof normalization, and plan-backed billing assertions.
- `DR-01-VENDOR-PLAN-AUTH-AND-TERMS::DR01-U008`: What unpublished fair-use or abuse thresholds could affect continuous high-frequency subscription audits? **Blocking scope:** High-volume unattended subscription automation.
- `DR-01-VENDOR-PLAN-AUTH-AND-TERMS::DR01-U009`: Can plan credentials be provisioned directly into a dedicated local OS account or VM without copying workstation session state? **Blocking scope:** Credential-isolated local broker workers.
- `DR-02-LOCAL-BROKER-AND-SELF-HOSTED-RUNNER-SECURITY::U-001`: Which plan-authenticated tools officially permit dedicated-user, VM, or disposable-worker deployment without copying unsupported login state? **Blocking scope:** Automatic plan-authenticated model execution for each affected tool.
- `DR-02-LOCAL-BROKER-AND-SELF-HOSTED-RUNNER-SECURITY::U-002`: Which tools can be proven to run with all shell, file-write, MCP, plugin, hook, memory, subagent, repository-instruction, and web surfaces disabled? **Blocking scope:** Data-only model invocation on a credential-bearing host or account.
- `DR-02-LOCAL-BROKER-AND-SELF-HOSTED-RUNNER-SECURITY::U-003`: What exact outbound endpoint allowlists are stable for each provider CLI, including login refresh, model calls, telemetry, and update checks? **Blocking scope:** Strict per-tool egress allowlisting.
- `DR-02-LOCAL-BROKER-AND-SELF-HOSTED-RUNNER-SECURITY::U-004`: Can GitHub artifact attestations be used as a durable, intended provenance layer for frequent request manifests on the repository plan in use? **Blocking scope:** Attestation-enhanced pull-mode pickup only; OIDC/API verification is not blocked.
- `DR-02-LOCAL-BROKER-AND-SELF-HOSTED-RUNNER-SECURITY::U-005`: Which disposable-worker technology is acceptable on the actual macOS host: Linux VM, macOS VM, container, or remote worker? **Blocking scope:** Final implementation choice, not the trust-boundary recommendation.
- `DR-03-TOOL-AUTOMATION-AND-CONTAINMENT::DR03-U001`: What exact authentication and billing route does each installed model-capable CLI use? **Blocking scope:** Unattended execution for every model-capable local adapter.
- `DR-03-TOOL-AUTOMATION-AND-CONTAINMENT::DR03-U002`: What provider-attested actual model identity is returned for each permitted live route? **Blocking scope:** Model identity proof and independence claims.
- `DR-03-TOOL-AUTOMATION-AND-CONTAINMENT::DR03-U003`: Can inherited configuration be completely isolated for Claude Code, Codex, Gemini CLI, OpenCode, Grok Build, and AGY? **Blocking scope:** Clean-room and unattended adapter promotion.
- `DR-03-TOOL-AUTOMATION-AND-CONTAINMENT::DR03-U004`: What stable, versioned exit-code contracts apply across the model tools? **Blocking scope:** Reliable orchestration, retry classification, and proof normalization.
- `DR-03-TOOL-AUTOMATION-AND-CONTAINMENT::DR03-U005`: Do Gemini CLI, OpenCode, and AGY support caller-supplied strict final-output schemas? **Blocking scope:** Direct proof-object emission without a normalizer.
- `DR-03-TOOL-AUTOMATION-AND-CONTAINMENT::DR03-U006`: Can OpenCode deterministically disable provider fallback and expose actual upstream provider and model identity? **Blocking scope:** OpenCode use in independence-critical or deterministic routes.
- `DR-03-TOOL-AUTOMATION-AND-CONTAINMENT::DR03-U007`: What containment contract applies specifically to installed Grok Build 0.2.99? **Blocking scope:** Grok Build operator-triggered or automated promotion.
- `DR-03-TOOL-AUTOMATION-AND-CONTAINMENT::DR03-U008`: Does AGY have an officially supported unattended receipt or export contract? **Blocking scope:** Any unattended AGY adapter.
- `DR-03-TOOL-AUTOMATION-AND-CONTAINMENT::DR03-U009`: Which OpenRouter routes enforce the required retention and zero-data-retention posture? **Blocking scope:** OpenRouter fallback enablement for non-public or sensitive repository data.
- `DR-04-AUDIT-ROUTING-EVALUATION-AND-INDEPENDENCE::DR04-U01`: What numeric routing thresholds are optimal for Dopemux? **Blocking scope:** Automatic route certification and promotion.
- `DR-04-AUDIT-ROUTING-EVALUATION-AND-INDEPENDENCE::DR04-U02`: Which plan-backed model tool should fill each lane? **Blocking scope:** Automatic model-lane binding.
- `DR-04-AUDIT-ROUTING-EVALUATION-AND-INDEPENDENCE::DR04-U03`: How do candidate routes perform on Dopemux repositories? **Blocking scope:** Claims of route quality, independence effectiveness, and certification.
- `DR-05-API-FALLBACK-PRIVACY-AND-COST::U-01`: What exact subscription credit or allowance does each audit request consume? **Blocking scope:** Subscription budget accounting and automatic admission.
- `DR-05-API-FALLBACK-PRIVACY-AND-COST::U-02`: What concurrency ceiling applies to each consumer or seat plan? **Blocking scope:** Unattended worker count and queue sizing.
- `DR-05-API-FALLBACK-PRIVACY-AND-COST::U-03`: What is the local runner hardware, electricity, maintenance, and failure cost? **Blocking scope:** Numerical total-cost comparison.
- `DR-05-API-FALLBACK-PRIVACY-AND-COST::U-04`: What contractual retention and compliance terms apply to the exact future OpenRouter upstream endpoint? **Blocking scope:** Any private or sensitive OpenRouter route.
- `DR-05-API-FALLBACK-PRIVACY-AND-COST::U-05`: Which low-cost models meet Dopemux audit-quality thresholds? **Blocking scope:** Automatic challenger or reviewer certification.
- `DR-05-API-FALLBACK-PRIVACY-AND-COST::U-06`: Do the repository and client contracts permit each direct provider API for private or client data? **Blocking scope:** Private/client-data egress.
- `DR-05-API-FALLBACK-PRIVACY-AND-COST::U-07`: Does Gemini expose a generic request-ID response header equivalent to OpenAI and Anthropic? **Blocking scope:** Uniform cross-provider request trace normalization.

## 9. Fail-closed synthesis conditions

Synthesis is authorized only with these non-negotiable conditions:

1. `UNKNOWN`, `CLAIMED`, or `CONFLICTING` auth, containment, identity, privacy, cost, or certification does not map to unattended execution.
2. The mechanical lane remains first-class and its authority is validator-specific.
3. A generic credential-bearing self-hosted runner capable of PR-controlled execution is excluded.
4. Candidate code and PR metadata remain hostile data. Prompt text is not a sandbox.
5. Vendor permission, credential lifecycle, installed-version conformance, network policy, and route certification are separate gates.
6. AGY remains manual/research-only; Grok Build remains operator-triggered or blocked until evidence clears its installed deployment.
7. OpenCode cannot establish upstream provider identity or terms permission by branding or configuration alone.
8. OpenRouter remains pinned API fallback transport, not a trust, identity, privacy, or release authority.
9. Plan exhaustion, runner failure, parser failure, and quota failure never silently select a stronger, more expensive, or less private route.
10. No model or API route receives merge, release, or governance authority. Human and existing proof/PR Steward contracts retain authority.
11. Route certification requires future shadow evaluation. No model is currently certified for Dopemux audit lanes.
12. Missing source dates and ledger mappings must not be upgraded into certainty during synthesis.

## 10. Input integrity and exclusions

`OBSERVED` All ten locally uploaded artifacts that also appear inside `PROOF_MANIFEST.json` match their declared SHA-256 values. `PROOF_MANIFEST.json` is itself included and independently hashed in the synthesis manifest.

`OBSERVED` All available campaign-kit files match the supplied `SHA256SUMS.txt` and `KIT-MANIFEST.json`. The convenience file `operator/DEEP-RESEARCH-OPERATOR-PASTE.md` is listed in the kit but was not supplied. It is not a governing acceptance input and is explicitly excluded.

`OBSERVED` Raw receipts and helper files named inside `PROOF_MANIFEST.json` were not uploaded. The acceptance review does not pretend to have inspected their content. The required accepted local summary artifacts listed in `START_HERE.md` are present, internally consistent, and hashable.

The complete accepted file inventory, hashes, exclusions, contradictions, unknowns, and authorization state are in `SYNTHESIS-INPUT-MANIFEST.json`.

## 11. Final acceptance

**Verdict:** `ACCEPT_WITH_CARRIED_UNKNOWNS`

`INFERRED` The evidence set is sufficiently complete, internally traceable, and conservative for GPT-5.6 Pro to synthesize a fail-closed architecture. It is not sufficient to enable model adapters, certify routing quality, claim model/provider independence, or assert plan-backed local operation without later evidence.
