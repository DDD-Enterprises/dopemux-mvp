# ADR: Data Classification & Residency

Status: Accepted
Date: 2025-09-17

Decision (Proposed)
- Adopt 4-level classification (Public, Internal, Sensitive, Restricted); support optional residency constraints (e.g., EU-only) via provider selection and storage policies.

Context
- Guides redaction and provider routing; some users require geographic controls.

Alternatives
- Single-level policy; per-project custom taxonomy; always-local storage.

Consequences
- Tagging and policy evaluation required across artifacts, memory, and logs; provider selection must honor residency.

Open Questions
- Which levels apply by default, and do we enforce residency by default?

Links
- V4 Security & Privacy; V3 Memory & Retrieval

Sources: user clarifications (Q5: not sure)
