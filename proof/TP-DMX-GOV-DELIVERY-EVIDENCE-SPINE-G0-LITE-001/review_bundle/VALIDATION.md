# Validation ledger

Audited content head: `37de7769a2c5b749dcb377a414500e83ad7d67af`

Audited parent: `ac0aa1a6c806819b6b9ce5a7d263f27ac396f724`

## PASS

- `python -m jsonschema -i task-packets/TP-DMX-GOV-DELIVERY-EVIDENCE-SPINE-G0-LITE-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` — exit `0`.
- packet correction assertions — exit `0`; no `rtk`, no one-sided `HEAD...source`, exactly seventeen planned payload paths in both symmetric diff commands, exact bounded fetch/SHA check, complete six-class vocabulary.
- `python3 scripts/governance/validate_change_contract.py --base ac0aa1a6c806819b6b9ce5a7d263f27ac396f724 --head 37de7769a2c5b749dcb377a414500e83ad7d67af --format text` — exit `0`; `status=PASS`, `max_lane=L0`, `paths=1`.
- `python3 scripts/governance/validate_change_contract.py --base origin/main --head 37de7769a2c5b749dcb377a414500e83ad7d67af --format text` — exit `0`; `status=PASS`, `max_lane=L0`, `paths=14` before proof regeneration.
- `pre-commit run --from-ref ac0aa1a6c806819b6b9ce5a7d263f27ac396f724 --to-ref 37de7769a2c5b749dcb377a414500e83ad7d67af` — all non-exempt hooks passed; sandbox-only index denial was retried with linked-worktree index access.
- `git diff --check ac0aa1a6c806819b6b9ce5a7d263f27ac396f724..37de7769a2c5b749dcb377a414500e83ad7d67af` — exit `0`.
- exact changed-path inventory — one modified Task Packet path.
- direct Claude Code CLI audit — exit `0`; `PASS_WITH_RISKS`; no blocking finding.
- failed-source custody ref resolves exactly to `caa4ec2913d0463c7e38835029f3f7adeb915ac6`; PR `#1268` was not mutated.
- implementation-authority path absent on observed `origin/main` `f0a01035832c02fc2c02b7a23a0f9c3517c69364`; implementation remains unauthorized.
- canonical `validate_audit_proof.py` — exit `0`; `1/1 PASS`.
- proof secret scan — `PASS`; eleven textual canonical bundle files scanned, detached signature excluded.
- review-bundle changed-path inventory and unified diff are byte-identical to raw Git output for `ac0aa1a6...37de7769`.
- structured Claude result validates against captured output schema; canonical projection preserves `PASS_WITH_RISKS`, three findings, three risks, exact head, and empty `fixes_applied`.

## FAIL

- None in deterministic packet validation or independent audit.

## NOT_RUN / pending

- Ordinary CI at corrected content head: `NOT_RUN`; head not pushed yet.
- Canonical and PR-scoped signature verification: pending additive proof-only successors.
- PR Steward at final signed proof head: `NOT_RUN`.
- G0-Lite payload implementation: `NOT_RUN`; supervisor implementation authority remains withheld.

## Custody notes

- No PAL/clink route was invoked.
- Raw Claude CLI envelope was not file-captured; normalized structured result and full model/usage custody are tracked.
- Instruction-like scanner: `NOT_RUN_DIRECT_CLAUDE_ROUTE`; auditor performed its own untrusted-content review and recorded F3.
