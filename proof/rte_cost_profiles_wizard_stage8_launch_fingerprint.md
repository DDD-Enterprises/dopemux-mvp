# Stage 8: Launch-Profile Fingerprint

## 1. Fingerprint Strategy
- **Identity:** `launch_profile_fingerprint` has been added to `_build_report_payload()` in `src/dopemux/commands/extractor_validation.py`.
- **Inputs:** It computes a deterministic SHA-256 fingerprint by concatenating `policy`, `max_cost`, and `promptset`.
- **Dry-Run vs Validator Parity:** The validation report payload now exposes `launch_profile_fingerprint` and `max_cost`, ensuring that pre-live execution artifacts contain a machine-readable record of the selected launch boundaries.

## 2. Verdict
**PASS.** The system now produces a deterministic fingerprint bridging `routing_policy`, `max_cost`, and the promptset root, making cost-profile validation machine-readable and explicitly auditable.
