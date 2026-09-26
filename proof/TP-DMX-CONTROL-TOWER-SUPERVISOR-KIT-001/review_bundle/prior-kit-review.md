# Prior Bounded Kit Review

An independent Luna agent reviewed the same unchanged payload in adOps PR #299.
These are prior review claims for the final auditor to evaluate independently,
not an operator disposition, accepted risk, or required verdict.

- P1 claim: route validation does not enforce schema_version=1.0. The function
  accepts 9.9 while the JSON schema rejects it. Determine actual severity and
  whether this permits bypassing a material required audit or authority check.
- P2 claim: return-pack allows absent reason and decision-needed and produces
  empty metadata. Assess consistency with the return schema and contract.
- P2 claim: runner-inventory invokes agy models, which may have helper/provider
  side effects; tool availability is not proof of execution capability.
- P2 claim: verify-zip checks ZIP CRC/readability only, not inventory/SHA256SUMS.
  Our smoke harness independently recomputed every manifest hash; the CLI itself
  must not be presented as doing more than its code supports.
- P2 claim: inherited Git fsmonitor IPC warnings can contaminate snapshot output.
  Local validation uses per-command core.fsmonitor=false; the payload does not.

The adOps reviewer also raised an L1/no-audit route classification finding in
adOps local state. That record is not part of this Dopemux diff. Dopemux uses
L2 with a mandatory final non-Codex independent audit; assess whether L3 is needed.
No prior kit finding is considered resolved or operator-accepted. No semantic
repair has been made to the supplied kit in response to this review.
