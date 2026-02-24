# Authority Map

## Canonical Sources
- **Runtime Behavior**: The repository code and CI workflows (especially `.github/workflows/ci-complete.yml`) are the ultimate authority for runtime behavior.
- **Operational Invariants**: Architecture Decision Records (ADRs) in `docs/90-adr/` define operational invariants and overrides.
- **Reference Documentation**: Documentation in `docs/03-reference/` describes current behavior (initially marked as "UNKNOWN until verified").

## Support Sources
- **Tutorials and How-To Guides**: Located in `docs/01-tutorials/` and `docs/02-how-to/`.
- **Research Notes and Audit Reports**: Located in `docs/04-explanation/` and `docs/05-audit-reports/`.

## Legacy Sources
- **Archived Documents**: Located in `docs/archive/`.
- **Old Plans and Screenshots**: Located in `docs/archive/` or other legacy directories.

## Conflict Resolution
- **Code and CI Win**: In case of conflicts, the repository code and CI workflows take precedence unless an ADR explicitly overrides them.
- **ADRs as Overrides**: ADRs in `docs/90-adr/` can explicitly override conflicts between documentation and code/CI.

## References
- **CI Contract**: See [CI_CONTRACT.md](CI_CONTRACT.md) for CI/CD expectations.
- **Runtime Contract**: See [RUNTIME_CONTRACT.md](RUNTIME_CONTRACT.md) for runtime expectations.
