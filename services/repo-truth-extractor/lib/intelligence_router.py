import hashlib
import json
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# Bump this only for identity-shape changes that older import validators cannot
# safely interpret. Add each compatible historical version to the supported set.
PRESCAN_ARTIFACT_VERSION = "1.0"
SUPPORTED_PRESCAN_ARTIFACT_VERSIONS = frozenset({PRESCAN_ARTIFACT_VERSION})
REQUIRED_IMPORT_IDENTITY_FIELDS = (
    "repo_root",
    "source_root",
    "prescan_artifact_version",
    "corpus_manifest_hash",
)
PRESCAN_INFLUENCE_CLASSES = (
    "scope_reduction",
    "partition_reorder",
    "tier_override",
    "context_brief",
    "compression_hint",
    "routing_model_hint",
    "phase_hint",
)
_SOURCE_IDENTITY_CACHE: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}


def _normalize_path_value(value: Any) -> Optional[str]:
    token = str(value or "").strip()
    if not token:
        return None
    try:
        return str(Path(token).expanduser().resolve(strict=False))
    except Exception:
        return token


def _git_sha_for_root(root: Path) -> Optional[str]:
    try:
        value = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return None
    if not value or value.upper() == "UNKNOWN":
        return None
    return value


def _entry_value(entry: Any, key: str) -> Any:
    if isinstance(entry, dict):
        return entry.get(key)
    return getattr(entry, key, None)


