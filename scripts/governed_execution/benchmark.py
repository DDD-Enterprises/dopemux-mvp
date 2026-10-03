#!/usr/bin/env python3
"""Deterministic, model-free before/after benchmark for the governed
execution flow (MACRO-DMX-GOVERNED-EXECUTION-CONTRACT-V2-001, workstream
W08).

This module reads files with :mod:`pathlib` only. It performs no network
call, no model or MCP call, and starts no other process. Two invocations
against byte-identical inputs produce byte-identical JSON and Markdown
output (all collections are sorted before being emitted; no wall-clock
value is ever written into the report itself).

CLI
---

    python scripts/governed_execution/benchmark.py \\
        --repo <repo-root> \\
        --baseline-manifest scripts/governed_execution/benchmark_inputs.baseline.json \\
        --after-dir <evidence-directory> \\
        --out <report.json> \\
        --out-md <report.md>

Exit codes: 0 on success (including when some or all metrics come back
UNKNOWN because their evidence is absent), 2 only when ``--after-dir`` does
not exist or is not a directory. A missing file *inside* ``--after-dir``,
or a baseline path recorded MISSING in the manifest, never raises an
exception; the affected metric is reported as UNKNOWN.

BASELINE vs AFTER
------------------

BASELINE is the fixed pre-v2 evidence sample named in
``benchmark_inputs.baseline.json`` (paths + sha256, recorded at the base
commit 1c915b9141e9a5c3d835a5c7ea953381782ae875). Its artifacts are
``PROOF.json``, ``AUDITOR_REPORT.md`` and ``review_bundle/*`` files under
``proof/<packet>/`` plus the corresponding ``task-packets/<packet>/*``
files. Those artifacts predate this MacroPacket's return-block
conventions, so BASELINE extractors scan file content generically
(regex over JSON/Markdown text).

AFTER is supplied at run time as ``--after-dir``: a read-only directory
holding this MacroPacket's own W01..W07 evidence, laid out as
``*_RETURN.md`` workstream return blocks, ``OPERATOR_DECISIONS_G0.md``,
``OPERATOR_GATE_RECEIPT_*.md``, ``W0N_REPAIR_REQUEST_*.md``,
``W0N_FREEZE_RECEIPT*.json``, ``evidence/a*-audit-run*/A*_AUDIT_RECORD.md``,
``G0_RETURN.md`` and ``W0N_VALIDATION_*.txt``. AFTER extractors match
those specific filename conventions rather than scanning everything, since
the layout is known and structured.

Each metric's extraction rule is documented on its extractor function
below. Every count-style metric is UNKNOWN when its entire evidence
category (all files of the relevant kind) is absent from the corpus; when
at least one file of that kind is present, the metric is a real, possibly
zero, count -- absence of a *category* is UNKNOWN, absence of *matches
inside present files* is zero.

Output schema (``schema_version: dopemux.governed_execution.benchmark.v1``):
``{baseline, post_change, deltas, retirement_candidates, retirement_authorized,
authority, inputs_digest}``. ``retirement_authorized`` is always ``false``
and ``authority`` is always ``"NONE"``: this harness can recommend, it
cannot authorize. Any relay defined as an operator/nondelegable gate is
filtered out of ``retirement_candidates`` unconditionally; it is never a
member of that list regardless of what any input file says.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

SCHEMA_VERSION = "dopemux.governed_execution.benchmark.v1"

METRIC_NAMES: tuple[str, ...] = (
    "audit_calls",
    "cycle_time",
    "maintenance_cost",
    "model_calls",
    "operator_touches",
    "proof_churn",
    "repair_loops",
    "review_calls",
    "safety_regressions",
    "stale_head_rework",
    "supervisor_relays",
)


# --------------------------------------------------------------------------
# Corpus: a read-only, in-memory view of files actually present on disk.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class FileEntry:
    """One file as seen by the harness.

    ``path`` is a forward-slash relative path (relative to the repo root
    for BASELINE entries, relative to ``--after-dir`` for AFTER entries).
    ``status`` is ``PRESENT`` (readable, content hash matches or is not
    checked against anything), ``MISSING`` (declared but absent, or
    unreadable), or ``MISMATCH`` (BASELINE only: content on disk no
    longer matches the sha256 recorded in the manifest -- drifted
    evidence is treated like missing evidence, never like a match).
    ``text`` is the UTF-8 decoded content when decodable, else ``None``.
    """

    path: str
    status: str
    sha256: Optional[str]
    text: Optional[str]


@dataclass(frozen=True)
class Corpus:
    """An immutable, sorted collection of :class:`FileEntry`."""

    entries: tuple[FileEntry, ...]


def _decode_text(data: bytes) -> Optional[str]:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _load_baseline_manifest(path: Path) -> dict[str, Any]:
    """Load the baseline manifest. Never raises: an unreadable or
    malformed manifest yields an empty entry list, which in turn makes
    every BASELINE metric UNKNOWN -- a missing manifest is itself a
    missing input.
    """
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"entries": []}
    if not isinstance(data, dict):
        return {"entries": []}
    return data


def build_baseline_corpus(repo_root: Path, manifest: dict[str, Any]) -> Corpus:
    """Resolve every manifest entry against ``repo_root``.

    A manifest entry declared ``MISSING`` stays ``MISSING``. A declared
    ``PRESENT`` entry whose file cannot be read also becomes ``MISSING``.
    A declared ``PRESENT`` entry whose on-disk sha256 no longer matches
    the manifest's recorded sha256 becomes ``MISMATCH`` (its content is
    not used for extraction, but its actual on-disk sha256 is recorded
    for the input digest and audit trail).
    """
    entries: list[FileEntry] = []
    raw_entries = manifest.get("entries")
    if not isinstance(raw_entries, list):
        raw_entries = []
    for item in raw_entries:
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        if not isinstance(path, str) or not path:
            continue
        declared_status = item.get("status")
        declared_sha = item.get("sha256")
        if declared_status == "MISSING":
            entries.append(FileEntry(path=path, status="MISSING", sha256=None, text=None))
            continue
        fpath = repo_root / path
        try:
            data = fpath.read_bytes()
        except OSError:
            entries.append(FileEntry(path=path, status="MISSING", sha256=None, text=None))
            continue
        actual_sha = hashlib.sha256(data).hexdigest()
        if declared_sha is not None and actual_sha != declared_sha:
            entries.append(FileEntry(path=path, status="MISMATCH", sha256=actual_sha, text=None))
            continue
        entries.append(FileEntry(path=path, status="PRESENT", sha256=actual_sha, text=_decode_text(data)))
    entries.sort(key=lambda e: e.path)
    return Corpus(entries=tuple(entries))


def build_after_corpus(after_dir: Path) -> Corpus:
    """Walk ``after_dir`` recursively (sorted) and record every file
    found. There is no manifest on the AFTER side: whatever is present
    under ``after_dir`` is the whole AFTER corpus.
    """
    entries: list[FileEntry] = []
    for candidate in sorted(after_dir.rglob("*")):
        if not candidate.is_file():
            continue
        rel = candidate.relative_to(after_dir).as_posix()
        try:
            data = candidate.read_bytes()
        except OSError:
            continue
        sha = hashlib.sha256(data).hexdigest()
        entries.append(FileEntry(path=rel, status="PRESENT", sha256=sha, text=_decode_text(data)))
    entries.sort(key=lambda e: e.path)
    return Corpus(entries=tuple(entries))


def _present_text(corpus: Corpus) -> tuple[FileEntry, ...]:
    return tuple(e for e in corpus.entries if e.status == "PRESENT" and e.text is not None)


def _present(corpus: Corpus) -> tuple[FileEntry, ...]:
    return tuple(e for e in corpus.entries if e.status == "PRESENT")


def _match_files(corpus: Corpus, pattern: re.Pattern[str]) -> tuple[FileEntry, ...]:
    return tuple(
        sorted((e for e in corpus.entries if e.status == "PRESENT" and pattern.search(e.path)), key=lambda e: e.path)
    )


# --------------------------------------------------------------------------
# MetricResult
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class MetricResult:
    """The outcome of one metric extractor.

    ``status`` is ``KNOWN`` or ``UNKNOWN``. ``value`` is a JSON-scalar
    (``int``, ``float`` or ``str``) when ``KNOWN``, else ``None``.
    ``evidence`` names the files that contributed to the value.
    ``gaps`` names relevant files that could not be matched to a
    counterpart needed to compute the metric (used by
    ``stale_head_rework``). ``note`` is an optional short explanation.
    """

    status: str
    value: Optional[Any]
    evidence: tuple[str, ...] = ()
    gaps: tuple[str, ...] = ()
    note: str = ""


def _unknown(evidence: Iterable[str] = ()) -> MetricResult:
    return MetricResult(status="UNKNOWN", value=None, evidence=tuple(sorted(set(evidence))))


def _known(
    value: Any,
    evidence: Iterable[str] = (),
    gaps: Iterable[str] = (),
    note: str = "",
) -> MetricResult:
    return MetricResult(
        status="KNOWN",
        value=value,
        evidence=tuple(sorted(set(evidence))),
        gaps=tuple(sorted(set(gaps))),
        note=note,
    )


# --------------------------------------------------------------------------
# Filename conventions (AFTER side) and content markers (both sides).
# --------------------------------------------------------------------------

RETURN_FILE_RE = re.compile(r"(?:^|/)[A-Za-z0-9]+_RETURN\.md$")
OPERATOR_DECISIONS_RE = re.compile(r"(?:^|/)OPERATOR_DECISIONS_G0\.md$")
OPERATOR_GATE_RECEIPT_RE = re.compile(r"(?:^|/)OPERATOR_GATE_RECEIPT_[^/]*\.md$")
REPAIR_REQUEST_RE = re.compile(r"(?:^|/)W\d{2}_REPAIR_REQUEST_[^/]*\.md$")
FREEZE_RECEIPT_RE = re.compile(r"(?:^|/)W\d{2}_FREEZE_RECEIPT[^/]*\.json$")
AUDIT_RECORD_RE = re.compile(r"(?:^|/)evidence/a[\w.-]*-audit-run[\w.-]*/A[\w.-]*_AUDIT_RECORD\.md$")
VALIDATION_TXT_RE = re.compile(r"(?:^|/)W\d{2}_VALIDATION_[^/]*\.txt$")
PROOF_JSON_RE = re.compile(r"(?:^|/)PROOF\.json$")
REVIEW_BUNDLE_RE = re.compile(r"(?:^|/)review_bundle/")
DIFF_FILE_RE = re.compile(r"(?:^|/)[^/]*DIFF[^/]*\.txt$|\.(?:diff|patch)$", re.IGNORECASE)

D_LINE_RE = re.compile(r"^\s*(?:[-*#]+\s*)?D\d+\b", re.MULTILINE)
RETURN_AT_RE = re.compile(r"^RETURN_AT=(\S+)", re.MULTILINE)
MODEL_CALLS_RE = re.compile(r"^MODEL_CALLS=(\S+)", re.MULTILINE)
MODEL_CALLS_JSON_RE = re.compile(r'"model_calls"\s*:\s*(-?\d+)')
WORKSTREAM_ID_RE = re.compile(r"^WORKSTREAM_ID=(\S+)", re.MULTILINE)
SUBJECT_SHA_RE = re.compile(r"^SUBJECT_SHA=([0-9a-fA-F]{40})", re.MULTILINE)
HEAD_SHA_JSON_RE = re.compile(r'"head_sha"\s*:\s*"([0-9a-f]{40})"')
GIT_OID_RE = re.compile(r"\b[0-9a-f]{40}\b")
INVARIANT_TOKEN_RE = re.compile(r"\bI(0[1-9]|1\d|20)\b")
OPERATOR_MARK_RE = re.compile(
    r'"ratification_record"|operator[_ -]ratification|operator[_ -]decision|operator[_ -]gate',
    re.IGNORECASE,
)
SUPERVISOR_MARK_RE = re.compile(r'"supervisor"|supervisor[_ -]relay|return packet', re.IGNORECASE)
AUDIT_MARK_RE = re.compile(r'"embedded_audit"|"auditor_model"|"auditor_tool"')
RFC3339_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})")
DIFF_TARGET_RE = re.compile(r"^\+\+\+ b/(\S+)")
MAINTENANCE_PATH_RE = re.compile(
    r"^(schemas/|scripts/governance/|scripts/governed_execution/|"
    r"docs/03-reference/governance/|tests/governance/|\.pre-commit-config\.yaml$)"
)


def _parse_rfc3339(raw: str) -> Optional[datetime]:
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


# --------------------------------------------------------------------------
# cycle_time
# --------------------------------------------------------------------------


def extract_cycle_time_baseline(corpus: Corpus) -> MetricResult:
    """BASELINE cycle_time: every RFC 3339 timestamp found anywhere in the
    present, text-decodable baseline files. UNKNOWN when fewer than two
    distinct, parseable timestamps are found across the whole corpus;
    otherwise the value is ``(max - min)`` in whole seconds.
    """
    timestamps: list[datetime] = []
    evidence: list[str] = []
    for entry in _present_text(corpus):
        for match in RFC3339_RE.finditer(entry.text or ""):
            parsed = _parse_rfc3339(match.group(0))
            if parsed is not None:
                timestamps.append(parsed)
                evidence.append(entry.path)
    if len(set(timestamps)) < 2:
        return _unknown(evidence)
    return _known(int((max(timestamps) - min(timestamps)).total_seconds()), evidence)


def extract_cycle_time_after(corpus: Corpus) -> MetricResult:
    """AFTER cycle_time: RFC 3339 timestamps pulled from ``RETURN_AT=``
    lines in every ``*_RETURN.md`` file (``G0_RETURN.md`` included), plus
    the first line of every ``W0N_VALIDATION_*.txt`` file. UNKNOWN when
    fewer than two distinct, parseable timestamps are found; otherwise the
    value is ``(max - min)`` in whole seconds.
    """
    timestamps: list[datetime] = []
    evidence: list[str] = []
    for entry in _match_files(corpus, RETURN_FILE_RE):
        for match in RETURN_AT_RE.finditer(entry.text or ""):
            parsed = _parse_rfc3339(match.group(1))
            if parsed is not None:
                timestamps.append(parsed)
                evidence.append(entry.path)
    for entry in _match_files(corpus, VALIDATION_TXT_RE):
        lines = (entry.text or "").splitlines()
        first_line = lines[0] if lines else ""
        match = RFC3339_RE.search(first_line)
        if match is not None:
            parsed = _parse_rfc3339(match.group(0))
            if parsed is not None:
                timestamps.append(parsed)
                evidence.append(entry.path)
    if len(set(timestamps)) < 2:
        return _unknown(evidence)
    return _known(int((max(timestamps) - min(timestamps)).total_seconds()), evidence)


# --------------------------------------------------------------------------
# operator_touches
# --------------------------------------------------------------------------


def extract_operator_touches_baseline(corpus: Corpus) -> MetricResult:
    """BASELINE operator_touches: count of content markers for a recorded
    human authorization -- a ``"ratification_record"`` JSON key, or the
    phrase "operator ratification" / "operator decision" / "operator
    gate" (case-insensitive) -- summed across all present, text-decodable
    baseline files. UNKNOWN only when the baseline corpus has no
    text-decodable file at all.
    """
    files = _present_text(corpus)
    if not files:
        return _unknown()
    total = 0
    evidence: list[str] = []
    for entry in files:
        found = OPERATOR_MARK_RE.findall(entry.text or "")
        if found:
            total += len(found)
            evidence.append(entry.path)
    return _known(total, evidence)


def extract_operator_touches_after(corpus: Corpus) -> MetricResult:
    """AFTER operator_touches: number of numbered decision lines
    (``D<n>``) in ``OPERATOR_DECISIONS_G0.md`` plus one per
    ``OPERATOR_GATE_RECEIPT_*.md`` file. UNKNOWN only when neither
    ``OPERATOR_DECISIONS_G0.md`` nor any ``OPERATOR_GATE_RECEIPT_*.md``
    file is present.
    """
    decision_files = _match_files(corpus, OPERATOR_DECISIONS_RE)
    gate_files = _match_files(corpus, OPERATOR_GATE_RECEIPT_RE)
    if not decision_files and not gate_files:
        return _unknown()
    total = 0
    evidence: list[str] = []
    for entry in decision_files:
        matches = D_LINE_RE.findall(entry.text or "")
        total += len(matches)
        if matches:
            evidence.append(entry.path)
    for entry in gate_files:
        total += 1
        evidence.append(entry.path)
    return _known(total, evidence)


# --------------------------------------------------------------------------
# supervisor_relays
# --------------------------------------------------------------------------


def extract_supervisor_relays_baseline(corpus: Corpus) -> MetricResult:
    """BASELINE supervisor_relays: the pre-v2 proof format records no
    dedicated "return to supervisor" artifact type. UNKNOWN unless a file
    explicitly mentions a ``"supervisor"`` field or a "return packet";
    when it does, the value is the number of such mentions.
    """
    total = 0
    evidence: list[str] = []
    for entry in _present_text(corpus):
        found = SUPERVISOR_MARK_RE.findall(entry.text or "")
        if found:
            total += len(found)
            evidence.append(entry.path)
    if not evidence:
        return _unknown()
    return _known(total, evidence)


def extract_supervisor_relays_after(corpus: Corpus) -> MetricResult:
    """AFTER supervisor_relays: count of ``*_RETURN.md`` files (including
    ``G0_RETURN.md``) -- each is one return packet handed to the
    supervisor/team-lead. UNKNOWN when zero such files are present.
    """
    files = _match_files(corpus, RETURN_FILE_RE)
    if not files:
        return _unknown()
    return _known(len(files), [f.path for f in files])


# --------------------------------------------------------------------------
# model_calls
# --------------------------------------------------------------------------


def extract_model_calls_baseline(corpus: Corpus) -> MetricResult:
    """BASELINE model_calls: sum of every JSON ``"model_calls": <n>``
    field found across present baseline files. UNKNOWN when no such field
    is found anywhere in the corpus.
    """
    total = 0
    evidence: list[str] = []
    for entry in _present_text(corpus):
        for match in MODEL_CALLS_JSON_RE.finditer(entry.text or ""):
            total += int(match.group(1))
            evidence.append(entry.path)
    if not evidence:
        return _unknown()
    return _known(total, evidence)


def extract_model_calls_after(corpus: Corpus) -> MetricResult:
    """AFTER model_calls: sum of every ``MODEL_CALLS=<n>`` line across
    ``*_RETURN.md`` and ``A*_AUDIT_RECORD.md`` files. UNKNOWN when no
    such line is found anywhere in those files, or when any found value
    is not an integer (a recorded ``MODEL_CALLS=UNKNOWN`` makes the sum
    itself unknowable, so the whole metric is reported UNKNOWN rather
    than silently dropping that contribution).
    """
    files = _match_files(corpus, RETURN_FILE_RE) + _match_files(corpus, AUDIT_RECORD_RE)
    if not files:
        return _unknown()
    total = 0
    evidence: list[str] = []
    for entry in sorted(files, key=lambda e: e.path):
        for match in MODEL_CALLS_RE.finditer(entry.text or ""):
            raw = match.group(1)
            try:
                total += int(raw)
            except ValueError:
                return _unknown([entry.path])
            evidence.append(entry.path)
    if not evidence:
        return _unknown()
    return _known(total, evidence)


# --------------------------------------------------------------------------
# audit_calls
# --------------------------------------------------------------------------


def extract_audit_calls_baseline(corpus: Corpus) -> MetricResult:
    """BASELINE audit_calls: number of present ``PROOF.json`` files that
    carry an ``"embedded_audit"``, ``"auditor_model"`` or
    ``"auditor_tool"`` marker (an independent-audit run was recorded).
    UNKNOWN when no ``PROOF.json`` file is present at all.
    """
    files = _match_files(corpus, PROOF_JSON_RE)
    if not files:
        return _unknown()
    hits = [e for e in files if e.text and AUDIT_MARK_RE.search(e.text)]
    return _known(len(hits), [e.path for e in hits])


def extract_audit_calls_after(corpus: Corpus) -> MetricResult:
    """AFTER audit_calls: count of
    ``evidence/a*-audit-run*/A*_AUDIT_RECORD.md`` files -- one per
    independent audit run. UNKNOWN when none are present.
    """
    files = _match_files(corpus, AUDIT_RECORD_RE)
    if not files:
        return _unknown()
    return _known(len(files), [f.path for f in files])


# --------------------------------------------------------------------------
# review_calls
# --------------------------------------------------------------------------


def extract_review_calls_baseline(corpus: Corpus) -> MetricResult:
    """BASELINE review_calls: number of distinct ``review_bundle/``
    directories present (each holds one CI/review-style artifact bundle
    for a proof packet). UNKNOWN when none are present.
    """
    files = tuple(e for e in _present(corpus) if REVIEW_BUNDLE_RE.search(e.path))
    if not files:
        return _unknown()
    bundle_dirs: set[str] = set()
    for entry in files:
        idx = entry.path.find("review_bundle/")
        bundle_dirs.add(entry.path[: idx + len("review_bundle")])
    return _known(len(bundle_dirs), [e.path for e in files])


def extract_review_calls_after(corpus: Corpus) -> MetricResult:
    """AFTER review_calls: count of ``W0N_VALIDATION_*.txt`` files -- each
    is one recorded local/CI verify run. UNKNOWN when none are present.
    """
    files = _match_files(corpus, VALIDATION_TXT_RE)
    if not files:
        return _unknown()
    return _known(len(files), [f.path for f in files])


# --------------------------------------------------------------------------
# repair_loops
# --------------------------------------------------------------------------


def extract_repair_loops_baseline(corpus: Corpus) -> MetricResult:
    """BASELINE repair_loops: total items in every present ``PROOF.json``
    file's ``embedded_audit.fixes_applied`` array. UNKNOWN when no
    ``PROOF.json`` file is present; a present ``PROOF.json`` with an
    empty or absent ``fixes_applied`` array contributes zero (a real
    zero, not UNKNOWN).
    """
    files = _match_files(corpus, PROOF_JSON_RE)
    if not files:
        return _unknown()
    total = 0
    evidence: list[str] = []
    for entry in files:
        if not entry.text:
            continue
        try:
            data = json.loads(entry.text)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        embedded = data.get("embedded_audit")
        if not isinstance(embedded, dict):
            continue
        fixes = embedded.get("fixes_applied")
        if isinstance(fixes, list) and fixes:
            total += len(fixes)
            evidence.append(entry.path)
    return _known(total, evidence)


def extract_repair_loops_after(corpus: Corpus) -> MetricResult:
    """AFTER repair_loops: count of ``W0N_REPAIR_REQUEST_*.md`` files --
    each is one repair-loop cycle. UNKNOWN when none are present.
    """
    files = _match_files(corpus, REPAIR_REQUEST_RE)
    if not files:
        return _unknown()
    return _known(len(files), [f.path for f in files])


# --------------------------------------------------------------------------
# proof_churn
# --------------------------------------------------------------------------


def extract_proof_churn_baseline(corpus: Corpus) -> MetricResult:
    """BASELINE proof_churn: number of present files whose basename
    contains ``SUPERSEDED`` (case-insensitive), or whose text mentions
    the standalone word ``SUPERSEDED``. UNKNOWN when the baseline corpus
    has no present file at all.
    """
    present_files = _present(corpus)
    if not present_files:
        return _unknown()
    hits: set[str] = set()
    for entry in present_files:
        basename = entry.path.rsplit("/", 1)[-1]
        if "SUPERSEDED" in basename.upper():
            hits.add(entry.path)
        elif entry.text and re.search(r"\bSUPERSEDED\b", entry.text, re.IGNORECASE):
            hits.add(entry.path)
    return _known(len(hits), sorted(hits))


def extract_proof_churn_after(corpus: Corpus) -> MetricResult:
    """AFTER proof_churn: count of ``W0N_FREEZE_RECEIPT*.json`` files
    whose basename contains ``SUPERSEDED`` -- a superseded freeze receipt
    is proof churn. UNKNOWN when no ``W0N_FREEZE_RECEIPT*.json`` file is
    present at all; if freeze receipts are present but none are
    superseded, the value is zero.
    """
    files = _match_files(corpus, FREEZE_RECEIPT_RE)
    if not files:
        return _unknown()
    superseded = [e for e in files if "SUPERSEDED" in e.path.rsplit("/", 1)[-1].upper()]
    return _known(len(superseded), [e.path for e in superseded])


# --------------------------------------------------------------------------
# stale_head_rework
# --------------------------------------------------------------------------


def extract_stale_head_rework_baseline(corpus: Corpus) -> MetricResult:
    """BASELINE stale_head_rework: a structural proxy, not a certified
    claim. Files are grouped by their first two path segments (one group
    per proof/task-packet directory). For each group with a present
    ``PROOF.json`` carrying a ``"head_sha"``, every 40-hex git object id
    found anywhere in the group (``PROOF.json`` itself included, e.g. an
    ``admission.post_merge_main_sha`` field) is compared to ``head_sha``;
    if at least one differs, the group counts once. UNKNOWN when there is
    no present file at all.
    """
    groups: dict[str, list[FileEntry]] = {}
    for entry in _present(corpus):
        parts = entry.path.split("/")
        if len(parts) < 2:
            continue
        key = "/".join(parts[:2])
        groups.setdefault(key, []).append(entry)
    if not groups:
        return _unknown()
    stale = 0
    evidence: list[str] = []
    for key in sorted(groups):
        files = groups[key]
        proof_json = next((f for f in files if f.path.endswith("PROOF.json") and f.text), None)
        if proof_json is None or not proof_json.text:
            continue
        match = HEAD_SHA_JSON_RE.search(proof_json.text)
        if match is None:
            continue
        head = match.group(1)
        group_oids: set[str] = set()
        for entry in files:
            if not entry.text:
                continue
            group_oids.update(GIT_OID_RE.findall(entry.text))
        if group_oids - {head}:
            stale += 1
            evidence.append(proof_json.path)
    return _known(stale, evidence)


def extract_stale_head_rework_after(corpus: Corpus) -> MetricResult:
    """AFTER stale_head_rework: each ``A*_AUDIT_RECORD.md`` carries
    ``WORKSTREAM_ID=`` and ``SUBJECT_SHA=``; each ``*_RETURN.md`` carries
    the same two fields for its own workstream. An audit record whose
    ``SUBJECT_SHA`` differs from the matching return file's
    ``SUBJECT_SHA`` is one instance of stale-head rework. A record with
    no ``WORKSTREAM_ID``/``SUBJECT_SHA`` pair, or no matching return
    file, is listed under ``gaps`` and not counted. UNKNOWN when no
    audit record file is present at all.
    """
    records = _match_files(corpus, AUDIT_RECORD_RE)
    if not records:
        return _unknown()
    returns_by_id: dict[str, list[tuple[str, str]]] = {}
    for entry in _match_files(corpus, RETURN_FILE_RE):
        id_match = WORKSTREAM_ID_RE.search(entry.text or "")
        sha_match = SUBJECT_SHA_RE.search(entry.text or "")
        if id_match and sha_match:
            returns_by_id.setdefault(id_match.group(1), []).append((entry.path, sha_match.group(1).lower()))
    stale_pairs: list[tuple[str, str]] = []
    gaps: list[str] = []
    for record in records:
        id_match = WORKSTREAM_ID_RE.search(record.text or "")
        sha_match = SUBJECT_SHA_RE.search(record.text or "")
        if not id_match or not sha_match:
            gaps.append(record.path)
            continue
        candidates = returns_by_id.get(id_match.group(1))
        if not candidates:
            gaps.append(record.path)
            continue
        record_sha = sha_match.group(1).lower()
        for return_path, return_sha in candidates:
            if return_sha != record_sha:
                stale_pairs.append((record.path, return_path))
    evidence = {path for pair in stale_pairs for path in pair}
    return _known(len(stale_pairs), evidence, gaps)


# --------------------------------------------------------------------------
# safety_regressions
# --------------------------------------------------------------------------


def _count_invariant_violation_lines(files: Iterable[FileEntry]) -> MetricResult:
    hits: list[str] = []
    evidence: set[str] = set()
    for entry in files:
        for line in (entry.text or "").splitlines():
            if not INVARIANT_TOKEN_RE.search(line):
                continue
            upper = line.upper()
            if ("VIOLAT" in upper or "FAIL" in upper) and "PASS" not in upper:
                hits.append(line.strip())
                evidence.add(entry.path)
    return _known(len(hits), evidence)


def extract_safety_regressions_baseline(corpus: Corpus) -> MetricResult:
    """BASELINE safety_regressions: count of lines, anywhere in present
    text-decodable baseline files, that name an invariant token
    ``I01``..``I20`` together with ``VIOLAT`` or ``FAIL`` and not
    ``PASS`` (case-insensitive). UNKNOWN when the baseline corpus has no
    text-decodable file at all; otherwise zero is a real, reportable
    finding of no recorded regression.
    """
    files = _present_text(corpus)
    if not files:
        return _unknown()
    return _count_invariant_violation_lines(files)


def extract_safety_regressions_after(corpus: Corpus) -> MetricResult:
    """AFTER safety_regressions: same line pattern as the BASELINE rule,
    scoped to ``A*_AUDIT_RECORD.md`` files only (the AFTER evidence
    layout separates audit output from everything else). UNKNOWN when no
    audit record file is present.
    """
    files = _match_files(corpus, AUDIT_RECORD_RE)
    if not files:
        return _unknown()
    return _count_invariant_violation_lines(files)


# --------------------------------------------------------------------------
# maintenance_cost (shared rule, both sides)
# --------------------------------------------------------------------------


def extract_maintenance_cost(corpus: Corpus) -> MetricResult:
    """maintenance_cost (both sides, identical rule): every file matching
    ``*DIFF*.txt``/``*.diff``/``*.patch`` is parsed as a unified diff.
    For each ``+++ b/<path>`` hunk target under
    ``schemas/``, ``scripts/governance/``, ``scripts/governed_execution/``,
    ``docs/03-reference/governance/``, ``tests/governance/`` or the file
    ``.pre-commit-config.yaml``, every added line (``+`` prefixed, not
    ``+++``) is counted. UNKNOWN when no diff-like file is present.
    """
    files = _match_files(corpus, DIFF_FILE_RE)
    if not files:
        return _unknown()
    total = 0
    evidence: list[str] = []
    for entry in files:
        current_target: Optional[str] = None
        counted = 0
        for line in (entry.text or "").splitlines():
            if line.startswith("+++"):
                match = DIFF_TARGET_RE.match(line)
                current_target = match.group(1) if match else None
                continue
            if current_target and MAINTENANCE_PATH_RE.match(current_target) and line.startswith("+"):
                total += 1
                counted += 1
        if counted:
            evidence.append(entry.path)
    return _known(total, evidence)


# --------------------------------------------------------------------------
# Extractor tables
# --------------------------------------------------------------------------

BASELINE_EXTRACTORS: dict[str, Callable[[Corpus], MetricResult]] = {
    "audit_calls": extract_audit_calls_baseline,
    "cycle_time": extract_cycle_time_baseline,
    "maintenance_cost": extract_maintenance_cost,
    "model_calls": extract_model_calls_baseline,
    "operator_touches": extract_operator_touches_baseline,
    "proof_churn": extract_proof_churn_baseline,
    "repair_loops": extract_repair_loops_baseline,
    "review_calls": extract_review_calls_baseline,
    "safety_regressions": extract_safety_regressions_baseline,
    "stale_head_rework": extract_stale_head_rework_baseline,
    "supervisor_relays": extract_supervisor_relays_baseline,
}

AFTER_EXTRACTORS: dict[str, Callable[[Corpus], MetricResult]] = {
    "audit_calls": extract_audit_calls_after,
    "cycle_time": extract_cycle_time_after,
    "maintenance_cost": extract_maintenance_cost,
    "model_calls": extract_model_calls_after,
    "operator_touches": extract_operator_touches_after,
    "proof_churn": extract_proof_churn_after,
    "repair_loops": extract_repair_loops_after,
    "review_calls": extract_review_calls_after,
    "safety_regressions": extract_safety_regressions_after,
    "stale_head_rework": extract_stale_head_rework_after,
    "supervisor_relays": extract_supervisor_relays_after,
}


# --------------------------------------------------------------------------
# Retirement candidates
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class RelayDef:
    """One relay in the fixed catalog this harness reasons about.

    ``operator_gate`` marks a relay as an operator/nondelegable gate
    (invariant I15): such a relay is never emitted in
    ``retirement_candidates``, regardless of what any input file says.
    """

    name: str
    metric: str
    operator_gate: bool


RELAY_CATALOG: tuple[RelayDef, ...] = (
    RelayDef("supervisor_return_relay", "supervisor_relays", False),
    RelayDef("independent_audit_dispatch_relay", "audit_calls", False),
    RelayDef("review_ci_relay", "review_calls", False),
    RelayDef("repair_loop_relay", "repair_loops", False),
    RelayDef("freeze_proof_relay", "proof_churn", False),
    RelayDef("operator_decision_gate", "operator_touches", True),
)


def build_retirement_candidates(post_metrics: dict[str, MetricResult]) -> list[dict[str, Any]]:
    """Score every non-gate relay in :data:`RELAY_CATALOG` against the
    AFTER metrics.

    ``safe`` is true only when ``safety_regressions`` is KNOWN and zero.
    ``observable`` is true when the relay's associated AFTER metric is
    KNOWN. ``reversible`` and ``authority_preserving`` are constant true
    for every cataloged, non-gate relay (each is a re-enableable process
    step, not an authority boundary -- gate relays never reach this
    function). ``measurably_useful`` is true when the relay's metric is
    KNOWN and greater than zero (the relay still fires in the AFTER
    flow). ``recommendation`` is ``INSUFFICIENT_EVIDENCE`` when not
    observable, ``RECOMMEND_RETIRE`` when observable, safe, and not
    measurably useful, else ``KEEP``.
    """
    safety = post_metrics.get("safety_regressions")
    is_safe = bool(safety is not None and safety.status == "KNOWN" and safety.value == 0)
    candidates: list[dict[str, Any]] = []
    for relay in RELAY_CATALOG:
        if relay.operator_gate:
            continue
        metric = post_metrics[relay.metric]
        observable = metric.status == "KNOWN"
        measurably_useful = bool(observable and isinstance(metric.value, (int, float)) and metric.value > 0)
        reversible = True
        authority_preserving = True
        if not observable:
            recommendation = "INSUFFICIENT_EVIDENCE"
        elif is_safe and not measurably_useful and reversible and authority_preserving:
            recommendation = "RECOMMEND_RETIRE"
        else:
            recommendation = "KEEP"
        candidates.append(
            {
                "relay": relay.name,
                "safe": is_safe,
                "observable": observable,
                "reversible": reversible,
                "measurably_useful": measurably_useful,
                "authority_preserving": authority_preserving,
                "recommendation": recommendation,
            }
        )
    return candidates


# --------------------------------------------------------------------------
# Report assembly
# --------------------------------------------------------------------------


def _metric_to_dict(metric: MetricResult) -> dict[str, Any]:
    return {
        "status": metric.status,
        "value": metric.value,
        "evidence": list(metric.evidence),
        "gaps": list(metric.gaps),
        "note": metric.note,
    }


def _compute_deltas(
    baseline: dict[str, MetricResult], post_change: dict[str, MetricResult]
) -> dict[str, dict[str, Any]]:
    deltas: dict[str, dict[str, Any]] = {}
    for name in METRIC_NAMES:
        base_metric = baseline[name]
        post_metric = post_change[name]
        both_numeric = (
            base_metric.status == "KNOWN"
            and post_metric.status == "KNOWN"
            and isinstance(base_metric.value, (int, float))
            and isinstance(post_metric.value, (int, float))
        )
        if both_numeric:
            deltas[name] = {"status": "KNOWN", "value": post_metric.value - base_metric.value}
        else:
            deltas[name] = {"status": "UNKNOWN", "value": None}
    return deltas


def _inputs_digest(baseline_corpus: Corpus, after_corpus: Corpus) -> str:
    rows: list[dict[str, Optional[str]]] = []
    for entry in baseline_corpus.entries:
        if entry.status in ("PRESENT", "MISMATCH"):
            rows.append({"side": "baseline", "path": entry.path, "sha256": entry.sha256})
    for entry in after_corpus.entries:
        if entry.status in ("PRESENT", "MISMATCH"):
            rows.append({"side": "after", "path": entry.path, "sha256": entry.sha256})
    rows.sort(key=lambda row: (row["side"] or "", row["path"] or ""))
    blob = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def build_report(baseline_corpus: Corpus, after_corpus: Corpus) -> dict[str, Any]:
    """Compute every metric on both sides and assemble the report dict.
    ``retirement_authorized`` and ``authority`` are hardcoded constants:
    no code path in this module can set them to anything else.
    """
    baseline_metrics = {name: fn(baseline_corpus) for name, fn in BASELINE_EXTRACTORS.items()}
    post_metrics = {name: fn(after_corpus) for name, fn in AFTER_EXTRACTORS.items()}
    return {
        "schema_version": SCHEMA_VERSION,
        "baseline": {name: _metric_to_dict(baseline_metrics[name]) for name in METRIC_NAMES},
        "post_change": {name: _metric_to_dict(post_metrics[name]) for name in METRIC_NAMES},
        "deltas": _compute_deltas(baseline_metrics, post_metrics),
        "retirement_candidates": build_retirement_candidates(post_metrics),
        "retirement_authorized": False,
        "authority": "NONE",
        "inputs_digest": _inputs_digest(baseline_corpus, after_corpus),
    }


def render_markdown(report: dict[str, Any]) -> str:
    """Render the report as Markdown. Deterministic: iterates
    :data:`METRIC_NAMES` in fixed order and never reads wall-clock time.
    """
    lines: list[str] = []
    lines.append("# Governed Execution Benchmark Report")
    lines.append("")
    lines.append(f"schema_version: `{report['schema_version']}`")
    lines.append("")
    lines.append("## Metrics")
    lines.append("")
    lines.append("| Metric | Baseline | Post-change | Delta (post - baseline) |")
    lines.append("| --- | --- | --- | --- |")
    for name in METRIC_NAMES:
        base = report["baseline"][name]
        post = report["post_change"][name]
        delta = report["deltas"][name]
        base_val = base["value"] if base["status"] == "KNOWN" else "UNKNOWN"
        post_val = post["value"] if post["status"] == "KNOWN" else "UNKNOWN"
        delta_val = delta["value"] if delta["status"] == "KNOWN" else "UNKNOWN"
        lines.append(f"| {name} | {base_val} | {post_val} | {delta_val} |")
    lines.append("")
    lines.append("## Retirement candidates")
    lines.append("")
    lines.append(
        "| Relay | Safe | Observable | Reversible | Measurably useful | Authority preserving | Recommendation |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for candidate in report["retirement_candidates"]:
        lines.append(
            f"| {candidate['relay']} | {candidate['safe']} | {candidate['observable']} | "
            f"{candidate['reversible']} | {candidate['measurably_useful']} | "
            f"{candidate['authority_preserving']} | {candidate['recommendation']} |"
        )
    lines.append("")
    lines.append(f"retirement_authorized: {str(report['retirement_authorized']).lower()}")
    lines.append("")
    lines.append(f"authority: {report['authority']}")
    lines.append("")
    lines.append(f"inputs_digest: `{report['inputs_digest']}`")
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    parser.add_argument("--repo", required=True, type=Path, help="Repo root BASELINE paths resolve against.")
    parser.add_argument("--baseline-manifest", required=True, type=Path, help="Path to the baseline manifest JSON.")
    parser.add_argument("--after-dir", required=True, type=Path, help="Read-only directory of AFTER evidence.")
    parser.add_argument("--out", required=True, type=Path, help="Where to write the JSON report.")
    parser.add_argument("--out-md", required=True, type=Path, help="Where to write the Markdown report.")
    args = parser.parse_args(argv)

    if not args.after_dir.is_dir():
        print(f"error: --after-dir {args.after_dir} is not a directory", file=sys.stderr)
        return 2

    manifest = _load_baseline_manifest(args.baseline_manifest)
    baseline_corpus = build_baseline_corpus(args.repo, manifest)
    after_corpus = build_after_corpus(args.after_dir)

    report = build_report(baseline_corpus, after_corpus)
    markdown = render_markdown(report)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(markdown, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
