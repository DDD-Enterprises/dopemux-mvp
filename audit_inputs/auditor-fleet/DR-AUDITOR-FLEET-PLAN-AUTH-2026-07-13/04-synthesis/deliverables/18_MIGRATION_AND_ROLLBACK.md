# Migration and Rollback

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Artifact:** `18_MIGRATION_AND_ROLLBACK.md`  
**Synthesis gate:** `ACCEPT_WITH_CARRIED_UNKNOWNS`  
**Architecture verdict:** `READY_WITH_BLOCKING_QUESTIONS`  
**Scope:** Specification only. No implementation, credential change, runner registration, live model probe, API call, route certification, or repository mutation is authorized.


## Migration strategy

`PROPOSED` Migrate from proof specification to automation in reversible slices. Each phase must preserve a functional fallback to manual plus mechanical validation.

## Phase plan

| Phase | Scope | Entry gate | Exit evidence | Rollback |
|---|---|---|---|---|
| `P0` Architecture and contracts | Independent review of these artifacts | Acceptance verdict | Approved ADR, threat model, contracts | Revise documents only |
| `P1` Mechanical-only broker | Local operator request, exact-head verification, disposable no-network validator worker, manual publication | P0 approval | Deterministic proof bundle and failure tests | Disable broker, use manual validators |
| `P2` Manual receipt intake | Normalize human-operated Grok, AGY, Codex, Claude, Gemini, OpenCode receipts | P1 stable | Receipt schema, exact-head binding, confidence labels | Stop intake, retain raw manual review |
| `P3` Static adapter conformance lab | Version-pinned negative checks without model calls where possible | Vendor auth path documented | Effective config and prohibited-surface receipts | Keep adapters disabled |
| `P4` Authorized bounded live conformance | One approved route at a time, synthetic/public input | Terms, privacy, credential and containment approval | Identity, output, exit, network, usage receipts | Revoke credential and disable adapter |
| `P5` Shadow evaluation | Candidate routes do not affect merge decisions | Live conformance pass | Adjudicated metrics and certification decision | Return to manual only |
| `P6` Operator-triggered certified adapters | Human approves every run | Current certificate | Stable operational evidence | Demote route to disabled |
| `P7` Trusted GitHub request pickup | GitHub-hosted request job and read-only local verifier | P1 and GitHub security review | Exact-head/replay/freshness tests | Disable workflow, use local operator requests |
| `P8` Separate publisher | Exact-head check publication | Publisher least-privilege review | Idempotent publication proof | Disable App, return to manual publication |
| `P9` Certified low-risk automation | Automatic execution only for narrow certified cohorts | Sustained shadow and operator approval | Production control limits | Return to operator-triggered mode |

## No big-bang activation

`REJECTED` Do not activate all tools behind one generic adapter or credential store. Each tool and auth class follows its own promotion path.

## Rollback triggers

Immediate rollback or demotion occurs on:

- stale-head publication;
- credential exposure or suspected compromise;
- containment or network-policy violation;
- model/provider identity drift;
- unapproved fallback;
- route-certificate expiry;
- severe production miss;
- schema-validity control breach;
- terms, privacy, or retention change;
- cost control failure;
- worker cleanup failure;
- GitHub workflow or publisher permission drift.

## Rollback targets

| Failure domain | Rollback target |
|---|---|
| Model adapter | `SPECIFIED_DISABLED` or `REVOKED` |
| API fallback | Disable profile and key; use local/manual review |
| GitHub request workflow | Local operator request file |
| Publisher | Human publication |
| Disposable worker image | Known-good previous image or manual validator host |
| Routing policy | Recommendation-only, mechanical lane only |
| Broker | Manual exact-head verification and proof assembly |

## Data and evidence rollback

`PROPOSED`

- Never delete incident evidence to make rollback cleaner.
- Mark superseded results and certificates, do not rewrite them.
- Preserve request/result hashes and chain of custody.
- Quarantine suspect worker images and outputs.
- Rotate or revoke affected credentials.
- Re-evaluate any result produced after the last known-good configuration point.

## Compatibility rules

`PROPOSED`

- Request and result schema versions are explicit.
- Broker may read the current and immediately previous version during migration, but writes only the current version.
- Publisher rejects unknown schema versions.
- Proof integration references the existing embedded-audit contract rather than forking it.
- Manual receipt support remains available through every phase.

## Migration stop conditions

Stop advancement when:

- required accepted evidence is missing or contradicted;
- exact-head behavior is not proven;
- a route depends on unsupported credential copying;
- a tool cannot disable prohibited surfaces;
- identity or privacy metadata is absent;
- shadow metrics do not meet approved gates;
- human operators cannot clearly distinguish blocked, failed, stale, and passed-within-authority states.
