---
packet_id: RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001
recommendation_id: R-OPUS-8
finding_label: HIGH-1
base_branch: main
base_ref: origin/main
worktree_path: /Users/hue/code/dopemux-mvp-rte-prelive-validator-error-shape
branch: codex/rte-prelive-validator-error-shape
status: in_progress
id: RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001
title: Rte Ux Pkt Prelive Validator Error Shape 001
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: Rte Ux Pkt Prelive Validator Error Shape 001 (explanation) for dopemux documentation
  and developer workflows.
---
# Task Packet — RTE UX Pre-Live Validator Error Shape

This task packet uses a Markdown transport because the requested artifact path is
`.md`. The fenced JSON payload below is the canonical schema payload for
validation against
`docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`.

```json
{
  "id": "RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001",
  "project": "dopemux-mvp",
  "target": "Improve operator-facing pre-live validator failure output so blocked live runs surface verdict, reason codes, output directory, sanitized stderr, and a safe next step without changing live-gate semantics.",
  "invariants": [
    "Failure-shape cleanup only.",
    "Preserve live-gate logic and verdict behavior.",
    "Preserve DPMX_LIVE_OK semantics.",
    "Preserve validator command construction and authorization boundaries.",
    "Do not bypass, weaken, relax, reorder, or skip pre-live validation.",
    "Do not change live execution consent requirements.",
    "Do not change provider behavior.",
    "Do not perform provider calls.",
    "Do not run live extraction.",
    "Do not run live preflight.",
    "Do not change routing, pricing, promptsets, or schemas.",
    "Do not implement DPMX_LIVE_OK hint or deprecation work.",
    "Do not implement run-help progressive disclosure.",
    "Do not start packet 5 or other follow-on packets.",
    "HIGH-1 remains valuation-derived unless the missing Opus source audit bundle exists locally.",
    "Runtime/source truth governs behavior claims."
  ],
  "depends_on": [
    "RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001",
    "RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001",
    "RTE-UX-PKT-CLAUDE-RTE-SAFETY-PROOF-CLEANUP-001",
    "RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001",
    "RTE-UX-VAL-001"
  ],
  "repo_binding": {
    "project_id": "dopemux-mvp",
    "repo_marker": ".dopetaskroot",
    "origin_hint": "https://github.com/DDD-Enterprises/dopemux-mvp.git",
    "require_identity_match": true
  },
  "series": {
    "id": "RTE-UX-PRELIVE-VALIDATOR-ERROR-SHAPE",
    "base_branch": "origin/main",
    "parent_tp_id": "RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001",
    "final_packet": false
  },
  "execution": {
    "agent": "codex",
    "branch": "codex/rte-prelive-validator-error-shape",
    "base_branch": "origin/main"
  },
  "commit": {
    "message": "RTE UX prelive validator error shape",
    "allowlist": [
      "services/repo-truth-extractor/run_extraction_v5.py",
      "services/repo-truth-extractor/tests/test_run_extraction_v5_validator.py",
      "task-packets/RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001.md",
      "out/rte-ux-prelive-validator-error-shape/RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001_AUDIT_NOTE.md",
      "proof/rte-ux/RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001/PROOF.json"
    ],
    "verify": [
      "python -m json.tool proof/rte-ux/RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001/PROOF.json >/dev/null",
      "python - <<'PY'\nimport json, re\nfrom pathlib import Path\nfrom jsonschema import Draft7Validator\npacket = Path('task-packets/RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001.md').read_text()\nmatch = re.search(r'```json\\n(.*?)\\n```', packet, re.S)\nassert match, 'missing fenced json payload'\npayload = json.loads(match.group(1))\nschema = json.loads(Path('docs/03-reference/spec/dopetask/dopetask-canonical-spec.json').read_text())\nerrors = sorted(Draft7Validator(schema).iter_errors(payload), key=lambda e: list(e.path))\nif errors:\n    raise SystemExit('\\n'.join('%s: %s' % (('/'.join(map(str, e.path)) or '<root>'), e.message) for e in errors))\nprint('PASS task packet payload schema validation')\nPY",
      "git diff --check",
      "git diff --name-only origin/main...HEAD",
      "git diff --name-only origin/main...HEAD | rg '^(promptsets/|schemas/)' && exit 1 || true",
      "git diff --name-only origin/main...HEAD | rg '(^|/)(routing|pricing|provider).*\\.(py|yaml|yml|json)$|src/dopemux/(routing_config|litellm_proxy|profile_models|claude_config)\\.py' && exit 1 || true",
      "git diff --name-only origin/main...HEAD | rg 'RTE-UX-PKT-RUN-HELP-PROGRESSIVE-DISCLOSURE-001|RTE-UX-PKT-UX-DOC-CLEANUP-001|RTE-UX-PKT-DPMX-LIVE-OK-HINTS-001' && exit 1 || true",
      "pytest services/repo-truth-extractor/tests/test_run_extraction_v5_validator.py -q --no-header",
      "python -m compileall -q src services tests",
      "pre-commit run --files services/repo-truth-extractor/run_extraction_v5.py services/repo-truth-extractor/tests/test_run_extraction_v5_validator.py task-packets/RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001.md out/rte-ux-prelive-validator-error-shape/RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001_AUDIT_NOTE.md proof/rte-ux/RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001/PROOF.json"
    ]
  },
  "pr": {
    "title": "RTE UX prelive validator error shape",
    "body": "## Summary\n- make pre-live validator blocks print structured, procedural failure detail\n- preserve live-gate command construction, consent semantics, verdict behavior, providers, routing, pricing, promptsets, and schemas\n- add focused no-provider tests for structured NO_GO, malformed stdout, and missing reason-code paths\n\n## Validation\n- proof JSON syntax\n- embedded task-packet schema validation\n- focused validator formatting tests\n- compileall\n- diff/scope guards\n- pre-commit on touched files when safe",
    "base": "main"
  },
  "pal_chain": {
    "enabled": false,
    "steps": [
      "analyze",
      "thinkdeep",
      "challenge",
      "planner",
      "challenge",
      "implement",
      "codereview",
      "precommit",
      "challenge"
    ]
  },
  "steps": [
    {
      "id": "S1",
      "task": "Verify PR #645 merge gate and refresh the existing packet-4 branch onto current origin/main without mutating the dirty primary checkout.",
      "requirements": [
        "Fetch origin/main.",
        "Verify PR #645 is merged, non-draft, based on main, and has merge commit b2558dfbc931f59d6dc338c63a8cc5d97ed592a0.",
        "Verify the PR #645 merge commit is an ancestor of origin/main.",
        "Create a backup branch before rebase.",
        "Stop if the local commit contains unexpected paths."
      ],
      "validation": [
        "gh pr view 645 --json state,isDraft,mergedAt,mergeCommit,baseRefName,url",
        "git merge-base --is-ancestor b2558dfbc931f59d6dc338c63a8cc5d97ed592a0 origin/main",
        "git diff --name-only origin/main...HEAD"
      ]
    },
    {
      "id": "S2",
      "task": "Inspect authority, valuation artifacts, prior packet proof/audit artifacts, and runtime validator failure paths before implementation.",
      "requirements": [
        "Treat HIGH-1 as valuation-derived if the Opus source audit bundle is absent.",
        "Identify where validator stdout, stderr, verdict, reason_codes, and output_dir are parsed.",
        "Identify how subprocess failure becomes RuntimeError or parser.error.",
        "Do not assume the Click CLI owns this surface if runtime evidence disagrees."
      ],
      "validation": [
        "Authority and runtime files listed in the proof JSON.",
        "Audit note records source audit bundle presence and preserved UNKNOWNs."
      ]
    },
    {
      "id": "S3",
      "task": "Implement deterministic pre-live validator block formatting while preserving gate behavior.",
      "requirements": [
        "Same validator command and subprocess invocation.",
        "Same enforcement conditions and live consent behavior.",
        "No provider calls, live extraction, live preflight, routing, pricing, promptset, or schema changes.",
        "Malformed stdout remains blocked fail-closed and does not hide stderr."
      ],
      "validation": [
        "Focused unit tests stub subprocess.run and assert structured NO_GO, malformed stdout, and missing reason-code failure shapes.",
        "Diff review confirms touched runtime changes are failure-message formatting only."
      ]
    },
    {
      "id": "S4",
      "task": "Validate scope, proof, tests, and precommit status before closeout.",
      "requirements": [
        "Create audit note and proof JSON.",
        "Validate proof JSON and embedded packet JSON.",
        "Run focused tests, compileall, diff checks, scope guards, and pre-commit where safe.",
        "Do not push or open a PR."
      ],
      "validation": [
        "python -m json.tool proof/rte-ux/RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001/PROOF.json >/dev/null",
        "Embedded packet JSON validates against docs/03-reference/spec/dopetask/dopetask-canonical-spec.json",
        "pytest services/repo-truth-extractor/tests/test_run_extraction_v5_validator.py -q --no-header",
        "python -m compileall -q src services tests",
        "git diff --check",
        "pre-commit run --files <all touched files>"
      ]
    }
  ]
}
```

