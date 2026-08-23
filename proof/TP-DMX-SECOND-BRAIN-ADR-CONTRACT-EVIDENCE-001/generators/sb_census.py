"""Fresh exhaustive census of the ratified Second Brain ADR candidate.

This replaces the superseded 97-clause denominator whose authority was the task
packet's own §5 list.  §5 calls itself a *minimum*, and the first independent
audit proved the derived denominator was materially incomplete (MUST_FIX 1) and
contained at least one authority value — ``dopeTask`` — that appears nowhere in
the candidate (BLOCKER 2).

Authority for this census is the operator ruling of 2026-08-12, reproduced
verbatim in DENOMINATOR_REFREEZE_RECEIPT.json.  Every clause below is derived by
reading the candidate document itself, sentence by sentence, under the operator's
INCLUDE / DO-NOT-INCLUDE rule.

Rule shapes are deliberately narrow.  Every clause must be *testable*: a label
like ``PURGE_DEPENDENCY_GRAPH`` states that something is named, not that anything
must be true, so no rule shape below can carry one (MUST_FIX 4).

    BOOLEAN               EQUALS              true | false
    NUMERIC               EQUALS | LESS_THAN_OR_EQUAL     int
    ENUM                  SET_EQUALS          list[str]  + source_enumeration
    CONSTANT              EQUALS              str        (normalized-grounded)
    AUTHORITY_TARGET      EQUALS              str        (normalized-grounded)
    AUTHORITY_TARGET      SET_EQUALS          list[str]  + source_enumeration
    INTERFACE_REQUIREMENT MUST_EXIST          str        (verbatim in candidate)

`section` records which subsection each clause's fragments come from.  The
validator rejects any clause grounded in a "Rejected alternatives" subsection:
"Vector-first answer generation" is verbatim candidate text, so without a
provenance rule a clause could cite a *rejected* design as its own grounding.
Rejected alternatives are adversarial oracles only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

CANDIDATE_PATH = (
    "docs/03-reference/architecture/second-brain/adr-candidates/"
    "second-brain-adr-candidates.md"
)

CONTEXT = "CONTEXT"
DECISION = "PROPOSED_DECISION"
MA06 = "MA06_AMENDMENT"
CONSEQ = "CONSEQUENCES"


@dataclass(frozen=True)
class Clause:
    suffix: str
    requirement_text: str
    subject: str
    rule_type: str
    operator: str
    machine_value: object
    section: str
    fragments: tuple[str, ...]
    source_enumeration: str | None = None
    covering: tuple[str, ...] = field(default=())
    prior_clause_id: str | None = None
    change: str = "ADDED"  # ADDED | UNCHANGED | MODIFIED


@dataclass(frozen=True)
class Adr:
    adr_id: str
    title: str
    sb_dec: tuple[str, ...]
    clauses: tuple[Clause, ...]


def _c(
    suffix,
    text,
    subject,
    rule_type,
    operator,
    value,
    section,
    fragments,
    enumeration=None,
    covering=(),
    prior=None,
    change="ADDED",
):
    return Clause(
        suffix=suffix,
        requirement_text=text,
        subject=subject,
        rule_type=rule_type,
        operator=operator,
        machine_value=value,
        section=section,
        fragments=tuple(fragments),
        source_enumeration=enumeration,
        covering=tuple(covering),
        prior_clause_id=prior,
        change=change,
    )


# --------------------------------------------------------------------------
# ADR-SB-001 — Extension Boundary and Non-Authority
# --------------------------------------------------------------------------

F001_OWNS = (
    "It owns control logic, derived read models, projections, local spool "
    "coordination, purge coordination, and receipts only."
)

ADR_001 = Adr(
    "ADR-SB-001",
    "Extension Boundary and Non-Authority",
    ("SB-DEC-001", "SB-DEC-002", "SB-DEC-027"),
    (
        _c("C01", "Second Brain is an extension, not a memory plane",
           "second_brain.form", "CONSTANT", "EQUALS", "EXTENSION",
           DECISION, ["Create a Dopemux PCP/DCP-compatible extension."],
           prior="ADR-SB-001-C01", change="MODIFIED"),
        _c("C02", "no canonical Second Brain database exists",
           "second_brain.canonical_database.exists", "BOOLEAN", "EQUALS", False,
           CONSEQ, ["No canonical SB database"],
           prior="ADR-SB-001-C02", change="MODIFIED"),
        _c("C03", "canonical writes target an existing authority",
           "second_brain.canonical_write.target_is_existing_authority",
           "BOOLEAN", "EQUALS", True,
           DECISION, ["Canonical writes go to existing authorities."],
           prior="ADR-SB-001-C03", change="MODIFIED"),
        _c("C04", "derived read models are not canonical",
           "second_brain.derived_read_model.canonical", "BOOLEAN", "EQUALS", False,
           DECISION, [F001_OWNS, "Canonical writes go to existing authorities."],
           prior="ADR-SB-001-C04", change="MODIFIED"),
        _c("C05", "coordination responsibilities confer no authority",
           "second_brain.coordination.confers_authority", "BOOLEAN", "EQUALS", False,
           DECISION, [F001_OWNS, "Canonical writes go to existing authorities."],
           prior="ADR-SB-001-C05", change="MODIFIED"),
        _c("C06", "the extension can be disabled without changing canonical stores",
           "second_brain.disable.requires_canonical_store_change",
           "BOOLEAN", "EQUALS", False,
           CONSEQ, ["Disable extension without changing canonical stores"],
           prior="ADR-SB-001-C06", change="MODIFIED"),
        _c("C07", "no fourth canonical memory plane is created",
           "second_brain.creates_fourth_canonical_memory_plane",
           "BOOLEAN", "EQUALS", False,
           CONTEXT, ["forbids a fourth canonical memory plane"]),
        _c("C08", "the extension is PCP/DCP compatible",
           "second_brain.pcp_dcp_compatible", "BOOLEAN", "EQUALS", True,
           DECISION, ["Create a Dopemux PCP/DCP-compatible extension."]),
        _c("C09", "closed set of what the extension owns",
           "second_brain.owned_responsibilities", "ENUM", "SET_EQUALS",
           ["CONTROL_LOGIC", "DERIVED_READ_MODELS", "PROJECTIONS",
            "LOCAL_SPOOL_COORDINATION", "PURGE_COORDINATION", "RECEIPTS"],
           DECISION, [F001_OWNS],
           enumeration=("control logic, derived read models, projections, local "
                        "spool coordination, purge coordination, and receipts")),
        _c("C10", "one package",
           "second_brain.deployment.package_count", "NUMERIC", "EQUALS", 1,
           CONSEQ, ["One package plus optional worker"]),
        _c("C11", "the worker is optional",
           "second_brain.deployment.worker_required", "BOOLEAN", "EQUALS", False,
           CONSEQ, ["One package plus optional worker"]),
    ),
)


# --------------------------------------------------------------------------
# ADR-SB-002 — Capture, Candidate, Review, and Promotion
# --------------------------------------------------------------------------

F002_CTX = (
    "Automatic capture must not silently promote candidates or mutate "
    "downstream authorities."
)

ADR_002 = Adr(
    "ADR-SB-002",
    "Capture, Candidate, Review, and Promotion",
    ("SB-DEC-003", "SB-DEC-004", "SB-DEC-005", "SB-DEC-006"),
    (
        _c("C01", "captured events are appended to Dope-Memory",
           "second_brain.capture.captured_event.append_target",
           "AUTHORITY_TARGET", "EQUALS", "Dope-Memory",
           DECISION, ["Append captured events and candidates to Dope-Memory"],
           prior="ADR-SB-002-C01", change="UNCHANGED"),
        _c("C02", "candidates are appended to Dope-Memory",
           "second_brain.capture.candidate.append_target",
           "AUTHORITY_TARGET", "EQUALS", "Dope-Memory",
           DECISION, ["Append captured events and candidates to Dope-Memory"],
           prior="ADR-SB-002-C02", change="UNCHANGED"),
        _c("C03", "the review read model is not canonical",
           "second_brain.review.read_model.canonical", "BOOLEAN", "EQUALS", False,
           DECISION, ["build a non-canonical review read model"],
           prior="ADR-SB-002-C03", change="MODIFIED"),
        _c("C04", "review is digest-bound",
           "second_brain.review.digest_bound", "BOOLEAN", "EQUALS", True,
           DECISION, ["require digest-bound affirmative review"],
           prior="ADR-SB-002-C04", change="MODIFIED"),
        _c("C05", "the review default disposition is DEFER",
           "second_brain.review.default_disposition", "CONSTANT", "EQUALS", "DEFER",
           CONSEQ, ["Default DEFER/NO MUTATION"],
           prior="ADR-SB-002-C05", change="MODIFIED"),
        _c("C06", "approved actions route to an exact canonical target",
           "second_brain.approved_action.routes_to_exact_canonical_target",
           "BOOLEAN", "EQUALS", True,
           DECISION, ["route approved actions to exact canonical targets"],
           prior="ADR-SB-002-C06", change="MODIFIED"),
        _c("C07", "promotion receipts are appended to Dope-Memory",
           "second_brain.promotion.receipt.append_target",
           "AUTHORITY_TARGET", "EQUALS", "Dope-Memory",
           DECISION, ["append promotion receipts to Dope-Memory"],
           prior="ADR-SB-002-C07", change="UNCHANGED"),
        _c("C08", "no cross-authority transaction is claimed",
           "second_brain.promotion.cross_authority_transaction",
           "BOOLEAN", "EQUALS", False,
           CONSEQ, ["No cross-authority transaction fiction"],
           prior="ADR-SB-002-C08", change="MODIFIED"),
        _c("C09", "the review default performs no mutation",
           "second_brain.review.default_mutation_performed",
           "BOOLEAN", "EQUALS", False,
           CONSEQ, ["Default DEFER/NO MUTATION"]),
        _c("C10", "review must be affirmative",
           "second_brain.review.affirmative_required", "BOOLEAN", "EQUALS", True,
           DECISION, ["require digest-bound affirmative review"]),
        _c("C11", "capture never silently promotes a candidate",
           "second_brain.capture.silent_promotion", "BOOLEAN", "EQUALS", False,
           CONTEXT, [F002_CTX]),
        _c("C12", "capture never silently mutates a downstream authority",
           "second_brain.capture.silent_downstream_authority_mutation",
           "BOOLEAN", "EQUALS", False,
           CONTEXT, [F002_CTX]),
        _c("C13", "candidate history is replayable",
           "second_brain.candidate_history.replayable", "BOOLEAN", "EQUALS", True,
           CONSEQ, ["Replayable candidate history"]),
        _c("C14", "capture is append-only",
           "second_brain.capture.append_only", "BOOLEAN", "EQUALS", True,
           DECISION, ["Append captured events and candidates to Dope-Memory"]),
    ),
)


# --------------------------------------------------------------------------
# ADR-SB-003 — Recall Fusion and Provenance
# --------------------------------------------------------------------------

F003_CTX = (
    "Recall spans structured authority, chronology, source-native state, and "
    "advisory retrieval without allowing search rank to become truth."
)
F003_DEC = (
    "Use deterministic authority-first fusion with pre-model policy filtering, "
    "freshness and contradiction detection, bounded advisory retrieval, and "
    "evidence/access/uncertainty metadata on every response."
)

ADR_003 = Adr(
    "ADR-SB-003",
    "Recall Fusion and Provenance",
    ("SB-DEC-016", "SB-DEC-017"),
    (
        _c("C01", "recall fusion is authority-first",
           "second_brain.recall.fusion.authority_first", "BOOLEAN", "EQUALS", True,
           DECISION, [F003_DEC],
           prior="ADR-SB-003-C01", change="MODIFIED"),
        _c("C02", "policy filtering occurs before model context assembly",
           "second_brain.recall.policy_filtering.occurs_before_model_context",
           "BOOLEAN", "EQUALS", True,
           DECISION, [F003_DEC],
           prior="ADR-SB-003-C02", change="MODIFIED"),
        _c("C03", "freshness detection is required",
           "second_brain.recall.freshness_detection.required",
           "BOOLEAN", "EQUALS", True,
           DECISION, [F003_DEC],
           prior="ADR-SB-003-C03", change="MODIFIED"),
        _c("C04", "contradiction detection is required",
           "second_brain.recall.contradiction_detection.required",
           "BOOLEAN", "EQUALS", True,
           DECISION, [F003_DEC],
           prior="ADR-SB-003-C04", change="MODIFIED"),
        _c("C05", "advisory retrieval is bounded",
           "second_brain.recall.advisory_retrieval.bounded",
           "BOOLEAN", "EQUALS", True,
           DECISION, [F003_DEC],
           prior="ADR-SB-003-C05", change="MODIFIED"),
        _c("C06", "response metadata set = evidence / access / uncertainty",
           "second_brain.recall.response.required_metadata", "ENUM", "SET_EQUALS",
           ["EVIDENCE", "ACCESS", "UNCERTAINTY"],
           DECISION, [F003_DEC],
           enumeration="evidence/access/uncertainty",
           prior="ADR-SB-003-C06", change="MODIFIED"),
        _c("C07", "partial outages are explicit",
           "second_brain.recall.partial_outage.explicit", "BOOLEAN", "EQUALS", True,
           CONSEQ, ["Partial outages are explicit"],
           prior="ADR-SB-003-C07", change="MODIFIED"),
        _c("C08", "search rank never becomes truth",
           "second_brain.recall.search_rank_is_truth", "BOOLEAN", "EQUALS", False,
           CONTEXT, [F003_CTX],
           prior="ADR-SB-003-C08", change="MODIFIED"),
        _c("C09", "fusion is deterministic",
           "second_brain.recall.fusion.deterministic", "BOOLEAN", "EQUALS", True,
           DECISION, [F003_DEC]),
        _c("C10", "closed set of recall source classes",
           "second_brain.recall.source_classes", "ENUM", "SET_EQUALS",
           ["STRUCTURED_AUTHORITY", "CHRONOLOGY", "SOURCE_NATIVE_STATE",
            "ADVISORY_RETRIEVAL"],
           CONTEXT, [F003_CTX],
           enumeration=("structured authority, chronology, source-native state, "
                        "and advisory retrieval")),
        _c("C11", "recall output is answer-first",
           "second_brain.recall.output.answer_first", "BOOLEAN", "EQUALS", True,
           CONSEQ, ["Answer-first output"]),
        _c("C12", "historical state and current state remain distinct",
           "second_brain.recall.historical_and_current_state_distinct",
           "BOOLEAN", "EQUALS", True,
           CONSEQ, ["Historical and current states remain distinct"]),
        _c("C13", "required metadata appears on every response",
           "second_brain.recall.response.metadata_required_on_every_response",
           "BOOLEAN", "EQUALS", True,
           DECISION, [F003_DEC]),
    ),
)


# --------------------------------------------------------------------------
# ADR-SB-004 — Domain, Classification, and Provider Policy
# --------------------------------------------------------------------------

F004_CTX = (
    "Domain and classification are separate dimensions, and unknown eligibility "
    "cannot be safely inferred by a model."
)
F004_EVAL = (
    "Evaluate identity, grants, provider, embedding, custody, backup, and "
    "operation policy before retrieval disclosure or model context assembly."
)

ADR_004 = Adr(
    "ADR-SB-004",
    "Domain, Classification, and Provider Policy",
    ("SB-DEC-010", "SB-DEC-011", "SB-DEC-012"),
    (
        _c("C01", "domain set = project / hue / dom / shared",
           "second_brain.policy.domain", "ENUM", "SET_EQUALS",
           ["PROJECT", "HUE", "DOM", "SHARED"],
           DECISION, ["Use project/hue/dom/shared"],
           enumeration="project/hue/dom/shared",
           prior="ADR-SB-004-C01", change="MODIFIED"),
        _c("C02", "classification set = public / internal / confidential / restricted",
           "second_brain.policy.classification", "ENUM", "SET_EQUALS",
           ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"],
           DECISION, ["public/internal/confidential/restricted"],
           enumeration="public/internal/confidential/restricted",
           prior="ADR-SB-004-C02", change="MODIFIED"),
        _c("C03", "policy evaluation precedes retrieval disclosure",
           "second_brain.policy.evaluation.occurs_before_retrieval_disclosure",
           "BOOLEAN", "EQUALS", True,
           DECISION, [F004_EVAL],
           prior="ADR-SB-004-C03", change="MODIFIED"),
        _c("C04", "unknown eligibility denies",
           "second_brain.policy.eligibility.unknown_denies",
           "BOOLEAN", "EQUALS", True,
           DECISION, ["Unknown denies."],
           prior="ADR-SB-004-C04", change="MODIFIED"),
        _c("C05", "the dom domain is synthetic-only",
           "second_brain.policy.domain.dom.data_path", "CONSTANT", "EQUALS",
           "SYNTHETIC_ONLY",
           CONSEQ, ["Dom synthetic-only"],
           prior="ADR-SB-004-C05", change="UNCHANGED"),
        _c("C06", "the shared domain requires a grant",
           "second_brain.policy.domain.shared.requires_grant",
           "BOOLEAN", "EQUALS", True,
           CONSEQ, ["Shared disabled without grant"],
           prior="ADR-SB-004-C06", change="UNCHANGED"),
        _c("C07", "confidential/restricted semantic indexing is disabled",
           "second_brain.policy.semantic_indexing.confidential_restricted_enabled",
           "BOOLEAN", "EQUALS", False,
           CONSEQ, ["No confidential/restricted semantic indexing in v1"],
           prior="ADR-SB-004-C07", change="MODIFIED"),
        _c("C08", "policy evaluation precedes model context assembly",
           "second_brain.policy.evaluation.occurs_before_model_context_assembly",
           "BOOLEAN", "EQUALS", True,
           DECISION, [F004_EVAL]),
        _c("C09", "closed set of policy evaluation dimensions",
           "second_brain.policy.evaluation.dimensions", "ENUM", "SET_EQUALS",
           ["IDENTITY", "GRANTS", "PROVIDER", "EMBEDDING", "CUSTODY", "BACKUP",
            "OPERATION"],
           DECISION, [F004_EVAL],
           enumeration=("identity, grants, provider, embedding, custody, backup, "
                        "and operation")),
        _c("C10", "domain and classification are separate dimensions",
           "second_brain.policy.domain_and_classification_are_separate_dimensions",
           "BOOLEAN", "EQUALS", True,
           CONTEXT, [F004_CTX]),
        _c("C11", "a model may not infer unknown eligibility",
           "second_brain.policy.unknown_eligibility.model_inference_permitted",
           "BOOLEAN", "EQUALS", False,
           CONTEXT, [F004_CTX]),
    ),
)


# --------------------------------------------------------------------------
# ADR-SB-005 — Markdown Projection Contract
# --------------------------------------------------------------------------

F005_CTX = (
    "Operators benefit from readable durable views, but Markdown and Obsidian "
    "must not become accidental authorities."
)
F005_DEC = (
    "Compile deterministic Markdown from canonical snapshot revisions with "
    "stable paths, managed/manual regions, visible freshness, content hashes, "
    "purge propagation, and no silent write-back."
)

ADR_005 = Adr(
    "ADR-SB-005",
    "Markdown Projection Contract",
    ("SB-DEC-018", "SB-DEC-019"),
    (
        _c("C01", "projection derives from canonical snapshot revisions",
           "second_brain.projection.source", "CONSTANT", "EQUALS",
           "CANONICAL_SNAPSHOT_REVISION",
           DECISION, [F005_DEC],
           prior="ADR-SB-005-C01", change="UNCHANGED"),
        _c("C02", "projection paths are stable",
           "second_brain.projection.path_stability", "CONSTANT", "EQUALS", "STABLE",
           DECISION, [F005_DEC],
           prior="ADR-SB-005-C02", change="UNCHANGED"),
        _c("C03", "region kinds = managed / manual",
           "second_brain.projection.region_kinds", "ENUM", "SET_EQUALS",
           ["MANAGED", "MANUAL"],
           DECISION, [F005_DEC],
           enumeration="managed/manual",
           prior="ADR-SB-005-C03", change="MODIFIED"),
        _c("C04", "freshness is visible",
           "second_brain.projection.freshness_visibility", "CONSTANT", "EQUALS",
           "VISIBLE",
           DECISION, [F005_DEC],
           prior="ADR-SB-005-C04", change="UNCHANGED"),
        _c("C05", "content hashes are required",
           "second_brain.projection.content_hash.required",
           "BOOLEAN", "EQUALS", True,
           DECISION, [F005_DEC],
           prior="ADR-SB-005-C05", change="MODIFIED"),
        _c("C06", "purge propagates into the projection",
           "second_brain.projection.purge_propagation", "BOOLEAN", "EQUALS", True,
           DECISION, [F005_DEC],
           prior="ADR-SB-005-C06", change="UNCHANGED"),
        _c("C07", "no silent write-back",
           "second_brain.projection.silent_write_back", "BOOLEAN", "EQUALS", False,
           DECISION, [F005_DEC],
           prior="ADR-SB-005-C07", change="MODIFIED"),
        _c("C08", "canonical sources win any conflict",
           "second_brain.projection.conflict.canonical_source_wins",
           "BOOLEAN", "EQUALS", True,
           CONSEQ, ["Canonical sources always win"],
           prior="ADR-SB-005-C08", change="MODIFIED"),
        _c("C09", "Obsidian is optional",
           "second_brain.projection.obsidian.required", "BOOLEAN", "EQUALS", False,
           DECISION, ["Obsidian is an optional opener."],
           prior="ADR-SB-005-C09", change="MODIFIED"),
        _c("C10", "Obsidian is never an authority",
           "second_brain.projection.obsidian.is_authority",
           "BOOLEAN", "EQUALS", False,
           CONTEXT, [F005_CTX]),
        _c("C11", "Markdown is never an authority",
           "second_brain.projection.markdown.is_authority",
           "BOOLEAN", "EQUALS", False,
           CONTEXT, [F005_CTX]),
        _c("C12", "Markdown compilation is deterministic",
           "second_brain.projection.compilation.deterministic",
           "BOOLEAN", "EQUALS", True,
           DECISION, [F005_DEC]),
        _c("C13", "the vault is regenerable",
           "second_brain.projection.vault.regenerable", "BOOLEAN", "EQUALS", True,
           CONSEQ, ["Regenerable vault"]),
        _c("C14", "manual regions are preserved",
           "second_brain.projection.manual_regions.preserved",
           "BOOLEAN", "EQUALS", True,
           CONSEQ, ["Manual regions preserved"]),
    ),
)


# --------------------------------------------------------------------------
# ADR-SB-006 — Local Spool and Custody Interface
# --------------------------------------------------------------------------

F006_REC = (
    "Spool records are non-canonical, identity/domain/class scoped, "
    "deterministic, integrity-protected, short-lived, idempotently flushed, "
    "purge-aware, and never remote backed up."
)
F006_CLS = (
    "Public is allowed; internal requires OS-protected storage; "
    "confidential/restricted remain disabled until verified encryption and key "
    "ownership."
)
SPOOL = "schemas/second_brain/contracts/local-spool-port.contract.json"
CUSTODY = "schemas/second_brain/contracts/custody-port.contract.json"

ADR_006 = Adr(
    "ADR-SB-006",
    "Local Spool and Custody Interface",
    ("SB-DEC-014", "SB-DEC-015"),
    (
        _c("C01", "LocalSpoolPort exists as a machine interface contract",
           "second_brain.local_spool_port", "INTERFACE_REQUIREMENT", "MUST_EXIST",
           "LocalSpoolPort",
           DECISION, ["Define `LocalSpoolPort` and `CustodyPort`."],
           covering=[SPOOL],
           prior="ADR-SB-006-C01", change="UNCHANGED"),
        _c("C02", "CustodyPort exists as a machine interface contract",
           "second_brain.custody_port", "INTERFACE_REQUIREMENT", "MUST_EXIST",
           "CustodyPort",
           DECISION, ["Define `LocalSpoolPort` and `CustodyPort`."],
           covering=[CUSTODY],
           prior="ADR-SB-006-C02", change="UNCHANGED"),
        _c("C03", "spool records are not canonical",
           "second_brain.local_spool.record.canonical", "BOOLEAN", "EQUALS", False,
           DECISION, [F006_REC], covering=[SPOOL],
           prior="ADR-SB-006-C03", change="MODIFIED"),
        _c("C04", "spool record scope = identity / domain / class",
           "second_brain.local_spool.record.scope_keys", "ENUM", "SET_EQUALS",
           ["IDENTITY", "DOMAIN", "CLASS"],
           DECISION, [F006_REC], enumeration="identity/domain/class",
           covering=[SPOOL],
           prior="ADR-SB-006-C04", change="MODIFIED"),
        _c("C05", "spool records are deterministic",
           "second_brain.local_spool.record.determinism", "CONSTANT", "EQUALS",
           "DETERMINISTIC",
           DECISION, [F006_REC], covering=[SPOOL],
           prior="ADR-SB-006-C05", change="UNCHANGED"),
        _c("C06", "spool records are integrity-protected",
           "second_brain.local_spool.record.integrity_protected",
           "BOOLEAN", "EQUALS", True,
           DECISION, [F006_REC], covering=[SPOOL],
           prior="ADR-SB-006-C06", change="MODIFIED"),
        _c("C07", "spool records are short-lived",
           "second_brain.local_spool.record.short_lived", "BOOLEAN", "EQUALS", True,
           DECISION, [F006_REC], covering=[SPOOL],
           prior="ADR-SB-006-C07", change="MODIFIED"),
        _c("C08", "spool flush is idempotent",
           "second_brain.local_spool.flush.idempotent", "BOOLEAN", "EQUALS", True,
           DECISION, [F006_REC], covering=[SPOOL],
           prior="ADR-SB-006-C08", change="UNCHANGED"),
        _c("C09", "the spool participates in purge",
           "second_brain.local_spool.purge_aware", "BOOLEAN", "EQUALS", True,
           DECISION, [F006_REC], covering=[SPOOL],
           prior="ADR-SB-006-C09", change="MODIFIED"),
        _c("C10", "spool records are never remote backed up",
           "second_brain.local_spool.remote_backup", "BOOLEAN", "EQUALS", False,
           DECISION, [F006_REC], covering=[SPOOL],
           prior="ADR-SB-006-C10", change="UNCHANGED"),
        _c("C11", "public classification is allowed to spool",
           "second_brain.local_spool.classification.public", "CONSTANT", "EQUALS",
           "ALLOWED",
           DECISION, [F006_CLS], covering=[SPOOL],
           prior="ADR-SB-006-C11", change="UNCHANGED"),
        _c("C12", "internal classification requires OS-protected storage",
           "second_brain.local_spool.classification.internal", "CONSTANT", "EQUALS",
           "REQUIRES_OS_PROTECTED_STORAGE",
           DECISION, [F006_CLS], covering=[SPOOL],
           prior="ADR-SB-006-C12", change="MODIFIED"),
        _c("C13", "confidential/restricted spooling is disabled until verified "
                  "encryption and key ownership",
           "second_brain.local_spool.classification.confidential_restricted",
           "CONSTANT", "EQUALS",
           "DISABLED_UNTIL_VERIFIED_ENCRYPTION_AND_KEY_OWNERSHIP",
           DECISION, [F006_CLS], covering=[SPOOL],
           prior="ADR-SB-006-C13", change="UNCHANGED"),
        _c("C14", "unknown-class spooling is not permitted",
           "second_brain.local_spool.classification.unknown.spooling_permitted",
           "BOOLEAN", "EQUALS", False,
           CONSEQ, ["No unknown-class spooling"], covering=[SPOOL],
           prior="ADR-SB-006-C14", change="MODIFIED"),
        _c("C15", "eligible capture is crash-safe",
           "second_brain.local_spool.capture.crash_safe", "BOOLEAN", "EQUALS", True,
           CONSEQ, ["Crash-safe eligible capture"], covering=[SPOOL]),
        _c("C16", "the custody product remains replaceable",
           "second_brain.custody.product.replaceable", "BOOLEAN", "EQUALS", True,
           CONSEQ, ["Custody product remains replaceable"], covering=[CUSTODY]),
        _c("C17", "closed set of confidential/restricted enablement preconditions",
           "second_brain.local_spool.classification."
           "confidential_restricted.enablement_preconditions",
           "ENUM", "SET_EQUALS", ["VERIFIED_ENCRYPTION", "KEY_OWNERSHIP"],
           DECISION, [F006_CLS],
           enumeration="verified encryption and key ownership",
           covering=[SPOOL]),
    ),
)


# --------------------------------------------------------------------------
# ADR-SB-007 — Forget, Purge, and Residual Verification
# --------------------------------------------------------------------------

F007_CTX = (
    "Hide-from-view, retrieval denial, logical tombstone, physical deletion, and "
    "backup expiry are different operations."
)
F007_BUILD = (
    "Build a dependency graph, impact preview, explicit approval, per-surface "
    "receipts, residual scan, and completion receipt."
)
F007_IMP = (
    "Impossible physical deletion uses explicit tombstone/retrieval denial and "
    "pending backup-expiry state."
)

ADR_007 = Adr(
    "ADR-SB-007",
    "Forget, Purge, and Residual Verification",
    ("SB-DEC-019", "SB-DEC-029"),
    (
        _c("C01", "deletion operations = Archive / Forget / Purge",
           "second_brain.deletion.operations", "ENUM", "SET_EQUALS",
           ["ARCHIVE", "FORGET", "PURGE"],
           DECISION, ["Model Archive, Forget, and Purge separately."],
           enumeration="Archive, Forget, and Purge",
           prior="ADR-SB-007-C01", change="UNCHANGED"),
        _c("C02", "a purge dependency graph is required",
           "second_brain.purge.dependency_graph.required",
           "BOOLEAN", "EQUALS", True,
           DECISION, [F007_BUILD],
           prior="ADR-SB-007-C02", change="MODIFIED"),
        _c("C03", "an impact preview is required",
           "second_brain.purge.impact_preview.required", "BOOLEAN", "EQUALS", True,
           DECISION, [F007_BUILD],
           prior="ADR-SB-007-C03", change="MODIFIED"),
        _c("C04", "explicit approval is required",
           "second_brain.purge.approval.explicit_required",
           "BOOLEAN", "EQUALS", True,
           DECISION, [F007_BUILD],
           prior="ADR-SB-007-C04", change="MODIFIED"),
        _c("C05", "receipts are per-surface",
           "second_brain.purge.receipts.granularity", "CONSTANT", "EQUALS",
           "PER_SURFACE",
           DECISION, [F007_BUILD],
           prior="ADR-SB-007-C05", change="UNCHANGED"),
        _c("C06", "a residual scan is required",
           "second_brain.purge.residual_scan.required", "BOOLEAN", "EQUALS", True,
           DECISION, [F007_BUILD],
           prior="ADR-SB-007-C06", change="MODIFIED"),
        _c("C07", "searchable residual count must be zero before success",
           "second_brain.purge.searchable_residual_count", "NUMERIC", "EQUALS", 0,
           DECISION, ["Searchable residual count must be zero before success."],
           prior="ADR-SB-007-C07", change="UNCHANGED"),
        _c("C08", "impossible physical deletion requires an explicit tombstone",
           "second_brain.purge.physical_deletion_impossible."
           "explicit_tombstone_required",
           "BOOLEAN", "EQUALS", True,
           DECISION, [F007_IMP],
           prior="ADR-SB-007-C08", change="MODIFIED"),
        _c("C09", "backup expiry may remain pending",
           "second_brain.purge.backup_expiry.state", "CONSTANT", "EQUALS",
           "PENDING_BACKUP_EXPIRY",
           DECISION, [F007_IMP],
           prior="ADR-SB-007-C09", change="UNCHANGED"),
        _c("C10", "irreversible steps require immediate confirmation",
           "second_brain.purge.irreversible_step.confirmation", "CONSTANT", "EQUALS",
           "IMMEDIATE",
           CONSEQ, ["Irreversible steps require immediate confirmation"],
           prior="ADR-SB-007-C10", change="UNCHANGED"),
        _c("C11", "derived representations participate in purge",
           "second_brain.purge.derived_representations.participate",
           "BOOLEAN", "EQUALS", True,
           CONSEQ, ["Derived representations participate"],
           prior="ADR-SB-007-C11", change="UNCHANGED"),
        _c("C12", "impossible physical deletion requires retrieval denial",
           "second_brain.purge.physical_deletion_impossible."
           "retrieval_denial_required",
           "BOOLEAN", "EQUALS", True,
           DECISION, [F007_IMP]),
        _c("C13", "a purge completion receipt is required",
           "second_brain.purge.completion_receipt.required",
           "BOOLEAN", "EQUALS", True,
           DECISION, [F007_BUILD]),
        _c("C14", "closed set of distinct deletion-adjacent operation classes",
           "second_brain.deletion.operation_classes", "ENUM", "SET_EQUALS",
           ["HIDE_FROM_VIEW", "RETRIEVAL_DENIAL", "LOGICAL_TOMBSTONE",
            "PHYSICAL_DELETION", "BACKUP_EXPIRY"],
           CONTEXT, [F007_CTX],
           enumeration=("Hide-from-view, retrieval denial, logical tombstone, "
                        "physical deletion, and backup expiry")),
        _c("C15", "those operation classes are different operations",
           "second_brain.deletion.operation_classes.distinct",
           "BOOLEAN", "EQUALS", True,
           CONTEXT, [F007_CTX]),
        _c("C16", "no soft-delete is accepted as a purge",
           "second_brain.purge.soft_delete_accepted", "BOOLEAN", "EQUALS", False,
           CONSEQ, ["No soft-delete masquerading as purge"]),
        _c("C17", "Archive, Forget, and Purge are modeled separately",
           "second_brain.deletion.archive_forget_purge_modeled_separately",
           "BOOLEAN", "EQUALS", True,
           DECISION, ["Model Archive, Forget, and Purge separately."]),
    ),
)


# --------------------------------------------------------------------------
# ADR-SB-008 — Open Loop and Task Proposal Boundary
# --------------------------------------------------------------------------

F008_CTX = (
    "An unresolved commitment is not necessarily a PM task, and the PM/workflow "
    "authority path is not yet operationally unambiguous."
)
F008_CONF = (
    "Confirmation appends open/close/cancel events to Dope-Memory; the active "
    "list is derived."
)
F008_TASK = (
    "Actual task creation requires Leantime plus Task Orchestrator proof and "
    "explicit approval; it is disabled initially."
)
F008_MARK = (
    "confirmed open-loop events are chronological attention markers, not tasks."
)
F008_NEVER = (
    "A confirmed open loop, and its derived current-state view, may never carry "
    "an assignee, PM priority, workflow status, sprint state, ownership "
    "assignment, due-driven escalation, automatic scheduling, or task completion "
    "state."
)
F008_SHAPED = (
    "Any task-shaped behavior must be represented as a separate `TaskProposal` "
    "and mutated only through the disabled `TaskPromotionRequest` path (Slice 6)."
)
F008_SOLE = (
    "Leantime and Task Orchestrator remain the sole authorities for PM and "
    "workflow semantics; this ADR does not grant Dope-Memory or the Second Brain "
    "any PM authority."
)
F008_ZERO = (
    "Open loops carry zero PM-semantic fields; `due_at` cannot trigger "
    "scheduling or escalation"
)
F008_NEVER_ENUM = (
    "assignee, PM priority, workflow status, sprint state, ownership assignment, "
    "due-driven escalation, automatic scheduling, or task completion state"
)
OLC = "schemas/second_brain/contracts/open-loop-candidate.schema.json"
TP = "schemas/second_brain/contracts/task-proposal.schema.json"
TPR = "schemas/second_brain/contracts/task-promotion-request.schema.json"


def _pm_field(suffix, term, subject_leaf, prior):
    return _c(
        suffix,
        f"a confirmed open loop may never carry {term}",
        f"second_brain.open_loop.field.{subject_leaf}.permitted",
        "BOOLEAN", "EQUALS", False,
        MA06, [F008_NEVER], covering=[OLC],
        prior=prior, change="MODIFIED",
    )


ADR_008 = Adr(
    "ADR-SB-008",
    "Open Loop and Task Proposal Boundary",
    ("SB-DEC-006", "SB-DEC-007", "SB-DEC-008", "SB-DEC-030"),
    (
        _c("C01", "OpenLoopCandidate exists as a machine data contract",
           "second_brain.open_loop_candidate", "INTERFACE_REQUIREMENT", "MUST_EXIST",
           "OpenLoopCandidate",
           MA06, ["`OpenLoopCandidate.due_at` is advisory display metadata only."],
           covering=[OLC], prior="ADR-SB-008-C01", change="UNCHANGED"),
        _c("C02", "TaskProposal exists as a separate machine data contract",
           "second_brain.task_proposal", "INTERFACE_REQUIREMENT", "MUST_EXIST",
           "TaskProposal",
           MA06, [F008_SHAPED], covering=[TP],
           prior="ADR-SB-008-C02", change="UNCHANGED"),
        _c("C03", "TaskPromotionRequest exists as a separate machine contract",
           "second_brain.task_promotion_request", "INTERFACE_REQUIREMENT",
           "MUST_EXIST", "TaskPromotionRequest",
           MA06, [F008_SHAPED], covering=[TPR],
           prior="ADR-SB-008-C03", change="UNCHANGED"),
        _c("C04", "confirmed open-loop events are appended to Dope-Memory",
           "second_brain.open_loop.confirmed_event.append_target",
           "AUTHORITY_TARGET", "EQUALS", "Dope-Memory",
           DECISION, [F008_CONF], prior="ADR-SB-008-C04", change="UNCHANGED"),
        _c("C05", "the active open-loop list is derived",
           "second_brain.open_loop.active_list.derived", "BOOLEAN", "EQUALS", True,
           DECISION, [F008_CONF], prior="ADR-SB-008-C05", change="MODIFIED"),
        _c("C06", "task creation requires Leantime proof",
           "second_brain.task_creation.requires_leantime_proof",
           "BOOLEAN", "EQUALS", True,
           DECISION, [F008_TASK], covering=[TPR],
           prior="ADR-SB-008-C06", change="MODIFIED"),
        _c("C07", "task promotion is disabled",
           "second_brain.task_promotion.enabled", "BOOLEAN", "EQUALS", False,
           DECISION, [F008_TASK], covering=[TPR],
           prior="ADR-SB-008-C07", change="UNCHANGED"),
        _pm_field("C08", "an assignee", "assignee", "ADR-SB-008-C08"),
        _pm_field("C09", "PM priority", "pm_priority", "ADR-SB-008-C09"),
        _pm_field("C10", "workflow status", "workflow_status", "ADR-SB-008-C10"),
        _pm_field("C11", "sprint state", "sprint_state", "ADR-SB-008-C11"),
        _pm_field("C12", "an ownership assignment", "ownership_assignment",
                  "ADR-SB-008-C12"),
        _pm_field("C13", "due-driven escalation", "due_driven_escalation",
                  "ADR-SB-008-C13"),
        _pm_field("C14", "automatic scheduling", "automatic_scheduling",
                  "ADR-SB-008-C14"),
        _pm_field("C15", "task completion state", "task_completion_state",
                  "ADR-SB-008-C15"),
        _c("C16", "due_at is advisory display metadata only",
           "second_brain.open_loop.due_at.semantics", "CONSTANT", "EQUALS",
           "ADVISORY_DISPLAY_METADATA_ONLY",
           MA06, ["`OpenLoopCandidate.due_at` is advisory display metadata only."],
           covering=[OLC], prior="ADR-SB-008-C16", change="UNCHANGED"),
        _c("C17", "task creation requires Task Orchestrator proof",
           "second_brain.task_creation.requires_task_orchestrator_proof",
           "BOOLEAN", "EQUALS", True,
           DECISION, [F008_TASK], covering=[TPR]),
        _c("C18", "task creation requires explicit approval",
           "second_brain.task_creation.requires_explicit_approval",
           "BOOLEAN", "EQUALS", True,
           DECISION, [F008_TASK], covering=[TPR]),
        _c("C19", "closed set of PM semantics a confirmed open loop may never carry",
           "second_brain.open_loop.forbidden_pm_semantics", "ENUM", "SET_EQUALS",
           ["ASSIGNEE", "PM_PRIORITY", "WORKFLOW_STATUS", "SPRINT_STATE",
            "OWNERSHIP_ASSIGNMENT", "DUE_DRIVEN_ESCALATION",
            "AUTOMATIC_SCHEDULING", "TASK_COMPLETION_STATE"],
           MA06, [F008_NEVER], enumeration=F008_NEVER_ENUM, covering=[OLC]),
        _c("C20", "an unresolved commitment is not necessarily a PM task",
           "second_brain.open_loop.is_pm_task", "BOOLEAN", "EQUALS", False,
           CONTEXT, [F008_CTX]),
        _c("C21", "detected loops are represented as suggested candidates",
           "second_brain.open_loop.represented_as_suggested_candidate",
           "BOOLEAN", "EQUALS", True,
           DECISION, ["Represent detected loops as suggested candidates."],
           covering=[OLC]),
        _c("C22", "confirmed loop event kinds = open / close / cancel",
           "second_brain.open_loop.confirmed_event.kinds", "ENUM", "SET_EQUALS",
           ["OPEN", "CLOSE", "CANCEL"],
           DECISION, [F008_CONF], enumeration="open/close/cancel"),
        _c("C23", "task proposals are separate candidates",
           "second_brain.task_proposal.separate_from_open_loop",
           "BOOLEAN", "EQUALS", True,
           DECISION, ["Task proposals are separate candidates."], covering=[TP]),
        _c("C24", "confirmed open-loop events are chronological attention markers",
           "second_brain.open_loop.confirmed_event.is_chronological_attention_marker",
           "BOOLEAN", "EQUALS", True,
           MA06, [F008_MARK]),
        _c("C25", "confirmed open-loop events are not tasks",
           "second_brain.open_loop.confirmed_event.is_task",
           "BOOLEAN", "EQUALS", False,
           MA06, [F008_MARK]),
        _c("C26", "the derived current-state view carries the same prohibition",
           "second_brain.open_loop.current_state_view.bound_by_pm_prohibition",
           "BOOLEAN", "EQUALS", True,
           MA06, [F008_NEVER]),
        _c("C27", "task-shaped behavior is represented as a separate TaskProposal",
           "second_brain.task_shaped_behavior.represented_as_task_proposal",
           "BOOLEAN", "EQUALS", True,
           MA06, [F008_SHAPED], covering=[TP]),
        _c("C28", "task mutation happens only through the TaskPromotionRequest path",
           "second_brain.task_mutation.only_through_task_promotion_request",
           "BOOLEAN", "EQUALS", True,
           MA06, [F008_SHAPED], covering=[TPR]),
        _c("C29", "sole PM and workflow authorities = Leantime / Task Orchestrator",
           "second_brain.pm_workflow.sole_authorities", "AUTHORITY_TARGET",
           "SET_EQUALS", ["Leantime", "Task Orchestrator"],
           MA06, [F008_SOLE], enumeration="Leantime and Task Orchestrator",
           covering=[TPR]),
        _c("C30", "Dope-Memory is granted no PM authority",
           "dope_memory.pm_authority", "BOOLEAN", "EQUALS", False,
           MA06, [F008_SOLE]),
        _c("C31", "the Second Brain is granted no PM authority",
           "second_brain.pm_authority", "BOOLEAN", "EQUALS", False,
           MA06, [F008_SOLE]),
        _c("C32", "no automatic task pressure",
           "second_brain.open_loop.automatic_task_pressure",
           "BOOLEAN", "EQUALS", False,
           CONSEQ, ["No automatic task pressure"]),
        _c("C33", "chronology remains in Dope-Memory",
           "second_brain.chronology.authority", "AUTHORITY_TARGET", "EQUALS",
           "Dope-Memory",
           CONSEQ, ["Chronology remains in Dope-Memory"]),
        _c("C34", "ConPort never owns task state",
           "conport.owns_task_state", "BOOLEAN", "EQUALS", False,
           CONSEQ, ["ConPort never owns task state"]),
        _c("C35", "open loops carry zero PM-semantic fields",
           "second_brain.open_loop.pm_semantic_field_count", "NUMERIC", "EQUALS", 0,
           CONSEQ, [F008_ZERO], covering=[OLC]),
        _c("C36", "due_at may not trigger scheduling or escalation",
           "second_brain.open_loop.due_at.forbidden_triggers", "ENUM", "SET_EQUALS",
           ["SCHEDULING", "ESCALATION"],
           CONSEQ, [F008_ZERO], enumeration="scheduling or escalation",
           covering=[OLC]),
    ),
)


# --------------------------------------------------------------------------
# ADR-SB-009 — Single-Project Safety and Identity Dependencies
# --------------------------------------------------------------------------

F009_CTX = (
    "Path hashes, ports, and singleton event streams cannot safely establish "
    "canonical project identity."
)
F009_REQ = (
    "Require registry-backed identity envelopes and current service capability "
    "receipts for authority operations."
)
F009_PERMIT = (
    "Permit one active automatic-capture project, explicit project switching, "
    "writer epochs, and wrong-project denial."
)
F009_MULTI = (
    "Multi-project background capture remains disabled until isolation proof."
)
ENV = "schemas/second_brain/contracts/project-identity-envelope.schema.json"
RCPT = "schemas/second_brain/contracts/service-capability-receipt.schema.json"

ADR_009 = Adr(
    "ADR-SB-009",
    "Single-Project Safety and Identity Dependencies",
    ("SB-DEC-009", "SB-DEC-013", "SB-DEC-022", "SB-DEC-024"),
    (
        _c("C01", "authority operations require a registry-backed identity envelope",
           "second_brain.authority_operation."
           "requires_registry_backed_identity_envelope",
           "BOOLEAN", "EQUALS", True,
           DECISION, [F009_REQ], covering=[ENV],
           prior="ADR-SB-009-C01", change="MODIFIED"),
        _c("C02", "authority operations require a current service capability receipt",
           "second_brain.authority_operation."
           "requires_current_service_capability_receipt",
           "BOOLEAN", "EQUALS", True,
           DECISION, [F009_REQ], covering=[RCPT],
           prior="ADR-SB-009-C02", change="MODIFIED"),
        _c("C03", "at most one active automatic-capture project",
           "second_brain.automatic_capture.active_project_count", "NUMERIC",
           "LESS_THAN_OR_EQUAL", 1,
           DECISION, [F009_PERMIT], covering=[ENV],
           prior="ADR-SB-009-C03", change="UNCHANGED"),
        _c("C04", "project switching is explicit",
           "second_brain.project_switch.mode", "CONSTANT", "EQUALS", "EXPLICIT",
           DECISION, [F009_PERMIT], covering=[ENV],
           prior="ADR-SB-009-C04", change="UNCHANGED"),
        _c("C05", "writer epochs are required",
           "second_brain.writer_epoch.required", "BOOLEAN", "EQUALS", True,
           DECISION, [F009_PERMIT], covering=[ENV],
           prior="ADR-SB-009-C05", change="MODIFIED"),
        _c("C06", "wrong-project writes are denied",
           "second_brain.write.wrong_project.denied", "BOOLEAN", "EQUALS", True,
           DECISION, [F009_PERMIT], covering=[ENV],
           prior="ADR-SB-009-C06", change="MODIFIED"),
        _c("C07", "closed set of identity sources that cannot establish identity",
           "second_brain.identity.rejected_sources", "ENUM", "SET_EQUALS",
           ["PATH_HASHES", "PORTS", "SINGLETON_EVENT_STREAMS"],
           CONTEXT, [F009_CTX],
           enumeration="Path hashes, ports, and singleton event streams",
           covering=[ENV], prior="ADR-SB-009-C07", change="MODIFIED"),
        _c("C08", "multi-project background capture is disabled",
           "second_brain.multi_project_background_capture.enabled",
           "BOOLEAN", "EQUALS", False,
           DECISION, [F009_MULTI], covering=[ENV],
           prior="ADR-SB-009-C08", change="UNCHANGED"),
        _c("C09", "enabling multi-project background capture requires isolation proof",
           "second_brain.multi_project_background_capture."
           "enablement_requires_isolation_proof",
           "BOOLEAN", "EQUALS", True,
           DECISION, [F009_MULTI], covering=[ENV]),
        _c("C10", "split-brain prevention is fail-closed",
           "second_brain.split_brain_prevention.fail_closed",
           "BOOLEAN", "EQUALS", True,
           CONSEQ, ["Fail-closed split-brain prevention"]),
        _c("C11", "no dedicated host is required",
           "second_brain.deployment.dedicated_host_required",
           "BOOLEAN", "EQUALS", False,
           CONSEQ, ["Mac mini remains optional"]),
        _c("C12", "no host-singleton routing authority",
           "second_brain.routing_authority.host_singleton",
           "BOOLEAN", "EQUALS", False,
           CONSEQ, ["No host-singleton routing authority"]),
    ),
)


# --------------------------------------------------------------------------
# ADR-SB-010 — UX Contract
# --------------------------------------------------------------------------

F010_CTX = (
    "ADHD-supportive operation requires low interruption and clear consequences "
    "without hiding authority or privacy decisions."
)
F010_DEC = (
    "Use Capture, Recall, Review; one dominant next action; at most seven "
    "visible queue items; answer-first recall; evidence one action away; "
    "session-end batching; and immediate interruption only for privacy, "
    "identity, data-loss, irreversible-action, or authority-conflict conditions."
)

ADR_010 = Adr(
    "ADR-SB-010",
    "UX Contract",
    ("SB-DEC-020", "SB-DEC-021"),
    (
        _c("C01", "UX operations = Capture / Recall / Review",
           "second_brain.ux.operations", "ENUM", "SET_EQUALS",
           ["CAPTURE", "RECALL", "REVIEW"],
           DECISION, [F010_DEC], enumeration="Capture, Recall, Review",
           prior="ADR-SB-010-C01", change="MODIFIED"),
        _c("C02", "one dominant next action",
           "second_brain.ux.dominant_next_action_count", "NUMERIC", "EQUALS", 1,
           DECISION, [F010_DEC], prior="ADR-SB-010-C02", change="MODIFIED"),
        _c("C03", "at most seven visible queue items",
           "second_brain.ux.visible_queue_max", "NUMERIC", "LESS_THAN_OR_EQUAL", 7,
           DECISION, [F010_DEC], prior="ADR-SB-010-C03", change="UNCHANGED"),
        _c("C04", "recall is answer-first",
           "second_brain.ux.recall.answer_first", "BOOLEAN", "EQUALS", True,
           DECISION, [F010_DEC], prior="ADR-SB-010-C04", change="MODIFIED"),
        _c("C05", "evidence is one action away",
           "second_brain.ux.evidence.max_actions_away", "NUMERIC",
           "LESS_THAN_OR_EQUAL", 1,
           DECISION, [F010_DEC], prior="ADR-SB-010-C05", change="UNCHANGED"),
        _c("C06", "notifications batch at session end",
           "second_brain.ux.notification.batching", "CONSTANT", "EQUALS",
           "SESSION_END",
           DECISION, [F010_DEC], prior="ADR-SB-010-C06", change="UNCHANGED"),
        _c("C07", "closed set of immediate-interruption conditions",
           "second_brain.ux.immediate_interruption.allowed_conditions", "ENUM",
           "SET_EQUALS",
           ["PRIVACY", "IDENTITY", "DATA_LOSS", "IRREVERSIBLE_ACTION",
            "AUTHORITY_CONFLICT"],
           DECISION, [F010_DEC],
           enumeration=("privacy, identity, data-loss, irreversible-action, or "
                        "authority-conflict"),
           prior="ADR-SB-010-C07", change="MODIFIED"),
        _c("C08", "consequential defaults = DEFER / CANCEL",
           "second_brain.ux.consequential_default", "ENUM", "SET_EQUALS",
           ["DEFER", "CANCEL"],
           DECISION, ["Consequential defaults are DEFER or CANCEL."],
           enumeration="DEFER or CANCEL",
           prior="ADR-SB-010-C08", change="MODIFIED"),
        _c("C09", "no productivity scoring",
           "second_brain.ux.productivity_scoring", "BOOLEAN", "EQUALS", False,
           CONSEQ, ["No productivity scoring or surprise writes"],
           prior="ADR-SB-010-C09", change="UNCHANGED"),
        _c("C10", "no surprise writes",
           "second_brain.ux.surprise_writes", "BOOLEAN", "EQUALS", False,
           CONSEQ, ["No productivity scoring or surprise writes"],
           prior="ADR-SB-010-C10", change="UNCHANGED"),
        _c("C11", "immediate interruption is restricted to the listed conditions",
           "second_brain.ux.immediate_interruption.restricted_to_listed_conditions",
           "BOOLEAN", "EQUALS", True,
           DECISION, [F010_DEC]),
        _c("C12", "the UX does not hide authority decisions",
           "second_brain.ux.hides_authority_decisions", "BOOLEAN", "EQUALS", False,
           CONTEXT, [F010_CTX]),
        _c("C13", "the UX does not hide privacy decisions",
           "second_brain.ux.hides_privacy_decisions", "BOOLEAN", "EQUALS", False,
           CONTEXT, [F010_CTX]),
        _c("C14", "terminal and agent UX stay quiet",
           "second_brain.ux.surface.quiet", "BOOLEAN", "EQUALS", True,
           CONSEQ, ["Quiet terminal and agent UX"]),
        _c("C15", "no dashboard dependency",
           "second_brain.ux.dashboard.required", "BOOLEAN", "EQUALS", False,
           CONSEQ, ["No dashboard dependency"]),
    ),
)


ADRS: tuple[Adr, ...] = (
    ADR_001, ADR_002, ADR_003, ADR_004, ADR_005,
    ADR_006, ADR_007, ADR_008, ADR_009, ADR_010,
)


# --------------------------------------------------------------------------
# Census worksheet — every normative unit of the candidate, disposed of.
# EXCLUDED units carry the operator's DO-NOT-INCLUDE reason verbatim.
# --------------------------------------------------------------------------

EXCLUSIONS = [
    {
        "unit": "Document preamble: 'These are architecture candidates only. Every "
                "ADR below remains `PROPOSED`; this synthesis does not alter the "
                "repository ADR index or confer implementation authority.'",
        "location": "document preamble",
        "disposition": "EXCLUDED",
        "reason": "Document-status narrative, not per-ADR architecture content. It "
                  "belongs to no ADR and therefore cannot be a clause of one. The "
                  "same invariant is enforced structurally by validator checks "
                  "A16-A18 (every contract records PROPOSED; the document status "
                  "is CANDIDATE; no ACCEPTED token appears).",
    },
    {
        "unit": "'Standing drift recheck precondition (MA-08)' section in full",
        "location": "standing section, lines 21-23",
        "disposition": "EXCLUDED",
        "reason": "Operator DO-NOT-INCLUDE: 'MA-08 process mechanics'. It governs "
                  "when an acceptance decision may be taken, not what the "
                  "architecture must be.",
    },
    {
        "unit": "Acceptance-condition bullets, all 10 ADRs (4 bullets each)",
        "location": "'### Acceptance conditions' in every ADR",
        "disposition": "EXCLUDED",
        "reason": "Operator DO-NOT-INCLUDE: 'the acceptance-condition boilerplate "
                  "itself'. Condition #2 is the reason this contract evidence "
                  "exists; it is not itself a decision the contracts must encode.",
    },
    {
        "unit": "'### Evidence and traceability' SB-DEC reference lists, all 10 ADRs",
        "location": "'### Evidence and traceability' in every ADR",
        "disposition": "EXCLUDED_AS_CLAUSE_RETAINED_AS_BINDING",
        "reason": "Operator DO-NOT-INCLUDE: 'Evidence/traceability references'. The "
                  "references are still carried on each contract as "
                  "sb_dec_references and cross-checked against the traceability "
                  "matrix (check B08), but they assert no architecture rule.",
    },
    {
        "unit": "'### Rejected alternatives' bullets, all 10 ADRs (20 bullets)",
        "location": "'### Rejected alternatives' in every ADR",
        "disposition": "EXCLUDED_AS_GROUNDING_USED_AS_ORACLE",
        "reason": "Operator: rejected alternatives may be used only 'as adversarial "
                  "oracles proving that a mutation crosses into an explicitly "
                  "rejected design'. Where the accepted decision independently "
                  "expresses the corresponding prohibition, that accepted sentence "
                  "is the clause's grounding instead. Validator check A22 rejects "
                  "any clause whose fragments come from this subsection: "
                  "'Vector-first answer generation' is verbatim candidate text, so "
                  "without that rule a clause could cite a rejected design as its "
                  "own justification.",
    },
    {
        "unit": "ADR-SB-006 Context: 'Outage capture needs bounded durability, but "
                "an unencrypted spool can become a private-data trapdoor.'",
        "location": "ADR-SB-006 Context",
        "disposition": "EXCLUDED",
        "reason": "Motivational narrative. Both invariants it motivates are stated "
                  "normatively in the Proposed decision and are captured there "
                  "(ADR-SB-006-C07 short-lived; ADR-SB-006-C13 confidential/"
                  "restricted disabled until verified encryption).",
    },
]

# Judgment calls recorded so the auditor can attack them directly rather than
# having to reconstruct them.
JUDGMENTS = [
    {
        "unit": "ADR-SB-001 Consequence 'One package plus optional worker'",
        "disposition": "INCLUDED (C10, C11)",
        "rationale": "The operator excludes 'packaging observations that do not "
                     "constrain architecture'. This one does constrain: it bounds "
                     "the component count and makes the worker optional, which is "
                     "an enablement constraint. Recorded as a judgment call.",
    },
    {
        "unit": "ADR-SB-009 Consequence 'Mac mini remains optional'",
        "disposition": "INCLUDED (C11)",
        "rationale": "Same rule applied consistently: host optionality is an "
                     "enablement constraint (the system must be enablable without "
                     "dedicated hardware), not a deployment aside.",
    },
    {
        "unit": "ADR-SB-009 rejected alternative 'Implicit current-directory "
                "project selection for writes'",
        "disposition": "NOT ADDED to the rejected-identity-source set",
        "rationale": "The accepted Context sentence enumerates exactly three "
                     "sources (path hashes, ports, singleton event streams). "
                     "CURRENT_DIRECTORY appeared in the superseded contract's "
                     "machine set but is grounded only in a rejected alternative. "
                     "The prohibition is independently expressed by 'explicit "
                     "project switching' (C04), so no set member is invented.",
    },
    {
        "unit": "ADR-SB-005 'Obsidian is an optional opener.'",
        "disposition": "INCLUDED as two clauses (C09 optional, C10 never an "
                       "authority); 'opener' itself carries no clause",
        "rationale": "The sentence constrains two things: Obsidian is not "
                     "required, and it is not an authority (the latter from the "
                     "Context sentence). 'Opener' is a functional description of "
                     "what it does when present, not an additional invariant, so "
                     "no clause asserts it. The superseded contract collapsed all "
                     "of this into one ungrounded token, "
                     "OPTIONAL_OPENER_NEVER_AUTHORITY.",
    },
    {
        "unit": "ADR-SB-009 ProjectIdentityEnvelope / ServiceCapabilityReceipt",
        "disposition": "NOT modelled as INTERFACE_REQUIREMENT clauses",
        "rationale": "Unlike LocalSpoolPort, CustodyPort, OpenLoopCandidate, "
                     "TaskProposal and TaskPromotionRequest, these two names do "
                     "not appear in the candidate — they are this repository's "
                     "names for things the candidate describes but does not name. "
                     "The clauses are therefore stated as the obligations the "
                     "candidate does express (C01, C02), and the schema files "
                     "carry an explicit naming note.",
    },
]
