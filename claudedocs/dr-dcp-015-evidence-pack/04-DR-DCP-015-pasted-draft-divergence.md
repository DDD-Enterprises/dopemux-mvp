# DR-DCP-015 — Pasted Draft (SUPERSEDED) — Divergence Record

The operator pasted two near-identical copies of a DR-DCP-015 draft. Both differ from the canonical ingested version ([`03-DR-DCP-015-canonical.md`](03-DR-DCP-015-canonical.md)) **only in §1 (Executive Recommendation) and its sequencing rationale** — the remaining sections (§2 surface matrix … §16 sources) track the canonical content. The divergence is reproduced here verbatim so the reconciliation is self-contained.

> **Status: SUPERSEDED.** Do not act on this headline. Canonical = `BUILD_AFTER_CORE_CONTRACTS` (file 03). See [`01-reconciliation-memo.md`](01-reconciliation-memo.md) §1 for why the canonical sequencing is correct, and [`02-core-contract-status-audit.md`](02-core-contract-status-audit.md) for proof the contract gate is currently CLOSED.

## Pasted §1 — Copy A (verbatim)

> **BUILD_TOOLING_LAYER_NOW**
> The Claude Code ecosystem already defines a clear extension architecture (plugins, hooks, skills) with published docs and use patterns. Building a core tooling layer now lets DCP standardize patterns early and validate them through real usage. Delaying waits for more API evolution but risks stove-piped tooling growth and inconsistent guardrails.
> **Rationale**
> - Extension hooks and plugins are first-class extensibility mechanisms.
> - Skills provide reusable domain logic that aligns with DCP's needs.
> - Waiting for "perfect docs" is unnecessary; standards exist and are evolving.

## Pasted §1 — Copy B (verbatim)

> **BUILD_TOOLING_LAYER_NOW**
> There's enough authoritative extensibility surface in the Claude Code ecosystem (published docs on plugins, hooks, and agent skills) and standard tooling patterns from Git and pre-commit to justify starting a core DCP tooling layer. Waiting for more internal docs only defers solving the real coordination problems DCP faces now and risks divergent ad-hoc tooling growth. We should start with a conservative, auditable baseline and iterate with repo evidence.

## Why it was overridden

1. **Sequencing inversion.** The pasted draft argues "ship now to avoid stovepiping." But the contracts (red-lane taxonomy, receipt schema, mutation classes, approval artifact, path/resource maps) *are* the anti-stovepipe mechanism. Deterministic enforcement of a contract that doesn't exist yet is impossible — you'd get probabilistic/LLM guards posing as hard gates ("vibe plane, not a red-lane gate").
2. **Empirically gated.** Per file 02, all 5 contracts are `.v0`/PROVISIONAL — the prerequisite is objectively unmet.
3. **Repo assumptions wrong.** The pasted draft's §4 (plugin package) and §7 (`dopemux dcp` CLI) assume infrastructure this repo doesn't have (no plugin manifest; no `dcp` CLI). See file 01 §2 + file 06.

Where the two drafts **agree** (and the canonical keeps): the deterministic-vs-LLM split, the receipt requirements, and the Never-build list. The disagreement is purely about **when**.
