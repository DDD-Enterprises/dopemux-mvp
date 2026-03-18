# Invariant Alignment

## Canonical invariants

- ConPort is canonical for decisions, progress, and structured durable project context.
- Projections, mirrors, caches, and graph/query projections remain non-canonical.
- PM-plane integrations must resolve mutations back to ConPort rather than wrapper-local state.

## Dark method decisions

| Method family | Decision |
|---|---|
| `fork_instance` | retain as internal/admin-only |
| `promote` | retain as internal/admin-only |
| `promote_all` | retain as internal/admin-only |

## Counts

- dark methods intentionally exposed to PM plane: `0`
- dark methods deprecated from active runtime: `0`
- dark methods retained internal/admin-only: `3`

## Remaining hardening gaps

- no repo-evidenced auth gate on active callable surfaces
- runtime AGE dependency remains environment-sensitive
- parity gaps still exist on JSON-RPC and FastMCP wrapper coverage
