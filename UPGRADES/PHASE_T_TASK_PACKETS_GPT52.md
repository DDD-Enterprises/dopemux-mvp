# Phase T (GPT-5.2): Task Packet factory

## Purpose
Turn R and X norm artifacts into deterministic, implementation-ready Task Packets for Codex execution.

## Canonical prompt sequence
- `PROMPT_T0_TASK_PACKET_FACTORY.md`
- `PROMPT_T1_EMIT_TASK_PACKETS___TOP10.md`
- `PROMPT_T2_PACKET_SCHEMA___AUTHORITY_RULES.md`
- `PROMPT_T3_PACKET_GENERATION___BATCHED.md`
- `PROMPT_T4_PACKET_DEDUP___COLLISION_RESOLUTION.md`
- `PROMPT_T5_PACKET_ORDERING___RUN_PLAN.md`
- `PROMPT_T9_MERGE___QA.md`

## Canonical outputs
- `TP_INDEX.json`
- `TP_MERGED.json`
- `TP_QA.json`
- `TP_SUMMARY.md`
- `TP_BACKLOG_TOPN.json`
