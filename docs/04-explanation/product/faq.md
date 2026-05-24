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

## What is the claim boundary?

Dopemux coordinates work across authority lanes. It does not collapse those
lanes into one owner.

Use public copy to explain the operator control surface, not to upgrade
adapters, mirrors, derived retrieval, or evidence artifacts into source truth.

## Is Dopemux one AI assistant?

No. Dopemux is an operator control surface for split-authority development
workflows. Agent authority remains `UNKNOWN` across multiple families unless a
specific runtime path is verified.

## Is Dopemux a monolithic assistant?

No. Dopemux is documented as a split-authority operator workspace. `dopemux`
owns operator control, but PM metadata, workflow transitions, structured
decisions, chronicle history, derived retrieval, bridge routing, operator
support, and repo audit have separate authority boundaries.

## Is Dopemux a PM platform?

No. Current repo evidence shows split PM authority: Leantime handles passive PM
metadata, task-orchestrator handles workflow-significant transitions, ConPort
handles structured decisions and progress, and dope-memory keeps mirrored
historical receipts. Dopemux routes and normalizes operator work across those
lanes; it is not one PM owner.

## Is Dopemux a memory system?

No. The repo has separate memory-adjacent lanes. dope-memory is chronicle and
receipt authority; ConPort owns structured context, decisions, progress, and
custom data; dope-context provides derived retrieval. Public docs should not
collapse those into one memory owner.

## What is implemented today?

Implemented repo evidence supports an operator CLI/control surface, execution
handoff through `dopetask`, PM authority split across Leantime,
task-orchestrator, ConPort, and dope-memory receipts, dope-context derived
retrieval, dopecon-bridge proxy/event routing, ADHD Engine support surfaces,
and Repo Truth Extractor evidence generation.

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

## Is Dopemux fully local, private, or offline?

`NEEDS_REPO_VERIFICATION`. This public-docs packet did not run deployment,
network, provider, credential, or data-flow validation. Do not claim local-only,
private-only, or offline default behavior unless a dedicated runtime/security
packet proves it.

## What should public copy avoid?

Avoid claiming autonomous learning, one unified memory layer, one PM authority,
bridge-owned workflow authority, local-only/private-only/offline defaults, or
runtime drift closure. Use grounded language such as "operator control
surface", "split-authority development workflows", "source of truth",
"authority boundaries", "derived retrieval", "audit trail", "repo-grounded",
and "current-state".
