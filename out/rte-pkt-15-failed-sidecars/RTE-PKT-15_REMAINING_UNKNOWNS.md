# RTE-PKT-15 Remaining Unknowns

## UNKNOWN: Packet 00 proof root

The current branch does not contain the named `out/rte-pkt-00-source-closure/` proof root, and a local sibling worktree search did not find it. The operator prompt supplied the packet-00 failed-sidecar risk context.

## UNKNOWN: comparison-lane failed text sidecar

`services/repo-truth-extractor/llm_runtime.py:1625` writes comparison-lane `.FAILED.txt` content directly from `failure_reason`.

This file is outside the packet allowlist, so it was not patched. If comparison-lane failed sidecars are in the live proof-storage boundary, a follow-up packet should either add `llm_runtime.py` to scope or prove comparison-lane failure text cannot contain provider, source, or exception secret-shaped content.

## ACCEPTED RESIDUAL: legacy v3 failed sidecar fixtures

Legacy v3 fixture sidecars were not modified. This packet focused on current v5 runtime failed sidecar safety. Existing fixture contents were not quoted in proof.

## PROCESS DRIFT: requested branch name collision

The requested branch already existed locally with broad unrelated drift against current `main`. This run used a clean branch and preserved the old branch untouched.
