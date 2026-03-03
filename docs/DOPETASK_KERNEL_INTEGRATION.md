---
id: DOPETASK_KERNEL_INTEGRATION
title: Dopetask Kernel Integration
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-20'
last_review: '2026-03-03'
next_review: '2026-06-03'
prelude: Dopetask Kernel Integration (explanation) for dopemux documentation and developer
  workflows.
---
# dopeTask Kernel Integration (Pip-Pinned)

## Purpose

Dopemux consumes dopeTask as an external deterministic kernel.

- Dopemux orchestrates workflows and context.
- dopeTask executes task-packet lifecycle commands and writes artifacts.
- Decision logic in Dopemux must use dopeTask artifacts, not stdout/stderr parsing.

## Contract

1. Call direction is strictly `Dopemux -> dopeTask`.
2. dopeTask never calls back into Dopemux APIs.
3. dopeTask results are consumed from filesystem artifacts.
4. Runtime and CI use the pinned pip package declared in `.dopetask-pin`.

## Repository Model

- Wrapper entrypoint is `scripts/dopetask`.
- Version pinning lives in `.dopetask-pin`.
- The local runtime is installed into `.dopetask_venv/`.
- The current pinned release is `dopetask==0.2.0`.

## Local Setup

```bash
scripts/dopetask --version
scripts/dopetask doctor --timestamp-mode deterministic
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

Subcommands delegate directly to `scripts/dopetask` and pass through trailing arguments unchanged.

## Updating dopeTask

```bash
python -m pip install --upgrade pip
pip install --upgrade dopetask==0.2.0
printf 'install=pip\ndep=dopetask\nversion=0.2.0\n' > .dopetask-pin
```

Then run:

```bash
scripts/dopetask --version
scripts/dopetask doctor --timestamp-mode deterministic
```

## Rollback

To roll back dopeTask integration state:

1. Restore `.dopetask-pin` to the prior known-good package version.
2. Remove `.dopetask_venv/` to force a clean reinstall on the next wrapper invocation.
3. Re-run `scripts/dopetask doctor --timestamp-mode deterministic`.
