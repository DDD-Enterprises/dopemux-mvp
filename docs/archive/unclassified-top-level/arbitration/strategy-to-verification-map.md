---
id: STRATEGY_TO_VERIFICATION_MAP
title: Strategy To Verification Map
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Strategy To Verification Map (explanation) for dopemux documentation and
  developer workflows.
---
# Strategy to Verification Map

## Overview
Every merge strategy in the high-risk arbitration lane carries specific mandatory verification requirements.

## Mapping Table

| Strategy ID | Mandatory Check Stages | Targeted Test Scope |
| :--- | :--- | :--- |
| **OURS_ONLY** | Structural Integrity | Regression suite |
| **THEIRS_ONLY** | Structural Integrity | Regression suite |
| **OURS_THEN_PORT_SELECTIVE** | Conflict Hunk Validation | Affected file logic |
| **THEIRS_THEN_REAPPLY_LOCAL** | Preserved Logic Audit | Preserved feature tests |
| **STAGED_SEQUENCE_MERGE** | Layered Verification | Build -> Config -> Logic |
| **MIGRATION_FIRST** | Data Integrity, Schema Validation | DB/Schema tests |
| **INTERFACE_FIRST** | Contract Consistency, API Signature | Contract/Protocol tests |
| **PATCH_ISOLATION_PLAN** | Isolated Patch Check | Patch-only scope |
| **REVERT_AND_REINTEGRATE** | Rollback Verification | Clean-base regression |
| **HUMAN_DEFER** | Manual Review Evidence | All |

## Rule: Non-Negotiable Pass
Regardless of the strategy, a `REMEDIATION_SESSION` is only considered 'SUCCESS' if all mandatory check stages for the chosen strategy return a `0` exit code.
