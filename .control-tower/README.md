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

## Local Repairs

The repair packet and focused tests record the supported validation, scanning,
packet identity, return metadata, inventory and ZIP-integrity behavior. The
original installed payload and prior audit evidence remain in Git history.

Reinstalling the original upstream kit can overwrite these repairs and its
managed `AGENTS.md` pointer. Review the diff and rerun the focused tests before
accepting an upgrade. Preserve repository-specific `project.json` settings and
consumed routing evidence; do not copy mutable state between repositories.

The extra routing and packaging workflow applies to supervised packets only.
Packaging is local evidence preparation, not audit acceptance, permission to
upload, approval to merge, or activation authority. Secret detection is heuristic;
successful scanning does not guarantee that an archive contains no sensitive data.
