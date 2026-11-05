---
id: subscription-only-pr-review
title: Subscription-Only PR Review
type: how-to
owner: '@hu3mann'
author: '@codex'
date: '2026-11-05'
last_review: '2026-11-05'
next_review: '2027-02-05'
prelude: Keep automatic PR checks provider-free and preserve pending security review.
---

# Subscription-Only PR Review

Automatic PR lifecycle events do not invoke the Gemini or Claude API review
actions. This applies to draft and ready PRs, forks, and repositories with
provider credentials configured. Merge-group security checks also exclude model
calls. Changing a draft to ready does not enable API review or rerun expensive
CI: the existing PR Steward recheck reuses exact-head audit evidence.

The security checks report `NOT_RUN` and pending independent review, and fail
closed. The existing required **Security Review** check remains blocking. A
successful deterministic CI summary does not approve security, satisfy that
check, or grant merge readiness. This policy supplies no replacement acceptance
route and does not change branch protection.

Run an independently authorized local review through an existing subscription,
then preserve its verdict, exact subject, and required proof. The trusted
`embedded-audit.yml` workflow validates imported signed audit evidence; it does
not invoke a provider. Its signer policy and fail-closed enforcement remain
unchanged. Passing that separate evidence gate does not turn a `NOT_RUN` model
security check into a passing review. Resolving the pending Security Review
context requires separate authorized policy work; do not bypass it.

Existing explicit `@gemini-cli` commands from trusted users in comments or
reviews remain available, as do existing issue triage, scheduled triage, and
non-PR security behavior. Those routes can use configured API credentials;
this change does not convert them to subscriptions or authorize invoking them.
A command embedded in a PR body is not an explicit comment request.

No API fallback, new provider route, credential change, permission change,
automatic ready promotion, or merge action is introduced.
