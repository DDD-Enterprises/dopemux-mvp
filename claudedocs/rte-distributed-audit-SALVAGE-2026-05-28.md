# RTE Distributed Audit — SALVAGED FINDINGS (run wf_09585c1c-f75, FAILED)

**HEAD:** 755bf3846 (main) · **Date:** 2026-05-28 · **Status:** workflow crashed at schema gate; these lanes left recoverable analysis.

> Recovered from agent transcripts. INSTALL is near-complete; USAGE is rich but pre-final; DISCOVER authority map is complete. CLI/MCP/RTE-core(S1-S8) left only orientation notes (not recoverable) — re-run covers them.

---

## INSTALL (devops-architect) — agent a9472555f05117aba

I'll audit the install/bootstrap surface without executing anything. Let me start by orienting — finding the actual files referenced in the contract.

Files located. There's a `Dockerfile` and `Dockerfile.frontend` at root but no `docker-compose*.yml` at root level. Let me find the compose files and read the primary install scripts in parallel.

I have the two main install scripts. Now let me read the remaining bootstrap files in parallel: the MCP server installer, MCP proxy setup, pyproject.toml, compose.yml, and both root Dockerfiles.

Now the Dockerfiles and compose.yml. Let me read all three root container artifacts plus the pymupdf-relevant Dockerfiles. The dope-context service mentions pymupdf source-build concerns from memory.

I have a lot of evidence. I found a real CRITICAL: a hardcoded LiteLLM master key in `compose.yml:312` (it shows as `<REDACTED_LITELLM_MASTER_KEY>` in my read output — the harness redacted an actual secret value present in the file). Let me verify the raw bytes of that line and several other claims with precise grep/sed before finalizing. I'll batch the verification commands.