## Objective

Improve the operator-facing failure surface when the pre-live validator blocks live
execution so blocked runs fail with structured, procedural detail (verdict, reason
codes, output directory, sanitized validator stderr, next safe action) instead of
collapsing into a single-line `RuntimeError` / `parser.error` message.

This packet is failure-shape cleanup only. It does not relax the pre-live gate, it
does not change verdict semantics in any operator-visible way, and it does not
invoke any provider/network surface.

## Authority Order

Authority precedence read for this packet (in order, evidence-first):

1. `AGENTS.md`
2. `.claude/PROJECT_INSTRUCTIONS.md`
3. `.claude/brand-voice-guidelines.md`
4. `docs/03-reference/governance/rules.md`
5. `docs/03-reference/truth/truth-canonicals.md`
6. `docs/03-reference/truth/truth-scope.md`
7. `docs/03-reference/systems/system-boundaries.md`
8. `docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md`
9. `out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_*` artifacts (accepted scope,
   packet sequence, valuation matrix, remaining unknowns, manifest, attestation).
10. Prior packet artifacts on `origin/main`:
    - `proof/rte-ux/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001/PROOF.json`
    - `proof/rte-ux/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001/PROOF.json`
    - `proof/rte-ux/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001/PROOF.json`
    - matching audit notes under `out/rte-ux-*`.

