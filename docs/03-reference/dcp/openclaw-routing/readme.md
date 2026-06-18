---
id: README
title: Readme
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-17'
last_review: '2026-06-17'
next_review: '2026-09-15'
prelude: Readme (explanation) for dopemux documentation and developer workflows.
---
# OpenClaw DCP Routing Contracts

These files are proposed routing-policy contracts for the OpenClaw plus DCP
multi-model routing lane. They are static policy and schema artifacts only.

Production routing is not enabled by this directory. The files here do not wire
OpenClaw execution, provider API calls, OpenRouter integration, benchmark
execution, route-engine behavior, or credential handling.

Benchmark certification is still required before any route can be treated as
certified. Current model availability, prices, provider behavior, and OpenClaw
adapter support remain `UNKNOWN` until verified by a later implementation
packet.

OpenRouter free routes remain sandbox-only. They are blocked for private,
secret-bearing, client-data, security, release, and schema-authority lanes.
Direct APIs remain preferred for authority-bearing lanes.

Implementer self-audit is forbidden. Release and high-risk routes require
independent audit, explicit human approval, or both according to the proposed
contracts.
