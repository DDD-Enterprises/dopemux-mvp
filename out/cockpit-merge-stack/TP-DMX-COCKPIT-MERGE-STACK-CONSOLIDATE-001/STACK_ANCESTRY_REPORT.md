# Stack Ancestry Report

Packet: `TP-DMX-COCKPIT-MERGE-STACK-CONSOLIDATE-001`
Generated: `2026-05-08T01:03:38Z`

Covered PR set after refresh: `{568, 569, 570, 571, 573}`
Declared merge-candidate order remains: `568 -> 569 -> 570 -> 571`

| Base | Head | Ancestor | Exit |
| --- | --- | --- | --- |
| PR568 base branch head | PR568 head | True | 0 |
| PR568 head | PR569 head | True | 0 |
| PR569 head | PR570 head | True | 0 |
| PR570 head | PR571 head | True | 0 |
| PR571 head | this packet branch HEAD before edits | True | 0 |

PR 573 evidence relation: merge commit `c0c32c1639e675d3415257f2444437ae1fa2ea3c` has base parent `b173efd83c871c30f2bd86530921c866d08e7e45` and head parent `1236757c15b1bfdf0926ee476908d56ed71b0dc6`. The proof bundle path is `out/cockpit-runtime-contract-fidelity/TP-DMX-COCKPIT-RUNTIME-CONTRACT-FIDELITY-001/PROOF.json`.

No unexpected divergence or required packet skip was detected from the inspected ancestry chain. PR 573 is covered as reviewed merged evidence and is intentionally excluded from the open stack merge-candidate ancestry chain.
