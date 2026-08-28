# Validation evidence

## Independent audit checks

Controlling AGY audit ran once against frozen content head
`79404f3929c47fe09434ac07a36b936190282b56` and returned `PASS` with no
blocking findings. Retained controller receipt records these independent checks
as passing:

- clean exact head and repository identity;
- three Task Packet schemas;
- late R1 proof validator;
- docs validator and frontmatter guard;
- changed-contract L2;
- diff check and eight-path allowlist;
- current packet/authority hash and blob bindings;
- six-way overlap stop semantics;
- late-proof identity and historical/current subject separation;
- truthful INDEX state;
- instruction-like-content acknowledgement.

No model audit was rerun for this proof-only successor.

## Proof-only closure checks

Fresh checks against provisional proof tree before final receipt-only amend:

- `python scripts/audit/validate_audit_proof.py
  proof/TP-DMX-GOV-G0-LITE-PR1282-REPAIR-002/PROOF.json`: exit `0`,
  `1/1 PASS`.
- R2 packet validation against
  `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`: exit `0`.
- SHA-256 and Git blob recomputation for R2 packet, current G0 packet,
  authority record, and late R1 proof: exit `0`; all values match
  `PROOF.json`.
- Final R2 comparison range: `16` paths, all within packet allowlist.
  Proof-only successor adds `8` paths, all under
  `proof/TP-DMX-GOV-G0-LITE-PR1282-REPAIR-002/**`.
- `gitleaks detect --no-git` on R2 proof root: exit `0`, no leaks found.
- `validate_change_contract.py --base origin/main --head HEAD`: exit `0`,
  `status=PASS`, `max_lane=L2`, `paths=25` for full PR range.
- Direct proof-only change-contract validation with content/audited head
  `79404f3929c47fe09434ac07a36b936190282b56` and final proof head: exit `0`,
  `status=PASS`, `max_lane=L0`, `proof_only=True`, `paths=8`, model re-audit
  `NOT_REQUIRED`.
- `pre-commit run --from-ref origin/main --to-ref HEAD`: exit `0`; all
  applicable hooks passed.
- Generic exact-commit pre-commit invocation failed closed only because its
  change-contract hook does not forward required proof-only content/audited/
  proof heads. Direct validator command above supplied those heads and passed;
  all other exact-commit hooks passed.
- Detached canonical `PROOF.json.sig` verifies for allowed principal
  `hue@local` under namespace `dopemux-embedded-audit`.
- `git diff --check origin/main...HEAD`: exit `0`.
- GitHub exact-head readback: PR head equals audited content head before proof
  materialization; `15` total review threads and `0` unresolved.

These receipts are deterministic proof-only closure evidence. They do not rerun
or replace independent content audit.
