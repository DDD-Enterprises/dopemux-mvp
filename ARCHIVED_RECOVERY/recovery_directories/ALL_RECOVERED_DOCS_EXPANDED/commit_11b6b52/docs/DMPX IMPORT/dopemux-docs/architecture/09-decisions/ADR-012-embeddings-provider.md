# ADR: Default Embeddings/Index Provider (External)

Status: Accepted
Date: 2025-09-17

Decision
- Use an external embedding/index provider by default (bring-your-own credentials), with a pluggable interface to allow local-only implementations.

Context
- External providers offer strong performance and reduce local resource demands; some users require local-only for privacy.

Consequences
- Provide config for provider selection and credentials; ensure redaction/privacy controls on data sent to providers.

Links
- V3 Memory & Retrieval; V1 Architecture (Crosscutting Concepts)

Sources: user clarifications (Q3)