The grep regex matched line 392 (a false positive — "task-orchestrator" contains no token; the regex `[A-Za-z0-9_-]{6,}` after "Bearer" — wait, that's odd). Let me re-check more precisely. The harness redacted the value in my Read output as `<REDACTED_LITELLM_MASTER_KEY>`, which strongly implies a real secret literal is on line 312. But my grep for `Bearer [A-Za-z0-9_-]{6,}` returned line 392 which is unrelated. Let me look at the exact line 312 bytes carefully and check git history for what's actually committed.

Important finding: the committed bytes literally contain the placeholder string `<REDACTED_LITELLM_MASTER_KEY>` — this is NOT a harness redaction of a real secret. It's a literal placeholder token checked into the file. `LEN=134` and the string is literally `<REDACTED_LITELLM_MASTER_KEY>` in both git HEAD and working tree. So the healthcheck curl uses a non-functional placeholder bearer token — the LiteLLM healthcheck would always fail auth (or the placeholder was scrubbed by a prior secret-removal pass and never replaced with an env reference). That's a real defect but NOT a leaked secret. Good — I avoided a false CRIT.

Now let me check the env_outputs directory (it contains files named `env_vars.txt` and `.env.codex` — these could be committed real secrets) and verify supply-chain claims: pymupdf, curl|sh, unpinned deps, and the `dhi.io/node` base image.

`scripts/env_outputs/env_vars.txt` IS git-tracked (committed). `.env.codex` is NOT tracked (it didn't appear in `git ls-files`, and `.env*` is gitignored at line 272). The grep found no real key prefixes in tracked files — `LITELLM_MASTER_KEY=` and `MASTER_KEY=` in `env_vars.txt:451,464` are empty (no value after `=`). Let me confirm those are empty placeholders and not real, then verify the supply-chain items (pymupdf, curl|sh, base images, pinning).

Confirmed:
- `env_vars.txt` (committed): **0 populated lines, 773 total** — pure key-name inventory, no secret values. Not a leak.
- `curl|sh` in actual install scripts: **none**. The two hits are (a) an *error-message echo* in a vendored pal-mcp `run-server.sh` and (b) a doc example for Ollama — neither executes in our bootstrap path. So the "curl|sh" supply-chain risk noted in the contract is NOT present in the audited scripts.
- `pymupdf>=1.23.0` is in `pyproject.toml [services]`, installed via `uv pip install --system --no-cache .[services]` in dope-context Dockerfile. pymupdf ships manylinux wheels for 1.23+ on cp311 — so source-build risk is real only if no wheel matches. Let me verify the `.[all]` install path in setup.sh (it installs bare `.` not `.[services]`, so pymupdf wouldn't even be pulled by setup.sh).

Let me confirm what `setup.sh`/`install.py` actually install (which extras), check `dhi.io/node` base image resolvability, and look at the install-adhd-integration child script and `.env.example` existence.

Key confirmations:
- `setup.sh:132` and `install.py:79` install **bare `.`** (no extras) — so the heavy `[services]` deps (pymupdf, pymilvus, qdrant, tree-sitter, etc.) are NOT installed by the CLI bootstrap. pymupdf source-build risk applies only to the dope-context **Docker** build, not the host CLI install. The memory note about pymupdf source-build was likely about a different/Docker path.
- `.env.example` exists ✓, `config/profiles/*.yaml` exists ✓.
- `scripts/setup/install-adhd-integration.sh` **does NOT exist** — setup.sh step 9 references a missing file. It's guarded by `if [ -f ... ]` so it degrades gracefully (prints "ADHD installer not found"). Minor.
- `Dockerfile.frontend` uses `dhi.io/node:18-alpine` — `dhi.io` is Docker Hardened Images, a **private registry requiring `docker login dhi.io`** (confirmed by the adhd_engine TODO comments at lines 6,35). The frontend image build will fail without auth and there's no preflight check for it.

This is a strong finding: the frontend Dockerfile hard-depends on an authenticated private registry with zero preflight detection. Let me verify whether `dhi.io/node` is actually used by any compose service (is the frontend even built by `compose.yml up`?) and check the `pip install -e . > /dev/null 2>&1` swallowing pattern more carefully, plus the `docker info` preflight gap in setup.sh.

Two more confirmed CRITICAL/HIGH findings:

1. **Network name mismatch (CRITICAL functional break)**: `compose.yml:24-27` declares `external: true` network named **`dopemux-network`**. But `setup.sh:170` creates **`dopemux-unified-network`**. So `setup.sh`'s `docker compose -f compose.yml up -d` (line 178) will FAIL with "network dopemux-network declared as external, but could not be found" — because the externally-created network has a different name. The setup script creates the wrong network and never creates the one compose actually needs.

2. **No docker daemon liveness preflight in setup.sh** — `check_command docker` (line 64) only checks the binary is on PATH, not that the daemon is running. `install-docker-mcp-servers.sh:110` does check `docker info`, but `setup.sh` (the documented "one-command install") does not. This is exactly the "Docker VM disk / daemon" blocker class from memory — no early detection.

The `159: dockerfile: Dockerfile` is the `leantime` build context — wait, line 159 is inside the leantime service which has `context: ./docker/leantime`. So root `./Dockerfile` is NOT used by compose either; it's the legacy `dopemux-backend` compat image built separately. Let me confirm that and the `> /dev/null 2>&1` error-swallowing, then I have enough to consult the advisor before finalizing.

Another real bug confirmed:

**`install.py:77` packaging path bug**: `current_dir = Path(__file__).parent` resolves to `scripts/` (since the script lives at `scripts/install.py`), then `pip install -e scripts/`. But there is **no `pyproject.toml` / `setup.py` in `scripts/`** (confirmed: `scripts/pyproject.toml` does not exist). So `install.py`'s `install_package()` will fail with "neither 'setup.py' nor 'pyproject.toml' found" — the venv-based installer is **broken**; it can never install the package. The comment says "from current directory" but `__file__.parent` is the script's directory, not CWD.

Also confirmed:
- `compose.yml:159` `dockerfile: Dockerfile` is **relative to `context: ./docker/leantime`** — i.e. `docker/leantime/Dockerfile`, NOT the root `./Dockerfile`. So root `Dockerfile` and `Dockerfile.frontend` are both built out-of-band (not by `compose up`). Good to state precisely.
- `setup.sh:132` swallows pip output with `> /dev/null 2>&1` then `exit 1` on failure — failure is caught (acceptable) but the diagnostic is hidden. Minor.

I have a solid evidence base. Let me consult the advisor before finalizing, since this is a multi-finding audit and I want to pressure-test severities (especially the network-name CRIT and the install.py CRIT) and make sure I'm not over/under-calling.

The advisor caught a real gap. I prematurely concluded the LiteLLM line was a literal placeholder — `git show` rendering `<REDACTED_...>` is consistent with BOTH a literal placeholder AND value-based harness redaction of a real key. The discriminator is the `grep -c` count rendered server-side. Let me run the discriminator and all the entrypoint-canonicality checks the advisor flagged.

The discriminator resolves it: `grep -c 'REDACTED_LITELLM_MASTER_KEY'` returns **1** (server-side count, both HEAD and working tree). If the harness were masking a real secret value, the literal string `REDACTED_LITELLM_MASTER_KEY` would not exist in the file to be counted — the count would be `0` and the mask would appear only in my rendered output. A count of 1 means the bytes `<REDACTED_LITELLM_MASTER_KEY>` are literally in the committed file. So it IS a literal placeholder, not a redacted live secret. My original conclusion was right, but now it's *verified* rather than assumed. The finding is MED: broken healthcheck (placeholder bearer token will never authenticate against LiteLLM), introduced by a secret-scrub during commit `7ef3d8475`.

Now the entrypoint-canonicality checks to calibrate CRIT vs HIGH/MED.

This is decisive evidence on multiple fronts:

1. **`setup.sh` is NOT pipefail-protected** — only `set -e` at line 13, no `set -o pipefail`. The advisor's masking analysis is confirmed: `docker compose ... up -d 2>&1 | tail -5` (line 178) — the `if` evaluates `tail`'s exit (always 0), so the `else ... exit 1` at 181-183 is **dead code**. Compose failure → setup.sh prints "✅ MCP services started" → reaches success banner. Partial-success-that-looks-complete confirmed.

2. **Network mismatch is a real, documented gap**: `compose.yml` needs external `dopemux-network`. `setup.sh:170` creates `dopemux-unified-network` (wrong name). The CORRECT creation lives in *other* scripts (`start.sh:75`, `smoke_up.sh:85`, `consolidate_docker_networks.sh`, `compose_nuke.sh:27`) — and even `docs/03-reference/governance/documentation-gap-register.md` DG-002 explicitly flags this as a known P0 gap. `consolidate_docker_networks.sh:3` confirms `dopemux-unified-network` is a *legacy/deprecated* network being consolidated away. So `setup.sh` creates a stale network name and the network compose needs is created by a different entrypoint (`start.sh`).

3. **Canonical entrypoint**: `.claude/CLAUDE.md` already told me `compose.yml` is "CANONICAL DEVELOPMENT ENTRYPOINT" with `docker compose up -d` — and `start.sh`/`smoke_up.sh` are the scripts that correctly create the network. `setup.sh` is documented in its own header as "One-Command Installation" but is desynced from the canonical compose. Neither `README.md` nor `Makefile` surfaced in the grep referencing setup.sh/install.py (only test-fixture and PM-inventory references to a *different* `installers/leantime/install.py`). Let me do one final confirmation of README's documented quickstart to nail entrypoint severity, and confirm the mas-sequential stale-bootstrap claim (pal vs mas in compose).

All claims now verified. Let me read the README lines around 88-95 to confirm the documented quickstart sequence and whether it mentions the network preflight (which would confirm setup.sh is NOT the canonical path).

Definitive. The **canonical documented path** (README:80-95, QUICK_START:15-20) is:
1. `uv sync --frozen --extra dev` (NOT `setup.sh`, NOT `install.py`)
2. `docker network inspect dopemux-network || docker network create dopemux-network` (correct network name)
3. `docker compose -f compose.yml up -d --build`

So:
- `setup.sh` and `install.py` are **vestigial/non-canonical** install paths. README never references them. This caps their bugs at **HIGH** (broken alternative path), not CRIT — the documented path works around the network issue and uses `uv sync --frozen` (reproducible). The advisor's calibration guidance applies: vestigial path → HIGH/MED.
- `install-docker-mcp-servers.sh` provisions `mas-sequential-thinking` which is **completely absent** from canonical compose.yml (count=0; canonical ships `pal` at line 269). Confirmed stale bootstrap, executing unpinned third-party code (`git clone` at HEAD, line 57; `git pull origin main` on update, line 54) then auto-running it (line 303).

I have everything. Writing findings. The deliverable is the structured output itself (no file to persist per the no-md-report rule). Let me record the ordered side-effects per script and finalize.

Audit complete. I read every file named in the contract (`scripts/install.py`, `scripts/setup.sh`, `scripts/install-docker-mcp-servers.sh`, `scripts/mcp-proxy-setup.sh`, `pyproject.toml`, `compose.yml`, root `Dockerfile`, `Dockerfile.frontend`, `services/dope-context/Dockerfile`) plus `README.md`/`QUICK_START.md` to establish the canonical path. Nothing was executed; all behavioral claims are tagged NOT_RUN with exact human-verify commands.

## Headline

The **canonical documented install** (README:80-95, QUICK_START.md:15-20) is `uv sync --frozen --extra dev` → manual `docker network create dopemux-network` → `docker compose -f compose.yml up -d --build`. That path is reproducible and sound. The defects cluster in the **non-canonical legacy installers** (`setup.sh`, `install.py`, `install-docker-mcp-servers.sh`), which is why most are HIGH, not CRIT.

## Top findings (file:line evidence)

- **F-INSTALL-001 (HIGH)** — `setup.sh` has `set -e` but **not** `set -o pipefail`; `docker compose up -d 2>&1 | tail -5` inside an `if` evaluates `tail`'s exit (always 0), so the `exit 1` branch at `scripts/setup.sh:181-183` is dead code. Compose failures print "✅ MCP services started" and reach the success banner. Partial-success-that-looks-complete.
- **F-INSTALL-002 (HIGH)** — `setup.sh:170` creates `dopemux-unified-network` (a *legacy* name per `consolidate_docker_networks.sh:3`), but `compose.yml:24-27` needs external `dopemux-network`. Already tracked as P0 DG-002. With F-001 it fails silently.
- **F-INSTALL-004 (HIGH)** — `install.py:77` `Path(__file__).parent` → `pip install -e scripts/`, but there's no build metadata in `scripts/`. The venv installer can never succeed.
- **F-INSTALL-005 (HIGH)** — `install-docker-mcp-servers.sh:57` git-clones a third-party repo at HEAD (unpinned), then builds and auto-runs it (`:303`) with operator API keys. Also provisions `mas-sequential-thinking`, which is absent from canonical `compose.yml` (which ships `pal`).
- **F-INSTALL-003 (MED)** — `setup.sh` checks `command -v docker` but never `docker info` (the sibling MCP script does at `:110`). No daemon-liveness/disk preflight — the known Docker-VM blocker class surfaces late.
- **F-INSTALL-006 (MED)** — `compose.yml:312` LiteLLM healthcheck uses a **literal** placeholder bearer token. I verified it is NOT a harness-redacted live secret via server-side `git show HEAD:compose.yml | grep -c 'REDACTED_LITELLM_MASTER_KEY'` → **1** (the token string is literally in committed bytes; a masked real value would be 0). It's a broken healthcheck, not a leak.
- **F-INSTALL-007 (MED)** — `Dockerfile.frontend` uses `dhi.io/node:18-alpine` (authenticated private registry, confirmed by `services/adhd_engine/Dockerfile:6` TODO) with no `docker login` preflight; plus `npm ci --only=production && npm install` defeats lockfile determinism.
- **F-INSTALL-008 (LOW)** — `:latest` base images + `>=`-only pins. Corrected a contract premise: the **pymupdf source-build risk is Docker-only** (`dope-context .[services]`); the CLI bootstrap installs bare `.` (`setup.sh:132`, `install.py:79`), so pymupdf is never pulled there.

## Cleared (OBS, with evidence)
- Committed `scripts/env_outputs/env_vars.txt` is key-names-only — `git show HEAD:... | grep -cE '=.+'` → **0**. Not a leak.
- **No `curl|sh`** in any audited install script (the two hits are an error-echo in vendored pal-mcp and an Ollama doc example — neither executes).
- `.env.example` and `config/profiles/*.yaml` present; missing `install-adhd-integration.sh` degrades gracefully via `-f` guard.

One advisor-driven correction shaped the result: I initially "cleared" the LiteLLM line as a placeholder on insufficient evidence (the redaction syntax was ambiguous between literal-placeholder and masked-real-secret). The server-side `grep -c` discriminator confirmed it's a literal placeholder — so the MED stands and no rotation is needed, but it's now verified rather than assumed.

Full structured findings (10 items, severity + evidence + falsifying checks) were submitted via the StructuredOutput tool.


---

## USAGE (technical-writer) — agent a93abd97afdd5ce26

I'll audit the documented usage of the Repo Truth Extractor against runtime truth. Let me start by orienting myself with the key documentation and the validation gate.

I have the README and the validation gate. Now let me read the other key documentation sources and start verifying against runtime. Let me read the root README, the how-to docs, and PHASE docs in parallel.

There's a large doc surface. The key user-facing docs are in `docs/02-how-to/extraction/` and `docs/01-tutorials/`. Let me read the most operationally important ones — the golden path docs — and the cost-profile guide.

The quickstart tutorial uses an entirely different command family (`dopemux audit prescan/wizard/status`) than the README's canonical (`dopemux rte`) and the first-live runbook's (`python ... run_extraction_v5.py`). This is a major drift candidate. Let me read the remaining how-to docs and verify the CLI surfaces against actual code.

Now I have a clear picture of a major contradiction. The user-guide explicitly says `dopemux extract truth-run` and `dopemux extractor` are "legacy/refusal surfaces, not the v5 operator path", while the **extraction-quickstart tutorial** (the entry point for new users, linked from "Step 5" with `dopemux extract truth-run --phase D`) uses `dopemux audit prescan/wizard/status` AND `dopemux extract truth-run`. Let me now verify the actual CLI against the runtime code. Let me inspect the CLI command surfaces.

The cli.py is large (236KB). The registrations may use a different pattern. Let me search more broadly for how the command groups are wired.

No `add_typer` in cli.py. The structure must be different. Let me look at how the CLI is actually built and where these subcommands live.

This is a `click`-based CLI, not typer. Let me find the command group definitions and how subcommands attach. Let me look at the entry point in pyproject and how groups register.

Now I can see the command structure. There's an `rte` group at line 4952, `extract` at 3092, `upgrades` at 3162, `extractor` at 3170, `audit` at 3218. Let me read the key registration lines and the `rte` group definition to verify the documented commands exist.

Critical finding confirmed: `extractor` is registered as a `LegacyReplacementCommand` with `replacement_by_arg` showing `prescan → "dopemux rte run"`. So `dopemux extractor` is a refusal surface. Now the quickstart tutorial uses `dopemux audit prescan/wizard` AND `dopemux extract truth-run` — I need to verify what those actually do. Let me check the `extract` group, the `audit` group, and the `rte` group definitions.

Now I see `rte` group has a `scan` subcommand. But the README documents `dopemux rte run`, `dopemux rte preflight`, `dopemux rte validate-live`. These must be defined elsewhere or shared with `upgrades`. Note line 5027: `@upgrades.command("list")`. The commands seem to be defined on `upgrades` and the `rte`/`upgrades` aliasing happens through shared registration. Let me find where `rte run`, `rte preflight`, `rte validate-live`, `rte status`, `rte promptset` are actually attached, and check the `extract` and `audit` groups.

The same command functions (`extractor_run`, `extractor_preflight`, `extractor_validate_live`, `extractor_status`, etc.) are registered on BOTH `upgrades` (lines 5060-5527) and `rte` (lines 5597-5603). So `dopemux rte run`, `dopemux rte preflight`, `dopemux rte validate-live`, `dopemux rte status`, `dopemux rte promptset`, `dopemux rte trace` all exist. README commands are verified. Now critically: line 5603 `rte.add_command(audit.commands["wizard"], "wizard")` — so `dopemux rte wizard` exists too.

Now let me verify the `extract` group (for `dopemux extract truth-run` used in the quickstart) and the `audit` group (for `dopemux audit prescan/wizard/status` in the quickstart). Let me look at the extract group and audit_commands.

Now I have the key facts. `extract truth-run` is at line 876 with `hidden=True`. The user-guide says it's a "refusal surface", but the truth-run-command.md doc and the runtime show line 1097 prints "dopemux rte run (via dopemux extract truth-run compatibility alias)" — suggesting it may actually delegate, not refuse. This is a contradiction I need to resolve. Let me read the truth_run function body to see if it refuses or executes.

Confirmed at line 998-1000: `truth_run` raises `click.ClickException("Legacy command disabled. Use dopemux rte run...")` immediately — and the body after it (line 1002+) is unreachable dead code. So `dopemux extract truth-run` is genuinely a **refusal surface**. The user-guide is correct; the **extraction-quickstart tutorial** (Step 5, line 165) tells users `dopemux extract truth-run --phase D` to "re-run just the docs phase" — which would fail with a refusal. This is confirmed doc-vs-code drift.

Now let me verify the `audit prescan/wizard` commands actually exist and whether the wizard `--execute` path can incur cost. This determines whether the quickstart's "first/safe" framing is honest. Let me read the audit_commands wizard and prescan bodies.

So `dopemux audit prescan`, `dopemux audit wizard`, `dopemux audit status` all exist and work. The quickstart's prescan/wizard/status flow is real. But note:
- `audit prescan` (line 56) delegates to `scripts/doc_audit_prescan.py` — NOT the RTE prescan runtime (`lib/prescan/`). It writes to `extraction/prescan/` per the quickstart, a different surface from RTE's v5 prescan.
- `audit wizard --execute` (line 81-83) does engage LLM providers. The quickstart Step 4 says "Show you the estimated cost before proceeding / Ask for confirmation before EACH phase" — that's a cost-control claim I should verify against WizardRunner, but it's a documented cost path so not a "surprise."

The real drift in the quickstart is Step 5/What's Next line 165: `dopemux extract truth-run --phase D` (refusal surface). Let me also verify the prescan output dir claim and check whether `audit prescan` matches `scripts/doc_audit_prescan.py`. Let me also confirm the `--preset first-live` and key flags in run_extraction_v5.py to validate the first-live runbook. Let me consult the advisor before finalizing, but first gather the remaining runtime verification on v5 flags and the validate-live consent posture.

Key verifications:
- README:160 says `--preset first-live` initial stage = `A,H,D,C`; code line 21541 confirms initial runs `A/H/D/C` ✓
- README:161 + first-live:233 say post-review runs `R,X,T,Z,S`; **code line 21541 says post-review runs `R/X/T/Z/S/SP`** — there's an extra `SP` step in code not documented. Minor drift.
- README:145 "raw v5 runner treats non-`--dry-run` execution as live; use `--execute`... set `DPMX_LIVE_OK=1`" — confirmed by lines 21462, 22859, 3289-3293 ✓
- All inspection flags exist ✓
- `--max-cost-usd` requires `--partition-workers 1` (line 3944) ✓ consistent with first-live preset defaults

Now one thing to verify carefully: README:145 says "raw v5 runner treats non-`--dry-run` execution as live". Does this mean running `run_extraction_v5.py --phase A` WITHOUT `--dry-run` and WITHOUT `--execute` will go live (surprise cost)? Let me check the default execution mode logic — this is a critical surprise-cost question. Let me also check the `--preset-stage` doc says default is "initial".

This logic shows: live operation is gated only when `args.execute` is set. But the README:145 claim is "raw v5 runner treats non-`--dry-run` execution as live." I need to find where the default `dry_run` resolution happens — whether absence of both `--dry-run` and `--execute` defaults to dry-run (safe) or live (surprise cost). Let me trace how `dry_run`/`execute` resolve into the RunnerConfig.

This is the critical line. Line 21913-21915:
```python
if args.execute:
    args.dry_run = False
args.execute = bool(args.execute or not args.dry_run)
```

So if the operator runs `run_extraction_v5.py --phase A` with NEITHER `--dry-run` NOR `--execute`:
- `args.dry_run` defaults to `False` (it's `store_true`, line 21556)
- line 21913: `args.execute` is False, so skip
- line 21915: `args.execute = bool(False or not False)` = `bool(True)` = **True**

So bare invocation with a phase and no flags becomes `execute=True`, `dry_run=False`. Then at line 22859, since `execute=True` and if `DPMX_LIVE_OK` is not set, it errors out with the consent message (safe). But IF `DPMX_LIVE_OK=1` is already in the environment, a bare `--phase A` (no `--dry-run`, no explicit `--execute`) goes **live** — matching README:145's warning. The README does document this ("treats non-`--dry-run` execution as live; use `--execute` for clarity and set `DPMX_LIVE_OK=1` before any live run"). So this is documented, not a hidden surprise — but it's a sharp edge. The DPMX_LIVE_OK gate is the backstop.

I have strong primary-source evidence on the main claims. Let me consult the advisor before finalizing, since this is a multi-finding audit and I want to pressure-test severity calls (especially the quickstart drift and the bare-invocation default).

The advisor identified three blocking items with likely findings. Let me execute these in parallel: verify the phase glossary against code, read `extractor_validate_live`, read the WizardRunner, and skim the two remaining how-to docs.

Two important resolutions:

1. **Phase glossary**: Code (`phases.py:49-130`) confirms canonical names are "Repo Plane", "Home Plane", "Docs Plane", "Code Plane", "Arbitration" (R). The **user-guide §2 (`:32-41`) names are WRONG**: A=Audit, H=Hygiene, D=Discovery, C=Collection, R=Reasoning, B=Boundaries — none match code `display_name`/`purpose`. Confirmed doc-vs-code drift in the canonical user guide. And H=Hygiene collides with `extraction_hygiene.py`. The quickstart table (`:106-121`) is much closer to code truth.

2. **`rte validate-live` flags**: `extractor_validate_live` (cli.py:5365-5417) DOES have `--stage`, `--provider`, `--pricing-manifest` — so user-guide §7 is accurate against THIS validator. This is a different validator from `validate_pre_live_gate_v25.py` (the gate has no such flags). So there are two distinct validators, and the docs invoke them in different places. The user-guide §7 commands are valid.

Now let me read the WizardRunner to resolve the surprise-cost/DPMX_LIVE_OK question, and skim the two remaining how-to docs.

`src/dopemux/ux/wizard.py` doesn't exist at that path. The import is `from ..ux.wizard import WizardRunner` from `audit_commands.py`. Let me locate it.

`WizardRunner` is in `src/dopemux/ux/wizard/runner.py`. Let me inspect it for the DPMX_LIVE_OK gating and per-phase confirmation.

runner.py is a thin (96-line) shim. It passes `execute_mode=execute` to something else. Let me read the whole file to find what it delegates to.

The extraction stage is in `.extraction` (`run_extraction`, line 13/62). That's where the live gating and per-phase confirmation live. Let me inspect the extraction stage module.

This is the key surprise-cost surface. Let me read the relevant portion — lines 20-160 — to see exactly how the wizard builds the command, whether it sets DPMX_LIVE_OK, and the per-phase confirmation.

Now I have the complete picture on the wizard. Resolution:

- The wizard builds `dopemux upgrades run --pipeline-version v5 ... --execute` (lines 27-51) and runs it via subprocess with `proc_env = dict(os.environ)` (line 146). It does **NOT** inject `DPMX_LIVE_OK=1`.
- The underlying `upgrades run` → `extractor_run` → v5 runner requires `--execute` AND `DPMX_LIVE_OK=1` (verified earlier at v5:22859-22871, 21462-21463). So if the operator runs `dopemux audit wizard --execute` WITHOUT `DPMX_LIVE_OK=1` in their environment, each phase subprocess will **fail closed** with the consent error.
- This means the quickstart Step 4 command `dopemux audit wizard --execute --routing-policy balanced_openrouter` (line 130) is **incomplete** — it will fail at the extraction stage unless the operator has separately exported `DPMX_LIVE_OK=1`, which the quickstart never mentions. This is a fail-closed gap (not a surprise-cost), consistent across the system but undocumented in the tutorial.
- Per-phase confirmation IS real (lines 122-128: "Run/Skip/Abort wizard" per phase). So quickstart's "Ask for confirmation before EACH phase" (line 136) is accurate. But the "Show you the estimated cost before proceeding" claim — the cost preview is Stage 5 (`run_cost_selection`), shown once, not per-phase; minor.

I now have enough to also confirm the wizard delegates to `upgrades` (legacy alias) rather than `rte` — a canonical-naming inconsistency in the runtime itself (line 32: `"upgrades"`), though functionally identical.

Let me do the final skim of the two remaining how-to docs the task named, then write findings.

This is decisive evidence on two fronts:

1. **`universal-extractor-usage.md`** uses `dopemux extractor init/validate/status` (lines 33-149) — but `extractor` is a `LegacyReplacementCommand` (cli.py:3170-3184) that refuses with replacement messages, AND `extractor init` is not even in its `replacement_by_arg` map (only run/status/prescan/promptset/init→"dopemux rte promptset sync"... wait, `init` IS mapped to "dopemux rte promptset sync"). So `dopemux extractor init/validate/status` are all refusal surfaces. This entire how-to doc targets a refused command family. Confirmed drift. (Note: README:37 also documents `dopemux extractor validate --output-dir` as if real.)

2. **`extraction-wizard.md` (the how-to, NOT the tutorial)** correctly documents `DPMX_LIVE_OK=1 dopemux audit wizard --execute` (lines 40, 90, 98) AND explicitly states the DPMX_LIVE_OK requirement (line 117) and that it delegates to `dopemux upgrades run` (lines 127-128). So the how-to is correct — which makes the **quickstart tutorial's omission of DPMX_LIVE_OK a clear intra-repo inconsistency**: the how-to knows the gate, the tutorial doesn't.

This confirms the `extractor validate` reference in README:37 is also drift. Let me do one final check: confirm `dopemux extractor validate` / `init` / `status` actually route through the refusal `LegacyReplacementCommand` and aren't separately defined as working commands (the `extractor` module exports might still wire real subcommands). Let me verify the LegacyReplacementCommand behavior and whether `extractor` real subcommands are shadowed.

Decisive confirmation. The `LegacyReplacementCommand` (cli.py:67-100):
- `invoke()` (line ~95-99) ALWAYS raises `click.ClickException("Legacy command disabled. Use ...")` 
- `parse_args` discards all args (`ctx.args = []`, returns `[]`)

And critically: `extractor_commands.py` DOES define real `init` (line 172), `validate` (line 406), `status` subcommands on the `extractor` group — BUT at registration time (cli.py:3170-3184), the real `extractor` group is **replaced** by the `LegacyReplacementCommand` named "extractor". So `cli.add_command(LegacyReplacementCommand(name="extractor", ...))` shadows the real group entirely. The real `init`/`validate`/`status` are unreachable via `dopemux extractor`. So `dopemux extractor init/validate/status` (universal-extractor-usage.md, README:37) all hit the refusal. Confirmed.

I have all evidence needed across all task-required surfaces. My deliverable (findings) will be returned via StructuredOutput, which is durable. Let me do a final advisor check to validate severity calibration and completeness before the terminal call.


---

## DISCOVER (authority map) — agent a1c558045bf596c12

I'll map the canonical authority of the Repo Truth Extractor. Let me start by orienting myself in the directory structure.

This is a read-only audit. Let me read the core authority files in parallel. The terminal engine is likely the largest/most-recent file (`run_extraction_v5.py` at 888KB, modified May 26 — most recent). Let me read the key dispatch points and the smaller authority files.

Now I have the critical config truth. `rte_config.py:126` clearly establishes `run_extraction_v5.py` as the canonical `RUNNER_SCRIPT`. Let me examine the v3/v4/v5 entry points and the registry/promptset truth, plus the gate validator. Given v5 is 888KB, I'll inspect its header and CLI dispatch rather than reading it whole.

Key finding: v4's docstring (line 3-9) explicitly states it "keeps v5 execution intact" and "executing v5 for supported phases" — so v4 is a **wrapper that delegates to v5** (`V5_RUNNER` at line 36). v3 has its own full `main()` (line 11237) but requires explicit `--enforce-v3-live` consent (line 11225, 11249) — it's gated legacy. Let me confirm v5 is the terminal engine and examine the registry truth and gate validator.

Now I have the full picture. The task asked for "two registry.json files" but I found 4 registry.json files plus the promptset.yaml truth. v5 has its own complete engine (`main()` at 21502, `OperatorArgumentParser` at 1829) and does NOT delegate to v3/v4 — confirming v5 is terminal. Let me confirm the gate validator's role and which runner v5 vs the prompts/v3 dir relationship, then verify v3's deprecation status and what references v3/v4/v5 across the codebase.

I now have enough evidence for a complete authority map. Let me do one final verification: confirm v3's live-execution gating (the `_enforce_v3_live_consent` mechanism) and check the README's own statement of which runner is canonical, plus verify the prompt root resolution (which promptset is the default truth).

I have all the evidence needed. Let me consult the advisor before finalizing, since this authority map will be the coordination baseline for parallel auditors and getting the terminal-vs-wrapper relationships wrong would cause exactly the contradiction this task aims to prevent.

The advisor flagged a real gap: I haven't resolved the default prompt-root question (`promptsets/v4` static vs `promptsets/generated/` auto-generated). Let me read `rte_promptset.py` and trace `_prompt_root_impl` to close it.

The central question is now closed with primary-source evidence. `rte_promptset.py:9-23` `prompt_root()` is the canonical resolver, imported into v5 as `_prompt_root_impl`. The default resolution order is unambiguous:

1. `REPO_TRUTH_EXTRACTOR_PROMPT_ROOT` env (`rte_promptset.py:15-19`)
2. else `LEGACY_PROMPT_ROOT_ENV_VAR` / `UPGRADES_PROMPT_ROOT` env (line 17)
3. else `promptsets/v4/prompts` if it exists (line 20-22) ← **default truth**
4. else `prompts/v3` (line 23) ← legacy fallback

The auto-generated `promptsets/generated/dopemux-mvp-2e346e2084bc/` is NOT in the default resolution path — it's only reachable via env override (it's the GX0 promptgen output, governed by `PROMPTGEN_*` constants in `rte_config.py:46-99`). That resolves the advisor's fork. I have everything needed.

---

# AUTHORITY MAP — Repo Truth Extractor (`services/repo-truth-extractor/`)

## Terminal execution engine
**`run_extraction_v5.py`** is the single canonical engine. Own `main()` (v5:21502), own `OperatorArgumentParser` (v5:1829); **no delegation** to v3/v4 (grep: zero `run_extraction_v3/v4` imports). Pinned as authority by `rte_config.py:126` (`RUNNER_SCRIPT = ...run_extraction_v5.py`), the gate `validate_pre_live_gate_v25.py:30` (`RUNNER_PATH`), and v4 (`run_extraction_v4.py:36` `V5_RUNNER`). README:101 names it the entrypoint; `dopemux extract truth-run` aliases here (README:43).

## Wrapper
**`run_extraction_v4.py`** — thin Typer wrapper that **subprocesses v5** and rebuilds deterministic v4 norm outputs (docstring v4:3-9). It is NOT an engine but IS the **default prompt/artifact-contract layer** (README:27 "v4 (default)"). Two axes, both true: *execution authority = v5*; *contract/promptset authority = v4*.

## Shadow / legacy
- **`run_extraction.py`** (bare) = **dead/shadow**. Raises `NotImplementedError` on live (run_extraction.py:272); zero non-test consumers. Do not treat as authority.
- **`run_extraction_v3.py`** = independent legacy engine, **consent-gated** (`--execute` + `DPMX_LIVE_OK=1`, v3:11225-11234). "Legacy but still imported" — live non-test consumers exist: `run_probe.py`, `run_repscan.py`, `tools/phase0_serialize_partitions.py`.
- **`phases.py`** = shared phase DAG/dependency truth (PhaseId, dependencies, required step IDs) consumed by all runners — authoritative, not a runner.

## Where prompt + registry truth lives (canonical resolver: `rte_promptset.py:9-23 prompt_root()`, imported into v5)
Default resolution: env `REPO_TRUTH_EXTRACTOR_PROMPT_ROOT` → legacy `UPGRADES_PROMPT_ROOT` → **`promptsets/v4/prompts/`** (default) → `prompts/v3/` (fallback).
- **Main-phase contract truth (A–Z):** `promptsets/v4/{promptset,artifacts,model_map}.yaml` + `prompt_artifact_coverage_map.json` (also pinned by the gate, validate:32-34).
- **Internal-phase truth:** 4× `registry.json` — `prompts/{prescan,phase_s,phase_s_int,phase_fl_int}/registry.json` (prescan registry is governance-only; real prompts are Python constants in `lib/prescan/grok_passes.py`).
- **`promptsets/generated/dopemux-mvp-2e346e2084bc/`** = GX0 promptgen output (rte_config.py:46-99). **NOT in the default path** — reachable only via env override.

## Top 3 fragmentation risks
1. **Three live runners, one engine.** v5 is terminal, but v3 (consent-gated, still imported by probe/repscan/tools) and the dead `run_extraction.py` coexist. Auditors touching v3 may mistake it for current behavior. Mitigation: treat ONLY v5 as runtime authority; v3 = compat surface.
2. **Bifurcated registry truth.** Main phases governed by `promptsets/v4/*.yaml`; internal phases (prescan/S/S_INT/FL_INT) by separate `registry.json` files; prescan's "prompts" are actually Python constants. No single registry index.
3. **Static vs generated promptset fork.** `promptsets/v4/` (hand-authored, default) vs `promptsets/generated/...` (auto-generated, env-gated). Editing the wrong tree silently no-ops at runtime unless the env var is set.

**Authority used:** runtime code (v3/v4/v5, rte_config, rte_promptset, phases, validate gate), registry/promptset files, README. **Validation:** static read + grep only; NOT_RUN on execution (read-only contract). To human-verify default prompt root: `REPO_TRUTH_EXTRACTOR_PROMPT_ROOT= python services/repo-truth-extractor/run_extraction_v5.py --print-phase-prompts ALL`. **Remaining uncertainty:** runtime selection between v4-contract layer and bare-v5 invocation depends on CLI flags I did not exhaustively enumerate; the generated-promptset activation path (which env value, set by whom) is inferred from `PROMPTGEN_*` constants, not traced to a writer.


---

