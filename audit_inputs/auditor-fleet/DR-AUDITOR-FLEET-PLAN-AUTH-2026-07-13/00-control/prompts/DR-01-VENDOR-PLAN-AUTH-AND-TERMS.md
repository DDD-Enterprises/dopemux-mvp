# DR-01: Vendor Plan Authentication and Automation Terms

## Objective

Determine, for each required tool, whether plan/subscription-backed authentication may be used
for local unattended or semi-unattended audit automation, under what official constraints, and
whether credentials may be isolated or moved to a dedicated local account, VM, broker, or
self-hosted runner.

## Required targets

- Claude Code
- Codex
- Gemini CLI
- OpenCode
- Grok Build
- AGY / Google Antigravity
- GitHub Copilot when used through OpenCode
- OpenRouter only as an API fallback

## Research questions

### Claude Code

- Which Claude subscriptions currently include Claude Code?
- What official authentication modes exist for local CLI use?
- What official token or setup-token mechanisms exist for scripts or CI?
- Are subscription/OAuth credentials supported for unattended local automation?
- Are they supported on a dedicated self-hosted runner or only a single-user workstation?
- What restrictions apply to credential sharing, service accounts, concurrent use, and automation?
- How long do tokens last, how are they refreshed, and what revocation controls exist?
- Which modes are API-billed rather than plan-billed?
- What official restrictions apply to third-party clients or wrappers?

### Codex

- Which ChatGPT plans include Codex CLI usage?
- What official sign-in modes exist for local and headless systems?
- Does device authentication support a persistent trusted machine?
- What enterprise or automation tokens exist?
- Which usage is plan-backed and which is API-billed?
- What restrictions apply to copied login state, shared runners, service accounts, or concurrency?
- What account and rate-limit behaviors matter for continuous audits?

### Gemini CLI and AGY

- Which Google plans or account classes include Gemini CLI or AGY usage?
- Which cached Google-login modes work headlessly?
- Are plan-backed credentials supported on a persistent local broker or custom runner?
- What restrictions apply to consumer accounts, Workspace accounts, and enterprise accounts?
- Is AGY automatable through an official interface, or is it app-only?
- How does AGY authentication differ from Gemini CLI authentication?

### OpenCode

- Which upstream subscription providers are officially supported?
- Which plan-backed routes are supported versus community workarounds?
- Are any provider terms explicitly hostile to third-party use?
- Can OpenCode run unattended using plan-backed auth without copying forbidden credentials?
- How are credentials stored and isolated?
- How does provider identity remain visible through OpenCode?

### Grok Build

- Is there a current official CLI, API, SDK, or headless automation interface?
- Is plan-backed use officially supported outside the first-party product?
- Are there account-sharing, automation, or fair-use restrictions?
- What model and usage evidence is exposed?

## Required deliverables

- Per-tool plan-auth support matrix.
- Per-tool allowed deployment matrix:
  - normal workstation;
  - dedicated local OS user;
  - dedicated local VM;
  - persistent self-hosted runner;
  - ephemeral self-hosted runner;
  - GitHub-hosted runner;
  - manual app only.
- Credential lifecycle and revocation matrix.
- Terms-risk matrix.
- Clear `SUPPORTED`, `SUPPORTED_WITH_LIMITS`, `UNSUPPORTED`, or `UNKNOWN` conclusions.

## Exclusions

Do not test accounts, authenticate, copy tokens, or infer permission from a community tutorial.
