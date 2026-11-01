Output a **unified diff (patch)** for the minimal set of changes to implement the approved plan.

Rules:
- Keep it surgical; do not include unrelated files.
- Ensure the patch applies with: `git apply -p0 < patch.diff` from repo root.
- After apply, run `make test-fast`, `make lint`, and `make type-check`; then update `/docs` & ADRs and proceed to PR.
