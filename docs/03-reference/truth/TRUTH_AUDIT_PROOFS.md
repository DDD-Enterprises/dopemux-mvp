# TRUTH: Audit Proofs

## Schema Enforcement

The `scripts/audit/validate_audit_proof.py` script enforces the schema for `PROOF.json` artifacts, specifically targeting the `embedded_audit` object.

To prevent breaking historical runs and to support progressive migration, the validation scope is bounded by `proof/.validator_scope.json`.

- **Enforced Paths**: Proof bundles matching `include_patterns` (e.g., `proof/TP-DMX-*/PROOF.json`) are strictly validated against the current schema.
- **Grandfathered Paths**: Bundles matching `exclude_patterns` are explicitly skipped. These are typically pre-existing bundles (e.g., `proof/legacy/**`, `proof/fast-dev-os/**`) that were generated before `embedded_audit` enforcement was added. They are grandfathered pending backfill (e.g., `TP-DMX-LEGACY-BACKFILL-NNN`).
- **Unmatched Paths**: By default, paths not matching any inclusion or exclusion pattern are skipped with a warning (`skip_with_warning`), ensuring fail-safe execution on unknown scopes.
