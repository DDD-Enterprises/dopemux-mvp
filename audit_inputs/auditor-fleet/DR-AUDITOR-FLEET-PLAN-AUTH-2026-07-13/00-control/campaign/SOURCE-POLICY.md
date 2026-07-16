# Source Policy

## Source order

Use sources in this order:

1. Current official vendor documentation.
2. Current official terms of service, acceptable-use policies, account policies, pricing,
   quota, security, and privacy documentation.
3. Official product repositories, release notes, CLI help references, and security advisories.
4. GitHub official Actions and self-hosted runner documentation.
5. Standards documents and peer-reviewed or preprint security research.
6. Reputable independent security advisories tied to reproducible technical evidence.
7. High-quality secondary reporting only when primary sources do not answer the question.

## Tool-specific primary sources

Research the official sources for:

- Anthropic and Claude Code;
- OpenAI and Codex;
- Google Gemini CLI and Google Antigravity / AGY;
- OpenCode;
- xAI / Grok Build;
- OpenRouter;
- GitHub Actions and self-hosted runners;
- container, VM, and credential-isolation mechanisms when directly relevant.

## Required distinctions

Never collapse these:

- technical possibility versus vendor-authorized use;
- interactive personal use versus unattended automation;
- plan/subscription authentication versus API billing;
- local cached credentials versus portable CI credentials;
- supported headless automation versus UI scripting;
- provider-attested identity versus requested/configured/displayed model;
- GitHub-hosted runner versus persistent self-hosted runner;
- custom audit broker versus generic GitHub runner;
- read-only prompt instruction versus OS/runner-enforced containment.

## Freshness

Prefer sources current on or after 2026-01-01. Older sources may be used for stable concepts,
but version-sensitive facts must be confirmed against current official documentation.

## Evidence rules

Every material finding must include:

- claim label;
- source title and publisher;
- publication or last-updated date when available;
- access date;
- source class;
- exact question answered;
- confidence;
- whether the finding conflicts with local probe evidence;
- decision impact.

Direct quotations should be short. Paraphrase rather than copying long source passages.

## Forbidden source behavior

Do not:

- rely on search snippets as final evidence;
- rely on affiliate blogs for pricing or terms;
- infer permissions from product behavior;
- treat GitHub issues as official policy;
- infer current subscription entitlements from old launch announcements;
- infer plan-credit conversion from token counts;
- treat consumer login cache portability as authorized CI use without official support;
- treat a model name displayed by a CLI as provider attestation.
