# MACRO-DMX-CMD-REPAIR-001 — Aggregate Return 03 (final; supersedes RETURN-01/02)

**Status**: `PASS_WITH_RISKS` (local, advisory). All six workstreams are implemented and committed on `fix/cmd-repair-001`. The single final independent audit of the frozen head returned `PASS_WITH_RISKS`. **Not pushed. No PR. No merge.**
**Authority**: NONE. This aggregate mints no READY/DONE. Acceptance, push, PR and merge are operator gates. PR Steward readiness is not claimed.

## Frozen subject

- **Audited content head**: `7c6cfc0370092c6076d227e7eaaf05203d379303`, base `95e95bee88cae5e6c95e6e34f7c28bb423ad9496`.
- **Size**: 6 commits, 48 files, +454/−107. The audited diff's sha256 is `ec458cc90e56166dc36203a95a881132562ba1356b3f30a7900c9d2d6d4135e6`.
- **Proof-only successor**: three commits on top add the proof bundle `proof/MACRO-DMX-CMD-REPAIR-001/` and the issuance package under `proof/MACRO-DMX-CMD-REPAIR-001/review_bundle/issuance/` (the package was first committed under `task-packets/`, then moved because the preflight rejects GEC v2 packets and these documents there; see its README). All paths are L0, and no audited content changed. The SHAs are in `git log` (`4a861a70d`, `571f727a6`, and this correction).

| Commit | WS | Files | Requested → observed model | Advisor |
|---|---|---|---|---|
| `55e4f6cad` | W01 ConPort/FTS names | 18 | haiku-5-5 → haiku-5-5 | 0 |
| `b0c505489` | W03 dead targets | 5 | sonnet-5-5 → sonnet-5-5 | 0 |
| `08130eb5c` | W02 model pins | 26 | haiku-5-5 → haiku-5-5 | 0 |
| `9c93afbb7` | W04 drift-gate test | 1 | sonnet-5-5 → sonnet-5-5 | 0 |
| `70eb50363` | W05 fleet snapshot (AMENDMENT-01) | 1 | sonnet-5-5 → sonnet-5-5 | 0 |
| `7c6cfc037` | W06 audit repairs (AMENDMENT-02) | 4 | sonnet-5-5 → sonnet-5-5 | 0 |

- **Observed model** is each child transcript's `message.model`. Effort was `runner-default`; observed UNKNOWN.
- **Coordinator turns**: Opus 5.5 until the operator switched to Sonnet 5.5 in the model menu; the W05 and W06 amendments and all later turns ran on Sonnet.
- **Children**: 6 launched, plus 2 resumes for supervisor rulings. All transcripts show no mutating git commands and no advisor calls.
- **Packet integrity**: the 6 pinned issuance members are byte-identical to issuance and `ct validate-macro` is STATIC_VALID. AMENDMENT-01 (W05) and AMENDMENT-02 (W06) are separate packets authorized in chat.

## Audit history

| | Head | Verdict | Disposition |
|---|---|---|---|
| AUDIT-01 | `70eb50363` | **FAIL** (1 BLOCKING, 1 HIGH, 2 MEDIUM, 1 LOW) | Findings F1, F2, F3, F5 confirmed from source and repaired by W06. Subject superseded. |
| AUDIT-02 | `7c6cfc037` | **PASS_WITH_RISKS** (0 BLOCKING, 0 HIGH, 1 MEDIUM, 2 LOW, 1 INFO) | Final result for the frozen head. No further repair, because a change would invalidate it. |

- **Route**: an operator-approved packet-specific fallback. `agy` 1.3.6 with `gemini-4-argon-high`, input limited to the frozen diff and the contract, no repo mount. This is recorded as `auditor_tool: agy`, `auditor_model: gemini` (generic).
- **Not met**: the embedded-audit doc's exact model `gemini-3.1-pro-high`, absent from `agy models`. **Exact-model evidence is unavailable.**
- **Independence**: a different family from the Claude implementers; provider-attested identity UNKNOWN.
- **Containment**: verified structurally for both runs. The streams have only `user_input` and `agent_response` steps, 1 turn each, and the auditor declared `tools_used: none`. It was not enforced: AGY's global MCP servers (desktop-commander, serena, dope-context) were reachable. I did not alter your global AGY config.
- **Detail**: `AUDIT-01/ADJUDICATION.md` and `AUDIT-02/ADJUDICATION.md`.

