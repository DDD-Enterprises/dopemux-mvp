---
id: ROLE_MODEL
title: Role Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Role Model (explanation) for dopemux documentation and developer workflows.
---
# Arbitration Role Model

## Overview
High-risk integration arbitration uses three distinct model roles to ensure factual reconstruction, adversarial critique, and objective adjudication.

## Roles

### 1. Analyzer
**Purpose**: Factual reconstruction and proposal.
- **Tasks**: Reconstruct changes, identify invariants, propose candidate end states and merge strategies.
- **Visibility**: Canonical Evidence Bundle only.
- **Output**: Detailed summary of 'ours', 'theirs', and proposed syntheses.

### 2. Challenger
**Purpose**: Adversarial critique.
- **Tasks**: Search for hidden regressions, policy violations, and unsafe assumptions in the Analyzer's proposals.
- **Visibility**: Canonical Evidence Bundle + Analyzer Report.
- **Output**: Explicit objections and risk identification.

### 3. Arbiter
**Purpose**: Adjudication and final recommendation.
- **Tasks**: Evaluate Analyzer proposals against Challenger objections. Select the best candidate or defer to human review.
- **Visibility**: Canonical Evidence Bundle + Analyzer Report + Challenge Report.
- **Output**: Preferred candidate selection or Defer reason.
