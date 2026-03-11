# Layer Policy

Mandatory behavior:

- Unit layer is always applicable.
- Smoke/integration/e2e/regression are generated when applicability signals are present.
- If a layer is not applicable, mark `N/A` with explicit rationale and evidence.

Applicability hints:

- Smoke: startup, health, deployment, compose, service lifecycle.
- Integration: multi-component workflows, bridges, API/db boundaries.
- E2E: user journey, CLI flow, UI/browser workflow.
- Regression: bugfixes, post-implementation validation, incident recurrence prevention.

Never skip explanation for a non-unit layer.
