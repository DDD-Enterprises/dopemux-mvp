---
id: system-hooks-audit-plan
title: System Hooks Audit Plan
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-18'
last_review: '2026-03-18'
next_review: '2026-06-16'
prelude: System Hooks Audit Plan (reference) for dopemux documentation and developer
  workflows.
---
# System Hooks Audit & Implementation Plan

## Objective
Perform a deep audit of the system hooks across the Dopemux MVP codebase, ensure correct implementation, verify wiring to all relevant components, and implement any missing handlers.

## Background & Motivation
An exhaustive audit of the `dopemux-mvp` hook systems was conducted using systematic multi-stage analysis (`thinkdeep`). The findings confirm that the project employs several distinct, isolated hook systems:
1. **`PreToolHookManager` (`src/dopemux/mcp/hooks.py`)**: Fully implemented. Actively optimizes and enforces budgets for MCP tool queries. Wired correctly into `mcp/broker.py`.
2. **`SafetyHooks` (`src/dopemux/claude_tools/safety_hooks.py`)**: Fully implemented. Successfully intercepts and sanitizes dangerous commands (e.g., `rm -rf`, `git push --force`).
3. **`ClaudeCodeHooks` (`src/dopemux/hooks/claude_code_hooks.py`)**: Fully implemented. Employs a background daemon (`monitor_daemon.py`) to monitor shell/file activity and correctly emits `dopemux memory capture emit` events.
4. **`Mobile Hooks` (`src/dopemux/mobile/hooks.py`)**: Fully implemented context manager for task notifications.
5. **`HookManager` (`src/dopemux/hooks/hook_manager.py`)**: **Structurally sound but functionally incomplete.** While it is correctly wired into the `MainOrchestrator` for routing editor and Claude events, its internal event handlers (`_index_file_background`, `_load_terminal_context`, `_validate_commit`) are entirely stubbed out with `await asyncio.sleep(...)` placeholders.

## Scope & Impact
The scope of this plan is strictly limited to resolving the incomplete implementation within `src/dopemux/hooks/hook_manager.py` to ensure the hook system provides actual business value (e.g., file indexing, context loading) rather than just logging placeholders.

## Proposed Solution
1. **Implement Missing Handlers in `HookManager`:**
   - **`_index_file_background(self, file_path: str, language: str)`**: Replace the `asyncio.sleep` stub with actual Dope-Context/memory indexing integration.
   - **`_load_terminal_context(self, terminal_name: str, shell_path: str)`**: Implement context preparation/loading logic.
   - **`_validate_commit(self, context: Dict[str, Any])`**: Implement git commit validation (e.g., format checking, complexity limits).
2. **Architectural Refinement for Validation Hooks:**
   - The current `trigger_hook` is "fire-and-forget" (`asyncio.create_task` or swallowed exceptions). For hooks like `git-commit` that require validation to potentially abort an action, `HookManager` must be adapted to return validation results (e.g., via a `trigger_and_wait` or by surfacing exceptions) so the caller can act upon failures.
3. **Verify Event Sources:**
   - Ensure the event parameters emitted by `ClaudeCodeHooks` (like `files`, `commit`, `commands`) correctly match the expected signatures in `HookManager`'s new handlers.

## Implementation Steps
1. **Refactor `trigger_hook`** in `HookManager` to optionally return statuses or handle blocking validation hooks.
2. **Implement `_index_file_background`**, hooking it into the existing context-management or memory-capture systems.
3. **Implement `_validate_commit`** with actual validation logic.
4. **Implement `_load_terminal_context`** with actual terminal context retrieval logic.
5. **Update existing tests** (e.g., `tests/scripts/test_hooks.py`) to verify the new handler logic and blocking behavior.

## Verification & Testing
- Trigger manual hook events (e.g., `dopemux trigger save --context '{"file": "test.py"}'`).
- Assert that the corresponding background operations (like file indexing) actually mutate the system state or database, rather than just sleeping.
- Assert that a failed `git-commit` validation hook properly aborts or logs the failure appropriately.
