# MACRO-DMX-RUNNER-MEMORY-2A-001 — Authorization Record

**Operator words (verbatim, chat, 2026-10-31):** "Approve and authorize"

**In answer to (verbatim, the supervisor's question):** "Approve the Wave 2A design and authorize the macro so W00 can start?"

**Recorded at:** 2026-10-31T20:13:58Z by the Control Tower supervisor session that issued the macro, now acting as team lead.

## What this authorizes

This answer is the operator's execution gate for this macro, equivalent to `AUTHORIZE_MACRO_DMX_RUNNER_MEMORY_2A_001_EXECUTION=YES` as defined in `ISSUANCE.md`:

- **Design approved:** `docs/91-rfc/rfc-2026-10-30-runner-memory-parity-2a.md` at sha256 `1fea60130d55d151dfbc70eb24571efb90c8ecee9e9183a05f3beb0915970cd3`. The design file stays byte-identical until J04-FREEZE (every child pins it); its `status:` frontmatter is **not** edited to record this approval. This file is the record.
- **Execution authorized:** W00-W08 inside `MACRO_PACKET.json` (sha256 `04d1615942d47a9f9890f9a34313b7caf3ba0337660ea1f709b8b049afcaeb08`), within its PROPOSED allowances, which this authorization accepts.

## What it does not authorize

- **The 4.0.0 image pull by W00** was offered as an optional addition and was **not** included; W00 stays bound by its R02 (no download).
- Every gate listed under "Not granted here" in `ISSUANCE.md` stays a separate operator step: push or PR, signing, the final audit route, token issuance, real-database migrations, the log-to-enforce switch, the orchestrator cutover, ADR amendment acceptance, the live Codex acceptance run, merge.
- A revision (R2) that W00's design changes would require needs its own authorization.

## State at authorization

| Check | Value |
|---|---|
| Branch / head | `feat/runner-memory-2a` / `1f185a03c` |
| origin/main | `97b6d5040` (unchanged; base is an ancestor of HEAD) |
| Design sha256 | matches the pin |
| Docker engine, this repo's ConPort and dope-memory | up, healthy |
| Free disk | 20 GiB (96% used; down from 38 GiB on 2026-10-30, cause unknown) |
