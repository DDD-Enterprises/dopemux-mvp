# TP-DMX-MERGE-FINALIZATION-203 Bounded Audit

Status: PASS_WITH_LIMITS

## Scope Reviewed

- `steward_gate(FINALIZATION)` queue-drain wiring before live merge execution.
- Direct merge execution path in `run_merge_with_fallback`.
- GitHub GraphQL command construction for `mergePullRequest` with `expectedHeadOid`.
- Default-off governed automerge behavior.
- Admin-bypass squash blocking.
- PR merge specialist skill template parity for changed runtime modules.

## Findings

- PASS: live merge execution now requires local finalization gate evidence before calling the merge engine.
- PASS: direct rebase merge no longer falls back to ungated `gh pr merge`; GraphQL failures produce blocked `UNKNOWN` evidence.
- PASS: missing PR head SHA blocks before GraphQL merge execution.
- PASS: governed automerge is disabled by default by both runtime behavior and policy config.
- PASS: approval-missing no longer selects admin-bypass squash.
- PASS: manual review found incorrect `--repo` use on `gh api graphql`; a failing test was added first and the command builder was fixed.

## Limits

- External embedded audit was not run in this local Codex session.
- No live GitHub merge was executed.
- Supervisor sign-off for red-lane finalization authority was not performed.

## Residual Risks

- Current GitHub auth scope for live `mergePullRequest(expectedHeadOid)` remains UNKNOWN until exercised under supervisor approval.
- Merge queue behavior under GraphQL finalization remains unexercised.
- Branch deletion after GraphQL merge is not implemented in this packet.
