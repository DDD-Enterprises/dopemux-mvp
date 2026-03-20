---
id: PATCH_PRESERVATION_RULES
title: Patch Preservation Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Patch Preservation Rules (explanation) for dopemux documentation and developer
  workflows.
---
# Patch Preservation Rules

## Overview
These rules define which existing template content must be preserved during a canonical patch.

## Content to Preserve
1. **Summary Descriptions**: If the `Summary` section contains custom explanatory text, it must be kept.
2. **Specific Check Items**: Existing repo-specific check items (e.g., `./test_installer_basic.sh`) must be merged into the new `Verification` checklist.
3. **Maintainer Instructions**: Any text clearly directed at maintainers or reviewers that doesn't conflict with canonical headings.
4. **Security/Docs Blocks**: Existing custom sections like `Security and Docs` should be preserved or integrated into `Reviewer Notes`.

## Rule: Append vs. Overwrite
The patcher should prefer appending missing canonical blocks to the end of the file or after their relative logical neighbors, rather than rewriting the file from scratch.
