---
id: ROLE_VISIBILITY_RULES
title: Role Visibility Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Role Visibility Rules (explanation) for dopemux documentation and developer
  workflows.
---
# Role Visibility Rules

## Information Containment
To ensure the integrity of the adversarial process, information visibility is strictly sequenced.

| Role | Sees Evidence Bundle | Sees Analyzer Report | Sees Challenge Report |
| :--- | :---: | :---: | :---: |
| **Analyzer** | ✅ | ❌ | ❌ |
| **Challenger** | ✅ | ✅ | ❌ |
| **Arbiter** | ✅ | ✅ | ✅ |

## Rules
1. **No Shared Context**: Roles must not see previous outputs except as defined in the matrix above.
2. **Authoritative Evidence**: The `ARBITRATION_EVIDENCE_BUNDLE.json` is the only source of ground truth for all roles.
3. **Sequence Enforcement**: Challenger must not start until Analyzer completes. Arbiter must not start until Challenger completes.
