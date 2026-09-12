# Control Tower Installation

This installation derives from `CONTROL_TOWER_SUPERVISOR_KIT_v1.0.0.zip`.
Repository-maintained validation and packaging repairs are tracked in Git; this
is not an unmodified upstream v1.0.0 payload or a new upstream release.

## Configuration Authority

`project.json` is the canonical installed runtime configuration. The upstream
installer reads `config/defaults.json` when creating or upgrading that file.
The CLI does not read or merge defaults at runtime. Editing the retained
installer defaults does not change an existing installation. Repository governance
and the authorized packet take precedence over generic kit recommendations.

## Routing Template Semantics

`templates/ROUTING_DECISION.template.json` is a schema-shape example only. Its
`Replace with ...` values and `runner_availability: UNKNOWN` are placeholders,
not evidence that a runner or model is installed, available, approved, or
independent. Replace every placeholder with packet-specific values, record the
decision with `.control-tower/bin/ct route-record`, and validate the emitted
route before substantive work. Template validation proves JSON/contract shape
only; it does not prove authority, model execution, audit independence, CI,
review state, merge permission, or activation.

## Local Repairs

The repair packet and focused tests record the supported validation, scanning,
packet identity, return metadata, inventory and ZIP-integrity behavior. The
original installed payload and prior audit evidence remain in Git history.

When a JSON packet declares `repo_binding.require_identity_match: true`,
packaging checks the marker-specific project identity and Git origin before
creating a ZIP. A generic packet without such a binding does not provide that
repository-identity guarantee. Markdown packets require one unambiguous
canonical packet-ID heading; fenced examples are not packet authority.

Packages include `COMMITTED_DIFF.patch` for the recorded merge-base-to-head
range and `WORKTREE_DIFF.patch` for staged/unstaged changes relative to HEAD.
`LIVE_STATE.json` records the base/head and `GIT_STATUS.txt` lists dirty and
untracked paths. Git diffs do not contain untracked-file contents; include
required untracked evidence explicitly with `--include` or `--proof-dir`.
Missing required Git evidence blocks packaging rather than producing an empty
success receipt. Neither diff is evidence of a later checkout or remote state.

Reinstalling the original upstream kit can overwrite these repairs and its
managed `AGENTS.md` pointer. Review the diff and rerun the focused tests before
accepting an upgrade. Preserve repository-specific `project.json` settings and
consumed routing evidence; do not copy mutable state between repositories.

The extra routing and packaging workflow applies to supervised packets only.
Packaging is local evidence preparation, not audit acceptance, permission to
upload, approval to merge, or activation authority. Secret detection is heuristic;
successful scanning does not guarantee that an archive contains no sensitive data.
