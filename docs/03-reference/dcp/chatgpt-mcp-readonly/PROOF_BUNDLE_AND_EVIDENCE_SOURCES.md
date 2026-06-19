---
id: PROOF_BUNDLE_AND_EVIDENCE_SOURCES
title: Proof Bundle And Evidence Sources
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-11'
last_review: '2026-06-11'
next_review: '2026-09-09'
prelude: Proof Bundle And Evidence Sources (reference) for dopemux documentation and
  developer workflows.
---
# Proof Bundle And Evidence Sources

## Proof Schemas / Contracts

- `AGENTS.md` proof and finality requirements
- `.taskorchestrator/config.yaml` note schemas and gate semantics
- task packet templates and generated task-packet indexes when present

## Proof Directories

- `proof/**`
- `audit_inputs/**`
- `extraction/**`
- `repo-truth-pack/**`

## Repo Truth Extractor Outputs

Repo Truth Extractor outputs are evidence artifacts. They do not outrank runtime code, compose wiring, tests, or active entrypoints.

## Handoff Bundles

Handoff and readiness artifacts are useful as chain-of-custody inputs when they include branch/head, validation state, and artifact hashes.

## PR Steward / Readiness Artifacts

PR readiness artifacts are advisory unless validated against current branch protection and current PR state.

## Chronicle / Memory Outputs

Dope-memory chronicle and replay outputs may support history/provenance, but must not be treated as PM, workflow, or code truth.
