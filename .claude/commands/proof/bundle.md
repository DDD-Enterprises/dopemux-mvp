---
description: "Scaffold, validate, or force-track a proof bundle (AGENTS.md §9 + TP-DMX-PROOF-TRACKING-POLICY-001)"
arguments: "<scaffold|validate|track> <TP-ID> [--strict]"
allowed-tools: ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]
model: "claude-sonnet-4-5"
---

# /proof:bundle — Proof Bundle Lifecycle

One command for the proof-bundle lifecycle: **scaffold → validate → track**. Wraps
`scripts/proof_bundle.sh`, `scripts/audit/validate_audit_proof.py`, and the
TP-DMX-PROOF-TRACKING-POLICY-001 force-add policy.

Closes the gap where AGENTS.md §9 requires ~13 proof fields but nothing checks them
until CI — or never, when the proof files are silently gitignored.

---

## Phase 1 — Argument Parsing

Parse `$ARGUMENTS`:

- First positional → mode: `scaffold` | `validate` | `track` (required)
- Second positional → TP-ID (required; e.g. `TP-DCP-MCP-RO-0007`)
- If TP-ID is omitted: `ls -dt proof/*/` and offer the most recently modified (max 3) as
  candidates — stop and ask the user to confirm before proceeding
- `--strict` → treat WARN as FAIL (recommended for pre-PR runs)

Unrecognized mode → print usage and stop.

---

## Phase 2 — mode: scaffold

Create a new proof bundle skeleton for the TP-ID.

**2a — Refuse if already exists.** Check `proof/<TP-ID>/PROOF.json`. If present, stop:
```
Bundle exists — use /proof:bundle validate <TP-ID> to check it.
```
Never overwrite an existing PROOF.json; proof is append-only evidence.

**2b — Resolve packet path.**
```bash
find task-packets -name "<TP-ID>.md" -o -name "<TP-ID>.json" 2>/dev/null | head -1
```
Use the first match as `tp_path`; set `"UNKNOWN"` if none found.

**2c — Collect git facts.**
```bash
git rev-parse --abbrev-ref HEAD           # branch
git rev-parse HEAD                        # head_sha
git rev-parse --show-toplevel             # worktree_path
git remote get-url origin 2>/dev/null     # repo_identity
git status --porcelain                    # dirty files list
git diff --stat $(git merge-base origin/main HEAD)..HEAD  # files_changed
```

**2d — Read AGENTS.md §9 and schemas/proof/embedded_audit.schema.json.** Use the Read
tool to get exact required fields and the embedded_audit shape before writing — do not
guess field names or enum values. The embedded_audit schema rejects `none`/`unknown`
auditor combos; use a compliant placeholder shape (e.g. `"auditor": "manual",
"status": "NOT_RUN"`).

**2e — Write `proof/<TP-ID>/PROOF.json`** (create the directory first):
Pre-fill with collected git facts plus empty-but-present keys for every AGENTS.md §9
field:
- `tp_id`, `tp_path`, `branch`, `head_sha`, `worktree_path`, `repo_identity`
- `files_changed` (from diff-stat)
- `slices` (array, empty)
- `validations` (array of `{command, exit_code, bucket}` — bucket ∈ PASS/FAIL/NOT_RUN)
- `codereview_status`, `precommit_status`, `commit_sha`, `pr_url_or_blocker`
- `residual_risks`, `unknowns`, `cleanup_status`
- `embedded_audit` (compliant placeholder per schema)

**2f — Write stubs.**
- `proof/<TP-ID>/SUMMARY.md` — heading skeleton only, body: `NOT_RUN`
- `proof/<TP-ID>/AUDIT.md` — heading skeleton only, body: `NOT_RUN`

**2g — Remind the operator** about `scripts/proof_bundle.sh`:
```
# Use proof_bundle.sh to capture command transcripts into the bundle:
scripts/proof_bundle.sh --tp <TP-ID> --cmd "<your validation command>"
```
Do not duplicate its logic.

**2h — Print the exact force-track command.** These files are gitignored by `proof/*`:
```bash
# TRACK-tier files must be force-added before the packet completes:
git add -f proof/<TP-ID>/PROOF.json proof/<TP-ID>/SUMMARY.md proof/<TP-ID>/AUDIT.md
```

---

## Phase 3 — mode: validate

Check an existing bundle for completeness, CI parity, and git-tracking status.

**3a — Schema layer** (CI parity — same gate as `ci-complete.yml:475`):
```bash
python scripts/audit/validate_audit_proof.py --all proof/<TP-ID>/
```
Capture stdout + exit code verbatim. Script missing → NOT_RUN, explain.

