# AUDITOR_REPORT.md — TP-DMX-FDOS-004-CHATGPT-PROJECT-SOURCE-REFRESH

**auditor_tool**: Claude Code CLI
**auditor_model**: claude-sonnet-5 (Sonnet)
**invocation**: Spawned as a separate `Agent` subagent (general-purpose type) by a distinct orchestrating Claude Code session, with no prior conversational context from the implementer session — this session started fresh, was handed only the packet identifiers and the audit checklist, and read all packet/implementation files itself from disk. This satisfies the packet's requirement that the implementer not audit itself.

**Repository**: DDD-Enterprises/dopemux-mvp, worktree `.claude/worktrees/chatgpt-40-source-refresh-f84dfc`, branch `claude/chatgpt-40-source-refresh-f84dfc`, PR under audit: #1152, head SHA `c6e0ebd19f5e5a299512e59239d68003b9016da9`, EXECUTION_BASE_SHA `5f862d36f5417801b9fe148fccbb439731627234`.

No files were modified by this audit except the two files this report describes. No fixes were applied.

---

## 1. Source authority ordering (spot-checked slot resolutions)

Independently re-derived 15 of the 37 slot resolutions against `EXECUTION_BASE_SHA` using `git cat-file -e` / `git show`:

- Confirmed **tracked and byte-identical**: slots 01 (AGENTS.md), 03 (PROJECT.md), 04 (ARCHITECTURE.md), 05 (system-boundaries.md), 06 (pm-plane.md), 08 (doc-trust-map.md), 09 (runtime-authority-verification.md), 15 (system-dopemux.md), 20 (system-dopecontext.md), 23 (system-repotruthextractor.md), 25 (dopetask-canonical-spec.json), 34 (model-routing.policy.yaml), 35/36 (adapter contract/schema), 37 (governance-model.md).
- Confirmed **genuinely missing at EXECUTION_BASE_SHA** (validating the "BLOCKED_SOURCE_MISSING" rejections): `RULES.md`, `SYSTEM_BOUNDARIES.md`, `TRUTH_CANONICALS.md`, `TRUTH_INTERFACES.md`, `TRUTH_GAPS.md`, `PAL_EXECUTION_RULES.md`, `dopetask-canonical-spec.json` (root), `dopetask-cannonical-spec.json` (misspelled root variant) — all absent, matching the source_set_v4.json rationale.
- Confirmed root **`ARCHITECTURE.md` and root `PM_PLANE.md` are both actually tracked** at EXECUTION_BASE_SHA (contrary to what a naive read of doc-trust-map.md's "untracked" note would suggest) — this validates the implementer's claim in slot 04's rationale that doc-trust-map is stale on that point.
- Confirmed slot 35/36 duplicate-blob claims: `docs/02-how-to/integrations/dopetask/adapter-contract.md` and `docs/integrations/dopetask/adapter-contract.md` share blob SHA `67a1763d...`; the schema pair shares `ce9e878c...`. Both duplicate claims are correct.

**Slot 06 (PM_PLANE.md) deep check — the one point I actively pushed back on**: I independently read `docs/03-reference/governance/doc-trust-map.md` in full. Its "PM plane references" row explicitly rates `docs/03-reference/planes/pm/pm-plane.md` HIGH. Its "Top-level promoted or user-provided packet docs" row is LOW and **explicitly lists** `RULES.md; PROJECT.md; ARCHITECTURE.md; SYSTEM_*.md; TRUTH_*.md; PAL_*.md; dopetask-cannonical-spec.json` — **root `PM_PLANE.md` is not literally named in that list** (it matches none of the listed literal names or glob patterns). The slot-6 rationale's claim that root PM_PLANE.md "is bucketed by the same doc-trust-map" under that LOW row therefore slightly overstates the source document — it is an analogical extension, not an explicit citation. That said, I diffed the two candidate files at EXECUTION_BASE_SHA: root `PM_PLANE.md` (254 lines, no frontmatter, no explicit authority chain) versus `docs/03-reference/planes/pm/pm-plane.md` (124 lines, dated frontmatter with `next_review`, and an explicit stated authority chain to `docs/03-reference/truth/*` and named runtime files). On substance, the HIGH-rated tracked file is the better-disciplined, better-evidenced choice regardless of the imprecise citation. **Finding: minor rationale-precision gap, not a wrong pick.**
- Slot 04 (ARCHITECTURE.md) by contrast explicitly overrides doc-trust-map's implied LOW/stale rating for the same document family, on the grounds that the file is in fact tracked. I note this as an internal inconsistency in how the two doc-trust-map rows were weighed (override in one case, selective-extension in the other) — but both outcomes are independently defensible on the file contents, so I do not treat this as a defect, only a documentation-precision observation.

## 2. Exact 40-file count and slot completeness — PASS

`find UPLOAD_FILES -maxdepth 1 -type f | wc -l` → **40**. Filenames are `01_AGENTS.md` … `40_OPEN_PR_IMPACT_LEDGER.md`, no hidden files, no duplicate filenames (`ls -la` shows only `.` and `..` plus the 40 regular files). The packet's own validator's `filename` gate independently confirms `"unique": true, "hidden": []` across all 40 slots.

## 3. Current-main byte identity — PASS

For all 15 slots checked above, `diff <(git show $SHA:<source_path>) UPLOAD_FILES/<bundle>` produced **zero output** (byte-identical) and `git rev-parse $SHA:<path>` matched the `source_blob_sha` recorded in `39_PROJECT_SOURCE_MANIFEST.json` for each. Beyond my manual spot-check, I ran the packet's own `scripts/project_sources/validate_chatgpt_project_sources.py` (see §7 below), whose `source_identity` and `hash` gates independently re-verify **all 37** copied slots, not just my sample, and reported `"pass": true` with empty detail (no mismatches) for both.

## 4. Stale/generated source removal — PASS

Grepped `UPLOAD_FILES/*` for the packet's named historical exclusions (`Package Verification Process`, `Multi-Model Routing Policy`, `task-packets/INDEX.md`) — no hits except one unrelated substring match inside `38_SOURCE_FRESHNESS_POLICY.md` which is itself the policy text *disclaiming* reliance on "any prior `Package Verification Process.txt`-style artifact" (i.e. correctly discussing, not including, the excluded artifact). `SOURCE_REJECTION_LEDGER.md` explicitly lists and classifies `Package Verification Process.txt`, `Multi-Model Routing Policy.txt`, `task-packets/INDEX.md`, `REPO_STRUCTURE.md`, `TOP40_SELECTION_RATIONALE.md`, `DRIFT_AND_GAPS_SUMMARY.md`, `agents.instructions.md`, `PAL_CHAINING_DOCTRINE.md`, `PAL_PACKET_TEMPLATE.md` as excluded, each with a specific reason code, matching packet §9/§18 intent.

## 5. Open-PR classification completeness and correctness — PASS, with disclosed drift

Ran `gh pr list --repo DDD-Enterprises/dopemux-mvp --state open --limit 200 --json number` live: returned **26 open PRs at the moment of my check** (later even 27, as new PRs continued landing mid-audit — this repo has very active concurrent automation). Excluding PR #1152 itself, that's 25+ open PRs versus the ledger's captured 21. All the extra PRs (#1151, #1153–#1156 and beyond) have `createdAt` timestamps **after** the ledger's `captured_at: 2026-07-28T00:15:00Z`, i.e. genuine post-capture churn, not omissions. This is exactly the kind of expected drift the task brief said not to penalize. The ledger's own conservation logic held: `open_pr_conservation` gate (run live by me, see §7) reported `initial_count: 21, ledger_count: 21, missing_from_ledger: [], extra_in_ledger: []` — internally consistent.

Spot-checked 4 classifications directly against live `gh` data:
- **PR #1123** (`SUPERSEDED_OR_CONFLICTING`): `gh pr view 1123 --json changedFiles,additions,deletions,mergeStateStatus` returned `changedFiles=16206, additions=5145096, deletions=9284, mergeStateStatus=DIRTY` — an **exact match** to the ledger's cited evidence numbers. Classification and evidence are real, not fabricated.
- **PR #1136** (`SOURCE_CONTENT_REFRESH_IF_MERGED`, slot 23): `gh pr view 1136 --json files` confirms `docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md` is indeed among its changed files, and `changedFiles=366, mergeStateStatus=BEHIND` matches the ledger (the ledger also correctly notes `gh`'s `files` connection caps display at 100 and cites the true 366 via `changedFiles` — verified true).
- **PR #1117** (`NO_PROJECT_SOURCE_IMPACT`): `gh pr view 1117 --json files,changedFiles` returned exactly 1 file, `ui-dashboard/package-lock.json` — no intersection with any selected slot. Correct.
- **PR #1140** (`NO_PROJECT_SOURCE_IMPACT`): confirmed 18 changed files including `docs/90-adr/adr-dmx-prsteward-soloowner-001.md` (MODIFIED, +32/-8). This path falls under the ledger's own watched-family glob `docs/90-adr/**`, which is presumptively material by the ledger's own rules. The ledger's evidence text addresses only slot 32 (`docs/ops/pr-steward.md`) and does not explicitly state that the touched ADR is a different file from the one actually selected as a source (slot 11 is `adr-memory-trinity-authority-and-interaction-model.md`, a distinct, unaffected file). I independently confirmed the two ADRs are different files, so the **classification outcome is correct**, but the written evidence has a **documentation completeness gap**: it doesn't explicitly say "checked against slot 11 / docs/90-adr family, confirmed a different file." Minor, non-blocking.
- Also independently verified PR #1150 (`SOURCE_CONTENT_REFRESH_IF_MERGED`, slots 1/15/17): live `gh pr view 1150` confirms `changedFiles=56`, `mergeStateStatus=UNSTABLE`, `headRefOid=edb265c9...`, and its file list does include `AGENTS.md`, `docs/03-reference/systems/dopemux/system-dopemux.md`, and `docs/03-reference/systems/task-orchestrator/system-taskorchestrator.md` exactly as claimed. This head SHA also matches the one recorded in the package's own `PR_DRIFT_RECHECK.md`, which documents that #1150's head changed once during the build window and the evidence was correctly refreshed before finalization.

## 6. No unmerged PR content promoted into current-main authority — PASS

Grepped all `UPLOAD_FILES/*.md|*.json|*.yaml` (excluding `40_OPEN_PR_IMPACT_LEDGER.md`) for open-PR branch names, dependabot branch patterns, and raw head-SHA-style tokens. No hits.

## 7. Manifest correctness — PASS

`python -m json.tool 39_PROJECT_SOURCE_MANIFEST.json` validates. `upload_file_count: 40`, `len(files) == 40`. Wrote and ran a standalone script computing a fresh `sha256`/byte-count for every bundle file on disk and comparing to the manifest's recorded `sha256`/`bytes`: **all 39 content-bearing entries matched exactly**; the one exception (slot 39, the manifest itself) has `sha256: null, bytes: null` by explicit, documented design (a manifest cannot self-hash before it is fully written), with the note correctly redirecting outer-package integrity to the ZIP sha256 sidecar. This is a legitimate, disclosed design choice, not a defect.

I also independently ran the packet's own validator, `scripts/project_sources/validate_chatgpt_project_sources.py`, live against the real repo state (not trusting the recorded `PACKAGE_VALIDATION.json`): exit code 0, all 9 gates (`source_count`, `filename`, `source_identity`, `hash`, `duplicate_content`, `json`, `yaml`, `open_pr_conservation`, `secret_scan`) reported `pass: true`.

## 8. Freshness policy — PASS

`38_SOURCE_FRESHNESS_POLICY.md` is a real, specific, usable policy: it defines 6 named freshness classes with concrete staleness triggers (day counts and "on any merged PR touching X" rules), 11 numbered required rules tying back to the manifest and ledger, and an explicit disposition-note section stating "No disposition in this family is ever 'final forever.'" This is not filler.

## 9. Secret scan — PASS

Ran targeted patterns (`sk-[A-Za-z0-9]{20,}`, `ghp_[A-Za-z0-9]{20,}`, `-----BEGIN ... PRIVATE KEY`, `AKIA[0-9A-Z]{16}`, `Authorization:\s*Bearer\s+\S`) against all of `UPLOAD_FILES/`: no matches. (A looser first pass on bare `sk-` produced false positives against substrings like "task-orchestrator"; the stricter pattern set correctly returned zero.)

## 10. Package integrity — PASS

From `out/chatgpt-project-upload-set/`: `unzip -t TP-DMX-FDOS-004-CHATGPT-PROJECT-SOURCE-REFRESH.zip` → "No errors detected in compressed data." `shasum -a 256 -c TP-DMX-FDOS-004-CHATGPT-PROJECT-SOURCE-REFRESH.zip.sha256` → `OK`. The zip contains 66 entries total (the 40 `UPLOAD_FILES/*` plus the supporting reports and `OPEN_PR_CAPTURE/*` raw evidence, i.e. the whole package directory, not only the 40-file subset) — confirmed the `UPLOAD_FILES/` entries inside the zip number exactly 40.

I also independently re-ran `scripts/project_sources/build_chatgpt_project_sources.py` from the same inputs (`source_set_v4.json`, `pr_classifications.json`, the `proof/.../open-pr-*.json` evidence, same `--generated-at` timestamp) into a scratch directory and diffed the rebuilt `UPLOAD_FILES/` against the committed one: `diff -rq` reported **zero differences** — reproducibility is real, not just claimed.

## 11. Allowlist compliance — PASS

`git diff --name-only 5f862d36f5417801b9fe148fccbb439731627234..HEAD` returns 123 changed files. Checked every path against the packet's declared allowlist regexes programmatically: **0 violations**. (Two unrelated, pre-existing local worktree artifacts — `.claude/claude_config.json` modified, `.claude/.untracked-work-probe-cache.json` untracked — are visible in `git status` but are not part of this branch's committed diff against base and are not attributable to this packet's work.)

## 12. Proof completeness — PASS

`proof/TP-DMX-FDOS-004-CHATGPT-PROJECT-SOURCE-REFRESH/` contains `EXECUTION_BASE_SHA.txt` (matches `5f862d36f5417801b9fe148fccbb439731627234`), `GIT_STATUS_BEFORE.txt`, `BRANCH.txt`, `GIT_REMOTES.txt`, `OPEN_PRS_INITIAL.json` (21 entries), `OPEN_PRS_CHANGED_FILE_COUNTS.json`, 21 `open-pr-*.json` files (+ matching `.stderr` files, all empty), and `PR_DRIFT_RECHECK.md` documenting a real recheck (origin/main unchanged, one PR head-SHA change for #1150 handled and re-verified before finalization).

## 13. Misleading completion/finality claims — PASS

Read the live PR #1152 body via `gh pr view 1152 --json body`. It states disposition `CURRENT_MAIN_VALID_PENDING_OPEN_PR_REFRESH` (not stronger), explicitly lists residual risks/UNKNOWNs (doc-trust-map near its own review horizon, #1123's classification not re-litigated, the `execution.agent` schema gap, embedded audit pending), and never claims permanence. `README.md` and `38_SOURCE_FRESHNESS_POLICY.md` both reiterate the same disposition and explicitly disclaim "final forever." No overreach found.

## 14. execution.agent="shell" schema workaround — PASS, genuinely required

Read `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` directly: the `execution.agent` property's `enum` is exactly `["gemini", "codex", "vibe", "shell"]` — there is no `"claude"` value. Validated the packet JSON against this exact schema file with `jsonschema.validate()`: it passes. The invariant in the packet JSON honestly documents the workaround and flags the missing enum value as a follow-up, rather than silently mislabeling the executor. This is not an avoidable shortcut; adding `"claude"` to the enum would be a schema change, correctly noted as out of scope per the packet's own §4.2.

---

## Findings Summary

1. **(Minor / documentation precision)** Slot 6's rationale in `source_set_v4.json` says root `PM_PLANE.md` "is bucketed by the same doc-trust-map" LOW row as `RULES.md`/`ARCHITECTURE.md`/etc. — but `doc-trust-map.md`'s explicit source-path list for that row does not literally name `PM_PLANE.md`. The underlying editorial choice (prefer the HIGH-rated, dated, authority-chain-citing tracked doc over an undated, unclassified root duplicate) is well-supported on the actual file contents, but the citation is an extension of the map, not a direct quote of it.
2. **(Minor / evidence completeness)** PR #1140's ledger entry doesn't explicitly note that its touched `docs/90-adr/adr-dmx-prsteward-soloowner-001.md` file (which does fall under the ledger's own watched `docs/90-adr/**` family) is a different file from the one actually selected as slot 11 (`adr-memory-trinity-authority-and-interaction-model.md`). The `NO_PROJECT_SOURCE_IMPACT` classification is still correct on independent verification, but the written evidence only discusses slot 32 and silently skips discussing the ADR-family intersection.
3. **(Disclosed, not a defect)** Open-PR count has drifted from 21 (capture time) to 25+ (audit time) purely due to new PRs landing after capture; the ledger's internal conservation check (21 captured = 21 in ledger) still holds and this drift is exactly the kind the packet anticipates and the freshness policy addresses.
4. **(Internal inconsistency, not a defect)** Slots 4 and 6 apply doc-trust-map's "top-level promoted docs are LOW" classification inconsistently — overridden for ARCHITECTURE.md (on the grounds the file is in fact tracked) but leaned on by analogy for PM_PLANE.md (which isn't even named in that row). Both individual outcomes are independently defensible on file content, but the reasoning style differs slot to slot.

No wrong byte content was found in any checked slot (15/37 manually verified byte-identical, all 37/37 verified via the packet's own validator run live by me). No missing or fabricated open-PR evidence was found (4 PRs independently cross-checked against live `gh` data, all accurate). No secrets found. No allowlist violations. No misleading finality claims. The execution.agent="shell" workaround is genuinely schema-required.

## Overall Verdict

**PASS_WITH_RISKS** — the package is accurate, reproducible, and honestly scoped. The findings above are real but minor (citation precision and evidence-completeness gaps that do not change any classification outcome or byte content), plus expected/disclosed PR-count drift. No finding rises to a wrong byte, a fabricated PR classification, a secret, an allowlist violation, or a false finality claim, so FAIL is not warranted; the two documentation-precision gaps are enough that a bare, unqualified PASS would overstate the rigor of the written evidence trail.
