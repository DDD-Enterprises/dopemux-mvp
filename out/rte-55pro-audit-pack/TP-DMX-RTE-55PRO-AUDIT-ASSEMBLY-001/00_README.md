# RTE GPT-5.5 Pro Audit Pack

Packet: `TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001`
Series: `DMX-RTE-55PRO-AUDIT`
Target subsystem: Repo Truth Extractor (RTE)
Created: `2026-05-14T08:23:19Z`

## Purpose

This pack is upload-safe advisory context for a GPT-5.5 Pro multi-pass audit of the Repo Truth Extractor. It organizes source pointers, current proof trail, prior audit material, known drift, upload order, and paste-ready audit prompts.

The pack is intended for a ChatGPT Project where GPT-5.5 Pro will audit RTE end to end across prescan, prompts, operator flow, model routing, escalation, sidefill/enrichment/repair, structured outputs, code architecture, proof artifacts, determinism, safety, and validation posture.

## How To Use

1. Upload the base authority sources listed in `16_UPLOAD_ORDER.md` first.
2. Upload the RTE runtime and proof sources listed next.
3. Upload these generated audit-pack files after source authority.
4. Paste `12_GPT55_PROJECT_INSTRUCTIONS.md` into the project instructions.
5. Start the project thread with `18_CHATGPT_PROJECT_PRIMING_PROMPT.md`.
6. Run `13_GPT55_PASS1_BROAD_AUDIT_PROMPT.md`, then specialist passes from `14_GPT55_SPECIALIST_PASS_PROMPTS.md`.

## Authority Warning

Runtime code, config, compose wiring, tests, and active entrypoints beat extracted, generated, historical, or advisory artifacts. This pack points to source evidence; it is not itself RTE runtime truth.

## Proof Boundary

This pack is not implementation proof for RTE behavior. It is proof that an audit assembly was generated from inspected repo sources under `TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001`. The proof files are in `proof/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/`.
