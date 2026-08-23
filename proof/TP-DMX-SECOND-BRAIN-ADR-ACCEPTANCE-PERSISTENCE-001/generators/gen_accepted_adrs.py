#!/usr/bin/env python3
"""Generate the ten accepted ADR records from the amended candidate bytes.

Deterministic and fail-closed. Every section of every emitted ADR is a byte-slice
of the candidate document at CANDIDATE_SHA256; nothing is paraphrased, and nothing
is salvaged from the superseded pre-amendment acceptance attempt at 19fa74faa9,
whose ADR files carry the OLD ambiguous AC#2 -- the substantive reason it was
superseded.

Run from the repository root. Writes docs/90-adr/adr-sb-00N-<slug>.md.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

CANDIDATE = Path("docs/03-reference/architecture/second-brain/adr-candidates/"
                 "second-brain-adr-candidates.md")
CANDIDATE_SHA256 = "e4b28946156096319557fd25e0289c5de4b593b6239cc5c7af9b3efed259b66c"
RATIFICATION_BINDING_SHA256 = ("a23efdc676c499cc56b76c5fe321acd0bcf60871be18a33c"
                               "7539e2350ba07b34")
FROZEN_INVENTORY_SHA256 = ("b164fc0b44597a5805aaa7a3f0c6eee047404121bc13bc7a2dc"
                           "d58af7f78a439")
ACCEPTANCE_DATE = "2026-08-14"
NEXT_REVIEW = "2026-11-14"
DISPOSITION_POINTER = ("proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PERSISTENCE-001/"
                       "ADR_OPERATOR_DECISION_LEDGER.yaml")
WORKSHEET_POINTER = ("proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-002/"
                     "04_ADR_DISPOSITION_WORKSHEET.md")

# The amended AC#2, carried verbatim into every accepted record. If this string is
# not found in the candidate exactly ten times the generator refuses to run, which
# is what stops the pre-amendment wording from ever reaching an accepted file.
AMENDED_AC2 = (
    "Machine contracts required by this ADR MUST parse and cover the decision at "
    "ADR acceptance. Required denial fixtures MUST be implemented, executed, and "
    "pass before the affected implementation capability is authorized for "
    "enablement. Absence of not-yet-implemented denial fixtures does not "
    "constitute implementation evidence and does not permit any runtime, "
    "production, or enablement claim."
)
SUPERSEDED_AC2 = "Machine contracts and denial fixtures parse and cover the decision."


def slug(title: str) -> str:
    """Deterministic slug rule, applied uniformly and never hand-shortened.

    Lowercase, every run of non-alphanumerics becomes a single hyphen, trim.
    The superseded attempt hand-shortened ADR-SB-009's slug; one rule, applied
    to all ten, removes that discretion.
    """
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def die(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    raw = CANDIDATE.read_bytes()
    observed = hashlib.sha256(raw).hexdigest()
    if observed != CANDIDATE_SHA256:
        die(f"candidate sha256 {observed} != pinned {CANDIDATE_SHA256}")
    text = raw.decode("utf-8")

    if text.count(AMENDED_AC2) != 10:
        die(f"amended AC#2 appears {text.count(AMENDED_AC2)}x, expected 10")
    if SUPERSEDED_AC2 in text:
        die("pre-amendment AC#2 wording is present in the candidate")
    if "\nstatus: CANDIDATE\n" not in text:
        die("candidate document is not CANDIDATE; it must not be promoted")

    heads = list(re.finditer(r"^## (ADR-SB-(\d{3})): (.+)$", text, re.M))
    if len(heads) != 10:
        die(f"found {len(heads)} ADR sections, expected 10")

    emitted = []
    for i, m in enumerate(heads):
        adr_id, num, title = m.group(1), m.group(2), m.group(3).strip()
        start = m.end()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        body = text[start:end]

        if "**Status:** `PROPOSED`" not in body:
            die(f"{adr_id} is not PROPOSED in the candidate")
        if AMENDED_AC2 not in body:
            die(f"{adr_id} does not carry the amended AC#2")

        # Body below the candidate's own status line, verbatim. The status line is
        # dropped because the accepted record states its own status; everything
        # else is a byte-slice.
        carried = body.split("**Status:** `PROPOSED`", 1)[1].lstrip("\n")

        path = Path("docs/90-adr") / f"adr-sb-{num}-{slug(title)}.md"
        contract = f"schemas/second_brain/contracts/{adr_id}.contract.json"

        doc = f"""---
id: {adr_id}
title: {title}
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '{ACCEPTANCE_DATE}'
last_review: '{ACCEPTANCE_DATE}'
next_review: '{NEXT_REVIEW}'
prelude: {title} (adr) for dopemux Second Brain architecture authority.
status: accepted
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PERSISTENCE-001
    - TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001
---
# {adr_id}: {title}

## Status

* Accepted by the human operator on {ACCEPTANCE_DATE}.

Acceptance makes this an accepted architecture record. **It confers no
implementation, runtime, production, or enablement authority**, and none may be
inferred from it. The implementation-time gates below remain exactly where they
were.

## Authority binding

```text
candidate document      {CANDIDATE.as_posix()}
candidate sha256        {CANDIDATE_SHA256}
ratification binding    {RATIFICATION_BINDING_SHA256}
clause inventory sha256 {FROZEN_INVENTORY_SHA256}
machine contract        {contract}
operator disposition    ACCEPT
disposition ledger      {DISPOSITION_POINTER}
disposition worksheet   {WORKSHEET_POINTER}
```

The decision text below is a byte-slice of the candidate document at the pinned
sha256. It is not a restatement.
{carried.rstrip()}

## Implementation-time gates, unchanged by acceptance

```text
denial fixtures            NOT_IMPLEMENTED
runtime conformance        NOT_RUN
retrieval benchmarks       NOT_RUN
purge completeness         NOT_RUN
multi-project isolation    NOT_RUN
split-brain proof          NOT_RUN
encryption implementation  ABSENT

implementation execution   NOT_AUTHORIZED
runtime enablement         NOT_AUTHORIZED
```
"""
        path.write_text(doc, encoding="utf-8")
        emitted.append({
            "adr_id": adr_id,
            "title": title,
            "path": path.as_posix(),
            "sha256": hashlib.sha256(doc.encode()).hexdigest(),
            "carried_body_is_candidate_substring": carried.rstrip() in text,
            "carries_amended_ac2": AMENDED_AC2 in doc,
            "carries_superseded_ac2": SUPERSEDED_AC2 in doc,
            "contract": contract,
        })

    bad = [e for e in emitted if not e["carried_body_is_candidate_substring"]
           or not e["carries_amended_ac2"] or e["carries_superseded_ac2"]]
    if bad:
        die(f"post-write verification failed for {[e['adr_id'] for e in bad]}")

    print(json.dumps(emitted, indent=2))


if __name__ == "__main__":
    main()
