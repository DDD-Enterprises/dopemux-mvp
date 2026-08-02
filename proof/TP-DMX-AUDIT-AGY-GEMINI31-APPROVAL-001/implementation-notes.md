# Implementation Notes

## Decision
Approve gemini-3.1-pro-high as the exact AGY auditor model identifier.

## Evidence
- AGY v1.1.9 lists gemini-3.1-pro-high
- AGY v1.1.9 does NOT list gemini-3.1-pro-preview

## Bootstrap Audit Rule
Use auditor_tool=agy and auditor_model=gemini under pre-change schema.
