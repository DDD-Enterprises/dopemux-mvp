---
id: TEMPLATE_PATH_AUTHORITY
title: Template Path Authority
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Template Path Authority (explanation) for dopemux documentation and developer
  workflows.
---
# PR Template Path Authority

## Overview
To prevent alignment ambiguity and ensure safe injection, this repository enforces a single canonical path for its pull request template.

## Canonical Target
**`/.github/pull_request_template.md`**

## Deprecated Paths
The following paths are explicitly deprecated and will be removed or ignored during template discovery:
- `.github/PULL_REQUEST_TEMPLATE.md` (Uppercase variant)
- `docs/PULL_REQUEST_TEMPLATE.md`
- `.github/PULL_REQUEST_TEMPLATE/default.md`
- `.github/pull_request_template.txt`

## Rationale
Multiple templates create a race condition in GitHub's UI presentation and introduce unacceptable risk when the automation layer attempts a non-destructive patch (e.g., injecting the High-Risk Integration Notes section). Declaring a single, lowercase target removes all ambiguity.