**3b — §9 completeness layer** (the gap CI alone doesn't fully cover):
Read `proof/<TP-ID>/PROOF.json`. For each AGENTS.md §9 required field:
- ✅ PASS — present and non-empty/non-placeholder
- ⚠️ WARN — present but empty string / empty array / placeholder value
- ❌ FAIL — key absent entirely

For `validations[]` entries: each must have integer `exit_code` and `bucket` ∈
PASS/FAIL/NOT_RUN. Flag any NOT_RUN entry that is missing a `reason` field.

**3c — Staleness layer:**
Compare `head_sha` in PROOF.json to `git rev-parse HEAD`. Mismatch → ⚠️ WARN
"head_sha is stale — re-run validations and update commit_sha". With `--strict` → ❌ FAIL.

**3d — Tracking layer** (per TP-DMX-PROOF-TRACKING-POLICY-001):
For each TRACK-tier filename present in `proof/<TP-ID>/`
(`PROOF.json`, `SUMMARY.md`, `AUDIT.md`, `MERGE_READINESS.json`, `VALIDATION.md`,
`CMD_SUMMARY.md`, `MODEL_ROUTING.json`, `MANIFEST.json`):
```bash
git ls-files --error-unmatch proof/<TP-ID>/<file>
```
Exit non-zero = untracked → ❌ FAIL with exact remediation:
```bash
git add -f proof/<TP-ID>/<file>
```
This is a **red-line stop condition** per
`docs/03-reference/development-factory/red-lines-and-stop-conditions.md`.

**3e — Output:** Single table — Layer / Check / PASS|FAIL|WARN|NOT_RUN / Remediation.

End with a footer formatted for direct paste into the bundle's own `VALIDATION.md`:
```
## Validation: /proof:bundle validate <TP-ID>
- schema:          <PASS/FAIL/NOT_RUN>  (validate_audit_proof.py exit <n>)
- §9 completeness: <PASS/FAIL/WARN>     (<n> missing or empty fields)
- staleness:       <PASS/WARN>          (head_sha match/mismatch)
- git-tracking:    <PASS/FAIL>          (<n> untracked TRACK-tier files)
```

---

## Phase 4 — mode: track

Stage TRACK-tier proof files for commit.

**4a — List and partition** `proof/<TP-ID>/`:
- **TRACK-tier**: `PROOF.json`, `SUMMARY.md`, `AUDIT.md`, `MERGE_READINESS.json`,
  `VALIDATION.md`, `CMD_SUMMARY.md`, `MODEL_ROUTING.json`, `MANIFEST.json`
- **DO_NOT_TRACK**: files >1MB, raw stdout/log/transcript files, any `.env`-like content,
  anything matching `*_stdout*`, `*_transcript*`, `*_raw_*`

**4b — Secret pre-scan** (mandatory, before any `git add -f`):
```bash
grep -rn "sk-\|AKIA\|BEGIN.*PRIVATE KEY\|Bearer [A-Za-z0-9._-]\{20,\}" \
  proof/<TP-ID>/<each-track-candidate>
```
Any match → **STOP immediately**. Report: "Potential credential pattern in `<path>` —
do not stage. Review and redact before tracking." Do NOT print the matched value or
the surrounding line content.

**4c — Stage clean TRACK-tier files:**
```bash
git add -f <track-tier-paths>
```
Print exactly what was staged and what was deliberately skipped (with reason).
**Never commits** — staging only; the operator/agent commits per normal workflow.

---

## Error Handling

- `proof/<TP-ID>/` does not exist (validate/track) → FAIL:
  "Run scaffold first: `/proof:bundle scaffold <TP-ID>`"
- `scripts/audit/validate_audit_proof.py` not found → NOT_RUN:
  "Script missing — ensure you are running from the repo root"
- `git` unavailable → NOT_RUN for git-dependent checks; proceed with non-git checks
- PROOF.json is unparseable JSON → FAIL in §9 layer with parse error message

---

## Notes for Claude

- validate and track modes are **read-only on bundle content** — never modify PROOF.json.
- `scripts/proof_bundle.sh` captures command transcripts; do not duplicate its logic.
- TRACK-tier files are gitignored by `proof/*` by design (safety net against raw output).
  The force-add is the deliberate exception per policy.
- Haiku is intentionally NOT used here — proof-bundle scaffolding requires judgment about
  AGENTS.md §9 field completeness. Sonnet is the correct tier.
- Model: `claude-sonnet-4-5` per routing policy.
