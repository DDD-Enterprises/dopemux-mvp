# A2 Pre-Push Automatic Spend Census

```text
PACKET=TP-DMX-EMBEDDED-AUDIT-COST-CONTAINMENT-001
AMENDMENT=TP-DMX-EMBEDDED-AUDIT-COST-CONTAINMENT-001-A2
CENSUS_AT_UTC=2026-08-28T06:28:17Z
TRUSTED_MAIN_SHA=5900c27d3c38b515204bd5dc4baed8b5e14e2a8e
SCOPE=.github/workflows/**
RESULT=STOP_PRE_PUSH_UNAUTHORIZED_SPEND_PATH
```

## Automatic model routes

```text
WORKFLOW=.github/workflows/ci-complete.yml
TRIGGER=pull_request opened,synchronize,reopened,ready_for_review
MODEL_ROUTE=anthropics/claude-code-security-review@main
BILLING_MODE=API_IF_ANTHROPIC_API_KEY_AVAILABLE
AUTOMATIC_SPEND_POSSIBLE=UNKNOWN
EVIDENCE=workflow active; repo-level ANTHROPIC_API_KEY absent; organization-level secret visibility unavailable (GitHub API 403 requiring organization-admin scope)
```

```text
WORKFLOW=.github/workflows/security-review.yml
TRIGGER=pull_request opened,synchronize,reopened
MODEL_ROUTE=anthropics/claude-code-security-review@main
BILLING_MODE=API_IF_ANTHROPIC_API_KEY_AVAILABLE
AUTOMATIC_SPEND_POSSIBLE=UNKNOWN
EVIDENCE=workflow active; repo-level ANTHROPIC_API_KEY absent; organization-level secret visibility unavailable (GitHub API 403 requiring organization-admin scope)
```

```text
WORKFLOW=.github/workflows/embedded-audit.yml
TRIGGER=pull_request_target on trusted main
MODEL_ROUTE=PAL/Claude provider route using ANTHROPIC_API_KEY or CLAUDE_API_KEY
BILLING_MODE=API_METERED_IF_ENABLED
AUTOMATIC_SPEND_POSSIBLE=NO
EVIDENCE=workflow state read back as disabled_manually after kill-switch restoration; repository CLAUDE_API_KEY secret name exists
```

```text
WORKFLOW=.github/workflows/gemini-dispatch.yml -> .github/workflows/gemini-review.yml
TRIGGER=pull_request opened for same-repository pull requests
MODEL_ROUTE=google-github-actions/run-gemini-cli@v0 using GEMINI_API_KEY
BILLING_MODE=API_METERED_IF_ENABLED
AUTOMATIC_SPEND_POSSIBLE=NO
EVIDENCE=gemini-dispatch workflow state disabled_manually; repository GEMINI_API_KEY secret name exists
```

```text
WORKFLOW=.github/workflows/gemini-scheduled-triage.yml
TRIGGER=schedule; pull_request/push only when workflow file changes on main or release branch
MODEL_ROUTE=Gemini provider-backed triage
BILLING_MODE=API_METERED_IF_ENABLED
AUTOMATIC_SPEND_POSSIBLE=NO
EVIDENCE=workflow state disabled_manually; hotfix paths and branch do not satisfy event filters
```

## Non-model false positives

```text
WORKFLOW=.github/workflows/containers.yml and .github/workflows/docker-scout.yml
TRIGGER=push/pull_request surfaces inspected
MODEL_ROUTE=none; image and identifier references to litellm/claude-brain only
BILLING_MODE=NO_MODEL_CALL
AUTOMATIC_SPEND_POSSIBLE=NO
```

## Secret and workflow-state readback

Repository Actions secret names observed without values:

```text
CLAUDE_API_KEY
GEMINI_API_KEY
```

Relevant repository Actions variables observed:

```text
GEMINI_MODEL
```

No repository-level `ANTHROPIC_API_KEY`, `GOOGLE_GENAI_USE_GCA`,
`GOOGLE_GENAI_USE_VERTEXAI`, or `GCP_WIF_PROVIDER` was observed. Organization-level
secret enumeration failed closed with HTTP 403, so organization-secret reachability is
`UNKNOWN`.

Workflow state readback:

```text
.github/workflows/ci-complete.yml=active
.github/workflows/security-review.yml=active
.github/workflows/embedded-audit.yml=disabled_manually
.github/workflows/gemini-dispatch.yml=disabled_manually
.github/workflows/gemini-scheduled-triage.yml=disabled_manually
```

During census, `.github/workflows/embedded-audit.yml` was unexpectedly observed active.
Existing kill-switch authority required `CURRENT_WORKFLOW_STATE=disabled_manually`, so
only that workflow was disabled. Post-action GitHub readback confirmed
`state=disabled_manually`. No other workflow was mutated.

## Gate disposition

Two active pull-request workflows retain an automatic Claude API route whose effective
secret availability and billing path cannot be proven `PLAN_BACKED / NO_SPEND`, disabled,
or unreachable. A2 requires `UNKNOWN` billing/spend paths to stop before first push.

```text
PUSH_ALLOWED=NO
DRAFT_PR_ALLOWED=NO
STOP=STOP_PRE_PUSH_UNAUTHORIZED_SPEND_PATH
```

## A3 successor disposition

Amendment `TP-DMX-EMBEDDED-AUDIT-COST-CONTAINMENT-001-A3` authorized a bounded
tracked repair for both active Claude paths. At `2026-08-28T06:54:08Z`, local
branch structure proves:

```text
.github/workflows/ci-complete.yml:
  pull_request/push-main/merge_group CI retained
  Claude action requires workflow_dispatch
  Claude action requires allow_api_spend == true
  Claude action requires nonempty ANTHROPIC_API_KEY
  allow_api_spend default=false

.github/workflows/security-review.yml:
  workflow_dispatch only
  Claude action requires workflow_dispatch
  Claude action requires allow_api_spend == true
  Claude action requires nonempty ANTHROPIC_API_KEY
  allow_api_spend default=false
```

`tests/ci/test_ai_spend_containment.py` passes 11 structural assertions. The
complete `tests/ci` result is 64 passed plus only the A2-adjudicated inherited
stale-count failure.

Live workflow-state readback before feature-branch push:

```text
.github/workflows/ci-complete.yml=active
.github/workflows/security-review.yml=active
.github/workflows/embedded-audit.yml=disabled_manually
.github/workflows/gemini-dispatch.yml=disabled_manually
.github/workflows/gemini-scheduled-triage.yml=disabled_manually
```

Both active inherited Claude workflows restrict `push` to `main`, so a feature
branch push cannot trigger them. No new automatic provider route was observed.
Draft PR creation remains held until A3's exact three-workflow bootstrap
disable and state readback are complete.

```text
A2_STOP=HISTORICAL_AND_CLOSED_BY_A3_LOCAL_REPAIR
FEATURE_BRANCH_AUTOMATIC_PROVIDER_PATHS=ZERO
FEATURE_BRANCH_PUSH=AUTHORIZED_AFTER_FINAL_LOCAL_GATES
DRAFT_PR=HOLD_PENDING_TEMP_WORKFLOW_DISABLE
METERED_SPEND_AUTHORIZED=NO
```
