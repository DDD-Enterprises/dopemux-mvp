---
id: upload-sets
title: Upload Sets
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-04'
last_review: '2026-06-04'
next_review: '2026-09-02'
prelude: Upload Sets (reference) for dopemux documentation and developer workflows.
---
# ChatGPT Projects Upload Sets Reference

This document maps out the specific sets of files to upload when creating or updating each ChatGPT Project.

> [!WARNING]
> **Secret Exclusions Invariant**: Never upload files containing raw API keys, secrets, local directories, or `.env` files. Ensure `.git` is ignored.

---

## 1. The Dopemux Top 40 Baseline
This is the standard baseline context pack for understanding `dopemux-mvp`. It is stored at [out/chatgpt-project-upload-set/TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP/UPLOAD_FILES/](file://[LOCAL_PATH_REDACTED]

1. `01_RULES.md`
2. `02_PROJECT.md` (Root `PROJECT.md`)
3. `03_ARCHITECTURE.md` (Root `ARCHITECTURE.md`)
4. `04_SYSTEM_BOUNDARIES.md`
5. `05_PM_PLANE.md` (Root `PM_PLANE.md`)
6. `06_SERVICE_CATALOG.md` (Root `SERVICE_CATALOG.md`)
7. `07_TRUTH_SCOPE.md`
8. `08_TRUTH_SYSTEMS.md`
9. `09_TRUTH_INTERFACES.md`
10. `10_TRUTH_DATA_EVENTS.md`
11. `11_TRUTH_CANONICALS.md`
12. `12_TRUTH_GAPS.md`
13. `13_SYSTEM_DOPEMUX.md`
14. `14_SYSTEM_DOPETASK.md`
15. `15_SYSTEM_TASKORCHESTRATOR.md`
16. `16_SYSTEM_CONPORT.md`
17. `17_SYSTEM_DOPEMEMORY.md`
18. `18_SYSTEM_DOPECONTEXT.md`
19. `19_SYSTEM_DOPECONBRIDGE.md`
20. `20_SYSTEM_ADHDENGINE.md`
21. `21_SYSTEM_REPOTRUTHEXTRACTOR.md`
22. `22_AGENTS.md` (Root `AGENTS.md`)
23. `23_PAL_EXECUTION_RULES.md`
24. `24_PAL_CHAINING_DOCTRINE.md`
25. `25_DOPETASK_CANONICAL_SPEC.json`
26. `26_PROOF_CONTRACT.md`
27. `27_PROOF_BUNDLE_SCHEMA.md`
28. `28_HANDOFF_CONTRACT.md`
29. `29_ADAPTER_CONTRACT.md`
30. `30_ADAPTER_SCHEMA.md`
31. `31_TASK_PACKET_TEMPLATE.md`
32. `32_AUTHORITY_MAP.md`
33. `33_DOC_TRUST_MAP.md`
34. `34_DOCUMENTATION_SOURCE_MAP.md`
35. `35_RUNTIME_AUTHORITY_VERIFICATION.md`
36. `36_CODEX_AUTHORITY_REFRESH.md`
37. `37_CODEX_PROMPT_PACK.md`
38. `38_CODEX_REFRESH_GAP_REGISTER.md`
39. `39_AGENT_WORKFLOW.md`
40. `40_GOVERNANCE_MODEL.md`

---

## 2. Project-Specific Upload Bundles

### DCP Core Supervisor Bundle
- [dcp-core-supervisor.md](file://[LOCAL_PATH_REDACTED]
- `dopetask-canonical-spec.json`
- `docs/03-reference/dcp/README.md`
- `docs/03-reference/dcp/artifacts/DCP_ARCHITECTURE_SYNTHESIS_REVISED_DELTA.md`
- `docs/03-reference/dcp/artifacts/DCP_ADVERSARIAL_ARCHITECTURE_AUDIT.md`

### Dopemux Supervisor Bundle
- [dopemux-supervisor.md](file://[LOCAL_PATH_REDACTED]
- The Top 40 Baseline Files.
- The 6 DCP artifacts in `docs/03-reference/dcp/artifacts/`.
- `docs/03-reference/dcp/README.md`.

### dNh-CRM Supervisor Bundle
- [dnh-crm-supervisor.md](file://[LOCAL_PATH_REDACTED]
- dNh-CRM local authority documents (RULES, PROJECT, ARCHITECTURE if they exist).
- `docs/03-reference/dcp/README.md`.
- `docs/03-reference/dcp/artifacts/DCP_DR_EXTERNAL_CONSTRAINTS_LEDGER.md`.
- `docs/03-reference/dcp/artifacts/DCP_ARCHITECTURE_SYNTHESIS_REVISED_DELTA.md`.

### DCP Packet Lab Bundle
- [dcp-packet-lab.md](file://[LOCAL_PATH_REDACTED]
- `AGENTS.md`
- `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- The specific `TP-XXXX-XXX.json` Task Packet.
