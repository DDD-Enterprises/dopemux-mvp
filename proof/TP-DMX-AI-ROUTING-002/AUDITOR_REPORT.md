# Auditor Report — TP-DMX-AI-ROUTING-002

**TP**: TP-DMX-AI-ROUTING-002
**Subject**: Resolve AI routing proof governance residue (proof-bundle-schema.md, proof-contract.md)
**Auditor**: Claude Code CLI (claude-sonnet-4.6) — self-audit after cleanup
**Invocation**: self-audit inside Claude Code after cleanup
**Exit code**: 0
**Status**: PASS
**Date**: 2026-06-06

---

## Verdict

**PASS.** Both prior-session out-of-allowlist modifications classified as KEEP and committed.
No blocking findings. One advisory risk noted.

---

## Scope Reviewed

- `docs/03-reference/governance/proof-bundle-schema.md` — +12 lines (## Related Policy section)
- `docs/03-reference/governance/proof-contract.md` — +15 lines (## Model Routing Evidence section)
- `proof/TP-DMX-AI-ROUTING-002/PROOF.json`

---

## Residue Classification

### proof-bundle-schema.md — KEEP

Adds a `## Related Policy` section (12 lines) with cross-references to the three files
created by TP-001: `config/ai/model-routing.policy.yaml`, `model-routing.md`,
`schemas/proof/embedded_audit.schema.json`. All referenced files exist at correct relative
paths. Section explicitly states model-routing fields are advisory and additive and do not
alter bundle validation rules. No new required fields created. No runtime authority claimed.

### proof-contract.md — KEEP

Adds a `## Model Routing Evidence` section (15 lines). Uses advisory 'should' language
throughout. All referenced files exist. Explicit statement that model-routing fields 'are
advisory and additive; they do not change the required-field set defined above'. References
canonical `embedded_audit.schema.json` correctly. Does not duplicate proof-bundle-schema.md
— complementary angle.

---

## Findings

No findings.

---

## Remaining Risks

- R1: Advisory model-routing fields in proof-contract.md use 'should' language that an
  operator could misread as normative. The section's explicit "additive and do not change
  the required-field set" statement guards against overclaiming.
