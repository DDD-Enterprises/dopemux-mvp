# Validation Baseline

Safe validation only. No live extraction, provider calls, API-key probes, broad RTE run, or external LLM commands were run.

| Command | Result | Notes |
| --- | --- | --- |
| `python -m json.tool task-packets/generated/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001.json >/dev/null` | PASS | Task packet JSON parsed. |
| `python -m json.tool out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/15_UPLOAD_MANIFEST.json >/dev/null` | PASS | Upload manifest JSON parsed. |
| `python -m json.tool proof/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/PROOF.json >/dev/null` | PASS | Proof JSON parsed. |
| `python -c '... Draft7Validator ... task-packets/generated/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001.json ...'` | PASS | Task packet validates against `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`. |
| `test -f out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/00_README.md` | PASS | Required artifact exists. |
| `test -f out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/13_GPT55_PASS1_BROAD_AUDIT_PROMPT.md` | PASS | Required artifact exists. |
| `test -f out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/18_CHATGPT_PROJECT_PRIMING_PROMPT.md` | PASS | Required artifact exists. |
| `test -f out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/RTE_55PRO_AUDIT_PACK_SHA256SUMS.txt` | PASS | Checksum file exists. |
| generated path existence script (`all-generated-paths-present 25`) | PASS | All expected task, pack, and proof paths exist, including ignored proof files. |
| `shasum -a 256 $(find out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001 proof/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001 -type f \| sort) task-packets/generated/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001.json` | PASS | SHA-256 command ran. The checksum file itself is intentionally not self-listed inside its own contents. |
| `git diff --check` | PASS | No whitespace errors reported. |
| `git diff --name-only` | PASS | Diff path listing available for allowlist review. |
| custom allowlist path check over `git status --short --untracked-files=all` plus the expected proof path | PASS | No forbidden paths changed. |
| `git status --short` | PASS | Dirty state is limited to allowlisted paths. |

## Existing Tests Identified But Not Run

NOT_RUN: broad RTE pytest suites under `services/repo-truth-extractor/tests/`. This assembly changed no RTE runtime/test code. Running broad tests would be higher cost and not directly falsify this artifact-only change.

NOT_RUN: live extraction phases, provider preflight probes, batch jobs, and external LLM calls. These are explicitly forbidden for this task.

NOT_RUN: `python -m compileall` on RTE runtime. No Python source was created or modified.
