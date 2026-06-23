# Remaining Risks

## Must fix before activation

- Configure trusted `assertion_verifier` with production issuer/key material
- Inject distributed `RedisDedupStore` for multi-replica deployments
- Wire runtime routing consumers to validate `route_decision.schema.json` before SELECTED use
- Enrich PR Steward harvest for proof refs / review comments / issue comments (or keep READY blocked)

## Acceptable documented debt

- DCP routing contracts are contracts-only until runtime activation
- Vendored schema copies in `dopemux.pcp` must stay synced with canonical `schemas/` on schema changes
- Generic `harvest_pr_intake` cannot emit READY without downstream enricher