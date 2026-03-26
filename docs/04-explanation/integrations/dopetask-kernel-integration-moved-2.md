---
id: TASKX_KERNEL_INTEGRATION
title: Taskx Kernel Integration
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Taskx Kernel Integration (explanation) for dopemux documentation and developer
  workflows.
---
# TaskX Kernel Integration (Submodule-First)

## Purpose

Dopemux consumes TaskX as an external deterministic kernel.

- Dopemux orchestrates workflows and context.
- TaskX executes task-packet lifecycle commands and writes artifacts.
- Decision logic in Dopemux must use TaskX artifacts, not stdout/stderr parsing.

## Contract

1. Call direction is strictly `Dopemux -> TaskX`.
2. TaskX never calls back into Dopemux APIs.
3. TaskX results are consumed from filesystem artifacts.
4. Runtime and CI use `vendor/taskx` as the source of truth.

## Repository Model

- TaskX is vendored as a git submodule at `vendor/taskx`.
- Wrapper entrypoint is `scripts/taskx`.
- `.taskx-pin` is deprecated for runtime and CI behavior.

## Local Setup

```bash
git submodule update --init --recursive vendor/taskx
scripts/taskx --version
scripts/taskx doctor --timestamp-mode deterministic
```

## Dopemux CLI Surface

Use the kernel lifecycle group:

```bash
dopemux kernel doctor --timestamp-mode deterministic
dopemux kernel compile -- --mode mvp
dopemux kernel run -- --task-id T001
dopemux kernel collect
dopemux kernel gate
dopemux kernel promote
dopemux kernel feedback
dopemux kernel loop
```

Subcommands delegate directly to `scripts/taskx` and pass through trailing arguments unchanged.

## Updating TaskX

```bash
git submodule update --remote vendor/taskx
cd vendor/taskx
git checkout <taskx-commit-or-tag>
cd ../..
git add vendor/taskx .gitmodules
```

Then run:

```bash
scripts/taskx --version
scripts/taskx doctor --timestamp-mode deterministic
```

## Rollback

To roll back TaskX integration state:

1. Checkout a previous Dopemux commit that points `vendor/taskx` to a known-good submodule revision.
2. Run `git submodule update --init --recursive vendor/taskx`.
3. Re-run `scripts/taskx doctor --timestamp-mode deterministic`.
