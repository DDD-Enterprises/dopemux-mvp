# Implementation Notes

Bundle generation is performed by `tools/dcp/build_comprehensive_bundle.py` from an isolated worktree based on `origin/main`.

The generator creates two synchronized packages under this directory, redacts local paths and secret-like values in text, records source hashes, preserves provenance classes, and captures read-only GitHub and Task Orchestrator reconciliation.

Primary checkout was not modified. Live provider calls, public tunnels, backend writes, Task Orchestrator mutations, commits, pushes, and PR creation are out of scope.
