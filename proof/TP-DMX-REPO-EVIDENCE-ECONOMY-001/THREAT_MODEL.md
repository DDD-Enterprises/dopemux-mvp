# Threat model — evidence economy

1. **Economy weakens audit** — Mitigated: L2/L3 still require one final independent audit; PR Steward unchanged for readiness.
2. **Path-lane under-classification** — Mitigated: uncertain defaults; security/workflow/auth patterns escalate to L3; governance/audit tooling to L2.
3. **Escaped proof-only paths** — Mitigated: fail-closed path allowlist in validate_change_contract.
4. **Hook-modified files pushed dirty** — Mitigated: hook_would_modify / frontmatter checks; docs require re-run after auto-fix.
