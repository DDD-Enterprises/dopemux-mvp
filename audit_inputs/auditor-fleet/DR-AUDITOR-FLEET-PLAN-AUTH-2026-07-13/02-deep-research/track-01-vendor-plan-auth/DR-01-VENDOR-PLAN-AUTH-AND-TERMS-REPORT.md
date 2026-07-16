# DR-01 Vendor Plan Authentication and Automation Terms

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Track:** `DR-01-VENDOR-PLAN-AUTH-AND-TERMS`  
**Research date:** 2026-07-13  
**Status:** `COMPLETE_WITH_UNKNOWNS`

## Scope and evidence posture

`OBSERVED` The supplied local capability probe was static-only. No provider account was tested, no credential store was inspected, no token was created or copied, no model was invoked, and no plan-backed billing route or actual model identity was observed. The external findings below extend vendor-policy knowledge but do not overwrite that host evidence.

`PROPOSED` A tool is eligible for unattended execution only when the vendor documents both a non-interactive credential and a deployment class compatible with the intended worker. Browser login, device login, cached state, or a working third-party integration is not sufficient by itself.

## Executive assessment

`CLAIMED` **Claude Code** has the clearest first-party subscription automation path: Anthropic documents subscription OAuth for Pro, Max, Team, and Enterprise and a one-year `claude setup-token` credential for CI, scripts, and non-browser environments. API keys and Workload Identity Federation are separate API-billed routes. [S01], [S02], [S04]

`CLAIMED` **Codex** documents ChatGPT sign-in, device authentication, API-key authentication, trusted-runner cached auth, and Business/Enterprise access tokens for non-interactive workflows. OpenAI still recommends API keys for general programmatic workflows, and plan usage remains quota-bound. [S05], [S06], [S07], [S08]

`CONFLICTING` **Gemini CLI** documentation still describes cached Google-account login for supported account classes, but Google ended consumer-tier service for Gemini Code Assist for individuals and Google AI Pro/Ultra on June 18, 2026. Fresh headless authentication without cached state is documented through API key or Vertex AI. [S12], [S13], [S14]

`CLAIMED` **Google Antigravity** has first-party CLI and SDK surfaces, silent-auth documentation, and enterprise Google Cloud integration. `UNKNOWN` Public documentation reviewed does not establish a complete subscription-token lifecycle or supported persistent and ephemeral runner classes. [S15], [S16], [S17], [S18]

`CLAIMED` **OpenCode** supports headless execution and per-user credential storage. `INFERRED` Its plan-auth eligibility is never broader than the upstream provider's permission. OpenCode states that Anthropic prohibits Claude Pro/Max subscription auth through OpenCode. [S21], [S22]

`CLAIMED` **Grok Build** officially supports headless scripts and bots, but its explicit non-browser authentication path is `XAI_API_KEY`. `UNKNOWN` Subscription-session lifecycle and runner permission are not documented sufficiently for unattended plan-backed deployment. [S25], [S26], [S27]

`CLAIMED` **OpenRouter** is an API fallback using API keys, management keys, credit caps, and OAuth-to-key flows. It is not plan authentication and not an identity authority. [S29], [S30], [S31], [S32]

## Per-tool conclusion matrix

| Target | Plan-auth conclusion | Narrowest defensible interpretation |
|---|---|---|
| Claude Code | `SUPPORTED_WITH_LIMITS` | First-party Claude Code only. Use `/login` for human use and `claude setup-token` for scripts or CI. Separate API/WIF billing from subscription use. |
| Codex | `SUPPORTED_WITH_LIMITS` | Strongest path is Business/Enterprise access tokens on trusted private workers. Personal cached auth is advanced, fragile, and unsuitable for shared pools. |
| Gemini CLI | `SUPPORTED_WITH_LIMITS` | `UNSUPPORTED` for consumer Google AI Pro/Ultra plan auth after 2026-06-18. Remaining Workspace/Code Assist cached-login use may work locally, but runner permission is `UNKNOWN`; API/Vertex is the supported fresh headless path. |
| Google Antigravity / AGY | `SUPPORTED_WITH_LIMITS` | First-party CLI/SDK automation exists. Keep plan-backed use operator-triggered until lifecycle and runner-class rules are documented. |
| OpenCode | `SUPPORTED_WITH_LIMITS` | Wrapper automation is supported, but every plan-auth route is conditional on upstream vendor permission. |
| Claude subscription through OpenCode | `UNSUPPORTED` | OpenCode documents Anthropic's prohibition; do not enable without direct Anthropic authorization. |
| GitHub Copilot through OpenCode | `SUPPORTED_WITH_LIMITS` | Named licensed user on a workstation. Shared or copied session state on runners remains `UNKNOWN`. |
| Grok Build | `SUPPORTED_WITH_LIMITS` | First-party plan-backed local use and official headless execution exist, but unattended non-browser automation is most clearly documented with API keys. |
| OpenRouter | `SUPPORTED` | API fallback only. Never describe it as plan-backed. |

