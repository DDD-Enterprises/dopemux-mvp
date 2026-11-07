# AGY message cap found by the size probe, 2026-11-04

Filler prompt 879,525 bytes, AGY 1.5.0, gemini-4-argon-high, conversation d2052f73-7b58-4695-b02a-3341542c1ef5.

- CLI log: promptLength=879524 accepted. Exit 0, status SUCCESS, reply {"size_probe":"OK"}, stderr empty.
- steps table: step 0 stores the whole prompt (both filler markers present).
- gen_metadata (the request record): 191,986 bytes of the prompt kept, then the literal text "<truncated 687943 bytes>".
- Usage: 74,939 input tokens. Same filler on Grok: 247,559. Kept 22% of filler (about 54K) plus the system prompt (about 20K) fits 75K.
- Comparison: PR 1486 r8, 188,058-byte prompt, AGY 1.4.12: no marker in gen_metadata.
- No error, warning or nonzero exit signals the cut. The reply proves nothing because the instruction sits at the head as well as the tail.

Effect: the frozen 879 KB audit prompt cannot reach AGY whole in one message. The AGY attempt is unspent.
Custody: custody/agy-probe-d2052f73.db and custody/cli-20261104_061325.log (email not yet redacted; redact before any repo copy).

Earlier AGY runs are a separate check and are not part of this bundle.
