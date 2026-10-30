# Grok final audit - run record (MACRO-DMX-PULSE-001)

**Subject**: `feat/pulse-001` @ `1d2219e8c894c5929ceba6ac5f2650dfe7ba2147`, base `95e95bee88cae5e6c95e6e34f7c28bb423ad9496`, frozen diff sha256 `aebcd086d35b262bd1a6b6bb59135cafec63f0186a9ede345e017bdcf27858b4` (8 files, +1174).
**Route**: operator-approved ("Approve the grok-cli grok-4.5 audit for MACRO-DMX-PULSE-001 instead of agy ... verified tool-less recipe ... no secrets"). Tool `grok-cli` 1.0.67, model `grok-4.5`.
**Launched**: 2026-10-22T11:24:24Z. **Exit**: 0.

## Observations the coordinator made at the time (attested, see EVIDENCE LOST)

- Probe 1 (`--tools ""`): the init event still listed 24 tools, so that flag does not contain the model.
- Probe 2 (deny list rebuilt from Grok's own `init.tools` plus a no-skills system prompt): `init.tools == []`.
- Audit run, from the stream: `init.model == grok-4.5`, `init.tools == []`, 1 turn, about 200 s, about USD 0.0436, exit 0, stderr empty.
- The model self-reported `grok-4` and `tools_used: none`.
- Input was a sealed directory holding only `AUDIT_PROMPT.txt` and `frozen.diff`. No repo mount and no secrets.

## Reproducibility checks done after the fact

- `GROK_frozen.diff` was regenerated from git for `95e95bee88cae5e6c95e6e34f7c28bb423ad9496..1d2219e8c894c5929ceba6ac5f2650dfe7ba2147`: sha256 matches the original, `aebcd086...58b4`.
- `GROK_AUDIT_PROMPT.txt` was regenerated with the original generator: 52805 bytes, sha256 `3e0510feceb6c9578e73d350933bb0288219fdc8ac7fac1bafe337be10e6ce69`; the prefix and size match the originals recorded at the time.
- `GROK_AUDIT_RESPONSE.txt` is a transcription of the response from the session transcript (the model's JSON). Its length, 11435 bytes, equals the original file's size. The original file's sha256 was not recorded, so byte identity is UNKNOWN.

## EVIDENCE LOST

The session scratchpad was deleted before these were copied into the repo. They are NOT in this bundle:

- `grok_out.jsonl` (raw event stream, the only machine evidence of `init.tools == []`)
- `grok_err.txt`, `grok_exit.txt`, `launched_at.txt`, `INVOCATION.sh`, `DISALLOWED.txt`
- `probe_out.jsonl`, `probe2_out.jsonl` (the two containment probes)
- the original `AUDIT_RESPONSE.txt` bytes and the agy attempt's raw files

Consequence: containment of the Grok run is the coordinator's attestation, not independently reproducible from this bundle. The operator should weigh that before attesting `independence: PROVEN`, or rerun the audit (a rerun needs a newly approved route).
