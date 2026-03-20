---
id: RUNTIME_MODEL
title: Runtime Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Runtime Model (explanation) for dopemux documentation and developer workflows.
---
# Arbitration Runtime Model

## Overview
The Arbitration Runtime provides a provider-agnostic transport layer for multi-model arbitration. It separates role logic from specific LLM providers (OpenAI, Anthropic, etc.) and enforces strict output schemas.

## Core Components
1. **ArbitrationLLMClient**: Abstract interface for executing role prompts.
2. **Provider Dispatcher**: Maps roles to specific models/providers based on configuration.
3. **Schema Validator**: Ensures model outputs match the required JSON structure for each role.
4. **Invocation Tracer**: Captures metadata (latency, tokens, provider, model) for every call.

## Runtime Modes
- **MOCK**: Replays fixture-backed responses for testing.
- **LIVE_SINGLE_PROVIDER**: Routes all roles to one primary provider.
- **LIVE_MULTI_PROVIDER**: Maps different roles to specialized models (e.g., Challenger on high-reasoning models).
- **SHADOW_COMPARE**: Replays decisions against secondary providers for comparison.

## Fail-Closed Mandate
Any runtime failure (timeout, bad JSON, refusal) MUST result in an automatic `DEFER_TO_HUMAN` decision to prevent unguided automation.
