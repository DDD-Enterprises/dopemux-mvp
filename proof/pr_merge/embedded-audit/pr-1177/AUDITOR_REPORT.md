# Independent Embedded Audit Report for PR #1177

- **PR Number**: 1177
- **Audited Content Head (F3)**: `5aa8b86ae5a008e3bddf4b98111c5c9afccaace4`
- **Auditor tool**: `claude-code-cli`
- **Auditor model (schema enum)**: `sonnet`
- **Implementer**: Grok (xAI) for F3 rendered-test salvage
- **Independence**: different-family (implementer Grok; auditor Claude Code CLI)
- **Status / Verdict**: `PASS`
- **Packet**: TP-DMX-PORTFOLIO-TOOLTIP-CLOSURE-SALVAGE-002

## Scope observed

- `ui-dashboard/src/components/TaskSequencer.tsx`
- `ui-dashboard/src/components/__tests__/Accessibility.test.tsx`

## Summary

F3 wraps the pending non-current Start button in an MUI Tooltip (title="Start task and switch active focus to: ${task.title}") with no other UI content change, matching the accepted F1 tooltip content. The new Accessibility.test.tsx test renders TaskSequencer, locates the pending Start button by accessible name (aria-label matching /^Start task: /) filtered to list items lacking aria-current="step" (excluding the ritual Start control), derives the task title from that aria-label, and asserts a rendered tooltip with the expected text appears both on keyboard focus and on mouse hover, closing the prior gap where tests only checked source text via string matching. Local validation (focused + full UI vitest, build) passed; only the two listed paths are changed vs main.

## Findings

### F-001: Rendered hover coverage added

- severity: `INFO`
- status: `RESOLVED`

New test fires mouseOver on a freshly remounted pending Start button and asserts screen.findByRole('tooltip') contains the expected 'Start task and switch active focus to: <title>' text, closing the previously accepted LOW risk that tests only checked source text.

### F-002: Rendered keyboard-focus coverage added

- severity: `INFO`
- status: `RESOLVED`

Test also calls button.focus() plus fireEvent.focus after a Tab keydown (needed for jsdom :focus-visible matching, since MUI Tooltip only opens on focus-visible) and asserts the same tooltip text appears, giving both interaction modalities real DOM coverage.

### F-003: Weakened source-text regex retained as secondary check

- severity: `LOW`
- status: `ACCEPTED_RISK`

The pre-existing string-match assertion (line ~175) was kept but loosened to a regex tolerant of whitespace around the Tooltip JSX; this is now redundant with the rendered test but is not harmful — it still fails if the Tooltip is removed or its title format changes structurally.

### F-004: Accessible-name disambiguation relies on DOM structure, not aria semantics

- severity: `LOW`
- status: `OPEN`

getPendingListStartButton() distinguishes the pending list Start button from the ritual 'Start Ritual' control via .closest('li') and aria-current!=='step' rather than a more robust selector (e.g., role='listitem' scoping or a dedicated test id). This works given current markup but is coupled to TaskSequencer's list structure and could silently break (find() returning undefined, caught by the explicit expect(pending).toBeTruthy()) if the DOM nesting changes materially in future refactors.

### F-005: Lint failure is a pre-existing environment gap, not introduced by F3

- severity: `INFO`
- status: `ACCEPTED_RISK`

ESLint fails on both candidate and main baseline due to missing eslint.config.* (ESLint 10 flat-config requirement), unrelated to this diff's content.

## Remaining risks

- Test relies on DOM traversal (closest('li'), aria-current attribute) to disambiguate the pending Start button from the ritual Start button rather than a purpose-built test hook, which is a maintainability/fragility risk if list markup changes.
- Lint tooling remains broken on both branches (pre-existing gap), so no lint signal is available for this or any other PR until eslint.config.* is added.

## Claims rejected / absent from diff

- No App.tsx changes
- No palette journal changes
- No PAL runner changes
- No merge or closure authorization

## Explicit non-claims

- No App.tsx changes in this PR.
- No palette journal changes in this PR.
- No PAL runner changes in this PR.
- Audit does **not** authorize merge or duplicate PR closure.

## Validation evidence considered

- focused Accessibility tests PASS (12)
- full UI vitest PASS (20)
- build PASS
- lint FAIL matching main baseline (missing eslint.config.*); residual tooling gap
