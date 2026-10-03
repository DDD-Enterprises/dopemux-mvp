# Independent L2 audit — PR #1402, dopemux-mvp

You are the **sole final independent auditor** for this pull request. You are not the implementer
(the implementer was Claude Code). Your verdict is binding evidence. You have **one** call. Be
adversarial: check every claim against primary files; do not accept a commit message's word.

## 0. Custody — do this first

Run `git rev-parse HEAD` in the mounted worktree. It **must** print exactly:

```
2b453caad13f19758923fee026cf69b52b7f0064
```

Otherwise stop and return `NEEDS_SUPERVISOR` with sole finding `CUSTODY_MISMATCH`. Base (merge-base
with `main`): `07b21e82a368c29adb96baf09573e03de74d4483`. Use `git diff 07b21e82a368c29adb96baf09573e03de74d4483..2b453caad13f19758923fee026cf69b52b7f0064` and `git show 07b21e82a368c29adb96baf09573e03de74d4483:<path>`.

**Filenames contain spaces** (`… (1).md`, `… DMPX IMPORT …`): use NUL-delimited listings
(`git diff -z --name-status`, `git ls-files -z`) or quote paths. **Do not create or modify any file in
the mounted worktree**; run checks inline or under `/tmp`. If you cannot run tools, set
`TOOL_ACCESS=NONE` and do not claim verification you did not perform.

## 1. What this PR is

Follow-ups to #1389 (merged as 07b21e82a). Three commits:

```
2b453caad chore(proof): exempt auditor_scratch evidence from git whitespace checks
30948e071 docs(mcp): label doctor as sidecar diagnostics; state there is no full-stack health gate
7215b5acd docs(history): remove 670 byte-identical '(1).md' duplicate copies
```

## 2. Challenge each point — UPHELD / DISPUTED / UNVERIFIABLE, with evidence

1. **Deletions are lossless.** Exactly 670 files are deleted, all under `docs/04-explanation/history/sourceFiles/`, all named `<name> (1).md`. For **every** one, verify the base-named twin `<name>.md` exists at HEAD and is byte-identical (sha256) to the deleted file's content at the base. Report the count verified and list any exception.
2. **Retained sole copies.** Exactly 9 `(1).md` files remain in that directory at HEAD. Verify each has **no** base-named twin at HEAD, so deleting it would have lost content. #1389 deleted some base-named files relying on these as kept copies; confirm none of those were removed here.
3. **No dangling references.** `git grep` at HEAD for each deleted path or basename, excluding dated records (`proof/`, `audit_inputs/`, `reports/`, `extraction/`, `claudedocs/`).
4. **Health-tool scope claims are true.** In `docker/.claude/claude.md`, `scripts/.claude/claude.md` and `.github/copilot-instructions.md`, verify against code:
   - `dopemux mcp doctor` scopes to the `.mcp.json` servers (conport, dope-memory, task-orchestrator): see `src/dopemux/mcp/doctor.py` desired-services logic and `.mcp.json`;
   - `tools/smoke_runtime_gate.py` (run by `scripts/smoke_up.sh`) checks container stability, ports and HTTP health only for `enabled_in_smoke` services in `services/registry.yaml` (count them, and the total);
   - `dopemux health` (`src/dopemux/health.py` `_check_docker_services`) only inspects containers whose name or image contains "mcp";
   - the claim "no single full-stack health gate exists" — is there any command in `src/`, `scripts/` or `tools/` that actually health-checks every compose/registry service? If so, DISPUTE.

   Also confirm `start-all`'s `--verify` is only forwarded when `scripts/start-all.sh` exists, and that the script is absent at HEAD.
5. **`proof/.gitattributes` is narrowly scoped.** It must only unset `whitespace` for `**/auditor_scratch/**` under `proof/`. Verify with `git check-attr whitespace` that auditor scratch files are `unset` while e.g. `proof/**/PROOF.json` and files outside `proof/` are `unspecified`. Verify `git diff --check 07b21e82a368c29adb96baf09573e03de74d4483 2b453caad13f19758923fee026cf69b52b7f0064` exits 0, and that `config/repo_hygiene/root_hygiene_policy.json` and `.pre-commit-config.yaml` are unchanged.
6. **Scope and doctrine.** No changes to AGENTS.md, governance doctrine, schemas, code or tests; no secrets, absolute machine paths or machine-specific ids. Every changed path fits the three stated purposes.

## 3. Output format (return exactly this structure)

```
TOOL_ACCESS=<FULL|PARTIAL|NONE>
CUSTODY=<MATCH|MISMATCH>  head=<sha you observed>
VERDICT=<PASS|PASS_WITH_RISKS|FAIL|NEEDS_SUPERVISOR>
POINTS:
  1: <UPHELD|DISPUTED|UNVERIFIABLE> — <evidence>
  ... (1-6)
FINDINGS:
  - id: F-01
    severity: <CRITICAL|HIGH|MEDIUM|LOW|INFO>
    blocking: <true|false>
    title: ...
    body: ... (file:line evidence)
REMAINING_RISKS:
  - ...
```

FAIL if any deletion is lossy, a sole copy was removed, a scope claim is false, or the
attributes change affects anything beyond auditor_scratch. PASS_WITH_RISKS for non-blocking defects.


> NOTE: This run is an ADVISORY second review (Codex). It is not the formal embedded audit. Same checks, same output format.
