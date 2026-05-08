# Settings / Admin / Runtime Specification

**Packet:** TP-DMX-COCKPIT-IA-RECONCILE-001
**Status:** NORMALIZED CANONICAL OUTPUT

Settings/Admin/Runtime is a **major secondary surface**, not a sixth top-level authority mode. It groups admin and runtime flows that cannot be safely mixed into PM, Implementer, Services, or Events home screens, while preserving the authority owners that already exist in the system.

## 1. Why It Is A Secondary Surface

The carried inventory places **62 rows** in the Settings/Admin family (`COMMAND_EXPOSURE_POLICY.json:metadata.source_counts.placement.Settings/Admin = 62`). These rows include routing/profile/env/MCP/service-startup/hooks/runtime/admin/debug actions. They share characteristics that make them inappropriate for primary mode chrome:

- They are admin/governance rows, not workflow steps.
- They have configuration-mutation, service-mutation, or environment-mutation side effects.
- They require admin gate confirmation, often with effective-config preview.
- They serve operator/runtime concerns rather than the PM, Implementer, Overview, Services, or Events workflow lenses.

Mixing them into Services would imply that Services owns admin/runtime mutation. The inventory and authority docs explicitly say that Services covers status and child-workload inspection, not admin mutation by default (`SCREEN_CONTRACT_MATRIX.md`). Mixing them into Overview would imply that Overview can mutate runtime state. Both placements would violate boundaries.

Settings/Admin/Runtime is therefore a separate **shell** the operator opens deliberately. It has its own home-screen contract but is not part of the primary mode bar. It does not create a new authority slice.

## 2. What Belongs Here

The surface groups the following flows. Each flow lists the authority owner that retains canonical truth; Settings/Admin/Runtime is the visible **placement**, not the owner.

| Flow group | Authority owner | Examples (from inventory) |
| --- | --- | --- |
| Routing / Model Provider | routing/model-provider support (LiteLLM/CCR) | `dopemux routing` family, `routing_cli.py` rows |
| Profile management | dopemux operator control | `dopemux profile` rows |
| Environment management | dopemux operator control | `dopemux env` rows |
| MCP server control | dopemux operator control + per-MCP authority | `dopemux mcp` rows, `mcp/servers/*` rows |
| Service startup / lifecycle | per-service authority (Cockpit shows status only) | service start/stop rows under their owners |
| Hooks / native-hooks | dopemux operator control | hooks/native-hooks rows |
| Runtime configuration | dopemux operator control | runtime config rows |
| Admin / safe / debug helpers | dopemux operator control | safe, debug helper rows |
| Drift inspection (read-only) | drift evidence (no execution) | links into `UNKNOWN_DRIFT_QUEUE_SPEC.md` |

## 3. Routing Rules

- The Command Palette routes admin/runtime rows to this surface.
- Overview links to this surface from drift / health summaries when an admin action is required.
- Services links to this surface only for admin-level actions; service status remains in Services.
- PM, Implementer, and Events do not link directly into admin actions; if a workflow needs an admin change, the workflow must open the palette which routes here.
- Every action in this surface invokes the Safe Action Gate (`SAFE_ACTION_GATE_SPEC.md`); no action executes inline.

## 4. Per-Flow Contract Summary

Each flow uses the existing screen contracts from `SCREEN_CONTRACT_MATRIX.md`. Settings/Admin/Runtime is the umbrella; the underlying screens retain their per-screen contracts (Routing/Model Provider, Hooks/Profile/Env, etc.).

| Flow | Allowed classes | Forbidden classes | Required gates |
| --- | --- | --- | --- |
| Routing / Model Provider | `DISPLAY_ONLY`, `INSPECT_ACTION`, `COMMAND_PALETTE_ONLY`, `CONFIRM_REQUIRED` (admin) | `BLOCKED_IN_COCKPIT`, `UNKNOWN` execution | T2 config mutation gate; effective config preview required. |
| Profile / Env | `DISPLAY_ONLY`, `INSPECT_ACTION`, `COMMAND_PALETTE_ONLY`, `CONFIRM_REQUIRED` (admin) | `BLOCKED_IN_COCKPIT`, `UNKNOWN` execution | T2 config mutation gate. |
| MCP server control | `DISPLAY_ONLY`, `INSPECT_ACTION`, `CONFIRM_REQUIRED` (admin) | direct destructive | T2 / T5 depending on action. |
| Service startup / lifecycle (admin) | `DISPLAY_ONLY`, `INSPECT_ACTION`, `CONFIRM_REQUIRED` (start/stop) | `BLOCKED_IN_COCKPIT` | T5 start/stop gate. |
| Hooks / native-hooks | `DISPLAY_ONLY`, `INSPECT_ACTION`, `COMMAND_PALETTE_ONLY`, `CONFIRM_REQUIRED` | `BLOCKED_IN_COCKPIT`, `UNKNOWN` execution | T2 config mutation gate. |
| Runtime / admin / debug helpers | `DISPLAY_ONLY`, `INSPECT_ACTION`, `COMMAND_PALETTE_ONLY` | `BLOCKED_IN_COCKPIT`, `UNKNOWN` execution | T0i / T2 / T5 as applicable. |

## 5. Why It Is Not A New Authority Mode

- It does not own state.
- It does not own truth (no PM, no decision, no workflow ownership).
- It does not provide an alternative path around the Safe Action Gate.
- It does not subsume Services (Services keeps status and child workload inspection).
- It is reachable from Overview/Services/Palette but is not part of the primary five-mode bar.

## 6. Forbidden Behaviors

- Adding admin rows to the primary mode bar.
- Mutating routing or environment without going through the Safe Action Gate.
- Implicit defaults that change runtime configuration on selection.
- Treating the surface as a PM or Implementer destination.
- Hiding `BLOCKED_IN_COCKPIT` admin rows; they must remain visible as blocked rows.

## 7. Source Artifact

This spec is new in this packet. It is derived from the `Settings/Admin` placement column in `RECONCILED_COCKPIT_IA.json` and the per-screen contracts in `SCREEN_CONTRACT_MATRIX.md`. No prior carried-forward artifact already filled this canonical name.
