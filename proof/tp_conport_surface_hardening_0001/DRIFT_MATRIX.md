# Drift Matrix

Open drift cases found: `6`

1. `log_progress` default mismatch
   - affected surfaces: FastMCP wrappers vs REST/JSON-RPC
   - state: fixed in code; canonical REST default is `IN_PROGRESS`
2. `log_decision` payload mismatch
   - affected surfaces: FastMCP wrapper vs REST
   - state: fixed in code; wrappers now send both `topic` and `summary`
3. `workspace_summary` missing from JSON-RPC parity
   - affected surfaces: JSON-RPC
   - state: documented compatibility gap
4. dark admin methods `fork_instance`, `promote`, `promote_all`
   - affected surfaces: REST, JSON-RPC, FastMCP
   - state: retained as internal/admin-only, not sanctioned PM-plane contract
5. unauthenticated access posture
   - affected surfaces: REST, JSON-RPC, FastMCP
   - state: documented hardening gap
6. AGE / `ag_catalog` dependency ambiguity
   - affected surfaces: REST and JSON-RPC implementation
   - state: documented deployment/runtime risk
