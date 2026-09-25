# AUDITOR_REPORT

TASK_ID=TP-DMX-PRMERGE-015-OPUS-AUDIT-1359
PR=1359
AUDITED_BASE=35df148a55864b0efc5ada79753f987207b2936c
AUDITED_HEAD=e0b256544ab7cf1e8796cfefba824cdfee104a72
RAW_MODEL_VERDICT=PASS_WITH_RISKS
RAW_MODEL_EMBEDDED_SCHEMA=FAIL
DETERMINISTIC_SCHEMA_PROJECTION=PASS
ADMISSION_DECISION=SUPERVISOR_REQUIRED

## Scope
Lock-only transitive bump soupsieve 2.8.4->2.9 in root uv.lock. (1) Lock consistency is verified: uv lock --check --offline passed with 276 packages, and the only semantic delta is the soupsieve version plus its artifact metadata. (2) The repo's BeautifulSoup usage is verified in an isolated env with bs4 4.14.3 and soupsieve 2.9. The repo calls html.parser, soup([...]) find_all, decompose and get_text, and none of those route through soupsieve's CSS engine. (3) Upstream SoupSieve 2.9 selector semantics beyond the smoke checks, and the repo's own test suites, were not exercised.

## Raw model findings
- F1 [INFO/ACKNOWLEDGED]: Lock delta is minimal and consistent — Only the soupsieve version and its artifact metadata changed; uv lock --check --offline exited 0 with 276 packages.
- F2 [LOW/ACKNOWLEDGED]: Repo usage barely touches soupsieve — Repo code uses html.parser, find_all via soup([...]), decompose and get_text. The isolated smoke on bs4 4.14.3 plus soupsieve 2.9 passed.
- F3 [LOW/OPEN]: Repo test suites not run at head — The root uv run lacked bs4 (an environment-selection limit), so no repo tests exercised soupsieve 2.9.

## Remaining risks
- SoupSieve 2.9 upstream behavior beyond the smoke checks is untested.
- The dope-context service tests were not run at head.
- Other transitive soupsieve consumers were not exercised.
- A possible service-specific environment resolution was not verified.

## Deterministic receipts
- git diff base..head --stat: PASS — 1 file changed: uv.lock, 3 insertions, 3 deletions
- semantic lock delta: PASS — soupsieve 2.8.4->2.9 with artifact metadata only; beautifulsoup4 4.14.3 unchanged
- root pyproject: INFO — beautifulsoup4>=4.12.0; no direct soupsieve requirement
- repo source search: INFO — bs4 used in services/dope-context/src/preprocessing/document_processor.py; no direct soupsieve import found
- uv lock --check --offline @head: PASS — exit 0, 276 packages resolved
- root uv run --frozen --offline smoke: NOT_APPLICABLE — ModuleNotFoundError: bs4 because bs4 was not installed in the default env; treated as env-selection evidence, not a compat failure
- isolated offline smoke with beautifulsoup4==4.14.3 and soupsieve==2.9: PASS — html.parser parse, select('div.card'), select_one('div.card span'), script/style match with decompose, and get_text all passed; reported versions bs4 4.14.3 and soupsieve 2.9
- instruction-like added-line scan: PASS — 0 matches

## Schema projection
- Raw embedded_audit failed the repository schema only because two finding statuses were ACKNOWLEDGED; allowed values are OPEN, RESOLVED, ACCEPTED_RISK.
- Projection maps those two embedded-only statuses ACKNOWLEDGED -> RESOLVED.
- Verdict, finding title/body/severity, top-level findings, risks, identity, subject and test receipts are unchanged.
- The raw model output is preserved separately. Control Tower must decide whether this transport-only repair is admissible under the frozen task contract.

## Audit identity
- Runner: Claude Code 2.1.282
- Requested selector: opus
- Observed canonical model: claude-opus-5-5
- Provider: firstParty
- Requested effort: high; native return did not separately attest effective effort.
- One model call, one model turn, zero model tool/web/subagent calls.
- Raw output tokens: 2623 / 4200 max.
- List-basis reported cost: USD 0.08557580; cash charge not attested.

## Instruction-like content
- detected=false, match_count=0, truncated=false

## Mutations
- Audited subject files mutated: none.
- Repository/GitHub/workflow/service/sign/merge effects: none.