Important authority drift recorded in this packet: the
valuation matrix names the failing surface as a `ClickException` collapse in the
CLI wrapper, but the live runtime in `src/dopemux/cli.py` does not host the
pre-live validator path — the validator is built and invoked entirely inside
`services/repo-truth-extractor/run_extraction_v5.py` (argparse based, not
click-based). `src/dopemux/cli.py` is therefore intentionally not touched.

## Allowlist

Files this packet is allowed to modify, create, or delete:

- `services/repo-truth-extractor/run_extraction_v5.py`
  - Add a structured formatter for pre-live validator block messages.
  - Update `enforce_pre_live_validator_for_execution` to emit the structured
    block to stderr before raising a short single-line `RuntimeError` whose
    structured detail does not get mangled by the line-prefixing logger.
  - Update the secondary `run_pre_live_validator` call site (validator-first
    preset flow) so blocked runs print the same structured block (parsed from
    the validator stdout payload) to stderr before `parser.error(...)`.
  - Tighten the malformed-stdout path to fail-closed and explicitly say so.
- `services/repo-truth-extractor/tests/test_run_extraction_v5_validator.py`
  - Add focused unit tests for the formatter and for both call sites'
    integration paths using monkeypatched `subprocess.run`.
- `task-packets/RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001.md` (this file).
- `out/rte-ux-prelive-validator-error-shape/RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001_AUDIT_NOTE.md`
- `proof/rte-ux/RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001/PROOF.json`

## Forbidden Files / Directories

- `promptsets/**`
- `schemas/**`
- Provider clients (e.g., gemini, openai, anthropic, xai, openrouter modules).
- Routing / pricing / provider config code paths.
- `services/repo-truth-extractor/validate_pre_live_gate_v25.py` — verdict logic
  inside the validator itself is out of scope.
- `src/dopemux/cli.py` — evidence shows the validator path is not invoked from
  the click CLI; the valuation matrix's "ClickException" framing is treated as
  valuation-derived, not runtime-grounded.
- `docs/03-reference/**`, `docs/02-how-to/**`, README files, `.claude/**`,
  `AGENTS.md` — no doc/tutorial prose edits in this packet.
- Tests outside the focused RTE validator path.
- Any artifacts for follow-on packets
  (`RTE-UX-PKT-RUN-HELP-PROGRESSIVE-DISCLOSURE-001`,
   `RTE-UX-PKT-UX-DOC-CLEANUP-001`,
   `RTE-UX-PKT-DPMX-LIVE-OK-HINTS-001`,
   any `ACCEPT_LATER` item).

## Implementation Steps

1. Add a pure helper `format_pre_live_validator_block(...)` in
   `run_extraction_v5.py` that takes normalized inputs (verdict, optional
   reason codes, optional output dir, optional sanitized stderr text, parse
   error flag, optional artifact path, optional next-step hint) and returns a
   multi-line operator-facing string.
2. Add a thin emit helper `_emit_pre_live_validator_block` that writes the
   structured block to `sys.stderr` with a trailing newline and flush. The
   logger format `[%(levelname)s] %(message)s` prefixes only the first line
   of a multi-line message; writing structured detail directly to stderr keeps
   each line unprefixed and readable, while leaving the subsequent
   `logger.error("%s", exc)` log entry single-line and backward-compatible.
