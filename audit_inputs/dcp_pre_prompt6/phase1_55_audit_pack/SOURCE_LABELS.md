# Source Labels and Provenance

Every artifact in this bundle is labeled with its source and verification method.

---

## Label Definitions

| Label | Meaning | Trust Level |
|-------|---------|------------|
| **OBSERVED_BY_RUNTIME** | Direct execution in current session (git, Python, bash) | HIGH |
| **OBSERVED_BY_GITHUB** | Fetched from GitHub API via gh CLI | HIGH |
| **OBSERVED_BY_LOCAL_FILE** | Copied from repo filesystem (present at assembly time) | HIGH |
| **CLAIMED_ONLY** | Asserted without direct observation | LOW |
| **UNKNOWN** | Source uncertain or not available | UNKNOWN |
| **MISSING** | Explicitly absent, not found in search | UNKNOWN |
| **STALE** | Known to be outdated at assembly time | LOW |
| **SUPERSEDED** | Replaced by newer evidence | SUPERSEDED |
| **INFERRED** | Derived from other evidence | MEDIUM |

---

## Artifact Provenance Table

### Authoritative Artifacts (High Confidence)

| Artifact | Path | Label | Source Command/File | Why Included | Caveat |
|----------|------|-------|-------|-------|---------|
| routing_classifier.py | files/routing_classifier.py | OBSERVED_BY_LOCAL_FILE | cp src/dopemux/dcp/routing_classifier.py | Current code post-#904 | None — direct copy from HEAD |
| test_routing_classifier.py | files/test_routing_classifier.py | OBSERVED_BY_LOCAL_FILE | cp tests/unit/dcp/test_routing_classifier.py | Current tests post-#904, 77 total | None — direct copy from HEAD |
| PR #902 info | github/pr902_info.txt | OBSERVED_BY_GITHUB | gh pr view 902 | Merge state, author, title | gh cli output truncated (body partial) |
| PR #904 info | github/pr904_info.txt | OBSERVED_BY_GITHUB | gh pr view 904 | Merge state, title | gh cli output truncated (body partial) |
| PR #902 diff | github/pr902.diff | OBSERVED_BY_GITHUB | gh pr diff 902 | Complete unified diff | May not include some GitHub-UI metadata |
| PR #904 diff | github/pr904.diff | OBSERVED_BY_GITHUB | gh pr diff 904 | Complete unified diff | May not include some GitHub-UI metadata |
| PR #902 patch | github/pr902.patch | OBSERVED_BY_GITHUB | gh pr diff 902 --patch | Git patch format | Standard git patch |
| PR #904 patch | github/pr904.patch | OBSERVED_BY_GITHUB | gh pr diff 904 --patch | Git patch format | Standard git patch |
| 0005 design spec | files/dcp-routing-0005-lane-engine-design-2026-06-16.md | OBSERVED_BY_LOCAL_FILE | cp claudedocs/dcp-routing-0005-lane-engine-design-2026-06-16.md | Next-phase design | Direct copy; may be draft |
| 0005 remediation packet | files/TP-DCP-0005-POSTMERGE-REMEDIATION.json | OBSERVED_BY_LOCAL_FILE | cp task-packets/TP-DCP-0005-POSTMERGE-REMEDIATION.json | Remediation actions | Direct copy; JSON validated |

### Supporting Artifacts

| Artifact | Path | Label | Source | Purpose | Caveat |
|----------|------|-------|--------|---------|---------|
| Phase 1 packet (0002) | files/DMX-DCP-PRE-PROMPT6-0002.md | OBSERVED_BY_LOCAL_FILE | cp task-packets/DMX-DCP-PRE-PROMPT6-0002.md | Phase 1 scope | Context only |
| 0005 PROOF.json | proof/TP-DCP-0005-PROOF.json | OBSERVED_BY_LOCAL_FILE | cp proof/TP-DCP-0005/PROOF.json | Post-merge proof state | Extracted from proof/ directory |
| 0005 MERGE_READINESS.json | proof/TP-DCP-0005-MERGE_READINESS.json | OBSERVED_BY_LOCAL_FILE | cp proof/TP-DCP-0005/MERGE_READINESS.json | Readiness gate | From proof directory |
| 0005 POST_MERGE_RECONCILIATION.json | proof/TP-DCP-0005-POST_MERGE_RECONCILIATION.json | OBSERVED_BY_LOCAL_FILE | cp proof/TP-DCP-0005/POST_MERGE_RECONCILIATION.json | Reconciliation state | From proof directory |
| Classifier tests output | proof/validation_classifier_tests.txt | OBSERVED_BY_RUNTIME | PYTHONPATH=src python -m pytest ... | 77/77 PASS | Direct pytest output, exit code 0 |
| DCP tests output | proof/validation_dcp_tests.txt | OBSERVED_BY_RUNTIME | PYTHONPATH=src python -m pytest ... | 275/276 PASS (1 expected) | Pre-existing failure, not Phase 1 |
| Compilation check | proof/validation_compileall.txt | OBSERVED_BY_RUNTIME | python -m compileall -q src/dopemux/dcp | No syntax errors | Exit code 0 |
| Diff check | proof/validation_diff_check.txt | OBSERVED_BY_RUNTIME | git diff --check | No format issues | Exit code 0 |
| Related artifacts list | proof/related_artifacts.txt | OBSERVED_BY_RUNTIME | find ... \| grep ... | Index of other audit/proof files | Informational only |

