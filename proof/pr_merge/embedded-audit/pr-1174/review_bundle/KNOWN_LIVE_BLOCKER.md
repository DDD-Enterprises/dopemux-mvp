# Live blocker before CCAR-001R

- Existing PR head before repair: 7a3f9d74762a70779d628c3a370d6b571307fe9a
- Existing proof/CCAR-001/PROOF.json is historical and does not bind the live head.
- Embedded-audit run 30598323114 concluded failure / NEEDS_SUPERVISOR.
- Final-readiness run 30598344306 skipped Steward and published failure.
- Trusted local-attestation fallback rejected the branch because the canonical
  proof/pr_merge/embedded-audit/pr-1174/ package was absent.
