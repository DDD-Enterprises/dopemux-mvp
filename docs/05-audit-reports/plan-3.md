---
id: PLAN
title: Plan
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-02'
last_review: '2026-03-02'
next_review: '2026-05-31'
prelude: Plan (reference) for dopemux documentation and developer workflows.
---
# TP1 + TP2 Execution Plan

## Goal
Complete deterministic rate-limit governor enforcement (concurrency + RPM + TPM) and runtime extractor wiring backed by routing.yaml.

## Deliverables
- Deterministic TokenBucket behavior with injectable clocks/sleep.
- Governor enforces RPM and TPM budgets.
- Extractor `call_llm` path wraps real provider request with governor admission.
- Routing config loader resolves canonical model keys from list-based `models`.
- Deterministic unit/integration tests.
- Proof bundle outputs for TP1 and TP2.

## Invariants
- Timeout behavior must not hang.
- Unknown-model policy remains unchanged.
- No secrets printed in logs.
- No RPD enforcement in this phase.
