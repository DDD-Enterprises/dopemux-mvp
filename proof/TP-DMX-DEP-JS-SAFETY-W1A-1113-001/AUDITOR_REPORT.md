# Supplemental L3 Auditor Report: TP-DMX-DEP-JS-SAFETY-W1A-1113-001

| Metadata | Details |
|---|---|
| Project | dopemux-mvp |
| Audited Head | `bc1bbb243a07420c2df33559aa4c30676e6addcd` |
| Base | `origin/main` = `33d6c353023ecc3aa6331ab39f4f076ae3ca1fda` |
| Auditor Tool | CommandCode CLI (`cmd`) |
| Auditor Model | `deepseek/deepseek-v4-flash` |
| Auditor Family | DeepSeek (independent different-family vs implementer Gemini) |
| Audit Type | Supplemental advisory audit |
| Date | 2026-08-07 |

## Invariant Verification

**1. Next.js 15.5.21 patch intent preserved, no Next 16 migration — PASS**
- `package.json` diff is exactly one line: `"next": "15.5.18"` -> `"next": "15.5.21"`.
- No `next@16`, no `eslint-config-next` migration, no other dependency or workflow change.
- Installed `node_modules/next` resolves to `15.5.21`.

**2. Product changes strictly confined to package.json + package-lock.json — PASS**
- Product file changes relative to `origin/main` are strictly `package.json` and `package-lock.json`.
- Merge resolved cleanly without force-push or rebase.

**3. Lockfile churn strictly bounded to root + next + @next/* closure — PASS**
- Changed package keys: `""`, `node_modules/next`, `node_modules/@next/env`, and 8x `@next/swc-*` platform packages.
- Zero unrelated package keys modified.

**4. npm ci / build / lint / audit baselines accurate — PASS (with pre-existing baseline caveats)**
- Peer dependency conflict (`eslint-config-next@16.1.6` vs `eslint@^8`) is pre-existing on `origin/main`; `npm ci --legacy-peer-deps` behavior matches `origin/main`.
- Build/lint failures (`Couldn't find any pages or app directory`) reproduce identically on `origin/main` baseline.
- `npm audit` comparison confirms all direct Next.js advisories are resolved by `15.5.21`. Remaining high findings (`postcss`, `sharp`, `nanoid`) match `origin/main` baseline.

**5. Secrets, tokens, or credentials absent from proof — PASS**
- Secret scan across all proof and task packet files returned zero matches.

## Findings & Risks

- **F1 (Medium - Fixed)**: `ROLLBACK.md` post-merge command syntax corrected.
- **F2 (Info)**: Transitive `postcss`/`sharp`/`nanoid` findings require Next 16 upgrade, which is out of scope for this packet and pre-existing on `main`.
- **F3 (Info)**: `npm run build` and `npm run lint` exit 1 due to missing `pages/app` directory in `dopemux-mvp` root; baseline equivalent.

## Supplemental Status

**PASS_WITH_RISKS (Supplemental).** All 5 invariants hold. This supplemental CommandCode/DeepSeek audit report is retained as advisory evidence; canonical embedded audit provenance is provided via signed local attestation under `proof/pr_merge/embedded-audit/pr-1113/`.