3. Update `enforce_pre_live_validator_for_execution`:
   - Run the validator command as today (no change to command construction or
     `subprocess.run` arguments).
   - Detect malformed validator stdout (`json.loads` raises) and set a
     `parse_error` flag.
   - Compute verdict using existing logic, but treat `parse_error` as
     fail-closed (block) even if returncode is zero. This is a defensive
     tightening required by the packet ("Do not treat malformed output as
     GO"). It does not introduce any new GO path; it only ensures the
     pre-existing fail-closed contract holds on every input.
   - When blocking, build the structured block via the new helper, sanitize
     stderr via existing `sanitize_text_for_output`, emit to stderr, and raise
     a short single-line `RuntimeError`.
4. Update the secondary call site in `main()` that runs `run_pre_live_validator`
   for the validator-first preset flow:
   - Parse `validator_payload["stdout"]` to extract verdict, reason codes, and
     output dir when available.
   - Emit the same structured block to stderr referencing the persisted
     `PRELIVE_VALIDATOR_RESULT.json` artifact path (`dirs["root"]`).
   - Keep `parser.error(...)` as the final exit path with a short message; do
     not bury stdout/stderr from the validator.
5. Do not change `should_enforce_pre_live_validator`, the validator command
   construction, the gate dispatch in `main()`, the `--skip-pre-live-validator`
   semantics, the `DPMX_LIVE_OK` consent semantics, or any provider/network
   behavior.
6. Add focused tests using monkeypatched `subprocess.run` / `capsys` to verify:
   a. Structured `NO_GO` payload yields a block with verdict, reason codes,
      and output dir, then raises.
   b. Malformed stdout with stderr yields a block whose `parse_status` line
      explicitly states the output was unparseable and surfaces stderr; gate
      remains fail-closed.
   c. Missing/empty `reason_codes` still produces a clear fail-closed message
      with `none reported`.
   d. Helper is unit-testable in isolation without any subprocess.

## Validation Plan

- `python -m json.tool` the proof JSON.
- Validate the embedded task-packet JSON against the canonical dopetask schema.
- `python -m compileall -q src services tests`.
- Focused test:
  `pytest services/repo-truth-extractor/tests/test_run_extraction_v5_validator.py
   -q --no-header`.
- `git diff --check`, `git status --short`, `git diff --name-only` scope check.
- Grep guard: no edits to `promptsets/**`, `schemas/**`, provider modules,
  routing config, `src/dopemux/cli.py`.
- Grep guard: no edits referencing follow-on packet ids outside valuation /
  sequencing context.
- Grep guard: primary checkout `/Users/hue/code/dopemux-mvp` is not modified.

## Proof Plan

`proof/rte-ux/RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001/PROOF.json` will
contain the fields enumerated in the implementer prompt (base_branch,
base_ref, branch, worktree_path, primary_checkout_path,
primary_checkout_modified, head_before, proof_commit_capture_note, PR gates
640/643/644/645, origin_main_head_verified, source_audit_bundle_present,
valuation_artifacts_read, authority_files_read, runtime_files_inspected,
files_touched, validator_failure_strings_changed, tests_added_or_updated,
forbidden_paths_touched, runtime_dispatch_changed,
validator_verdict_logic_changed, live_gate_semantics_changed,
provider_calls_run, live_extraction_run, live_preflight_run,
promptsets_changed, schemas_changed, pricing_or_routing_changed,
dpmx_live_ok_semantics_changed, help_progressive_disclosure_changed,
future_packets_started, unknowns_preserved, validation_commands,
validation_results, commit_plan, rollback_plan).

## Commit Plan

Single commit on `codex/rte-prelive-validator-error-shape` with the message:

```
RTE UX prelive validator error shape
```

Staged files only — task packet, runtime change, tests, audit note, proof.
No push, no PR from this packet.

## Rollback Plan

`git reset --hard origin/main` on the worktree (followed by
`git worktree remove`) cleanly removes all changes. No state outside the
worktree is mutated.

## Live-Gate Preservation Statement

The pre-live validator's command construction, dispatch conditions, and verdict
semantics in the operator-visible sense are preserved. The only verdict-related
change is making the malformed-stdout edge case explicitly fail-closed (it was
previously fail-OPEN only when both `returncode == 0` AND stdout was unparseable;
that combination is implausible against the real validator but the packet asks
for fail-closed). This is a tightening of safety, not a relaxation, and adds no
new GO path. `DPMX_LIVE_OK` semantics and `--skip-pre-live-validator` semantics
are untouched.
