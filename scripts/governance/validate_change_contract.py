#!/usr/bin/env python3
"""Deterministic offline change-contract preflight (evidence economy).

No network, no model calls, no file mutation.

Exit codes:
  0 — PASS
  1 — FAIL (contract violations)
  2 — usage / environment error
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]

LANE_RANK = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}

# Higher-priority patterns first. First match wins for a path.
# Checked-in deterministic mapping — update deliberately.
_PATH_RULES: list[tuple[str, re.Pattern[str]]] = [
    # L3 — red lane
    ("L3", re.compile(r"(^|/)(\.env|secrets?|credentials?)(/|$)", re.I)),
    ("L3", re.compile(r"(^|/)(sign_local_audit_proof|local_audit_acceptance|embedded-audit-allowed-signers)")),
    ("L3", re.compile(r"^config/audit/")),
    ("L3", re.compile(r"^\.github/workflows/")),
    ("L3", re.compile(r"(^|/)(auth|oauth|permission|rbac|migrate|migration)s?(/|\.|$)", re.I)),
    ("L3", re.compile(r"(^|/)production(/|\.|$)", re.I)),
    # L2 — material / governance / audit tooling
    ("L2", re.compile(r"^AGENTS\.md$")),
    ("L2", re.compile(r"^RULES\.md$")),
    ("L2", re.compile(r"^docs/03-reference/governance/")),
    ("L2", re.compile(r"^docs/ops/(embedded-audit|pr-steward)\.md$")),
    ("L2", re.compile(r"^config/ai/model-routing")),
    ("L2", re.compile(r"^scripts/governance/")),
    ("L2", re.compile(r"^scripts/audit/")),
    ("L2", re.compile(r"^schemas/")),
    ("L2", re.compile(r"^\.pre-commit-config\.yaml$")),
    ("L2", re.compile(r"^tests/(governance|audit|pr_steward)/")),
    ("L2", re.compile(r"^(src|services)/")),
    ("L2", re.compile(r"^compose\.ya?ml$")),
    # L0 — deterministic metadata / proof packaging
    ("L0", re.compile(r"^proof/pr_merge/embedded-audit/pr-\d+/")),
    ("L0", re.compile(r"^proof/[^/]+/(PROOF\.json|PROOF\.json\.sig|AUDITOR_REPORT\.md|review_bundle/)")),
    ("L0", re.compile(r"^proof/[^/]+/.*\.(txt|json|md)$")),
    ("L0", re.compile(r"^task-packets/.*\.(json|md)$")),
]

# Unmatched / uncertain paths escalate to L2 (require final independent audit).
# Do not silently treat unknown surfaces as L1 bounded.
_DEFAULT_LANE = "L2"

_FM_REQUIRED = ("id", "title", "type", "owner", "last_review", "next_review")
_FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)

# Tight proof-only path closure: enumerated artifact names only.
# review_bundle allows a single basename segment (no / or ..) with safe text-like
# extensions only — rejects evil.bin and path-traversal segments.
_PROOF_ARTIFACT = (
    r"(PROOF\.json|PROOF\.json\.sig|AUDITOR_REPORT\.md|"
    r"AUDIT_[A-Z0-9_]+\.(md|json)|COMMAND_LOG\.md|HANDOFF\.md|"
    r"THREAT_MODEL\.md|VALIDATION\.json|MODEL_CALL_BUDGET\.md|"
    r"C\d+_HEAD\.txt|"
    r"review_bundle/[A-Za-z0-9][A-Za-z0-9._-]*\.(txt|json|md|diff))"
)
_PROOF_ONLY_ALLOWED = re.compile(
    rf"^("
    rf"proof/pr_merge/embedded-audit/pr-\d+/{_PROOF_ARTIFACT}"
    rf"|proof/[^/]+/{_PROOF_ARTIFACT}"
    rf")$"
)


@dataclass
class Finding:
    code: str
    severity: str  # error|warning|info
    path: str = ""
    message: str = ""


@dataclass
class Result:
    status: str  # PASS|FAIL
    max_lane: str
    paths: list[dict[str, str]] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    proof_only: bool = False
    model_audit_required: bool = False
    notes: list[str] = field(default_factory=list)

    def add(self, code: str, severity: str, message: str, path: str = "") -> None:
        self.findings.append(Finding(code=code, severity=severity, path=path, message=message))


def classify_path(path: str) -> str:
    norm = path.replace("\\", "/")
    while norm.startswith("./"):
        norm = norm[2:]
    norm = norm.lstrip("/")
    for lane, pat in _PATH_RULES:
        if pat.search(norm):
            return lane
    return _DEFAULT_LANE


def max_lane(lanes: Iterable[str]) -> str:
    best = "L0"
    for lane in lanes:
        if LANE_RANK.get(lane, 1) > LANE_RANK.get(best, 0):
            best = lane
    return best


def _run_git(args: list[str], cwd: Path) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"git {' '.join(args)} failed")
    return proc.stdout


def changed_paths(base: str, head: str, cwd: Path) -> list[str]:
    out = _run_git(["diff", "--name-only", f"{base}...{head}"], cwd)
    return sorted({p.strip().replace("\\", "/") for p in out.splitlines() if p.strip()})


def read_blob(ref: str, path: str, cwd: Path) -> Optional[str]:
    proc = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def parse_frontmatter(text: str) -> Optional[dict[str, Any]]:
    m = _FM_RE.match(text)
    if not m:
        return None
    data: dict[str, Any] = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        data[key.strip()] = val.strip().strip("'\"")
    return data


def validate_frontmatter(path: str, text: str, result: Result) -> None:
    fm = parse_frontmatter(text)
    if fm is None:
        result.add(
            "frontmatter_missing",
            "error",
            "Markdown lacks YAML frontmatter block; docs-frontmatter-guard would modify it",
            path,
        )
        return
    missing = [k for k in _FM_REQUIRED if k not in fm or not str(fm.get(k, "")).strip()]
    if missing:
        result.add(
            "frontmatter_incomplete",
            "error",
            f"Missing frontmatter keys: {', '.join(missing)}; hook would modify file",
            path,
        )


def validate_task_packet_json(path: str, text: str, result: Result, cwd: Path) -> None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        result.add("packet_json_invalid", "error", f"JSON parse error: {exc}", path)
        return
    schema_path = cwd / "docs/03-reference/spec/dopetask/dopetask-canonical-spec.json"
    if not schema_path.is_file():
        result.add("packet_schema_missing", "warning", f"Schema not found: {schema_path}", path)
        return
    try:
        import jsonschema  # type: ignore
    except ImportError:
        result.add("jsonschema_unavailable", "warning", "jsonschema not installed; skipped schema check", path)
        return
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    if errors:
        msg = "; ".join(
            f"{'/'.join(map(str, e.path)) or '(root)'}: {e.message}" for e in errors[:5]
        )
        result.add("packet_schema_fail", "error", msg, path)


def validate_proof_json(path: str, text: str, result: Result, cwd: Path) -> None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        result.add("proof_json_invalid", "error", f"JSON parse error: {exc}", path)
        return
    if "embedded_audit" not in payload:
        # Only enforce for paths under include pattern used by CI validator
        if re.match(r"^proof/TP-DMX-.*/PROOF\.json$", path.replace("\\", "/")):
            result.add(
                "proof_missing_embedded_audit",
                "error",
                "PROOF.json missing top-level embedded_audit (required for TP-DMX-* packages)",
                path,
            )
        return
    schema_path = cwd / "schemas/proof/embedded_audit.schema.json"
    if not schema_path.is_file():
        result.add("audit_schema_missing", "warning", "embedded_audit schema missing", path)
        return
    try:
        import jsonschema  # type: ignore
    except ImportError:
        result.add("jsonschema_unavailable", "warning", "jsonschema not installed; skipped proof schema", path)
        return
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    # Local acceptance intentionally skips report_path for pr_merge; full schema for TP packages
    embedded = payload["embedded_audit"]
    if not isinstance(embedded, dict):
        result.add("proof_embedded_not_object", "error", "embedded_audit must be object", path)
        return
    # Soften report_path for pr_merge packages (matches CI local-attestation practice)
    if path.replace("\\", "/").startswith("proof/pr_merge/"):
        schema = dict(schema)
        props = dict(schema.get("properties") or {})
        if "report_path" in props:
            rp = dict(props["report_path"])
            rp.pop("pattern", None)
            props["report_path"] = rp
            schema["properties"] = props
    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(embedded), key=lambda e: list(e.path))
    if errors:
        msg = "; ".join(
            f"{'/'.join(map(str, e.path)) or '(root)'}: {e.message}" for e in errors[:5]
        )
        result.add("proof_schema_fail", "error", msg, path)


def _load_json_object(text: str) -> Optional[dict[str, Any]]:
    try:
        data = json.loads(text)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _is_quarantine_skipped_proof(text: str) -> bool:
    """True when PROOF.json is a deliberate SKIPPED quarantine (not audited PASS)."""
    data = _load_json_object(text)
    if not data:
        return False
    embedded = data.get("embedded_audit")
    if not isinstance(embedded, dict):
        return False
    if embedded.get("status") != "SKIPPED":
        return False
    return bool(str(embedded.get("skip_reason") or "").strip())


def _resolve_text(
    path: str,
    *,
    cwd: Path,
    head: str,
    file_text: Optional[dict[str, str]],
) -> Optional[str]:
    if file_text is not None and path in file_text:
        return file_text[path]
    wt = cwd / path
    if head in {"HEAD", ""} and wt.is_file():
        return wt.read_text(encoding="utf-8")
    return read_blob(head, path, cwd)


def validate_proof_only_closure(
    paths: list[str],
    result: Result,
    *,
    content_head: Optional[str],
    proof_head: Optional[str],
    audited_head: Optional[str],
    cwd: Path,
    head: str = "HEAD",
    file_text: Optional[dict[str, str]] = None,
    quarantine_mode: bool = False,
) -> None:
    """Fail closed on escaped paths / head binding; audited PASS requires signatures.

    Quarantine mode (explicit flag or detected SKIPPED PROOF.json):
      - requires content_head + proof_head only (not audited_head)
      - forbids PROOF.json.sig (no audit-pass signature on NOT_PROVEN quarantine)
      - requires each PROOF.json to be schema-shaped SKIPPED with non-empty skip_reason
    Audited proof-only successor mode (default):
      - requires content_head + audited_head + proof_head
      - requires audited_head == content_head
      - requires PROOF.json.sig for every PROOF.json
    """
    norm_paths = [p.replace("\\", "/") for p in paths]
    escaped = [p for p in norm_paths if not _PROOF_ONLY_ALLOWED.match(p)]
    if escaped:
        for p in escaped:
            result.add(
                "proof_only_escaped_path",
                "error",
                "Path outside proof-only allowlist in proof-only successor",
                p,
            )
        return
    result.proof_only = True
    result.notes.append("All changed paths are within proof-only allowlist")

    # Detect quarantine from PROOF.json bodies (or explicit flag).
    proof_json_paths = [p for p in norm_paths if p.endswith("PROOF.json")]
    quarantine_hits: list[str] = []
    non_quarantine_proofs: list[str] = []
    for path in proof_json_paths:
        text = _resolve_text(path, cwd=cwd, head=head, file_text=file_text)
        if text is None:
            # deleted PROOF.json — neither audited-pass nor quarantine
            continue
        if _is_quarantine_skipped_proof(text):
            quarantine_hits.append(path)
        else:
            non_quarantine_proofs.append(path)

    if quarantine_mode or quarantine_hits:
        if non_quarantine_proofs:
            for path in non_quarantine_proofs:
                result.add(
                    "quarantine_mixed_proof_status",
                    "error",
                    "Quarantine mode requires every PROOF.json to be status=SKIPPED "
                    "with non-empty skip_reason (no audited PASS in the same package)",
                    path,
                )
            return
        if not quarantine_hits and quarantine_mode:
            result.add(
                "quarantine_missing_skipped_proof",
                "error",
                "Quarantine mode requires at least one PROOF.json with status=SKIPPED "
                "and non-empty skip_reason",
            )
            return
        result.notes.append(
            "Quarantine mode: SKIPPED post-merge/exact-head-NOT_PROVEN package "
            "(signature forbidden; audited_head not required)"
        )
        missing = [
            name
            for name, value in (
                ("content_head", content_head),
                ("proof_head", proof_head),
            )
            if not value
        ]
        if missing:
            result.add(
                "proof_only_missing_heads",
                "error",
                "Quarantine mode requires --content-head and --proof-head "
                f"(missing: {', '.join(missing)}; audited_head is not required)",
            )
            return
    else:
        # Fail closed: audited proof-only successors must bind all three heads.
        missing = [
            name
            for name, value in (
                ("content_head", content_head),
                ("audited_head", audited_head),
                ("proof_head", proof_head),
            )
            if not value
        ]
        if missing:
            result.add(
                "proof_only_missing_heads",
                "error",
                "Proof-only mode requires --content-head, --audited-head, and --proof-head "
                f"(missing: {', '.join(missing)})",
            )
            return

        if audited_head != content_head:
            result.add(
                "proof_only_stale_content_head",
                "error",
                f"audited_head {audited_head} != content_head {content_head}",
            )

    # proof head must be descendant of content head
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", content_head, proof_head],  # type: ignore[arg-type]
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        result.add(
            "proof_only_ancestry_fail",
            "error",
            f"content_head {content_head} is not an ancestor of proof_head {proof_head}",
        )

    # Fail closed: derive the real content_head..proof_head delta from git.
    # Caller-supplied --paths cannot redefine a non-proof delta as proof-only.
    delta_proc = subprocess.run(
        ["git", "diff", "--name-only", f"{content_head}..{proof_head}"],  # type: ignore[arg-type]
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if delta_proc.returncode != 0:
        result.add(
            "proof_only_delta_unreadable",
            "error",
            "Unable to read git diff for content_head..proof_head; cannot prove proof-only closure",
        )
        return
    derived = sorted(
        {
            p.strip().replace("\\", "/")
            for p in delta_proc.stdout.splitlines()
            if p.strip()
        }
    )
    if not derived:
        result.add(
            "proof_only_empty_delta",
            "error",
            "content_head..proof_head has no changed paths",
        )
        return
    if set(norm_paths) != set(derived):
        result.add(
            "proof_only_path_mismatch",
            "error",
            "Declared paths do not exactly match git diff content_head..proof_head "
            f"(declared={len(norm_paths)} derived={len(derived)})",
        )
        # Continue validating the derived set for escape/signature closure.
    # Always enforce allowlist on the derived delta, not caller paths alone.
    norm_paths = derived
    escaped_derived = [p for p in norm_paths if not _PROOF_ONLY_ALLOWED.match(p)]
    if escaped_derived:
        for p in escaped_derived:
            result.add(
                "proof_only_escaped_path",
                "error",
                "Derived proof-only delta path outside allowlist",
                p,
            )
        return

    path_set = set(norm_paths)
    quarantine_active = quarantine_mode or bool(quarantine_hits)

    if quarantine_active:
        # Forbids audit-pass signatures on deliberate NOT_PROVEN quarantines.
        for path in norm_paths:
            if not path.endswith("PROOF.json"):
                continue
            sig_path = f"{path}.sig"
            sig_present = sig_path in path_set
            if not sig_present and proof_head:
                if read_blob(proof_head, sig_path, cwd) is not None:
                    sig_present = True
            if not sig_present and proof_head in {"HEAD", ""} and (cwd / sig_path).is_file():
                sig_present = True
            if sig_present:
                result.add(
                    "quarantine_forbids_signature",
                    "error",
                    "Quarantine SKIPPED package must not carry PROOF.json.sig "
                    "(do not invent or restore an audit-pass signature)",
                    path,
                )
        return

    # Audited proof-only: signature presence for every PROOF.json.
    for path in norm_paths:
        if not path.endswith("PROOF.json"):
            continue
        sig_path = f"{path}.sig"
        if sig_path in path_set:
            continue
        # Accept signature already present at proof_head blob (rare same-path update).
        if proof_head and read_blob(proof_head, sig_path, cwd) is not None:
            continue
        # Accept signature in working tree when proof_head is HEAD.
        if proof_head in {"HEAD", ""} and (cwd / sig_path).is_file():
            continue
        result.add(
            "proof_only_missing_signature",
            "error",
            "PROOF.json in proof-only successor requires co-changed or bound PROOF.json.sig",
            path,
        )


def detect_hook_would_modify(path: str, text: str, result: Result) -> None:
    """Simulate docs-frontmatter-guard check mode (no write)."""
    if not path.endswith(".md"):
        return
    if not (
        path.startswith("docs/")
        or path.startswith("task-packets/")
        or path.startswith("UPGRADES/")
    ):
        return
    # Reuse frontmatter completeness as proxy for "hook would modify"
    fm = parse_frontmatter(text)
    if fm is None or any(k not in fm or not str(fm.get(k, "")).strip() for k in _FM_REQUIRED):
        result.add(
            "hook_would_modify",
            "error",
            "docs-frontmatter-guard would modify this file; fix before push and re-run hooks",
            path,
        )


def evaluate(
    *,
    paths: list[str],
    cwd: Path,
    head: str = "HEAD",
    proof_only_mode: bool = False,
    content_head: Optional[str] = None,
    proof_head: Optional[str] = None,
    audited_head: Optional[str] = None,
    file_text: Optional[dict[str, str]] = None,
    quarantine_mode: bool = False,
    range_base: Optional[str] = None,
) -> Result:
    result = Result(status="PASS", max_lane="L0")
    path_rows: list[dict[str, str]] = []
    lanes: list[str] = []
    for path in sorted(paths):
        lane = classify_path(path)
        lanes.append(lane)
        path_rows.append({"path": path, "lane": lane})
    result.paths = path_rows
    result.max_lane = max_lane(lanes) if lanes else "L0"
    result.model_audit_required = result.max_lane in {"L2", "L3"}

    pure_proof = bool(
        paths and all(_PROOF_ONLY_ALLOWED.match(p.replace("\\", "/")) for p in paths)
    )
    if proof_only_mode or pure_proof:
        # Auto-detect quarantine SKIPPED when heads omitted (pre-commit range only).
        eff_quarantine = quarantine_mode
        eff_content = content_head
        eff_proof = proof_head
        if pure_proof and not content_head and not proof_head and not audited_head:
            for path in paths:
                npath = path.replace("\\", "/")
                if not npath.endswith("PROOF.json"):
                    continue
                text = _resolve_text(
                    npath, cwd=cwd, head=head, file_text=file_text
                )
                if text and _is_quarantine_skipped_proof(text):
                    eff_quarantine = True
                    break
        if eff_quarantine:
            # Bind range refs only for quarantine — never invent audited_head.
            if not eff_content and range_base:
                eff_content = range_base
            if not eff_proof:
                eff_proof = head
        validate_proof_only_closure(
            paths,
            result,
            content_head=eff_content,
            proof_head=eff_proof,
            audited_head=audited_head,
            cwd=cwd,
            head=head,
            file_text=file_text,
            quarantine_mode=eff_quarantine,
        )
        # Proof-only does not escalate lane for audit budget only when closure is clean.
        if result.proof_only and not any(
            f.severity == "error"
            and (f.code.startswith("proof_only_") or f.code.startswith("quarantine_"))
            for f in result.findings
        ):
            result.max_lane = "L0"
            result.model_audit_required = False
            if eff_quarantine or any("Quarantine mode" in n for n in result.notes):
                result.notes.append(
                    "Quarantine package: model re-audit of content NOT_REQUIRED "
                    "(exact-head audit NOT_PROVEN)"
                )
            else:
                result.notes.append(
                    "Proof-only successor: model re-audit of content NOT_REQUIRED"
                )

    for path in paths:
        text: Optional[str]
        if file_text is not None and path in file_text:
            text = file_text[path]
        else:
            # Prefer working tree for HEAD when file exists
            wt = cwd / path
            if head in {"HEAD", ""} and wt.is_file():
                text = wt.read_text(encoding="utf-8")
            else:
                text = read_blob(head, path, cwd)
        if text is None:
            # deleted path
            continue
        if path.endswith(".md") and (
            path.startswith("docs/") or path.startswith("task-packets/")
        ):
            validate_frontmatter(path, text, result)
            detect_hook_would_modify(path, text, result)
        if re.match(r"^task-packets/.*\.json$", path.replace("\\", "/")):
            validate_task_packet_json(path, text, result, cwd)
        if path.endswith("PROOF.json") and path.startswith("proof/"):
            validate_proof_json(path, text, result, cwd)

    if any(f.severity == "error" for f in result.findings):
        result.status = "FAIL"
    else:
        result.status = "PASS"
    return result


def to_dict(result: Result) -> dict[str, Any]:
    return {
        "status": result.status,
        "max_lane": result.max_lane,
        "model_audit_required": result.model_audit_required,
        "proof_only": result.proof_only,
        "paths": result.paths,
        "findings": [asdict(f) for f in result.findings],
        "notes": result.notes,
        "model_call_budget": {
            "L0": {"implementer": 0, "auditor": 0},
            "L1": {"implementer": 1, "auditor": 0},
            "L2": {"implementer": 1, "auditor": 1},
            "L3": {"implementer": 1, "auditor": 1, "operator_gate": True},
        }.get(result.max_lane, {}),
    }


def format_text(result: Result) -> str:
    lines = [
        f"status={result.status}",
        f"max_lane={result.max_lane}",
        f"model_audit_required={result.model_audit_required}",
        f"proof_only={result.proof_only}",
        f"paths={len(result.paths)}",
    ]
    for row in result.paths:
        lines.append(f"  [{row['lane']}] {row['path']}")
    if result.notes:
        lines.append("notes:")
        for n in result.notes:
            lines.append(f"  - {n}")
    if result.findings:
        lines.append("findings:")
        for f in result.findings:
            loc = f" ({f.path})" if f.path else ""
            lines.append(f"  - [{f.severity}] {f.code}{loc}: {f.message}")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base", default=None, help="Git base ref (e.g. origin/main)")
    p.add_argument("--head", default="HEAD", help="Git head ref (default HEAD)")
    p.add_argument("--paths", nargs="*", help="Explicit paths (skip git diff)")
    p.add_argument("--repo", type=Path, default=REPO_ROOT, help="Repository root")
    p.add_argument("--format", choices=("text", "json"), default="text")
    p.add_argument("--proof-only", action="store_true", help="Force proof-only closure checks")
    p.add_argument(
        "--quarantine",
        action="store_true",
        help=(
            "Post-merge / exact-head-NOT_PROVEN quarantine mode: require content_head+proof_head, "
            "require PROOF.json status=SKIPPED, and forbid PROOF.json.sig"
        ),
    )
    p.add_argument("--content-head", default=None, help="Frozen content head SHA")
    p.add_argument("--proof-head", default=None, help="Proof-only successor head SHA")
    p.add_argument("--audited-head", default=None, help="Audited content head SHA")
    p.add_argument("--allowlist", nargs="*", help="If set, fail when changed path outside allowlist")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    cwd = args.repo.resolve()
    if not (cwd / ".git").exists() and not (cwd / "pyproject.toml").exists():
        print(f"error: not a repo root: {cwd}", file=sys.stderr)
        return 2

    # Honor pre-commit --from-ref/--to-ref range when present so the hook
    # validates the selected commit range, not an empty working tree.
    if args.base is None:
        env_base = os.environ.get("PRE_COMMIT_FROM_REF") or os.environ.get("PRE_COMMIT_ORIGIN")
        env_head = os.environ.get("PRE_COMMIT_TO_REF") or os.environ.get("PRE_COMMIT_SOURCE")
        if env_base:
            args.base = env_base
            if env_head and args.head == "HEAD":
                args.head = env_head

    try:
        if args.paths is not None and len(args.paths) > 0:
            paths = sorted({p.replace("\\", "/") for p in args.paths})
        elif args.base:
            paths = changed_paths(args.base, args.head, cwd)
        else:
            # Staged + unstaged vs HEAD (local commit without from-ref range)
            staged = _run_git(["diff", "--cached", "--name-only"], cwd)
            unstaged = _run_git(["diff", "--name-only"], cwd)
            paths = sorted(
                {
                    p.strip().replace("\\", "/")
                    for p in (staged + "\n" + unstaged).splitlines()
                    if p.strip()
                }
            )
            # Fail closed for always_run hook with no selected range and no paths:
            # require explicit base or paths rather than validating the empty set.
            if not paths and args.paths is None:
                print(
                    "error: no changed paths and no --base/PRE_COMMIT_FROM_REF; "
                    "refusing empty validation",
                    file=sys.stderr,
                )
                return 2
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = evaluate(
        paths=paths,
        cwd=cwd,
        head=args.head,
        proof_only_mode=args.proof_only or args.quarantine,
        content_head=args.content_head,
        proof_head=args.proof_head,
        audited_head=args.audited_head,
        quarantine_mode=args.quarantine,
        range_base=args.base,
    )

    if args.allowlist is not None:
        allow = {a.replace("\\", "/") for a in args.allowlist}
        # support ** style prefix: trailing /**
        def allowed(path: str) -> bool:
            for a in allow:
                if a.endswith("/**"):
                    if path.startswith(a[:-3]):
                        return True
                elif a.endswith("/*"):
                    if path.startswith(a[:-1]):
                        return True
                elif a == path:
                    return True
            return False

        for path in paths:
            if not allowed(path):
                result.add(
                    "allowlist_violation",
                    "error",
                    "Path outside provided allowlist",
                    path,
                )
        if any(f.severity == "error" for f in result.findings):
            result.status = "FAIL"

    if args.format == "json":
        sys.stdout.write(json.dumps(to_dict(result), indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(format_text(result))
    return 0 if result.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
