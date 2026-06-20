# ChatGPT Delta Challenge Prompt (supersedes full A–F re-review)

**Pack**: Use the newly uploaded supervisor input pack only. Treat any earlier **100KB / 30-file** pack as **superseded**.

**Current pack marker**: `115KB+` rebuild includes:
- `D2_D3_D4_EVIDENCE.md`
- `docs/docs_index.yaml`
- `templates/plugin/l0_membership.json`
- `SUPERVISOR_FINAL_REVIEW.md` / `.json`
- `PR_939_LIVE_REFRESH.md`
- Refreshed `PROOF.json` with `embedded_audit` (post `7199c61a8`)

Verdict already exists in:
- `proof/TP-DMX-MEMORY-TRINITY-001/SUPERVISOR_FINAL_REVIEW.md`
- `proof/TP-DMX-MEMORY-TRINITY-001/SUPERVISOR_FINAL_REVIEW.json`

**Do not** re-run the full A–F review unless you find a contradiction. Perform a **delta challenge only**:

1. Verify `SUPERVISOR_FINAL_REVIEW.md` and `.json` agree.
2. Inspect `D2_D3_D4_EVIDENCE.md` before marking D2/D3/D4 UNKNOWN.
3. Confirm `docs/docs_index.yaml` and `l0_membership.json` are present before changing D3/D5.
4. Check whether `merge_verdict: BLOCKED` and `pr_939: MERGE_WITH_FOLLOWUPS` are explicitly reconciled via `pr_939_note`.
5. Preserve **CLAIMED vs OBSERVED**: Codex runtime logs are claimed evidence, not re-run runtime.
6. Do not treat `origin/main` absence of branch-only files as branch failure.

**Release readiness policy** (2026-06-17): requires current head SHA, current CI/checks, current proof, and independent audit or human approval. Stale proof is an explicit blocker. `merge_verdict: BLOCKED` means **release readiness blocked**, not necessarily "never merge PR."

Output only:
- accepted deltas
- challenged deltas
- unresolved UNKNOWNs
- final JSON recommendation