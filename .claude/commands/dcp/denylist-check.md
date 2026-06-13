---
description: "DCP regression gate: red-lane scanner + denied-route token sweep + denylist tests; output paste-ready for COMMAND_LOG.md"
arguments: "[--files <paths>] [--base <ref>]"
allowed-tools: ["Bash", "Read", "Grep", "Glob"]
model: "claude-sonnet-4-5"
---

# /dcp:denylist-check — DCP Regression Gate

Packet-grade regression gate for the DCP read-only facade. Runs the three checks
that every TP-DCP-MCP-RO-XXXX packet requires and formats output for direct paste
into `COMMAND_LOG.md`.

Use before filing slice notes on any packet that touches facade adapters, the
route manifest, or files near the red-lane seam.

---

## Phase 1 — Determine File Set

- `--files <paths>` → use exactly those files (space-separated)
- Otherwise, changed files vs `--base` (default `origin/main`):
  ```bash
  git diff --name-only $(git merge-base origin/main HEAD)..HEAD
  git status --porcelain   # also include dirty (unstaged) files
  ```
  Combine and deduplicate the two lists.

---

## Phase 2 — Red-Lane Gate

Run the canonical engine — do not reimplement:
```bash
PYTHONPATH=src python -m dopemux.dcp.red_lane_scanner \
  --repo-root . \
  --files <file1> <file2> ... \
  [--proof-paths proof/<TP-ID>/PROOF.json \
   --expected-sha $(git rev-parse HEAD)]
```

Exit 0 = PASS. Exit 1 = BLOCKED/UNKNOWN/CONFLICTING.

**Important**: UNKNOWN without `--proof-paths` is the scanner's documented fail-closed
default — when no proof path is provided, label it
`UNKNOWN (no proof supplied — expected pre-proof)` rather than treating it as a diff failure.
Include `--proof-paths` if a proof bundle exists for this packet.

---

## Phase 3 — Token Sweep

Extract `DENIED_TOKENS` at runtime from `route_manifest.py` — never copy the list:
```bash
python -c "
import importlib.util as u
s = u.spec_from_file_location('rm',
  'services/dcp-readonly-facade/src/dcp_facade/route_manifest.py')
m = u.module_from_spec(s)
s.loader.exec_module(m)
print('\n'.join(m.DENIED_TOKENS))
"
```

Then search across the facade source:
```bash
rg -n '<token>' services/dcp-readonly-facade/src/dcp_facade/
```
(One `rg` call per token, or combine with alternation.)

Classify every hit:
| Location | Classification |
|----------|----------------|
| `route_manifest.py` | ✅ **acceptable** — denylist data |
| `tests/` | ✅ **acceptable** — assertions |
| Docstring / comment in adapter | ⚠️ **acceptable-with-eyeball** — list it; human confirms |
| Any other line in `src/dcp_facade/*.py` | ❌ **VIOLATION** |

The token list comes from the runtime import. If `route_manifest.py` changes, this
sweep automatically reflects it — do not hardcode the list.

---

## Phase 4 — Denylist Tests

```bash
python -m pytest -q services/dcp-readonly-facade/tests/test_route_denylist.py
```
Report pass/fail count.

---

## Phase 5 — Report

**Summary table** (three rows):
| Gate | Result | Notes |
|------|--------|-------|
| Red-lane scan | PASS / FAIL / UNKNOWN | exit code N |
| Token sweep | PASS / VIOLATION | N tokens, N hits |
| Denylist tests | PASS / FAIL / NOT_RUN | N passed |

**COMMAND_LOG block** (paste directly into the packet's `COMMAND_LOG.md`):
````
```
## /dcp:denylist-check — <date>

### Phase 2: Red-lane scan
$ PYTHONPATH=src python -m dopemux.dcp.red_lane_scanner --repo-root . --files <files>
exit: <n>
result: <PASS/UNKNOWN/BLOCKED>

### Phase 3: Token sweep
$ python -c "..." | xargs rg -n ...
result: <PASS/VIOLATION>
<list any violations: token, file:line>

### Phase 4: Denylist tests
$ python -m pytest -q services/dcp-readonly-facade/tests/test_route_denylist.py
exit: <n>
result: <N passed / N failed>
```
````

---

## Error Handling

- `red_lane_scanner` module not found → FAIL Phase 2 with `PYTHONPATH=src python -m dopemux.dcp.red_lane_scanner: module not importable`
- `rg` (ripgrep) not available → fall back to `grep -rn` for token sweep; note the fallback
- `route_manifest.py` not importable → FAIL Phase 3 — do not proceed with token sweep using a hardcoded list

---

## Notes for Claude

- The token list **must** come from the runtime import of `route_manifest.py`. Never
  hardcode it — that's a drift hazard.
- UNKNOWN in Phase 2 without proof-paths is expected before a proof bundle exists.
  Only flag it as a problem when proof-paths are provided and the scanner still returns
  non-zero.
- This command is read-only — it never modifies the manifest, adapters, or tests.
- Model: `claude-sonnet-4-5` per routing policy.
