---
id: product-faq
title: Product FAQ
type: explanation
owner: '@hu3mann'
author: codex
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: Repo-faithful Dopemux product FAQ with limitations and known drift.
---
# Product FAQ

## Is Dopemux a monolithic assistant?

No. Dopemux is documented as a split-authority operator workspace. `dopemux`
owns operator control, but PM metadata, workflow transitions, structured
decisions, chronicle memory, retrieval, bridge routing, ADHD support, and repo
audit have separate authority boundaries.

## What is implemented today?

Implemented repo evidence supports an operator CLI/control surface, execution
handoff through `dopetask`, PM authority split across Leantime,
task-orchestrator, ConPort, and dope-memory receipts, dope-context retrieval,
dopecon-bridge proxy/event routing, ADHD Engine support surfaces, and Repo Truth
Extractor evidence generation.

## Is dopecon-bridge the PM or workflow authority?

No. dopecon-bridge routes, proxies, adapts, and transports events. It can expose
PM-like, KG-like, decision, progress, and event routes, but those routes do not
make it the canonical owner. The upstream authority must be named.

## Is dope-context source truth?

No. dope-context provides derived code/docs indexing and retrieval. Its output
can help an operator find evidence, but the retrieved source file, runtime code,
config, tests, and active entrypoints remain stronger.

## Is dope-memory all memory?

No. dope-memory is the chronicle and receipt authority. ConPort owns structured
decisions, progress, project context, and custom data. Working-memory-assistant
has adjacent support surfaces. These are related but not interchangeable.

## Does Repo Truth Extractor override runtime truth?

No. Repo Truth Extractor produces audit and extraction artifacts. Those
artifacts are useful evidence, but they do not outrank runtime code, config,
compose wiring, tests, or active entrypoints.

## What known Drift remains?

Known Drift includes task-orchestrator historical runtime/port references,
ConPort access-surface splits, dope-memory and working-memory-assistant naming
overlap, stale or duplicate support services, and unresolved agent-family
ownership.

## What remains UNKNOWN?

The repo does not prove one canonical repo-wide agent runtime. Some support
service persistence and deployment authority also remains UNKNOWN. Live compose
startup and service health for all profiles remain NEEDS_REPO_VERIFICATION
unless a packet actually runs that validation.

## Is Dopemux production-ready?

This documentation does not claim production readiness. `pyproject.toml` marks
the package as alpha, and the documentation forge is docs-only. Production,
runtime health, and drift-closure claims require targeted validation.

## What should public copy avoid?

Avoid claiming autonomous learning, one unified memory layer, one PM authority,
bridge-owned workflow authority, or runtime drift closure. Use grounded language
such as "operator-control workspace", "split-authority", "derived retrieval",
"chronicle receipts", and "evidence artifacts".
