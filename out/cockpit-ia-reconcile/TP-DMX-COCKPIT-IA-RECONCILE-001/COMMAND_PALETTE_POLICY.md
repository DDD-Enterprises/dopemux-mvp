# Command Palette Policy

## What Belongs In Command Palette

- Rare commands that do not deserve primary navigation.
- Parameter-heavy commands where the operator must see inputs before invocation.
- Admin/runtime commands such as routing, profile, hooks, env, safe, debug, and update surfaces.
- Specialist commands such as PR merge and GitHub specialist flows, with remote mutation blocked unless later policy approves it.
- Confirm-required generated artifact or execution-handoff commands after preview.
- Deprecated, external-only, or unknown commands as non-executable rows when visibility helps drift management.

## What Does Not Belong

- Primary status rows that should live in Overview, Services, PM, Implementer, or Events.
- One-click destructive actions.
- Unknown actions with execution affordances.
- Hidden retries, default destructive parameters, or silent routing changes.

## Parameter-Heavy Action Behavior

The palette must show command path, authority domain, safety class, required parameters, default values, cwd/worktree target, output target, and whether proof/TP/governance is required. The operator must confirm the fully resolved command before any side effect.

## Rare Action Behavior

Rare actions may be searchable but should not occupy fixed mode chrome. A rare action row may open documentation, preview parameters, or route into Safe Action Gate.

## High-Risk Action Behavior

High-risk actions must route into Safe Action Gate. If the action is blocked, the row remains visible only as BLOCKED_IN_COCKPIT or EXTERNAL_ONLY and cannot execute.

## Command Search / Index Fields

Required index fields:

- command_path
- parent_group
- authority_domain
- classification
- safe_UI_exposure
- likely_cockpit_placement
- current_Cockpit_coverage
- activation_status
- source_file
- source_symbol
- help_text_or_summary
- evidence_path_or_command

## Confirmation Model

Confirmation is class-specific. The palette never executes directly. It either opens an inspect action, opens Safe Action Gate, or shows blocked/external-only status.

## Blocked Action Display Model

Blocked rows show command path, block class, reason, replacement command if known, and required external workflow. They do not show run buttons or keyboard execution shortcuts.

## Proof Requirement Display Model

Rows requiring proof show the expected proof artifact, validation command, TP/governance requirement, and post-action evidence surface before confirmation.
