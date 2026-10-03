# Auditor Report: TP-DMX-MD-R6-WORKFLOW-SETUPPYTHON-001

- Auditor: claude-code-cli (Claude Code, runtime model claude-sonnet-5-5), Tier-1 independent final auditor, read-only
- Base: `b2dc31f871bf31dbb6bbea73c5a328b67dfcbb30` (equals current `origin/main` and the merge-base)
- Candidate head: `64547395e92d433e821a0790f52a5e257e7dc404`
- Donor: PR #1280 (actions/setup-python 5 to 7)
- **Verdict: PASS** (INFO findings only)

## 1. Scope containment: PASS
`git diff --name-status origin/main HEAD` lists exactly six paths: five `M` workflows (`ci-complete`, `clobber-guard`, `docs`, `pr-steward`, `preflight`) and one `A` (`task-packets/TP-DMX-MD-R6-WORKFLOW-SETUPPYTHON-001.json`). Nothing else changed. The scripted check found 0 changed paths outside this set. The task packet allowlist also covers the packet's own `proof/` directory. That directory is untracked and holds the review bundle plus these audit files.

## 2. Implementation correctness: PASS
- The diff contains 15 `-`/`+` line pairs, and every one is `actions/setup-python@v5` to `@v7`. That is 11 in ci-complete and 1 each in the other four workflows.
- No `setup-python@v[0-6]` remains anywhere under `.github/`. The only remaining hits are in archived docs (`docs/archive/...`, `docs/04-explanation/history/...`), which are out of scope.
- For each of the five files, base content with `v5` replaced by `v7` is byte-identical to the candidate. This proves nothing else changed (inputs, steps, caching, `needs`, indentation).
- Inputs: the only setup-python input used is `python-version` ("3.11" or "3.12"). There is no `cache`, `check-latest` or similar input. Caching in these files comes from `astral-sh/setup-uv`, which is untouched. All 18 `runs-on` values are `ubuntu-latest`.
- Upstream: tags `v7` and `v7.0.0` exist (`5fda3b95...`, verified with `git ls-remote`).
- YAML: all five files parse with `yaml.safe_load` at both base and head, with unchanged job counts (14, 1, 1, 1, 1).
- Task packet: its invariants ("Primary checkout is read-only", "No force/admin/service/credential/PAYG effects") are present. Its branch, base, allowlist and verify commands match the observed work.
- `review_bundle/TASK_PACKET.json` is identical to the committed packet. `review_bundle/DIFF.patch` equals `git diff origin/main HEAD`. `BASE_SHA.txt` and `CANDIDATE_HEAD.txt` match the observed SHAs. `STAT.txt` matches.

## 3. Validation re-run: PASS
| Check | Result |
|---|---|
| `python3 scripts/governance/validate_change_contract.py --base origin/main --head HEAD --format text` | exit 0, status=PASS, max_lane=L3, model_audit_required=True, paths=6 (5x L3 workflows, packet L0) |
| `git diff --check origin/main HEAD` | exit 0, clean |
| Workflow YAML parse (base and head) | PASS, 5/5 |
| `VALIDATION_RECEIPTS.json` | consistent with the re-runs above |

## Findings (all INFO, accepted)
- **AUDIT-001 Legacy-shape packet.** The packet does not validate against `schemas/governed_execution/task_packet.v2.schema.json`. It fails both oneOf branches (no `schema_version`, `macro_id`, `workstream_id` or `risk_lane`; agent `shell` with `pal_chain.enabled=false`). Sibling packets `TP-DMX-DEPENDABOT-ACTIONS-TOKEN-1169-001` and `TP-DMX-STEWARD-DEPENDABOT-ACTOR-1207-001` fail identically. None of the 289 files in `task-packets/` carries `schema_version`. v2 is therefore not the governing schema for this packet family, and the packet follows repo precedent. Its key set differs from the sibling only by `pal_chain` and `execution.stacked_because`.
- **AUDIT-002 Not executed / upstream notes unread.** The workflows were not run by the auditor, and the v7 release notes were not read. Input surface is minimal (see §2). A known risk class for newer setup-python majors is a Node runtime bump needing a recent runner, which GitHub-hosted `ubuntu-latest` satisfies. CI on the PR is the first runtime proof.
- **AUDIT-003 Floating major tag.** `@v7` is a mutable major tag, as `@v5` was. This is no regression, and SHA pinning is out of scope.

## Remaining risks
1. CI on the PR must run the five workflows.
2. Upstream v7 release notes were not independently reviewed.
3. The task packet is legacy-shape (AUDIT-001).

## Notes
- The auditor made no source changes, so `fixes_applied` is empty. Nothing was committed, and the new `proof/` files are untracked.
- `PROOF.json` wraps the audit under `embedded_audit`, which is the shape `scripts/audit/validate_audit_proof.py` consumes. The schema enum has no `claude-sonnet-5-5`, so `auditor_model` is `sonnet` and the literal model id is in `invocation`. `AUDIT_RETURN.json` holds the schema-pure object. Identity fields are in `AUDIT_RETURN.identity.json`, following the R5 precedent.
- `PROOF.json.sig` is not produced. The auditor holds no signing authority for it.
