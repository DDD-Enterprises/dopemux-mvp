"""Grounding primitives shared by the census generator.

The validator carries its own independent implementation of the same rules.
That duplication is deliberate: two implementations agreeing is stronger
evidence than one shared helper that both sides trust by construction.
"""

from __future__ import annotations

import hashlib
import re

# Longest separators first, or ", and " gets consumed by ",\s*" and leaves
# "and Purge" as a token.
_SEP = re.compile(
    r"\s*,\s+and\s+|\s*,\s+or\s+|\s*,\s*|\s+and\s+|\s+or\s+|\s+plus\s+|\s*/\s*"
)
_NONWORD = re.compile(r"[^A-Za-z0-9]+")

NUMBER_WORDS = {
    0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
    6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
}

ALLOWED_SECTIONS = {"CONTEXT", "PROPOSED_DECISION", "MA06_AMENDMENT", "CONSEQUENCES"}

# Subsection headings whose text may never ground a clause.
FORBIDDEN_SUBSECTIONS = (
    "Rejected alternatives",
    "Evidence and traceability",
    "Acceptance conditions",
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize(text: str) -> str:
    """UPPER_SNAKE projection used for token grounding."""
    return _NONWORD.sub("_", text).strip("_").upper()


def tokenize_enumeration(text: str) -> list[str]:
    """Split a verbatim enumeration into its members, deterministically."""
    return [p.strip() for p in _SEP.split(text) if p.strip()]


def adr_allowed_span(candidate: str, adr_id: str) -> str:
    """Text of one ADR minus its rejected-alternatives/evidence/acceptance parts.

    Returns Context + Proposed decision (which contains the MA-06 amendment)
    + Consequences, concatenated.  A fragment must be a substring of this.
    """
    start = candidate.find(f"\n## {adr_id}:")
    if start < 0:
        raise ValueError(f"{adr_id}: section not found in candidate")
    nxt = candidate.find("\n## ", start + 1)
    block = candidate[start : nxt if nxt >= 0 else len(candidate)]

    keep: list[str] = []
    current_ok = True
    for line in block.splitlines():
        if line.startswith("### "):
            current_ok = line[4:].strip() not in FORBIDDEN_SUBSECTIONS
        if current_ok:
            keep.append(line)
    return "\n".join(keep)


def check_fragment(fragment: str, allowed_span: str, candidate: str) -> str | None:
    if fragment not in candidate:
        return "not a verbatim substring of the candidate document"
    if fragment not in allowed_span:
        return (
            "present in the candidate but outside this ADR's Context / Proposed "
            "decision / Consequences span (rejected alternatives, evidence and "
            "acceptance conditions may not ground a clause)"
        )
    return None


def check_grounding(clause: dict) -> str | None:
    """Return an error string when a clause's machine value is not grounded.

    BOOLEAN values carry no text to match; they are protected instead by the
    const-pinned inventory hash, which is what closes the bilateral-edit class.
    """
    rt = clause["rule_type"]
    op = clause["operator"]
    val = clause["machine_value"]
    joined = "\n".join(clause["source_fragments"])
    norm_text = normalize(joined)

    if rt == "BOOLEAN":
        if op != "EQUALS" or not isinstance(val, bool):
            return "BOOLEAN clauses must be EQUALS with a true/false value"
        return None

    if rt == "NUMERIC":
        if op not in ("EQUALS", "LESS_THAN_OR_EQUAL") or isinstance(val, bool) \
                or not isinstance(val, int):
            return "NUMERIC clauses must be EQUALS/LESS_THAN_OR_EQUAL with an int"
        word = NUMBER_WORDS.get(val)
        low = joined.lower()
        if str(val) not in joined and (word is None or word not in low):
            return f"numeric value {val} appears in no cited fragment"
        return None

    if rt in ("ENUM", "AUTHORITY_TARGET") and op == "SET_EQUALS":
        enumeration = clause.get("source_enumeration")
        if not enumeration:
            return "SET_EQUALS requires a verbatim source_enumeration"
        if enumeration not in joined:
            return "source_enumeration is not a substring of the cited fragments"
        derived = {normalize(t) for t in tokenize_enumeration(enumeration)}
        asserted = {normalize(m) for m in val}
        if derived != asserted:
            missing = sorted(derived - asserted)
            extra = sorted(asserted - derived)
            return (
                "set is not exactly the source-derived set "
                f"(dropped from source: {missing}; not in source: {extra})"
            )
        return None

    if rt in ("CONSTANT", "AUTHORITY_TARGET") and op == "EQUALS":
        if not isinstance(val, str):
            return f"{rt}/EQUALS requires a string value"
        if normalize(val) not in norm_text:
            return (
                f"value {val!r} does not appear in the cited text "
                "(normalized token match)"
            )
        return None

    if rt == "INTERFACE_REQUIREMENT" and op == "MUST_EXIST":
        if not isinstance(val, str):
            return "INTERFACE_REQUIREMENT requires a string value"
        if val not in joined:
            return f"interface name {val!r} is not verbatim in the cited text"
        return None

    return f"unsupported rule shape {rt}/{op}"
