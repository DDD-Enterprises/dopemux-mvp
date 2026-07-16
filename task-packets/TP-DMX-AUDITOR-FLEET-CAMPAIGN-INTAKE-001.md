---
id: TP-DMX-AUDITOR-FLEET-CAMPAIGN-INTAKE-001
title: Tp Dmx Auditor Fleet Campaign Intake 001
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-15'
last_review: '2026-07-15'
next_review: '2026-10-13'
prelude: Tp Dmx Auditor Fleet Campaign Intake 001 (explanation) for dopemux documentation
  and developer workflows.
---
# Task Packet: TP-DMX-AUDITOR-FLEET-CAMPAIGN-INTAKE-001

## 🎯 Objective
Deterministic evidence intake for auditor fleet campaign `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`, organizing scattered capability-probes, Deep Research reports, acceptance review sheets, synthesis plans, and archives into a hash-verified, repo-governed evidence tree.

---

## 🔍 Scope

### IN Scope
- Discover campaign artifacts in allowed home download/tmp staging locations.
- Verify exact cryptographic hashes and file sizes against the `SYNTHESIS-INPUT-MANIFEST.json` list of accepted artifacts.
- Copy verified artifacts to their designated destinations under `audit_inputs/auditor-fleet/DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13/`.
- Record metadata and diagnostics files in `99-intake/`.
- Generate pointer indexes in `docs/06-research/` and `docs/05-audit-reports/`.
- Gather verified zip files in `06-source-bundles/`.
- Verify the staged diff against allowlist and hygiene policies.

### OUT Scope
- No runner reconfiguration, route certification, adapter implementation, or model execution.
- No deletion, movement, normalization, or rewriting of original source campaign files.
- No provider calls, credentials caching, or secret configuration.
- No editing files outside the task packet allowlist.

---

## 🛡️ Invariants
- External campaign evidence is always subordinate to repository runtime truth.
- Absent artifacts remain classified as `MISSING` or `EXCLUDED`; do not synthesize or fake any inputs.
- Post-acceptance synthesis deliverables remain labeled `PRESENT_UNACCEPTED`, never upgraded to `ACCEPTED` without subsequent adjudications.
- The Git index must stay clean of untracked files outside the allowlist.

---

## 📂 Target Destination Layout
```text
audit_inputs/auditor-fleet/DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13/
├── README.md
├── CAMPAIGN-CONTENT-MANIFEST.json
├── CAMPAIGN-CONTENT-MANIFEST.md
├── SHA256SUMS.txt
├── 00-control/
│   ├── campaign/
│   ├── schemas/
│   └── prompts/
├── 01-local-capability-probe/
│   ├── accepted/
│   ├── raw-receipts/
│   ├── tools/
│   ├── fixtures/
│   └── excluded-or-missing/
├── 02-deep-research/
│   ├── track-01-vendor-plan-auth/
│   ├── track-02-runner-security/
│   ├── track-03-tool-containment/
│   ├── track-04-routing-evaluation/
│   ├── track-05-api-fallback/
│   └── source-ledgers/
├── 03-acceptance/
├── 04-synthesis/
│   ├── accepted-input-bundle/
│   ├── deliverables/
│   └── status/
├── 05-independent-audit/
│   ├── inputs/
│   ├── outputs/
│   └── status/
├── 06-source-bundles/
│   ├── campaign-kit/
│   ├── capability-probe-kit/
│   └── audit-input-kit/
└── 99-intake/
    ├── SOURCE-LOCATIONS.json
    ├── DISCOVERY-REPORT.md
    ├── DUPLICATE-CANDIDATES.json
    ├── MISSING-OR-MISMATCHED.json
    ├── EXCLUDED-ARTIFACTS.json
    └── INTAKE-STATUS.json
```

---

## 📜 Allowed Files for Modification
```text
task-packets/TP-DMX-AUDITOR-FLEET-CAMPAIGN-INTAKE-001.json
task-packets/TP-DMX-AUDITOR-FLEET-CAMPAIGN-INTAKE-001.md
task-packets/INDEX.md
audit_inputs/auditor-fleet/DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13/**
docs/06-research/auditor-fleet/2026-07-13-auditor-fleet-plan-auth-campaign.md
docs/05-audit-reports/auditor-fleet/2026-07-13-auditor-fleet-campaign-acceptance.md
proof/TP-DMX-AUDITOR-FLEET-CAMPAIGN-INTAKE-001/**
```