## Allowed deployment matrix

The cells describe plan-backed use. API-key routes may be broader, but they are separate billing and privacy decisions.

| Tool | Normal workstation | Dedicated local OS user | Dedicated local VM | Persistent self-hosted runner | Ephemeral self-hosted runner | GitHub-hosted runner | Manual app only |
|---|---|---|---|---|---|---|---|
| Claude Code | `SUPPORTED` | `SUPPORTED` | `SUPPORTED` | `SUPPORTED_WITH_LIMITS` | `SUPPORTED_WITH_LIMITS` | `SUPPORTED_WITH_LIMITS` | No |
| Codex | `SUPPORTED` | `SUPPORTED_WITH_LIMITS` | `SUPPORTED_WITH_LIMITS` | `SUPPORTED_WITH_LIMITS` for Business/Enterprise access tokens | `SUPPORTED_WITH_LIMITS` for trusted workers | `UNSUPPORTED` for copied personal auth; API route separate | No |
| Gemini CLI | `SUPPORTED_WITH_LIMITS` for remaining supported account classes | `SUPPORTED_WITH_LIMITS` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNSUPPORTED` for consumer plan auth | No |
| Antigravity | `SUPPORTED` | `SUPPORTED_WITH_LIMITS` | `SUPPORTED_WITH_LIMITS` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | No |
| OpenCode | `SUPPORTED` if upstream route is permitted | `SUPPORTED_WITH_LIMITS` | `SUPPORTED_WITH_LIMITS` | `UNKNOWN` per provider | `UNKNOWN` per provider | `UNKNOWN` per provider | No |
| Copilot through OpenCode | `SUPPORTED_WITH_LIMITS` | `SUPPORTED_WITH_LIMITS` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | No |
| Grok Build | `SUPPORTED` | `SUPPORTED_WITH_LIMITS` | `SUPPORTED_WITH_LIMITS` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | No |
| OpenRouter | Not plan-backed | Not plan-backed | Not plan-backed | Not plan-backed | Not plan-backed | Not plan-backed | No |

## Credential lifecycle and revocation matrix

| Tool | Storage / isolation | Lifetime / refresh | Revocation | Disposition |
|---|---|---|---|---|
| Claude Code | Per-user Claude Code credential storage; environment token supported; API WIF is a separate workload identity route. | `setup-token` documented for one year; interactive login expiry is renewed interactively; WIF tokens are short-lived. | `UNKNOWN` for a complete setup-token inventory and immediate admin revocation flow in reviewed docs. | Prefer dedicated user/VM and explicit setup-token handling. |
| Codex | `~/.codex/auth.json` or OS credential store; access tokens may be supplied to trusted clients. | ChatGPT sessions refresh; access tokens support configurable expiry. | Workspace admins can revoke access tokens; logout clears local current credentials. | Best documented plan-backed runner lifecycle in this track. |
| Gemini CLI | Cached Google login or environment-based API/Vertex credentials. | Google-login lifetime not established here; fresh headless auth uses API/Vertex. | Account/API/service-account controls exist, but Gemini-login cache revocation details are incomplete. | Consumer plan route rejected; remaining plan-backed runner use blocked. |
| Antigravity | First-party silent auth and enterprise GCP integration are documented. | `UNKNOWN`. | `UNKNOWN`. | Operator-triggered only pending lifecycle evidence. |
| OpenCode | Provider credentials stored under the user's local OpenCode data directory. | Upstream-provider dependent. | Local logout removes stored copy; upstream revocation remains provider-specific. | Isolation is technically feasible but does not prove permission. |
| Copilot through OpenCode | OpenCode local credential store plus GitHub device login. | `UNKNOWN` in reviewed OpenCode-specific docs. | Local logout plus GitHub-side authorization/session revocation. | Named-user only until runner support is documented. |
| Grok Build | Browser login for first launch; `XAI_API_KEY` for non-browser use. | Subscription-session lifecycle `UNKNOWN`. | Subscription-session revocation `UNKNOWN`; API keys managed through xAI console. | API key for unattended automation. |
| OpenRouter | API keys, management keys, per-environment caps. | Normal API-key lifecycle. | Programmatic key management documented. | Suitable API fallback with explicit hard caps. |

## Terms-risk matrix

| Route | Risk | Reason |
|---|---|---|
| Claude Code first-party `setup-token` | Medium | Explicit automation mechanism, but seat ownership, revocation, and secure storage still matter. |
| Claude plan auth through OpenCode | High | OpenCode states the route is prohibited by Anthropic. |
| Codex Business/Enterprise access token | Medium | Explicit trusted-workflow mechanism, but only on trusted private infrastructure. |
| Codex copied personal auth | High | Advanced cached-state reuse is not a service-account model and should not become a shared pool. |
| Gemini CLI consumer plan auth | High | Consumer service ended on 2026-06-18. |
| Gemini CLI Workspace/Code Assist cached auth | Medium to High | Account-class support may remain, but persistent runner permission is not established. |
| Antigravity first-party plan auth | Medium | Official product surface, incomplete lifecycle and runner guidance. |
| OpenCode provider route | Provider-dependent | Wrapper support is not upstream permission. |
| Copilot through OpenCode | Medium | Device login is official; shared user credentials are not. |
| Grok Build plan session | Medium to High | Headless execution is official, but plan-session runner governance is incomplete. |
| OpenRouter API key | Low for auth terms | Normal API route; privacy, provider, model, and cost policy remain separate controls. |

## Questions answered

- Claude Code plan inclusion and first-party auth modes: `ANSWERED`.
- Claude scripts/CI token path: `ANSWERED`.
- Claude revocation and third-party wrapper restrictions: `PARTIAL`.
- Codex plan inclusion: `CONFLICTING`.
- Codex trusted non-interactive credentials: `ANSWERED`.
- Codex personal-plan concurrency and copied-state limits: `PARTIAL`.
- Gemini account classes and current consumer deprecation: `CONFLICTING`, resolved by date and account scope.
- Gemini persistent plan-backed broker permission: `PARTIAL`.
- Antigravity official automation surfaces: `ANSWERED`.
- Antigravity lifecycle and runner classes: `UNKNOWN`.
- OpenCode plan routes and upstream authorization: `PARTIAL`.
- Copilot through OpenCode unattended runner authorization: `PARTIAL`.
- Grok Build official headless surfaces: `ANSWERED`.
- Grok Build subscription runner lifecycle: `PARTIAL`.
- OpenRouter fallback authentication: `ANSWERED`.

## Contradictions

1. `CONFLICTING` OpenAI plan lists differ between Help Center and developer documentation. Carry the discrepancy and verify the actual workspace entitlement before deployment. [S05], [S11]
2. `CONFLICTING` Gemini's general auth guide still describes Google login while the newer consumer deprecation removes individual and AI Pro/Ultra service. The deprecation controls consumer tiers; the auth guide applies only to remaining supported account classes. [S12], [S13]
3. `CONFLICTING` The explicit Claude-through-OpenCode prohibition was found in OpenCode documentation, not a directly matching Anthropic terms page. Operationally block it until Anthropic confirms otherwise. [S03], [S22]
4. `CONFLICTING` Grok Build is officially headless, but non-browser auth is explicitly API-key based and plan-session runner permission is absent. [S25], [S26], [S27]

## Unknowns

- Claude `setup-token` inventory and immediate revocation workflow.
- Personal-plan Codex concurrency and permitted number of trusted auth copies.
- Workspace or Code Assist Gemini CLI support on persistent and ephemeral custom runners.
- Antigravity token storage, lifetime, refresh, revocation, and runner classes.
- First-party OpenAI or GitHub authorization for unattended OpenCode subscription use.
- Grok Build plan-session lifecycle, sharing, fair-use, and runner permission.
- Actual model identity and plan-versus-API billing evidence for any local invocation.
- Unpublished anti-abuse thresholds for continuous subscription automation.
- Direct credential provisioning into dedicated OS users or VMs without copying workstation state.

## Activities not run

- Account login, entitlement checks, or authenticated-page automation.
- Credential-file, cookie, token, keychain, or session-database inspection.
- Token creation, refresh, copying, rotation, or revocation.
- Provider API calls, model invocations, concurrency tests, or benchmarks.
- Runner registration, GitHub mutation, or implementation work.

## Recommendations

1. `PROPOSED` Claude Code: allow only first-party subscription auth; use `setup-token` for scripts or CI and block third-party Claude plan bridges.
2. `PROPOSED` Codex: use Business/Enterprise access tokens on trusted private workers; keep personal cached auth manual or operator-triggered.
3. `PROPOSED` Gemini CLI: reject consumer plan auth; use API/Vertex for unattended use and keep Workspace plan-backed runners blocked pending evidence.
4. `BLOCKED` Antigravity: operator-triggered only until lifecycle and runner documentation exists.
5. `PROPOSED` OpenCode: permit only provider routes with explicit upstream authorization.
6. `BLOCKED` Copilot through OpenCode: named-user workstation only until GitHub documents unattended third-party runner use.
7. `PROPOSED` Grok Build: plan auth for operator-triggered local use; API key for unattended workers.
8. `PROPOSED` OpenRouter: API fallback only, with per-environment keys and hard limits.
9. `PROPOSED` Treat every `UNKNOWN`, `CONFLICTING`, or cached-interactive credential as non-executable.
10. `PROPOSED` Record auth class, credential owner, deployment class, billing route, model evidence, and revocation handle in every future proof receipt.

## Synthesis implications

- Do not automatically select any locally installed model tool based on this research alone.
- Claude Code and Codex are the strongest candidates for plan-backed automation because they expose explicit first-party non-interactive credentials.
- Gemini CLI consumer plan authentication is removed; Workspace and enterprise scope must remain distinct.
- Antigravity and Grok Build should remain operator-triggered until plan credential lifecycle and runner permission are established.
- OpenCode is an adapter, not an auth or terms authority.
- OpenRouter is API fallback only.
- A dedicated OS account or VM is necessary isolation, not proof of vendor permission.
- Actual model identity and actual billing route remain separate proof obligations.
- No plan-credit conversion from tokens is established.

## Source ledger

| ID | Source | Publisher | Class | Update date | Questions |
|---|---|---|---|---|---|
| S01 | [Authentication - Claude Code Docs](https://code.claude.com/docs/en/authentication) | Anthropic | `OFFICIAL_DOCUMENTATION` | Not stated | DR01-Q01, DR01-Q02, DR01-Q03 |
| S02 | [Workload Identity Federation - Claude Platform Docs](https://platform.claude.com/docs/en/manage-claude/workload-identity-federation) | Anthropic | `OFFICIAL_DOCUMENTATION` | Not stated | DR01-Q02, DR01-Q03 |
| S03 | [Commercial Terms of Service](https://www.anthropic.com/legal/commercial-terms) | Anthropic | `OFFICIAL_TERMS` | Not stated | DR01-Q03, DR01-Q10 |
| S04 | [Plans and Pricing](https://claude.com/pricing) | Anthropic | `OFFICIAL_PRICING` | Not stated | DR01-Q01 |
| S05 | [Authentication - Codex](https://developers.openai.com/codex/auth) | OpenAI | `OFFICIAL_DOCUMENTATION` | Not stated | DR01-Q04, DR01-Q05, DR01-Q06 |
| S06 | [Access Tokens - Codex](https://developers.openai.com/codex/enterprise/access-tokens) | OpenAI | `OFFICIAL_DOCUMENTATION` | Not stated | DR01-Q05, DR01-Q06 |
| S07 | [Maintain Codex Account Auth in CI/CD (Advanced)](https://developers.openai.com/codex/auth/ci-cd-auth) | OpenAI | `OFFICIAL_DOCUMENTATION` | Not stated | DR01-Q04, DR01-Q05, DR01-Q06 |
| S08 | [Codex Pricing](https://developers.openai.com/codex/pricing) | OpenAI | `OFFICIAL_PRICING` | Not stated | DR01-Q06 |
| S09 | [Terms of Use](https://openai.com/policies/terms-of-use/) | OpenAI | `OFFICIAL_TERMS` | Not stated | DR01-Q06, DR01-Q10 |
| S10 | [OpenAI Services Agreement](https://openai.com/policies/business-terms/) | OpenAI | `OFFICIAL_TERMS` | Not stated | DR01-Q06, DR01-Q10 |
| S11 | [Using Codex with Your ChatGPT Plan](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan) | OpenAI | `OFFICIAL_DOCUMENTATION` | Not stated | DR01-Q04 |
| S12 | [Gemini CLI Authentication Setup](https://github.com/google-gemini/gemini-cli/blob/main/docs/get-started/authentication.mdx) | Google | `OFFICIAL_REPOSITORY` | Not stated | DR01-Q07, DR01-Q08 |
| S13 | [Gemini Code Assist Consumer Accounts Deprecation](https://developers.google.com/gemini-code-assist/docs/deprecations/code-assist-individuals) | Google | `OFFICIAL_DOCUMENTATION` | 2026-05-18 | DR01-Q07, DR01-Q08 |
| S14 | [Gemini CLI Quotas and Pricing](https://github.com/google-gemini/gemini-cli/blob/main/docs/resources/quota-and-pricing.md) | Google | `OFFICIAL_REPOSITORY` | 2026-06-18 | DR01-Q07, DR01-Q08 |
| S15 | [Antigravity CLI Overview](https://antigravity.google/docs/cli/overview) | Google | `OFFICIAL_DOCUMENTATION` | Not stated | DR01-Q09 |
| S16 | [Antigravity SDK Overview](https://antigravity.google/docs/sdk/overview) | Google | `OFFICIAL_DOCUMENTATION` | Not stated | DR01-Q09 |
| S17 | [Antigravity and Gemini Enterprise Agent Platform](https://antigravity.google/docs/enterprise) | Google | `OFFICIAL_DOCUMENTATION` | Not stated | DR01-Q09 |
| S18 | [Google Antigravity FAQ](https://antigravity.google/docs/faq) | Google | `OFFICIAL_DOCUMENTATION` | Not stated | DR01-Q09, DR01-Q10 |
| S19 | [Use Google AI Pro Benefits](https://support.google.com/googleone/answer/14534406?hl=en) | Google | `OFFICIAL_PRICING` | Not stated | DR01-Q09 |
| S20 | [Use Google AI Ultra Benefits](https://support.google.com/googleone/answer/16286513?hl=en) | Google | `OFFICIAL_PRICING` | Not stated | DR01-Q09 |
| S21 | [OpenCode CLI](https://opencode.ai/docs/cli/) | OpenCode | `OFFICIAL_DOCUMENTATION` | Not stated | DR01-Q10, DR01-Q11 |
| S22 | [OpenCode Providers](https://opencode.ai/docs/providers/) | OpenCode | `OFFICIAL_DOCUMENTATION` | Not stated | DR01-Q03, DR01-Q10, DR01-Q11, DR01-Q12 |
| S23 | [Authenticating GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/authenticate-copilot-cli) | GitHub | `OFFICIAL_DOCUMENTATION` | Not stated | DR01-Q12 |
| S24 | [GitHub Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service) | GitHub | `OFFICIAL_TERMS` | Not stated | DR01-Q12 |
| S25 | [Grok Build Overview](https://docs.x.ai/build/overview) | xAI | `OFFICIAL_DOCUMENTATION` | Not stated | DR01-Q13, DR01-Q14 |
| S26 | [Grok Build Enterprise Deployments](https://docs.x.ai/build/enterprise) | xAI | `OFFICIAL_DOCUMENTATION` | 2026-06-16 | DR01-Q13, DR01-Q14 |
| S27 | [Introducing Grok Build](https://x.ai/news/grok-build-cli) | xAI | `OFFICIAL_DOCUMENTATION` | 2026-05-25 | DR01-Q13, DR01-Q14 |
| S28 | [xAI API Pricing](https://docs.x.ai/developers/pricing) | xAI | `OFFICIAL_PRICING` | 2026-07-03 | DR01-Q14 |
| S29 | [OpenRouter API Authentication](https://openrouter.ai/docs/api/reference/authentication) | OpenRouter | `OFFICIAL_DOCUMENTATION` | Not stated | DR01-Q15 |
| S30 | [OpenRouter Management API Keys](https://openrouter.ai/docs/guides/overview/auth/management-api-keys) | OpenRouter | `OFFICIAL_DOCUMENTATION` | Not stated | DR01-Q15 |
| S31 | [OpenRouter OAuth PKCE](https://openrouter.ai/docs/guides/overview/auth/oauth) | OpenRouter | `OFFICIAL_DOCUMENTATION` | Not stated | DR01-Q15 |
| S32 | [OpenRouter Pricing](https://openrouter.ai/pricing) | OpenRouter | `OFFICIAL_PRICING` | Not stated | DR01-Q15 |

## Final disposition

`COMPLETE_WITH_UNKNOWNS`

The research is sufficient to distinguish first-party plan automation from API billing and from third-party credential workarounds. It is not sufficient to authorize unattended deployment for Antigravity, Grok Build plan sessions, Gemini Workspace plan auth, or OpenCode subscription routes without additional vendor evidence. Those states must remain non-executable.