## Validation (audited head)

| Check | Result |
|---|---|
| `pytest tests/arch -q` | PASS (202) |
| New drift-gate tests | PASS (18); the negative controls fail on the old regexes |
| Dead-name gates over `.claude/commands` | PASS (empty) |
| Per-commit allowlist | PASS: W01 18/18, W03 5/5, W02 26/26, W04 1/1, W05 1/1, W06 4/4 |
| `validate_change_contract.py` | PASS, max lane L2 |
| `pre-commit run --from-ref origin/main --to-ref HEAD` | PASS |
| `git diff --check` | PASS |
| black / flake8 on the new test | PASS / PASS |
| `ct validate-binding` coordinator + W01–W06 | PASS |
| `embedded_audit` against the schema | PASS (0 errors; a bad-combination control fails as expected). The repo's pre-commit hook "Validate proof bundle embedded_audit schema" also passed on the final head. Only `validate_audit_proof.py --all` skipped this path, because `proof/.validator_scope.json` doesn't list this id. |
| `make test` full suite | NOT_RUN |
| Live ConPort :3005 qualification | NOT_RUN (the July capture is historical; source agrees) |
| `ct return-pack` | NOT_RUN |
| `PROOF.json.sig` | NOT_RUN: signing needs the operator's key |
| Preflight on the final head (`origin/main..HEAD`) | PASS (max lane L2). An earlier proof head failed it because of the `task-packets/` placement; relocated in `571f727a6` |

## Residual risks and open items

1. **Prose scan deferred.** The drift gate skips the `/mcp <server> <tool>` form and prose tool names, leaving 6 command files unguarded. `zen.md` and `zen-continue.md` reference a nonexistent `zen` server. **Follow-up packet** (needs its own authorization): retire or repoint those commands, then add the scan.
2. **`pal` vs `pal-stdio` naming**: `plan.md` versus `dx/implement.md` and `dx/note.md`. Pre-existing, out of scope.
3. **Two minor regex edges** in the drift gate: underscore server names, and malformed tokens like `get_context--bad` truncating to a valid prefix. Only `MCP_DOCKER` has an underscore and no command references it.
4. **ConPort semantics**: `get_custom_data` fetches whole categories; `search_content` has no limit; `update_context` merge-versus-replace is UNKNOWN.
5. **PR Steward / CI**: the exact-model gap means PR Steward may not treat the audit as READY. The pre-commit schema hook validated this bundle; only the `--all` scope list in `proof/.validator_scope.json` omits this id (corrected from an earlier draft that said CI would not enforce the bundle).
6. **Docs drift**: `docs/02-how-to/mcp-integration-guide.md:165-167` still describes the old snapshot. It is outside every allowlist.
7. **Main checkout** still holds another actor's uncommitted doctrine edits, plus the pre-existing untracked files. Untouched.

## Operator gates

- **Push the branch and open a draft PR.** I did not do either.
- **Accept the fallback-audit result**, or request a re-audit on `gemini-3.1-pro-high` when it returns.
- **Authorize the `zen` follow-up** and the docs fix.
- **Sign the proof** (`PROOF.json.sig`) if the repo's gates require it.
- **Delete the branch/worktree** when done.

## Closure

- **Children**: all terminated; no background processes. The two `agy` audit runs exited.
- **Worktree**: `.worktrees/cmd-repair-001`, branch `fix/cmd-repair-001`, retained.
- **Quota**: weekly usage was 2% at the last read; extra usage OFF.
- **Local state**: `.control-tower/state/bindings/` in the worktree holds the 7 execution bindings (ignored by git).

## Rollback

```bash
git worktree remove .worktrees/cmd-repair-001
git branch -D fix/cmd-repair-001
```

Branch deletion is an operator-only gate. To keep the branch, revert any single workstream commit.
