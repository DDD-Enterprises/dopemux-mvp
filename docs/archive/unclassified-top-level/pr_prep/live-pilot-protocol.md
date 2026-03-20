---
id: LIVE_PILOT_PROTOCOL
title: Live Pilot Protocol
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Live Pilot Protocol for pr-prep-specialist operational testing.
---
# Live Pilot Protocol

The Live Pilot is a controlled execution of the `pr-prep-specialist` on real branches. It is designed to prove that the skill is operationally useful and safe when acting within the governance constraints established in TP-PRPS-007.

## Pilot Modes
The pilot must strictly adhere to the approved governance decision:
- **PACKAGE_ONLY**: The skill analyzes the branch and generates artifacts (including the PR draft), but does not interact with the forge (e.g., GitHub).
- **DRAFT_FIRST**: The skill is permitted to create PRs, but they must be explicitly flagged as Drafts, ensuring a human reviews the output before it becomes active.
- **SUPERVISED_FINAL_CREATION**: The skill can create non-draft PRs, but an operator must explicitly approve the action in the loop.

## Execution Flow
1. **Intake & Audit**: Run the pipeline on the selected pilot branch.
2. **Handoff Generation**: Generate the final decision and handoff bundle.
3. **Operator Review**: Present the artifacts to the operator via the `OPERATOR_REVIEW_FORM`.
4. **Data Capture**: Record acceptance, overrides, obligation accuracy, handoff usefulness, and any incidents.
5. **Synthesis**: Roll the results up into a `PILOT_HEALTH_SUMMARY`.
