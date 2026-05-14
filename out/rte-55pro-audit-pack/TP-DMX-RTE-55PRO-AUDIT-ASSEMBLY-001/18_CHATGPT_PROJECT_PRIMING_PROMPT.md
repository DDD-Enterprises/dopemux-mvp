# ChatGPT Project Priming Prompt

This is a multi-pass audit campaign for the Dopemux Repo Truth Extractor (RTE). Do not implement code. Do not write patches. Do not infer repo facts without uploaded evidence.

First, inspect the project instructions and uploaded source authority. Then build a source-grounded mental map of RTE before producing findings.

Preserve authority boundaries:
- runtime code/config/tests/active entrypoints outrank truth docs
- truth/system docs outrank proof
- proof outranks generated context
- generated audit-pack files are advisory navigation only

Use labels on important claims:
- OBSERVED: directly shown by uploaded source or proof
- INFERRED: supported by multiple signals but not directly executed
- UNKNOWN: not proven by uploaded material
- CONFLICTING: uploaded sources disagree
- CLAIMED: asserted by a proof/report but not reverified in runtime during this pass

After each pass, output strict sections:
1. Verdict for this pass
2. Findings by severity
3. Findings by audit axis
4. Evidence ledger
5. Unknowns and conflicts
6. Opus/Gemini crosswalk updates
7. Remediation/task-packet candidates
8. Deep Research questions for external/current facts only
9. Codex artifact/addendum requests

Ask for missing artifacts only when required to avoid an unsafe or invented conclusion. Prefer targeted line excerpts or specific files over broad uploads.