### Git Evidence

| Item | Source | Label | Notes |
|------|--------|-------|-------|
| GIT_STATE.md | git commands + local capture | OBSERVED_BY_RUNTIME | HEAD, branch, log, status |
| GITHUB_STATE.md | gh CLI + local capture | OBSERVED_BY_GITHUB | PR metadata, diffs |
| COMMAND_LOG.md | Assembly log | OBSERVED_BY_RUNTIME | All commands executed |
| Phase 1 merge commits | git rev-parse, git log | OBSERVED_BY_RUNTIME | a740edc40 (#902), ba36b58cb (#904) |

---

## Missing/Unknown Artifacts (Explicit)

| Item | Status | Label | Why It Matters | Why Absent |
|------|--------|-------|---|---|
| Local State Doctor | MISSING | UNKNOWN | Pre-Phase-1 system state audit | Out-of-scope for Phase 1 (which was narrowed to #902/#904) |
| Opus adversarial audit | MISSING | UNKNOWN | Independent architectural review | Deferred to Phase 1 Audit pass (this bundle is the audit pass) |
| PR #873 evidence bundle | DEFERRED | STALE | gpt-5.5 synthesis (80 files) | Behind main, out-of-scope for Phase 1 focus |
| 0006/0009/0010 packets | MISSING | UNKNOWN | Deferred lane packets | Not yet created/authored |
| PR #902 PR Steward artifacts | UNKNOWN | UNKNOWN | Steward proof for #902 | Not located in standard paths (may be in proof/pr_merge/) |
| CI check results for #904 | UNKNOWN | UNKNOWN | GitHub Checks status | gh pr checks did not return data |

---

## Authority Ranking (for conflicts)

If two artifacts provide conflicting information:

1. **OBSERVED_BY_RUNTIME** (git, Python tests) — highest trust
2. **OBSERVED_BY_GITHUB** (gh CLI, direct GitHub API) — high trust
3. **OBSERVED_BY_LOCAL_FILE** (filesystem copies) — high trust (limited to file content, not state)
4. **INFERRED** (derived from other evidence) — medium trust
5. **CLAIMED_ONLY** (asserted without evidence) — low trust
6. **UNKNOWN** (uncertain source) — unknown trust
7. **STALE** / **SUPERSEDED** (outdated) — not trustworthy

---

## Validation of Artifacts

All authoritative artifacts have been validated:

✅ **routing_classifier.py** — Python compiles, file exists, 20 KB  
✅ **test_routing_classifier.py** — All 77 tests pass, file exists, 52 KB  
✅ **PR diffs** — Available via gh cli, reasonable size (14 KB each)  
✅ **0005 spec** — Markdown file, readable, 5.8 KB  
✅ **0005 remediation** — JSON valid, readable  
✅ **Test results** — Exit codes recorded, pytest output captured  
✅ **Git evidence** — All commits verified on main  

---

## Chain of Custody

| Step | Who | What | When | Where |
|------|-----|------|------|-------|
| Assembly | claude-code | Gathered evidence | 2026-06-16 18:45 UTC | /Users/hue/code/dopemux-mvp |
| Verification | (GPT-5.5) | Audit & verdict | 2026-06-16 (TBD) | This bundle |
| Disposition | (Operator) | Action/merge | 2026-06-16 (TBD) | dopemux-mvp main |

---

## Confidence Summary

| Category | Confidence | Notes |
|----------|-----------|-------|
| Phase 1 completeness | HIGH | Both PRs merged, tests pass |
| Code quality | HIGH | 77/77 tests pass, Python compiles |
| Design readiness | MEDIUM | 0005 spec present but not yet audited |
| Scope clarity | HIGH | Documented in PRs and packets |
| Evidence completeness | MEDIUM-HIGH | Essential artifacts present, some GitHub data partial |
| Bundle integrity | HIGH | All files verified, ZIP checksummed |

---

**Total artifacts**: ~30  
**Authoritative**: ~9 (high confidence)  
**Supporting**: ~12 (context/validation)  
**Missing/Unknown**: ~6 (explicitly documented)  
**Overall bundle confidence**: **HIGH**
