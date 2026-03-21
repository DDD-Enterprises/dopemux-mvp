## Summary

Stages the vetted shortlist onto `dev` using a clean integration branch built from `upstream/dev` (`cb24a7eb4`).

This branch integrates:

- PR `#218` for the narrow AI completion detection fix in `services/session-manager/src/agent_spawner.py`
- PR `#215` for the focused ConPort memory-server row-mapping optimization
- PR `#233` as the selected Palette TaskSequencer UX/accessibility candidate

It also includes one required follow-up fix in `ui-dashboard/src/theme.ts` because `upstream/dev` already referenced token fields (`borders`, `shadows`, `surfaces`, `text`, `gradients.focusCard`) that were not exported by the theme contract. Without that repair, `ui-dashboard` did not build even before the shortlist merge was complete.

Branch head:

- integration branch: `codex/dev-shortlist-20260320`
- current tip: `a8d3fad8b`
- base: `upstream/dev` at `cb24a7eb4`

Changed files relative to `upstream/dev`:

- `.Jules/palette.md`
- `src/conport/memory_server.py`
- `ui-dashboard/src/App.tsx`
- `ui-dashboard/src/components/TaskSequencer.tsx`
- `ui-dashboard/src/components/__tests__/Accessibility.test.ts`
- `ui-dashboard/src/theme.ts`

## Type of Change

- [x] Bug fix
- [x] Feature
- [ ] Refactor
- [ ] Documentation
- [ ] CI/CD
- [ ] Security hardening

## Validation

- [ ] `python scripts/check_root_hygiene.py --all-files`
- [ ] `pytest tests/unit --maxfail=1 --disable-warnings --no-cov`
- [ ] `./test_installer_basic.sh` (when install/runtime paths changed)
- [x] Added/updated tests for behavior changes

Validation actually run on this integration branch:

- `python3 -m py_compile services/session-manager/src/agent_spawner.py`
- `python3 -m py_compile src/conport/memory_server.py`
- `cd ui-dashboard && npm ci`
- `cd ui-dashboard && npm test -- --run src/components/__tests__/Accessibility.test.ts`
- `cd ui-dashboard && npm run build`

Observed results:

- targeted accessibility test: 9 tests passed
- `ui-dashboard` production build: passed

Not run:

- repo-wide Python/unit suites
- repo-wide docs gates
- installer/runtime scripts outside the touched surfaces

## Risk and Rollback

- [x] Risk level documented (low/medium/high)
- [x] Rollback plan provided for risky changes

Risk level:

- medium

Why:

- `#218` and `#215` are low-blast-radius changes
- `#233` required semantic conflict resolution against `dev`
- one additional theme-contract repair was needed to restore an already-broken `ui-dashboard` build on `dev`

Rollback plan:

1. Revert commit `a8d3fad8b` if the theme-contract repair is not wanted.
2. Revert merge commit `a6c7cd936` to remove the Palette shortlist integration.
3. Revert merge commit `4c5847358` to remove the ConPort optimization.
4. Revert merge commit `902c09180` to remove the AI completion detection fix.

## Security and Docs

- [x] No secrets/credentials added
- [x] Security implications reviewed
- [ ] Docs updated (README/INSTALL/QUICK_START/docs) as needed

Notes:

- No credentials or secrets were introduced.
- Security posture was preserved; no auth or safety gates were weakened.
- No operator docs were updated in this packet because the changed surfaces are implementation-focused and the work was staged as an integration branch rather than a merged operator release.