def corpus_manifest_identity_hash(entries: Iterable[Any]) -> str:
    """Hash the deterministic source identity fields from a prescan manifest walk."""
    rows: list[dict[str, Any]] = []
    for entry in entries:
        rel_path = _entry_value(entry, "rel_path") or _entry_value(entry, "path")
        rows.append(
            {
                "content_hash": _entry_value(entry, "content_hash"),
                "exclude_reason": _entry_value(entry, "exclude_reason"),
                "extension": _entry_value(entry, "extension"),
                "include": bool(_entry_value(entry, "include")),
                "rel_path": str(rel_path or ""),
                "size_bytes": int(_entry_value(entry, "size_bytes") or 0),
            }
        )
    rows.sort(key=lambda item: item["rel_path"])
    payload = {
        "identity_schema": "prescan_corpus_manifest_identity_v1",
        "entries": rows,
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _walk_source_identity_entries(source_root: Path) -> list[Any]:
    try:
        from .prescan.corpus_walker import CorpusWalker
        from .prescan.models import DEFAULT_PRESCAN_EXCLUDE_GLOBS, PrescanConfig
    except ImportError:
        from lib.prescan.corpus_walker import CorpusWalker  # type: ignore
        from lib.prescan.models import DEFAULT_PRESCAN_EXCLUDE_GLOBS, PrescanConfig  # type: ignore

    config = PrescanConfig(
        repo_root=source_root,
        output_dir=source_root,
        enable_code_prescan=False,
        enable_git_enrichment=False,
        batch_mode=False,
        exclude_globs=list(DEFAULT_PRESCAN_EXCLUDE_GLOBS),
    )
    return CorpusWalker(config).walk()


def build_prescan_source_identity(
    repo_root: Path,
    source_root: Optional[Path] = None,
    *,
    git_sha: Optional[str] = None,
    entries: Optional[Iterable[Any]] = None,
    artifact_root: Optional[Path] = None,
    prescan_mode: str = "local_prescan",
) -> Dict[str, Any]:
    """Build local-only identity metadata used to decide whether imports are fresh."""
    current_source_root = source_root or repo_root
    current_git_sha = (
        git_sha
        if git_sha and git_sha.upper() != "UNKNOWN"
        else _git_sha_for_root(repo_root)
    )
    cache_key = None
    if entries is None and current_git_sha:
        cache_key = (
            str(repo_root.expanduser().resolve(strict=False)),
            str(current_source_root.expanduser().resolve(strict=False)),
            current_git_sha,
            prescan_mode,
        )
        cached = _SOURCE_IDENTITY_CACHE.get(cache_key)
        if cached is not None:
            identity = dict(cached)
            identity["artifact_root"] = (
                str(artifact_root.expanduser().resolve(strict=False))
                if artifact_root is not None
                else None
            )
            return identity
    source_entries = (
        list(entries)
        if entries is not None
        else _walk_source_identity_entries(current_source_root)
    )
    identity: Dict[str, Any] = {
        "artifact_root": (
            str(artifact_root.expanduser().resolve(strict=False))
            if artifact_root is not None
            else None
        ),
        "corpus_manifest_hash": corpus_manifest_identity_hash(source_entries),
        "git_sha": current_git_sha,
        "prescan_artifact_version": PRESCAN_ARTIFACT_VERSION,
        "prescan_mode": prescan_mode,
        "repo_root": str(repo_root.expanduser().resolve(strict=False)),
        "source_root": str(current_source_root.expanduser().resolve(strict=False)),
    }
    if cache_key is not None:
        cached_identity = dict(identity)
        cached_identity["artifact_root"] = None
        _SOURCE_IDENTITY_CACHE[cache_key] = cached_identity
    return identity


def _identity_field(data: Dict[str, Any], key: str) -> Any:
    source_identity = data.get("source_identity")
    if key in data:
        return data.get(key)
    if isinstance(source_identity, dict):
        return source_identity.get(key)
    return None


def _imported_identity_from_intelligence(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "corpus_manifest_hash": _identity_field(data, "corpus_manifest_hash"),
        "generated_at": _identity_field(data, "generated_at") or data.get("generated_at"),
        "git_sha": _identity_field(data, "git_sha"),
        "prescan_artifact_version": _identity_field(data, "prescan_artifact_version"),
        "prescan_mode": _identity_field(data, "prescan_mode"),
        "repo_root": _identity_field(data, "repo_root"),
        "run_id": _identity_field(data, "run_id"),
        "source_root": _identity_field(data, "source_root"),
    }


@dataclass
class PrescanImportValidation:
    mode: str
    verdict: str
    reason_codes: List[str] = field(default_factory=list)
    prescan_import_dir: Optional[str] = None
    repo_root_current: Optional[str] = None
    repo_root_imported_if_present: Optional[str] = None
    source_root_current: Optional[str] = None
    source_root_imported_if_present: Optional[str] = None
    git_sha_current_if_available: Optional[str] = None
    git_sha_imported_if_present: Optional[str] = None
    corpus_manifest_hash_current_if_available: Optional[str] = None
    corpus_manifest_hash_imported_if_present: Optional[str] = None
    prescan_artifact_version: Optional[str] = None
    can_influence_execution: bool = False
    advisory_only: bool = True
    generated_at: Optional[str] = None

    def to_receipt_fields(self) -> Dict[str, Any]:
        return {
            "advisory_only": self.advisory_only,
            "can_influence_execution": self.can_influence_execution,
            "corpus_manifest_hash_current_if_available": self.corpus_manifest_hash_current_if_available,
            "corpus_manifest_hash_imported_if_present": self.corpus_manifest_hash_imported_if_present,
            "generated_at_imported_if_present": self.generated_at,
            "git_sha_current_if_available": self.git_sha_current_if_available,
            "git_sha_imported_if_present": self.git_sha_imported_if_present,
            "mode": self.mode,
            "prescan_artifact_version": self.prescan_artifact_version,
            "prescan_import_dir": self.prescan_import_dir,
            "reason_codes": list(self.reason_codes),
            "repo_root_current": self.repo_root_current,
            "repo_root_imported_if_present": self.repo_root_imported_if_present,
            "source_root_current": self.source_root_current,
            "source_root_imported_if_present": self.source_root_imported_if_present,
            "verdict": self.verdict,
        }

    def rejected(self, reason_code: str) -> "PrescanImportValidation":
        codes = list(dict.fromkeys([*self.reason_codes, reason_code]))
        return PrescanImportValidation(
            advisory_only=True,
            can_influence_execution=False,
            corpus_manifest_hash_current_if_available=self.corpus_manifest_hash_current_if_available,
            corpus_manifest_hash_imported_if_present=self.corpus_manifest_hash_imported_if_present,
            generated_at=self.generated_at,
            git_sha_current_if_available=self.git_sha_current_if_available,
            git_sha_imported_if_present=self.git_sha_imported_if_present,
            mode="imported_prescan_rejected_stale",
            prescan_artifact_version=self.prescan_artifact_version,
            prescan_import_dir=self.prescan_import_dir,
            reason_codes=codes,
            repo_root_current=self.repo_root_current,
            repo_root_imported_if_present=self.repo_root_imported_if_present,
            source_root_current=self.source_root_current,
            source_root_imported_if_present=self.source_root_imported_if_present,
            verdict="rejected_stale",
        )


class IntelligenceRouter:
    ARTIFACT_VERSION = PRESCAN_ARTIFACT_VERSION

    def __init__(self, prescan_intelligence: Dict[str, Any]):
        self.intel = prescan_intelligence
        self.code_intel = prescan_intelligence.get("code_intelligence", {})
        self.hints = prescan_intelligence.get("extraction_hints", {})
        self.import_validation: Optional[PrescanImportValidation] = None

        # Pre-processed lookups
        self._base_skip_list = set(self.hints.get("skip_duplicates", []))
        self.skip_list = set(self._base_skip_list)
        # S3-07: compress_candidates schema permits bare strings OR objects. Index
        # objects by chain_id; normalize bare strings to a minimal record so an
        # imported, schema-valid prescan can't crash router construction with a
        # TypeError. Malformed members are skipped rather than fatal.
        self.compress_map = {}
        for c in self.hints.get("compress_candidates", []):
            if isinstance(c, dict) and "chain_id" in c:
                self.compress_map[c["chain_id"]] = c
            elif isinstance(c, str):
                self.compress_map[c] = {"chain_id": c}

        # Load topological order if available
        self.topological_order = self.code_intel.get("topological_order", [])
        self.topo_index = {path: i for i, path in enumerate(self.topological_order)}

        # Code intelligence report data
        self.code_report: Dict[str, Any] = {}
        self.processing_order: Dict[str, float] = {}
        self.orphan_set: Set[str] = set()
        self.partition_briefs: Dict[str, List[str]] = {}

        # Grok optimize pass data
        self._phase_routing: Dict[str, str] = {}
        self._model_routing: List[Dict[str, Any]] = []
        self._grok_skip_list: Set[str] = set()

        # Batch plan data
        self.batch_plan: Dict[str, Any] = {}
        self.archaeology_report: Dict[str, Any] = {}

        # Load grok optimize pass results if available
        grok_passes = prescan_intelligence.get("grok_passes", {})
        optimize = grok_passes.get("optimize", {})
        if optimize:
            self._grok_skip_list = set(optimize.get("skip_list", []))
            self.skip_list |= self._grok_skip_list
            for cc in optimize.get("compress_chains", []):
                if cc.get("send_summary_instead"):
                    self.compress_map[cc.get("chain_id", "")] = cc
            for pr in optimize.get("phase_routing_overrides", []):
                self._phase_routing[pr.get("path", "")] = pr.get("recommended_phase", "")
            self._model_routing = optimize.get("model_routing_hints", [])

            # Populate compress_candidates in hints
            if optimize.get("compress_chains"):
                self.hints.setdefault("compress_candidates", []).extend(
                    optimize["compress_chains"]
                )

    def _identity_dict(self) -> Dict[str, Any]:
        source_identity = self.intel.get("source_identity")
        return source_identity if isinstance(source_identity, dict) else {}

    def _source_roots(self) -> List[Path]:
        roots: List[Path] = []
        identity = self._identity_dict()
        for value in (
            identity.get("source_root"),
            identity.get("repo_root"),
            self.intel.get("source_root"),
            self.intel.get("repo_root"),
        ):
            token = str(value or "").strip()
            if not token:
                continue
            try:
                root = Path(token).expanduser().resolve(strict=False)
            except Exception:
                continue
            if root not in roots:
                roots.append(root)
        return roots

    def _path_keys(self, rel_path: str) -> List[str]:
        token = str(rel_path or "").strip()
        if not token:
            return []
        keys: List[str] = []

        def add(value: str) -> None:
            clean = value.strip()
            while clean.startswith("./"):
                clean = clean[2:]
            if clean and clean not in keys:
                keys.append(clean)

        add(token)
        try:
            path = Path(token)
            add(path.as_posix())
            if path.is_absolute():
                resolved = path.expanduser().resolve(strict=False)
                add(str(resolved))
                for root in self._source_roots():
                    try:
                        add(resolved.relative_to(root).as_posix())
                    except ValueError:
                        continue
        except Exception:
            pass
        return keys

    def _first_matching_key(self, rel_path: str, candidates: Iterable[str]) -> Optional[str]:
        candidate_set = {str(candidate) for candidate in candidates}
        for key in self._path_keys(rel_path):
            if key in candidate_set:
                return key
        return None

    def influence_common_fields(self) -> Dict[str, Any]:
        """Return non-secret common metadata for prescan influence proof labels."""
        if self.import_validation is not None:
            fields = self.import_validation.to_receipt_fields()
            mode = str(fields.get("mode") or "imported_prescan_accepted")
            return {
                "advisory_only": bool(fields.get("advisory_only", True)),
                "can_influence_execution": bool(
                    fields.get("can_influence_execution", False)
                ),
                "generated_at": fields.get("generated_at_imported_if_present")
                or self.intel.get("generated_at"),
                "influence_applied": False,
                "influence_classes": [],
                "prescan_import_dir_if_any": fields.get("prescan_import_dir"),
                "prescan_mode": mode,
                "prescan_verdict": fields.get("verdict") or "UNKNOWN",
                "reason_codes": list(fields.get("reason_codes") or []),
            }

        identity = self._identity_dict()
        mode = str(
            identity.get("prescan_mode")
            or self.intel.get("prescan_mode")
            or "local_prescan"
        )
        return {
            "advisory_only": False,
            "can_influence_execution": True,
            "generated_at": self.intel.get("generated_at"),
            "influence_applied": False,
            "influence_classes": [],
            "prescan_import_dir_if_any": None,
            "prescan_mode": mode,
            "prescan_verdict": "local_prescan" if mode == "local_prescan" else "accepted",
            "reason_codes": ["local_prescan_loaded"],
        }

    def can_influence_execution(self) -> bool:
        return bool(self.influence_common_fields().get("can_influence_execution"))

    def available_influence_classes(self) -> List[str]:
        classes: List[str] = []

        def add(class_name: str, condition: bool) -> None:
            if condition and class_name not in classes:
                classes.append(class_name)

        add("scope_reduction", bool(self.skip_list))
        add(
            "partition_reorder",
            bool(self.topological_order or self.processing_order),
        )
        add("context_brief", bool(self.code_report))
        add("compression_hint", bool(self.hints.get("compress_candidates")))
        add(
            "routing_model_hint",
            bool(self._model_routing),
        )
        add(
            "tier_override",
            bool(
                self._model_routing
                or self.code_report.get("hotspots")
                or self.code_report.get("pagerank_scores")
            ),
        )
        add("phase_hint", bool(self._phase_routing))
        return [
            class_name
            for class_name in PRESCAN_INFLUENCE_CLASSES
            if class_name in classes
        ]

    def get_scope_reduction_source(self, rel_path: str) -> Optional[str]:
        if self._first_matching_key(rel_path, self._grok_skip_list):
            return "prescan.grok_passes.optimize.skip_list"
        if self._first_matching_key(rel_path, self._base_skip_list):
            return "prescan.extraction_hints.skip_duplicates"
        if self._first_matching_key(rel_path, self.skip_list):
            return "prescan.skip_list"
        return None

    def get_compression_hint_source(self, rel_path: str) -> Optional[str]:
        path_keys = set(self._path_keys(rel_path))
        for chain_id, members in self.intel.get("version_chains", {}).items():
            paths = {str(m.get("path") or "") for m in members if isinstance(m, dict)}
            if not path_keys.intersection(paths):
                continue
            for candidate in self.hints.get("compress_candidates", []):
                if (
                    candidate.get("chain_id") == chain_id
                    and candidate.get("send_summary_instead")
                ):
                    return "prescan.extraction_hints.compress_candidates"
        return None

    def get_model_routing_hint_details(self, rel_path: str) -> Optional[Dict[str, Any]]:
        import fnmatch as _fnmatch

        path_keys = self._path_keys(rel_path)
        for hint in self._model_routing:
            pattern = str(hint.get("partition_pattern") or "")
            if any(_fnmatch.fnmatch(path_key, pattern) for path_key in path_keys):
                hinted = (
                    hint.get("recommended_model")
                    or hint.get("suggested_model")
                    or hint.get("model_id")
                    or hint.get("provider")
                )
                return {
                    "hinted_provider_or_model_if_present": hinted,
                    "hint_source": "prescan.grok_passes.optimize.model_routing_hints",
                }
        return None

    def get_tier_override_source(self, rel_path: str) -> Optional[str]:
        if self.get_model_routing_hint_details(rel_path):
            return "prescan.grok_passes.optimize.model_routing_hints"
        path_key = self._first_matching_key(
            rel_path,
            [
                str(h.get("rel_path") or "")
                for h in self.code_report.get("hotspots", [])
                if isinstance(h, dict) and h.get("hotspot_score", 0) > 0.7
            ],
        )
        if path_key:
            return "prescan.code_intelligence_report.hotspots"
        if self._first_matching_key(
            rel_path,
            self.code_report.get("pagerank_scores", {}).keys(),
        ):
            return "prescan.code_intelligence_report.pagerank_scores"
        return None

    @classmethod
    def validate_import_dir(
        cls,
        prescan_dir: Path,
        *,
        current_repo_root: Path,
        current_source_root: Optional[Path] = None,
        current_git_sha: Optional[str] = None,
        current_corpus_manifest_hash: Optional[str] = None,
    ) -> PrescanImportValidation:
        import_dir = prescan_dir.expanduser().resolve(strict=False)
        repo_current = _normalize_path_value(current_repo_root)
        source_current = _normalize_path_value(current_source_root or current_repo_root)
        git_current = (
            current_git_sha
            if current_git_sha and current_git_sha.upper() != "UNKNOWN"
            else _git_sha_for_root(current_repo_root)
        )
        base = PrescanImportValidation(
            mode="imported_prescan_rejected_stale",
            verdict="rejected_stale",
            prescan_import_dir=str(import_dir),
            repo_root_current=repo_current,
            source_root_current=source_current,
            git_sha_current_if_available=git_current,
        )

        intel_path = import_dir / "prescan_intelligence.json"
        if not intel_path.exists():
            return base.rejected("missing_prescan_intelligence")

        try:
            with open(intel_path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return base.rejected("prescan_intelligence_parse_failed")
        if not isinstance(data, dict):
            return base.rejected("prescan_intelligence_not_object")

        imported_identity = _imported_identity_from_intelligence(data)
        repo_imported = _normalize_path_value(imported_identity.get("repo_root"))
        source_imported = _normalize_path_value(imported_identity.get("source_root"))
        version = (
            str(imported_identity.get("prescan_artifact_version")).strip()
            if imported_identity.get("prescan_artifact_version") is not None
            else None
        )
        corpus_hash_imported = (
            str(imported_identity.get("corpus_manifest_hash")).strip()
            if imported_identity.get("corpus_manifest_hash") is not None
            else None
        )
        git_imported = (
            str(imported_identity.get("git_sha")).strip()
            if imported_identity.get("git_sha") is not None
            else None
        )
        validation = PrescanImportValidation(
            mode="imported_prescan_rejected_stale",
            verdict="rejected_stale",
            prescan_import_dir=str(import_dir),
            repo_root_current=repo_current,
            repo_root_imported_if_present=repo_imported,
            source_root_current=source_current,
            source_root_imported_if_present=source_imported,
            git_sha_current_if_available=git_current,
            git_sha_imported_if_present=git_imported,
            corpus_manifest_hash_imported_if_present=corpus_hash_imported,
            prescan_artifact_version=version,
            generated_at=(
                str(imported_identity.get("generated_at"))
                if imported_identity.get("generated_at") is not None
                else None
            ),
        )

        missing = [
            identity_field_name
            for identity_field_name in REQUIRED_IMPORT_IDENTITY_FIELDS
            if imported_identity.get(identity_field_name) in (None, "")
        ]
        if missing:
            validation.mode = "imported_prescan_missing_metadata"
            validation.verdict = "missing_metadata"
            validation.reason_codes = [
                f"missing_{identity_field_name}"
                for identity_field_name in missing
            ]
            validation.advisory_only = True
            validation.can_influence_execution = False
            return validation

        if version not in SUPPORTED_PRESCAN_ARTIFACT_VERSIONS:
            return validation.rejected("unsupported_prescan_artifact_version")

        corpus_hash_current = current_corpus_manifest_hash
        if not corpus_hash_current:
            try:
                current_identity = build_prescan_source_identity(
                    current_repo_root,
                    current_source_root or current_repo_root,
                    git_sha=git_current,
                )
                corpus_hash_current = str(current_identity["corpus_manifest_hash"])
            except Exception:
                return validation.rejected("current_corpus_manifest_hash_unavailable")
        validation.corpus_manifest_hash_current_if_available = str(corpus_hash_current)

        if repo_imported != repo_current:
            return validation.rejected("repo_root_mismatch")
        if source_imported != source_current:
            return validation.rejected("source_root_mismatch")
        if corpus_hash_imported != str(corpus_hash_current):
            return validation.rejected("corpus_manifest_hash_mismatch")
        if git_current and git_imported and git_current != git_imported:
            return validation.rejected("git_sha_mismatch")

        reason_codes = ["identity_match"]
        if not git_imported:
            reason_codes.append("warn_missing_git_sha_imported")
        if not git_current:
            reason_codes.append("warn_missing_git_sha_current")
        return PrescanImportValidation(
            advisory_only=False,
            can_influence_execution=True,
            corpus_manifest_hash_current_if_available=str(corpus_hash_current),
            corpus_manifest_hash_imported_if_present=corpus_hash_imported,
            generated_at=validation.generated_at,
            git_sha_current_if_available=git_current,
            git_sha_imported_if_present=git_imported,
            mode="imported_prescan_accepted",
            prescan_artifact_version=version,
            prescan_import_dir=str(import_dir),
            reason_codes=reason_codes,
            repo_root_current=repo_current,
            repo_root_imported_if_present=repo_imported,
            source_root_current=source_current,
            source_root_imported_if_present=source_imported,
            verdict="accepted",
        )

    @classmethod
    def load_imported(
        cls,
        prescan_dir: Path,
        *,
        current_repo_root: Path,
        current_source_root: Optional[Path] = None,
        current_git_sha: Optional[str] = None,
        current_corpus_manifest_hash: Optional[str] = None,
    ) -> Tuple[Optional["IntelligenceRouter"], PrescanImportValidation]:
        validation = cls.validate_import_dir(
            prescan_dir,
            current_repo_root=current_repo_root,
            current_source_root=current_source_root,
            current_git_sha=current_git_sha,
            current_corpus_manifest_hash=current_corpus_manifest_hash,
        )
        if not validation.can_influence_execution:
            return None, validation
        router = cls.from_dir(prescan_dir)
        if router is None:
            return None, validation.rejected("router_load_failed_after_validation")
        router.import_validation = validation
        return router, validation

    @classmethod
    def from_dir(cls, prescan_dir: Path) -> Optional["IntelligenceRouter"]:
        intel_path = prescan_dir / "prescan_intelligence.json"
        if not intel_path.exists():
            return None

        try:
            with open(intel_path, encoding="utf-8") as f:
                data = json.load(f)
            router = cls(data)

            # Load code intelligence report
            code_report_path = prescan_dir / "code_intelligence_report.json"
            if code_report_path.exists():
                with open(code_report_path, encoding="utf-8") as f:
                    router.code_report = json.load(f)
                # Build processing order lookup
                for entry in router.code_report.get("processing_order", []):
                    router.processing_order[entry["rel_path"]] = entry["score"]
                # Build orphan set (confidence >= 0.7)
                for orphan in router.code_report.get("orphans", []):
                    if orphan.get("confidence", 0) >= 0.7:
                        router.orphan_set.add(orphan["rel_path"])

            # Load batch plan
            batch_plan_path = prescan_dir / "batch_plan.json"
            if batch_plan_path.exists():
                with open(batch_plan_path, encoding="utf-8") as f:
                    router.batch_plan = json.load(f)

            # Load archaeology report
            arch_path = prescan_dir / "archaeology_report.json"
            if arch_path.exists():
                with open(arch_path, encoding="utf-8") as f:
                    router.archaeology_report = json.load(f)

            return router
        except Exception as e:
            logger.error(f"Failed to load intelligence router: {e}")
            return None

    def should_skip(self, rel_path: str) -> bool:
        """Check if a file should be skipped based on prescan."""
        return self._first_matching_key(rel_path, self.skip_list) is not None

    def get_compression_hint(self, rel_path: str) -> Optional[str]:
        """Return a summary hint if this file is part of a compressed version chain."""
        path_keys = set(self._path_keys(rel_path))
        for chain_id, members in self.intel.get("version_chains", {}).items():
            paths = {str(m.get("path") or "") for m in members if isinstance(m, dict)}
            if path_keys.intersection(paths):
                for cc in self.hints.get("compress_candidates", []):
                    if cc.get("chain_id") == chain_id and cc.get("send_summary_instead"):
                        return cc.get("summary_hint", "Superseded by newer version.")
        return None

    def get_routing_priority(self, rel_path: str) -> int:
        """Return priority score (higher = extract earlier/more detail)."""
        priority = 50
        key = self._first_matching_key(rel_path, self.topo_index.keys())
        if key is not None:
            priority += (100 - min(self.topo_index[key], 50))
        return priority

    def get_composite_priority(self, rel_path: str) -> float:
        """Returns composite priority score (0-1). Higher = extract first."""
        key = self._first_matching_key(rel_path, self.processing_order.keys())
        return self.processing_order.get(key, 0.5) if key is not None else 0.5

    def should_skip_code(self, rel_path: str) -> bool:
        """Dead code deprioritization (advisory only, never auto-skip).

        Returns True if confidence >= 0.7 (unreachable + zero importers).
        Never returns True for entry points, test files, or config files.
        """
        return self._first_matching_key(rel_path, self.orphan_set) is not None

    def get_model_tier(self, rel_path: str) -> str:
        """Route complex/important files to better models.

        Returns 'premium', 'standard', or 'economy'.
        """
        # Check grok optimize model routing hints
        import fnmatch as _fnmatch
        path_keys = self._path_keys(rel_path)
        for hint in self._model_routing:
            pattern = hint.get("partition_pattern", "")
            if any(_fnmatch.fnmatch(path_key, pattern) for path_key in path_keys):
                # S3-03: the LLM-emitted recommended_model is free text. Only the three
                # tier tokens are honored downstream; anything else (e.g. a raw model
                # name) was previously returned verbatim and then silently dropped while
                # still being labeled applied=True. Coerce to the valid tier set here so
                # the value the engine consumes and the influence label always agree.
                recommended = hint.get("recommended_model", "standard")
                return recommended if recommended in ("premium", "standard", "economy") else "standard"

        # Check code intelligence
        if self.code_report:
            hotspots = self.code_report.get("hotspots", [])
            for h in hotspots[:10]:  # Top 10 hotspots
                if (
                    self._first_matching_key(rel_path, [h.get("rel_path")])
                    and h.get("hotspot_score", 0) > 0.7
                ):
                    return "premium"

            pagerank = self.code_report.get("pagerank_scores", {})
            if pagerank:
                scores = sorted(pagerank.values(), reverse=True)
                top_10_pct = scores[max(0, len(scores) // 10)] if scores else 0
                key = self._first_matching_key(rel_path, pagerank.keys())
                if key and pagerank.get(key, 0) >= top_10_pct and top_10_pct > 0:
                    return "premium"

        return "standard"

    def get_partition_brief(self, phase_key: str, partition_idx: int) -> Optional[str]:
        """Retrieve pre-generated context brief for a specific partition."""
        briefs = self.partition_briefs.get(phase_key, [])
        if partition_idx < len(briefs):
            return briefs[partition_idx]
        return None

    def get_phase_routing_override(self, rel_path: str) -> Optional[str]:
        """Return phase override from optimize pass, or None."""
        key = self._first_matching_key(rel_path, self._phase_routing.keys())
        return self._phase_routing.get(key) if key is not None else None

    def get_model_routing_hint(self, rel_path: str) -> Optional[str]:
        """Return model routing hint from optimize pass, or None."""
        details = self.get_model_routing_hint_details(rel_path)
        return (
            str(details.get("hinted_provider_or_model_if_present"))
            if details and details.get("hinted_provider_or_model_if_present")
            else None
        )

    def get_test_file(self, rel_path: str) -> Optional[str]:
        """Return mapped test file path, or None."""
        for mapping in self.code_report.get("test_mappings", []):
            if self._first_matching_key(rel_path, [mapping.get("source_path")]):
                return mapping.get("test_path")
        return None

    def get_bundling_group(self, rel_path: str) -> Optional[str]:
        """Suggest a bundling group (e.g. dependency cluster)."""
        for i, cluster in enumerate(self.code_intel.get("dependency_clusters", [])):
            if self._first_matching_key(rel_path, cluster):
                return f"cluster_{i}"
        return None

    def estimate_token_savings(self, manifest: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Estimate token savings based on skip/compress rules."""
        stats = self.intel.get("corpus_summary", {})
        total_size = stats.get("total_included_size_bytes", 0)

        skipped_size = 0
        if manifest:
            for m in manifest:
                if m.get("rel_path") in self.skip_list:
                    skipped_size += m.get("size_bytes", 0)

        reduction_pct = round((skipped_size / total_size * 100), 1) if total_size > 0 else 0

        return {
            "skipped_files_count": len(self.skip_list),
            "skipped_bytes": skipped_size,
            "total_bytes": total_size,
            "estimated_reduction_pct": reduction_pct,
        }

    def reorder_partition(self, partition_files: List[str]) -> List[str]:
        """Reorder files within a partition by composite priority (descending)."""
        return sorted(
            partition_files,
            key=lambda f: self.get_composite_priority(f),
            reverse=True,
        )