---

## 🛠️ Exact Commands
- Create task packet validation check:
  `python3 -c "import json, jsonschema; schema=json.load(open('docs/03-reference/spec/dopetask/dopetask-canonical-spec.json')); packet=json.load(open('task-packets/TP-DMX-AUDITOR-FLEET-CAMPAIGN-INTAKE-001.json')); jsonschema.validate(packet, schema); print('TP VALID')"`
- Local execution of validation rules:
  `python3 scratch/verify_and_copy_evidence.py`
- Verify copy completion and SHA hashes:
  `git status --short --branch`
  `git diff --check`
  `git diff --stat`

---

## 🔬 Validation Gates
1. Schema verification of `TP-DMX-AUDITOR-FLEET-CAMPAIGN-INTAKE-001.json` returns PASS.
2. Every accepted file maps to a source artifact whose calculated SHA-256 and size matches `SYNTHESIS-INPUT-MANIFEST.json` exactly.
3. Every unaccepted file is classified correctly.
4. Changed paths reside strictly within the allowlist.
5. All generated JSON files are parsable and lint-free.
6. Secret scanning check runs cleanly without exposing value tokens.

---

## 📂 Proof Requirements
Staged in `proof/TP-DMX-AUDITOR-FLEET-CAMPAIGN-INTAKE-001/`:
- `PROOF.json` (Proves collection, destinations, and hashes)
- `PROOF_MANIFEST.json` (List of proof files and hashes)
- `COMMAND_LOG.md` (Logs executed commands during runtime)
- `BASELINE.json` (Initial state records)
- `SOURCE_DISCOVERY.json` (Discovered candidate files)
- `PATH_ALLOWLIST_CHECK.json` (Confirms allowlisted boundaries)
- `HASH_VALIDATION.json` (Hash validation records)
- `ZIP_VALIDATION.json` (ZIP archive checksum/CRC status)
- `DOCS_HYGIENE.json` (Docs placement policy status)
- `SECRET_SCAN.json` (Secret scanning confirmation logs)
- `GIT_STATUS_BEFORE.txt` (Initial git status)
- `GIT_STATUS_AFTER.txt` (Staged git status)
- `GIT_DIFF_STAT.txt` (Diff statistics)
- `GIT_DIFF.patch` (Staged patch)
- `INTAKE_SUMMARY.md` (Human-readable intake verdict and gaps)

---

## 🚨 Stop Conditions
Stop immediately and return diagnostics when:
- Repository workspace is wrong or dirty prior to branch setup.
- `SYNTHESIS-INPUT-MANIFEST.json` is missing or fails to parse.
- Campaign ID differs from `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`.
- Acceptance review verdict is not `ACCEPT_WITH_CARRIED_UNKNOWNS`.
- Hash or size mismatch occurs on a manifest-declared accepted artifact.
- Symlinks are encountered during source discovery.
- Secrets pattern scan flags a potential token in the staged changes.
- Post-acceptance files are mislabeled as `ACCEPTED`.

---

## 🔄 Rollback
Rollback must remove only files added by this packet and restore `task-packets/INDEX.md` to its original state.
`git checkout HEAD -- task-packets/INDEX.md`
`rm -rf audit_inputs/auditor-fleet/DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13/`
`rm -rf proof/TP-DMX-AUDITOR-FLEET-CAMPAIGN-INTAKE-001/`
`rm -f task-packets/TP-DMX-AUDITOR-FLEET-CAMPAIGN-INTAKE-001.json task-packets/TP-DMX-AUDITOR-FLEET-CAMPAIGN-INTAKE-001.md`

---

## 📤 Expected Output
Clean workspace containing:
- Canonical folder structure populated under `audit_inputs/auditor-fleet/DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13/`.
- Verified pointer summaries inside `docs/05-audit-reports/` and `docs/06-research/`.
- Full proof logs and validation markers staged inside `proof/TP-DMX-AUDITOR-FLEET-CAMPAIGN-INTAKE-001/`.
- `INTAKE_STATUS` set to either `INTAKE_VERIFIED` or `INTAKE_WITH_GAPS` based on exact outcomes.
