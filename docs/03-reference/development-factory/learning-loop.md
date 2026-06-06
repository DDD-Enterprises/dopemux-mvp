# Learning Loop

How the factory learns from capsule executions and improves its own policies — with explicit safeguards against silent self-modification.

---

## Loop Flow

```
capsule execution completes
  → metrics extracted:
      - success/failure verdict
      - actual vs estimated time
      - which stop conditions fired
      - which models were used per stage
      - proof completeness score
      - scope escape incidents
  → lesson candidate generated:
      - what went wrong / right
      - which model routing stage was wrong
      - which obligation class was underestimated
      - proposed template or routing policy change
  → reviewed by human or GPT-5.5 Pro:
      - accept / reject / modify
  → if accepted:
      - update docs/03-reference/development-factory/ (this packet's domain)
      - update model routing policy (via TP-DMX-MODEL-ROUTING-POLICY-001)
      - update EXECUTION_CAPSULE_TEMPLATE.md (via TP-DMX-EXECUTION-CAPSULE-SCHEMA-001)
```

---

## No Silent Self-Modification

**No silent self-modifying brain-worms.**

The factory never updates its own policies without a human or GPT-5.5 review step. All policy changes — including changes to this file, to `model-routing.md`, to `execution-capsule.md`, or to any template — require a proof bundle treated the same as any other capsule execution.

Learning loop output is a lesson **CANDIDATE**, not an automatic update. A candidate that is not explicitly accepted by a recognized reviewer is discarded. There is no auto-accept path.

| Step | Who acts | What happens |
|---|---|---|
| Metrics extraction | Capsule post-processor | Reads PROOF.json + CI results; produces candidate JSON |
| Lesson candidate review | GPT-5.5 Pro or human | Accept / reject / modify with rationale |
| Policy update | Capsule (with its own proof) | Writes to `docs/03-reference/development-factory/` or template files |
| Proof bundle for update | Same as any capsule | `PROOF.json` + `SUMMARY.md` required; supervisor sign-off required |

### What "accepted" means

A lesson candidate is **accepted** when a recognized reviewer (GPT-5.5 Pro or human operator) explicitly emits:

```
LESSON_ACCEPTED: <lesson-id>
rationale: <why>
```

Silence is not acceptance. Inferred acceptance from a downstream action is not acceptance.

### What changes are in scope

The learning loop may propose changes to:

- Any file under `docs/03-reference/development-factory/`
- `model-routing.md` routing tiers and model assignments
- `EXECUTION_CAPSULE_TEMPLATE.md` field schema or defaults
- Obligation class definitions in `obligation-ledger.md`

The learning loop may NOT propose changes to:

- `AGENTS.md` (repo governance — human-only change)
- `schemas/dcp/` (contract-sensitive — requires ADR)
- `.claude/settings.json` or hook scripts (operator-only via `update-config` skill)
- Any active red line definition in `red-lines-and-stop-conditions.md` without a matching ADR
