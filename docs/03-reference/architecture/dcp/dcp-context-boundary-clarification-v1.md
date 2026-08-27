---
id: dcp-context-boundary-clarification-v1
title: "DCP Context Boundary Clarification V1"
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-08-27'
last_review: '2026-08-27'
next_review: '2026-09-27'
status: accepted
prelude: Distinguish prospective ContextPlan policy from derived non-executable RunContextPacket evidence.
---

# DCP Context Boundary Clarification V1

## Two different records

`ContextPlan` describes required sources, capability references, authority
order, retrieval policy, and budget. It is prospective. It must not include
fulfilled evidence, freshness claims, dereference claims, or execution results.

`RunContextPacket` records derived evidence for one exact project/head subject.
It is the only P0 runtime context-envelope contract. It cannot authorize tool
execution, repository mutation, task mutation, or activation.

## READY rule

`READY` is valid only when:

- each context item is `FRESH`;
- each item was dereferenced;
- no item was truncated;
- no conflict exists;
- packet stays bound to exact subject and digest-bearing evidence.

`STALE`, `UNKNOWN`, `CONFLICTING`, missing dereference, or truncation blocks
READY. Retrieval candidates are not evidence until dereferenced. Advisory or
Wiki content never outranks runtime/source or accepted authority.

## One-envelope rule

Legacy and executable envelope variants are rejected. Current accepted contract
identifier is exactly `DCP_RUN_CONTEXT_PACKET_V1`.
