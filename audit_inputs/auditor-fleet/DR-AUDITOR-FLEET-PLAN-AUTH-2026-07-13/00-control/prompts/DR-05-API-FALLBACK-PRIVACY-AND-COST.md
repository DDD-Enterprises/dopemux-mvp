# DR-05: API Fallback, Privacy, and Cost

## Objective

Determine when API fallback is justified, how OpenRouter can be constrained, and how to compare
subscription-plan usage, API cost, privacy, and operational cost without inventing unavailable
measurements.

## Research questions

### Subscription economics

- What published usage limits, rolling windows, rate limits, fair-use rules, and concurrency
  restrictions apply to the target subscription plans?
- Are plan credits exposed per request?
- What can and cannot be measured?
- How should plan exhaustion or throttling be represented?
- What risks exist for unattended high-frequency use?

### OpenRouter

- How can provider and model be pinned?
- Can provider fallbacks be disabled?
- How are actual model/provider and request IDs reported?
- What data-policy, zero-data-retention, and provider-selection controls exist?
- How do strict structured outputs and parameter enforcement work?
- How should price ceilings and route profiles be enforced?
- Which low-cost models are suitable only as challengers or public low-risk reviewers?
- What limitations prevent OpenRouter from being an identity or trust oracle?

### Direct APIs

- Which APIs support strict structured output, usage accounting, request IDs, and model metadata?
- Which are economically viable for exceptional fallback only?
- How should API cost approval and hard caps work?

### Privacy

- Which routes are appropriate for:
  - public repository;
  - private repository without secrets;
  - possible secrets;
  - client data;
  - security-sensitive diffs;
  - release authority?
- What source retention and training-use terms matter?
- What can ZDR actually guarantee, and who enforces it?

### Total cost

Compare:

- subscription cost already paid;
- incremental API cost;
- self-hosted runner hardware and electricity;
- maintenance time;
- failed-run/operator burden;
- audit latency;
- risk of account suspension or quota exhaustion.

## Required deliverables

- Cost and privacy matrix.
- OpenRouter route-profile recommendations.
- API fallback trigger policy.
- Hard cost-cap model.
- Unknown-measurement policy.
- Recommendation for which routes are allowed only for public, low-risk work.
