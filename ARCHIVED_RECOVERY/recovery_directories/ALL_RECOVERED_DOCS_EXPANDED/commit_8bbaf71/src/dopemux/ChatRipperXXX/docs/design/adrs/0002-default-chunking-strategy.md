ADR-0002: Default Chunking Strategy

Status: Accepted | Owner: You | Last Updated: 2025-09-02 PT

## Context

Transforming message streams into LLM-ready windows requires a consistent default that balances retrieval quality, determinism, and performance across dense vs. sparse conversations. Prior docs contained conflicting defaults (turns:20 vs. turns:40).

## Decision

Adopt `turns:40, stride:10` as the default chunking for dense chats, with automatic fallback to daily windows for sparse periods.

- Deterministic re-chunking with identical inputs/seeds.
- Stride 10 enables overlap for continuity without excessive duplication.
- Daily fallback avoids over-fragmenting sparse timelines.

## Consequences

- Update CLI docs and examples to reflect `turns:40` default.
- Align NFRs, Interfaces, and Developer Guide. Tests that asserted `turns:20` expectations should be adjusted.

## Alternatives Considered

- `turns:20`: Higher precision on local context but more windows, higher index size, and slightly worse recall in practice.
- Time-only chunking: Simpler but loses turn-based discourse boundaries in dense chats.

## References

- Acceptance Criteria – Transform determinism
- Interfaces.md – CLI contracts  
- Non-Functional Requirements – Defaults

