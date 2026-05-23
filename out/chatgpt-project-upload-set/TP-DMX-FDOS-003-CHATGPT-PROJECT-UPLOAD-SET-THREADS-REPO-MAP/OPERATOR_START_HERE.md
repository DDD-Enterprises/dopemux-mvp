# Operator Start Here

## Fast Setup

1. Upload all files from:
   `UPLOAD_FILES/`

2. In Thread 00 Intake / Supervisor Ledger, attach:
   - `GPT55_INVESTIGATION_INTAKE.md`
   - `REPO_MAP_CURRENT_RECON.md`
   - `REPO_MAP_DIGEST.md`
   - `UPLOAD_FILES_MANIFEST.md`
   - `DRIFT_AND_UNKNOWN_REPORT.md`

3. Paste Project Instructions:
   `PROJECT_INSTRUCTIONS_UNDER_8000.txt`

4. Create these threads:
   - `00 Intake / Supervisor Ledger`
   - `01 TP Forge`
   - `02 Implementation Intake`
   - `03 Audit / Red Team`
   - `04 Cockpit / dopeUI`
   - `05 dopeTask / dope-agent Integration`
   - `06 Vendor Research / Tool Behavior`

5. Paste the matching priming prompt from:
   `THREAD_PRIMING_PROMPTS/`

6. Start Thread 00 by pasting:
   `INTAKE_START_PROMPT.md`

## What Thread 00 Should Do First

Thread 00 should:
- ingest the GPT-5.5 investigation
- ingest the repo map/current recon
- re-check live GitHub state
- build the current operating ledger
- recommend whether the first action is rebase/evidence-refresh, packet forge, audit, or implementation intake

## Warning

If the GPT-5.5 investigation or repo map exists only on local Downloads, cloud Codex cannot see it. This package copies those files into the upload bundle when available.

Do not start implementation from stale recon.
Do not merge stale PRs just because checks passed.
Do not skip Task Packets for non-trivial work.
