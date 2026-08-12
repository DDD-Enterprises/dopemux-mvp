# Independent-audit route discovery — supervisor-directed continuation

Supervisor disposition (2026-08-12) ruled the prior audit (Claude Code `quality-engineer`
subagent) `LIMITED` independence — same runtime/company family as the implementer
(Claude Code / Sonnet 5) — and required a genuinely different-family/runtime L3 audit
before the packet can claim `PASS_WITH_NONBLOCKING_RISKS_READY_FOR_PROOF_CLOSURE`.

Preferred route order from the supervisor: (1) AGY + non-Anthropic model, (2) Gemini CLI,
(3) CommandCode + non-Anthropic family, (4) another approved route. Each was live-probed
in order; requested/configured/claimed identities recorded below verbatim.

## Route 1 — AGY (`/Users/hue/.local/bin/agy`, v1.1.12) — REJECTED, non-functional

```
$ agy --version
1.1.12

$ agy models
gemini-3.6-flash-high	Gemini 3.6 Flash (High)
gemini-3.6-flash-medium	Gemini 3.6 Flash (Medium)
gemini-3.6-flash-low	Gemini 3.6 Flash (Low)
gemini-3.5-flash-high	Gemini 3.5 Flash (High)
gemini-3.5-flash-medium	Gemini 3.5 Flash (Medium)
gemini-3.5-flash-low	Gemini 3.5 Flash (Low)
gemini-3.1-pro-high	Gemini 3.1 Pro (High)     <-- packet-preferred selector, listed
gemini-3.1-pro-low	Gemini 3.1 Pro (Low)
claude-sonnet-4-6	Claude Sonnet 4.6 (Thinking)
claude-opus-4-6-thinking	Claude Opus 4.6 (Thinking)
gpt-oss-120b-medium	GPT-OSS 120B (Medium)
```

`gemini-3.1-pro-high` (the packet's stated-preferred selector) is listed as available.
However, invoking it in print mode does not process the supplied prompt at all — it
returns a fixed self-description regardless of prompt content:

```
$ agy --print --model gemini-3.1-pro-high "What is 2+2? Reply with only the number."
You are currently using the **Gemini 3.1 Pro** model.
Let me know if there's anything else you'd like to do!

$ agy --print --model gemini-3.1-pro-high "List the files in the current working directory."
You are currently chatting with the Gemini 3.1 Pro model. Let me know how I can help you!
```

Repeated with distinct prompts (file-read request, arithmetic, directory listing) — every
response is a variant of "I am Gemini 3.1 Pro", never engaging with the actual request.
This is the same class of failure noted in a prior session's memory record (local Grok
CLI could select `grok-4.5-build` and reported it, but the route was non-functional).
**Route rejected: model selects but does not process input.**

## Route 2 — native Gemini CLI (`/opt/homebrew/bin/gemini`, v0.46.0) — REJECTED, hard error

```
$ gemini -m gemini-3.1-pro-high -p "What is 2+2? Reply with only the number."
...
An unexpected critical error occurred: IneligibleTierError: This client is no longer
supported for Gemini Code Assist for individuals. To continue using Gemini, please
migrate to the Antigravity suite of products: https://antigravity.google
    at throwIneligibleOrProjectIdError (.../chunk-RCJSF5RP.js:307474:11)
    at _doSetupUser (.../chunk-RCJSF5RP.js:307463:5)
```

Exit code 1. This is a genuine, provable auth/tier failure (free-tier client deprecated),
not a configuration ambiguity. **Route rejected: hard error, unusable.**

## Route 3 — CommandCode (`/Users/hue/.local/share/mise/installs/node/25/bin/commandcode`,
v1.17.0) — ACCEPTED, functional, genuinely independent model families available

```
$ commandcode --list-models
Available models · 52 models
Open Source: deepseek/deepseek-v4-pro, deepseek/deepseek-v4-flash (default),
  moonshotai/kimi-*, zai-org/glm-*, minimaxai/minimax-*, qwen/qwen3.*, ...
Anthropic: claude-sonnet-5, claude-sonnet-4-6, claude-fable-5, claude-opus-5
OpenAI: gpt-5.4, gpt-5.3-codex, gpt-5.4-mini
Google: google/gemini-3.6-flash, google/gemini-3.5-flash, ...
Sakana / Meta / xAI: fugu-ultra, muse-spark-*, grok-4.5
```

Verified functional (reads real files, runs real shell commands, produces contextual
non-canned answers):

```
$ commandcode -p "Read the file task-packets/TP-DMX-TRUST-GATE-FAIL-CLOSED-001.md ... reply with exactly its first heading line" \
    --model gpt-5.3-codex --no-session --trust
# TP-DMX-TRUST-GATE-FAIL-CLOSED-001 - DCP Evidence Completeness and False-Ready Repair
```

`gpt-5.3-codex` (OpenAI) selected — a genuinely different vendor/family/runtime from both
the implementer (Claude Code / Sonnet 5) and the prior limited-independence auditor
(Claude Code `quality-engineer` subagent). **Route accepted.**

## Selector discipline note

`--yolo`/`--dangerously-skip-permissions` is required for CommandCode to execute shell
commands in non-interactive `-p` mode (`--trust` alone only skips the initial project-trust
prompt, not per-tool-call permission gating). This was invoked deliberately, scoped to a
single read-only-instructed audit session, with the auditor explicitly told not to mutate
any files, and worktree cleanliness (`git status --porcelain`) verified clean before and
after the run.

A CLI quirk was discovered and is recorded for accuracy: resuming a CommandCode session
via `--session <id>` without re-passing `--model` silently falls back to the CLI's
*default* model (`deepseek/deepseek-v4-flash`) rather than continuing on the
originally-selected model. This was not anticipated when the audit was split across an
initial evidence-gathering turn and a "continue" turn to elicit the full written report.
The practical effect: the audit's evidence-gathering phase (diff review, full source read,
first pytest run) executed on `gpt-5.3-codex`; the continuation phase (additional repros —
CLAIMED-state edge case, last-writer-wins comparison, baseline-failure range trace,
adversarial PASS-path hunt — and the final written report) executed on
`deepseek/deepseek-v4-flash`. Both are confirmed via the CLI's own `model_request_start`
event metadata (ground truth), not the model's self-report text. **Both segments are
non-Anthropic and satisfy different-family/runtime independence from the implementer**;
the split was an accidental CLI default-fallback, not a deliberate multi-model design, and
is disclosed here for full transparency.

## Self-report reliability caveat

The `deepseek/deepseek-v4-flash`-backed continuation's final report opens with: "Model
family/runtime (self-report): Anthropic Claude (Claude Sonnet 5)... invoked via
`command-code` CLI session." **This self-report is factually wrong** — the CLI's own
`model_request_start` event for every request in that turn records
`"model":"deepseek/deepseek-v4-flash"`, never Claude. This is recorded here as a materially
important finding in its own right: the model hallucinated its own identity. The proof
record uses the ground-truth API metadata, not the model's self-description, as the
authoritative identity source — consistent with this packet's own governing principle
(claimed identity is not proof of identity; only positively observed evidence is).
