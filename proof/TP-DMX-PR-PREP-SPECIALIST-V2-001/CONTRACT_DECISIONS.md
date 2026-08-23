# Contract Decisions — S1_FREEZE_V2_CONTRACT

## Single authority

`docs/03-reference/pr-pipeline/prep/operator-contract.md` is the sole
behavioral source of truth for `pr-prep-specialist`. `skill-model.md`,
`workflow-sequence.md`, `handoff-to-prms-contract.md`,
`deterministic-gate-rules.md`, `go-no-go-criteria.md`,
`pr-creation-policy.md`, and `high-risk-handoff-rules.md` in the same
canonical directory are now pointer stubs into `operator-contract.md`,
not independent contracts. `docs/03-reference/pr-pipeline/merge/handoff-from-prps-contract.md`
is the paired receiving contract.

## Retired

- exact seven-step artifact ceremony (`INSPECT_BRANCH_STATE` → ... →
  `HANDOFF_TO_PRMS`) → replaced by conditional S0-S8.
- LOW/MEDIUM/HIGH risk classification → replaced by L0_DETERMINISTIC /
  L1_BOUNDED / L2_MATERIAL / L3_RED.
- `GO_DRAFT_FIRST` / `GO_DIRECT` / `AWAIT_REVIEW` governing-posture enum and
  `AWAIT_REVIEW` / `MERGE_READY` / `BLOCKED` next-step enum → replaced by
  the eight prep states (§6) and free-text `recommended_next_step`
  consistent with them.
- `GO_SUPERVISED_FINAL_CREATION` / `GO_DRAFT_FIRST` / `GO_PACKAGE_ONLY` /
  `NO_GO_LIMIT_TO_ARTIFACTS_ONLY` / `ROLLBACK_TO_HUMAN_PREP` decision bands
  → replaced by prep states + S6 audit verdicts.
- `CREATE_READY` / `DRAFT_RECOMMENDED` / `BLOCKED_*` / `PACKAGE_ONLY`
  creation-decision vocabulary → replaced by the single `DRAFT_ONLY`
  default posture (§S4).
- `MERGE_SPECIALIST_NORMAL_FLOW` / `MERGE_SPECIALIST_DRAFT_FLOW` /
  `MERGE_SPECIALIST_HIGH_RISK_AWARE_FLOW` / `NO_HANDOFF_BLOCKED` fixed
  next-step tokens → replaced by `risk_lane` + `governing_posture` +
  `pr_steward` derivation (§8, §9).
- fixed `TP-PRPS-<n>-HANDOFF-<seq>` handoff id format and fixed
  seven-artifact `authoritative_artifacts` list → replaced by
  `schema_version: "2.0.0"` handoff bundle with open-ended artifact lists.

## Preserved (no weakening)

- PR Prep never grants merge authority; PR Steward remains the sole
  merge-readiness source (§3, §9 field guidance, receiving contract's
  re-verify-PR-Steward guard).
- L2/L3 requires one independent audit against the frozen `C1` (§5 S6, §9).
- Proof-only successor `C2` does not trigger re-audit of unchanged
  substantive content (§5 S7).
- No merge, close, mark-ready, force-push, history rewrite, branch
  deletion, permission/credential/signer/release/migration/production
  mutation is authorized by this contract (§3).
- Ordinary main drift is not an automatic stop condition; only
  `CONFLICTING`/materially `UNKNOWN` overlap blocks (§5 S1).

## One authority, no duplicated PR Steward authority

`operator-contract.md` §6 (prep states) is the only prep-state authority.
No other canonical-tree file redefines prep states, risk lanes, or the
handoff schema — they all point into `operator-contract.md` by section
reference rather than restating semantics.
