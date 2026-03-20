---
id: NORMALIZATION_POLICY
title: Normalization Policy
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Normalization Policy (explanation) for dopemux documentation and developer
  workflows.
---
# Template Normalization Policy

## 1. Discovery and Deduplication
The automation layer must scan all known legacy paths for PR templates. On case-insensitive filesystems (like macOS APFS), it must explicitly deduplicate paths pointing to the same physical inode to prevent false-positive ambiguity flags.

## 2. Canonical Enforcement
Once discovered, if multiple distinct templates exist, the system must not guess. It must halt and escalate `AMBIGUOUS`. The repository maintainer must manually normalize to `.github/pull_request_template.md`.

## 3. Safe Injection Precondition
A patch plan or template injection may ONLY proceed if the `TemplateDiscoverer` resolves exactly one primary target path matching `.github/pull_request_template.md`.

## 4. Preservation
If an uppercase template or alternative path contains custom workflow content, it must be migrated to the canonical lowercase path before the alternative path is deleted from version control.
