# Command Exposure Policy

This policy is derived from the prior command inventory, not from visual preference.

## DISPLAY_ONLY
- Meaning: Read-only state or status data that Cockpit may render without presenting an execution affordance.
- Allowed UI form: status row; read-only table row; badge; detail inspector
- Forbidden UI form: primary action button; silent refresh that mutates state
- Required evidence/proof: source authority label; last observed timestamp when available
- Examples: `./scripts/dopetask`, `./scripts/dopetask bundle`, `./scripts/dopetask case`, `./scripts/dopetask ci-gate`, `./scripts/dopetask docs`
- Risk rationale: Safe to show, but still must not imply Cockpit owns the underlying authority.

## INSPECT_ACTION
- Meaning: Read-only or diagnostic action the operator intentionally invokes to inspect state.
- Allowed UI form: inspect command row; diagnostic drawer; doctor/preflight button with no write semantics
- Forbidden UI form: default-on polling with side effects; success chip before result exists
- Required evidence/proof: command path; exit/result summary; source authority
- Examples: `./scripts/dopetask doctor`, `./scripts/dopetask manifest check`, `./scripts/dopetask ops doctor`, `./scripts/dopetask project doctor`, `./scripts/dopetask tp git doctor`
- Risk rationale: Diagnostics can be expensive or environment-sensitive; they require explicit operator invocation.

## CONFIRM_REQUIRED
- Meaning: Action may mutate local state, generate artifacts, start services, or hand off execution; it needs explicit confirmation and post-action evidence.
- Allowed UI form: secondary action behind confirmation; safe action gate; command palette preview plus confirm
- Forbidden UI form: one-click primary button; auto-run on selection; success state without proof
- Required evidence/proof: preflight summary; confirmation record; post-action artifact or exit code
- Examples: `./scripts/dopetask bundle export`, `./scripts/dopetask bundle ingest`, `./scripts/dopetask case audit`, `./scripts/dopetask collect-evidence`, `./scripts/dopetask compile-tasks`
- Risk rationale: The inventory contains 111 confirm-required rows; direct buttons would hide risk and authority boundaries.

## COMMAND_PALETTE_ONLY
- Meaning: Rare, parameter-heavy, admin, or specialist action that must not occupy primary navigation.
- Allowed UI form: global command palette result; parameter preview; dry-run/preflight first
- Forbidden UI form: mode home-screen button; toolbar shortcut; implicit default parameters
- Required evidence/proof: parameter display; authority domain; safety class; required gate state
- Examples: `./scripts/dopetask project disable`, `./scripts/dopetask project enable`, `./scripts/dopetask project init`, `./scripts/dopetask project mode set`, `./scripts/dopetask project shell init`
- Risk rationale: The inventory places 139 rows in Command Palette and 40 rows explicitly as command-palette-only.

## BLOCKED_IN_COCKPIT
- Meaning: Action must not execute from Cockpit because it is destructive, high-trust, legacy-blocked, or unsafe without external governance.
- Allowed UI form: blocked row; external instruction reference; reason and required external workflow
- Forbidden UI form: button; confirm modal that still executes; keyboard shortcut
- Required evidence/proof: block reason; replacement command or external workflow if any
- Examples: `./scripts/dopetask commit-run`, `./scripts/dopetask commit-sequence`, `./scripts/dopetask finish`, `./scripts/dopetask metrics reset`, `./scripts/dopetask tmux kill`
- Risk rationale: The inventory contains 48 blocked rows; Cockpit must preserve fail-closed behavior.

## EXTERNAL_ONLY
- Meaning: Action is outside Cockpit execution scope even if visible as documentation or provenance.
- Allowed UI form: external-only row; copyable command text; link to runbook
- Forbidden UI form: Cockpit execution path; state mutation from UI
- Required evidence/proof: external authority owner; reason Cockpit cannot own it
- Examples: `dopemux decisions energy analytics`, `dopemux decisions energy log`, `dopemux decisions energy status`, `dopemux decisions graph`, `dopemux decisions list`
- Risk rationale: External-only keeps raw wrappers, deprecated commands, and specialist flows from becoming accidental UI authority.

## UNKNOWN
- Meaning: Activation, authority, side effects, or runtime ownership is unresolved.
- Allowed UI form: unknown/drift queue row; blocked until classified
- Forbidden UI form: execution affordance; success or readiness claim
- Required evidence/proof: missing authority note; required investigation packet
- Examples: `dopemux genetic`, `dopemux vault`, `dopemux worktree`, `dopemux worktrees`, `python -m dopemux`
- Risk rationale: Unknown actions must fail closed; UI can track them but cannot execute or imply readiness.

