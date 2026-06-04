# DCP Packet Lab

## Purpose
The **DCP Packet Lab** is a temporary, ultra-lean ChatGPT Project designed to focus exclusively on executing and verifying a single Task Packet and its corresponding proof.

## Lean Posture
- **No Archaeology**: Avoid uploading historical logs, large design synthesis bundles, or unrelated reference material.
- **Keep Context Small**: This project is created for speed, focus, and to avoid token bloat/context pollution.

## Minimal Upload Set
At any time, the Packet Lab should contain at most:
1. `AGENTS.md` (for governance rules).
2. `dopetask-canonical-spec.json` (schema).
3. The specific active `TP-XXXX-XXX.json` Task Packet.
4. The draft/compiled `PROOF.json` file.
5. The specific target files under development.

## Handoff
Once the target task packet is validated, committed, and its PR is created, the Packet Lab project context should be deleted or wiped clean for the next packet.

## Project Custom Instructions
```text
You are the DCP Packet Lab.
Your scope is strictly limited to the active Task Packet.
Verify the packet against the schema, ensure its code changes are within the allowlist, and check that the resulting PROOF.json matches all validation checks.
Do not reference or invent scope outside the active packet.
```
