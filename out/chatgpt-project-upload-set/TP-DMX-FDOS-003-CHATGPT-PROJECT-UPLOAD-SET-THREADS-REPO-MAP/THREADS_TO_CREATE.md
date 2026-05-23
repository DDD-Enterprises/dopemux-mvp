# Threads To Create

## 00 Intake / Supervisor Ledger
Purpose: ingest upload set, GPT-5.5 investigation, repo map/current recon, establish current operating ledger.
Attach: GPT55_INVESTIGATION_INTAKE.md, REPO_MAP_CURRENT_RECON.md, REPO_MAP_DIGEST.md, UPLOAD_FILES_MANIFEST.md, DRIFT_AND_UNKNOWN_REPORT.md.
Prompt: THREAD_PRIMING_PROMPTS/00-intake-supervisor-ledger.md
Use when: starting the project, refreshing repo posture, deciding next macro-packet.
Do not use for: implementation.

## 01 TP Forge
Purpose: produce schema-valid macro Task Packets and implementer prompts.
Attach: upload set as needed, manifest, current Thread 00 ledger.
Prompt: THREAD_PRIMING_PROMPTS/01-tp-forge.md
Use when: turning approved outcomes into packets.
Do not use for: accepting implementation proof.

## 02 Implementation Intake
Purpose: review implementer proof, PRs, changed files, validation, blockers.
Attach: packet, proof ledger, PR diff/body, command outputs.
Prompt: THREAD_PRIMING_PROMPTS/02-implementation-intake.md
Use when: an implementer returns work.
Do not use for: speculative planning.

## 03 Audit / Red Team
Purpose: independent review for high-risk or boundary-sensitive work.
Attach: packet, diff, proof, Thread 00 ledger.
Prompt: THREAD_PRIMING_PROMPTS/03-audit-red-team.md
Use when: risk earns reviewer.
Do not use for: low-risk typo/docs fixes.

## 04 Cockpit / dopeUI
Purpose: protect Cockpit as display/gate/proof surface.
Attach: Cockpit docs/proof/diffs.
Prompt: THREAD_PRIMING_PROMPTS/04-cockpit-dopeui.md
Use when: UI/Cockpit/gate/proof display work appears.
Do not use for: PM/execution ownership changes.

## 05 dopeTask / dope-agent Integration
Purpose: review dopeTask packets/adapters/proof and dope-agent role claims.
Attach: schema, packet, adapter/proof/handoff docs, agent runtime evidence.
Prompt: THREAD_PRIMING_PROMPTS/05-dopetask-dopeagent-integration.md
Use when: execution/agent packaging changes.
Do not use to promote agents into authority without runtime proof.

## 06 Vendor Research / Tool Behavior
Purpose: current official vendor/API/tool behavior research.
Attach: specific tool question and acceptance need.
Prompt: THREAD_PRIMING_PROMPTS/06-research-vendor-tools.md
Use when: tool behavior may be stale.
Do not use for repo truth that can be inspected locally.
