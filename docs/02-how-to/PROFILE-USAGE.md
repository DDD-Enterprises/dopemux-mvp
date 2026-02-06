---
id: PROFILE_USAGE_2026_02_06
title: Profile Usage
type: how-to
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-02-20'
status: active
prelude: Practical guide for listing, validating, selecting, and launching Dopemux profiles, including explicit start profile usage and YAML schema examples.
---
# Profile Usage

## Quick Start

Use an explicit profile at launch:

```bash
dopemux start --profile developer
```

Preview without launching:

```bash
dopemux start --profile developer --dry-run
```

## Inspect and Validate Profiles

List available profiles:

```bash
dopemux profile list
```

Show one profile:

```bash
dopemux profile show developer
```

Validate a single profile:

```bash
dopemux profile validate developer
```

Validate all profiles:

```bash
dopemux profile validate --all
```

## Apply Profiles During a Session

Apply or switch active profile marker:

```bash
dopemux profile apply developer
dopemux switch developer
```

Show the current active profile marker:

```bash
dopemux profile current
```

## Create and Maintain Custom Profiles

Create a new profile interactively:

```bash
dopemux profile init
```

Edit, copy, and archive profiles:

```bash
dopemux profile edit developer
dopemux profile copy developer developer-quiet
dopemux profile delete developer-quiet
```

## YAML Schema and Examples

Canonical schema reference:

- `docs/03-reference/configuration/PROFILE-YAML-SCHEMA.md`

Minimal example:

```yaml
name: developer
display_name: "Developer"
description: "Code implementation and debugging"
mcps:
  - conport
  - serena-v2
  - zen
adhd_config:
  energy_preference: medium
  attention_mode: focused
  session_duration: 50
```

Notes:

1. `conport` is required in all profiles.
2. MCP names can map to runtime aliases (for example `serena-v2` to `serena` in Claude config).
3. Backup and rollback safeguards are active when profile-backed config writes occur.
