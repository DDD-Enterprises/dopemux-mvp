#!/usr/bin/env python3
"""Batch-apply domain-specific extraction procedures to all benchmark prompts."""
import re, json, sys
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"

GENERIC_EP = """## Extraction Procedure
1. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
2. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
3. Attach evidence to every non-derived field and every relationship edge.
4. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
5. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
6. Emit exactly the declared outputs and no additional files."""

GENERIC_FM = """## Failure Modes
- Missing input files: emit valid empty containers plus `missing_inputs` list in output items.
- Partial scan coverage: emit partial results with explicit `coverage_notes` and evidence gaps.
- Schema violation risk: drop unverifiable fields, keep item `id` + `evidence` + `UNKNOWN` placeholders.
- Parse/runtime ambiguity: keep all plausible candidates but mark `status: needs_review` with evidence."""

FOUNDATION_STEPS = """6. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files."""

def load_rewrites():
    """Return dict mapping prompt prefix to (domain_steps, extra_failure_modes)."""
    return json.loads((Path(__file__).parent / "rewrite_data.json").read_text())

def apply_rewrite(filepath, domain_steps, extra_fms):
    text = filepath.read_text()
    if "1. Enumerate candidate facts" not in text:
        return False  # already rewritten
    # Build new EP
    new_ep_lines = ["## Extraction Procedure"]
    for i, step in enumerate(domain_steps, 1):
        new_ep_lines.append(f"{i}. {step}")
    n = len(domain_steps)
    # Add foundation steps renumbered
    new_ep_lines.append(f"{n+1}. Legacy Context is intent guidance only and is never evidence.")
    new_ep_lines.append(f"{n+2}. Enumerate candidate facts only from in-scope inputs and upstream artifacts.")
    new_ep_lines.append(f"{n+3}. Build deterministic IDs using stable content keys (path/symbol/name/service_id).")
    new_ep_lines.append(f"{n+4}. Attach evidence to every non-derived field and every relationship edge.")
    new_ep_lines.append(f"{n+5}. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).")
    new_ep_lines.append(f"{n+6}. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.")
    new_ep_lines.append(f"{n+7}. Emit exactly the declared outputs and no additional files.")
    new_ep = "\n".join(new_ep_lines)
    text = text.replace(GENERIC_EP, new_ep)
    # Build new FM
    new_fm = GENERIC_FM
    for fm in extra_fms:
        new_fm += f"\n- {fm}"
    text = text.replace(GENERIC_FM, new_fm)
    filepath.write_text(text)
    return True

def main():
    data = load_rewrites()
    ok, skip, miss = 0, 0, 0
    for fname, info in sorted(data.items()):
        fp = PROMPTS_DIR / fname
        if not fp.exists():
            print(f"MISS: {fname}")
            miss += 1
            continue
        if apply_rewrite(fp, info["steps"], info["failure_modes"]):
            print(f"  OK: {fname}")
            ok += 1
        else:
            print(f"SKIP: {fname} (already rewritten)")
            skip += 1
    print(f"\nDone: {ok} rewritten, {skip} skipped, {miss} missing")

if __name__ == "__main__":
    main()
