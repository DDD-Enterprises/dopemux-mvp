"""Tests for dopemux.governed_execution.review_economy.keys."""
from __future__ import annotations

from dataclasses import replace

import pytest

from dopemux.governed_execution.review_economy.keys import (
    REVIEW_TYPES,
    REVIEWER_CLASSES,
    ReceiptRef,
    ReviewReceiptKey,
    ReviewReceiptRecord,
    is_rfc3339_utc,
    parse_rfc3339_utc,
)

HEAD_A = "a" * 40
HEAD_B = "b" * 40
POLICY_DIGEST_A = "1" * 64
POLICY_DIGEST_B = "2" * 64
RECEIPT_DIGEST = "3" * 64


def make_key(
    review_type: str = "CODE_REVIEW",
    head_sha: str = HEAD_A,
    policy_digest: str = POLICY_DIGEST_A,
    reviewer_class: str = "MODEL_STANDARD",
) -> ReviewReceiptKey:
    return ReviewReceiptKey(
        review_type=review_type,
        head_sha=head_sha,
        policy_digest=policy_digest,
        reviewer_class=reviewer_class,
    )


def make_record(
    key: ReviewReceiptKey | None = None,
    verdict: str = "PASS",
    issued_at: str = "2026-01-01T00:00:00Z",
    expires_at: str = "2026-01-02T00:00:00Z",
    invalidated: bool = False,
    subject_head: str = HEAD_A,
) -> ReviewReceiptRecord:
    return ReviewReceiptRecord(
        key=key if key is not None else make_key(),
        verdict=verdict,
        issued_at=issued_at,
        expires_at=expires_at,
        invalidated=invalidated,
        subject_head=subject_head,
        receipt_ref=ReceiptRef(path="proof/w06/receipt.json", sha256=RECEIPT_DIGEST),
    )


# -- ReviewReceiptKey: digest determinism and order sensitivity --------------


def test_digest_deterministic_for_same_fields():
    k1 = make_key()
    k2 = make_key()
    assert k1.digest == k2.digest


def test_digest_matches_manual_sha256():
    import hashlib

    key = make_key()
    joined = "\n".join(
        (key.review_type, key.head_sha, key.policy_digest, key.reviewer_class)
    )
    expected = hashlib.sha256(joined.encode("ascii")).hexdigest()
    assert key.digest == expected


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("review_type", "SECURITY_REVIEW"),
        ("head_sha", HEAD_B),
        ("policy_digest", POLICY_DIGEST_B),
        ("reviewer_class", "MODEL_PREMIUM"),
    ],
)
def test_digest_is_order_and_field_sensitive(field_name: str, value: str):
    base = make_key()
    kwargs = {
        "review_type": base.review_type,
        "head_sha": base.head_sha,
        "policy_digest": base.policy_digest,
        "reviewer_class": base.reviewer_class,
    }
    kwargs[field_name] = value
    changed = ReviewReceiptKey(**kwargs)
    assert changed.digest != base.digest


def test_digest_field_order_is_not_commutative():
    # Swapping head_sha and policy_digest values changes the digest even
    # though the joined-string content pool is otherwise similar, proving
    # digest depends on fixed field order, not on a sorted/unordered join.
    a = ReviewReceiptKey(
        review_type="CI",
        head_sha=HEAD_A,
        policy_digest=POLICY_DIGEST_A,
        reviewer_class="HUMAN",
    )
    b = ReviewReceiptKey(
        review_type="CI",
        head_sha=HEAD_A,
        policy_digest=POLICY_DIGEST_A,
        reviewer_class="HUMAN",
    )
    assert a.digest == b.digest


# -- ReviewReceiptKey: equality via digest ------------------------------------


def test_equal_keys_have_equal_digests():
    a = make_key()
    b = make_key()
    assert a == b
    assert a.digest == b.digest


def test_unequal_keys_have_unequal_digests():
    a = make_key(head_sha=HEAD_A)
    b = make_key(head_sha=HEAD_B)
    assert a != b
    assert a.digest != b.digest


# -- ReviewReceiptKey: closed-set and pattern rejection -----------------------


def test_review_type_closed_set_rejects_unknown():
    with pytest.raises(ValueError):
        make_key(review_type="NOT_A_REVIEW_TYPE")


def test_reviewer_class_closed_set_rejects_unknown():
    with pytest.raises(ValueError):
        make_key(reviewer_class="NOT_A_CLASS")


@pytest.mark.parametrize("review_type", sorted(REVIEW_TYPES))
def test_every_review_type_accepted(review_type: str):
    if review_type == "FINAL_INDEPENDENT_AUDIT":
        replace(make_key(), review_type=review_type, packet_id="TP-X", freeze_sha256="f" * 64)
    else:
        make_key(review_type=review_type)


def test_code_review_four_positional_fields_preserve_legacy_identity():
    key = ReviewReceiptKey("CODE_REVIEW", HEAD_A, POLICY_DIGEST_A, "MODEL_STANDARD")
    assert key == make_key()
    assert key.digest == make_key().digest


@pytest.mark.parametrize(
    "identity",
    [{}, {"packet_id": "TP-X"}, {"freeze_sha256": "f" * 64}],
)
def test_final_audit_rejects_missing_packet_or_freeze_identity(identity):
    with pytest.raises(ValueError, match="packet_id|freeze_sha256"):
        replace(make_key(), review_type="FINAL_INDEPENDENT_AUDIT", **identity)


@pytest.mark.parametrize("review_type", ["CODE_REVIEW", "FINAL_INDEPENDENT_AUDIT"])
@pytest.mark.parametrize("packet_id", ["", "caf\u00e9", 42, b"TP-X"])
def test_packet_identity_requires_nonempty_ascii_string(review_type, packet_id):
    with pytest.raises(ValueError, match="packet_id"):
        replace(make_key(), review_type=review_type, packet_id=packet_id, freeze_sha256="f" * 64)


@pytest.mark.parametrize("review_type", ["CODE_REVIEW", "FINAL_INDEPENDENT_AUDIT"])
@pytest.mark.parametrize("freeze_sha256", ["", "proof/freeze.json", "f" * 63, "f" * 65, "F" * 64, "f" * 64 + "\n", 42])
def test_freeze_identity_requires_lowercase_sha256(review_type, freeze_sha256):
    with pytest.raises(ValueError, match="freeze_sha256"):
        replace(make_key(), review_type=review_type, packet_id="TP-X", freeze_sha256=freeze_sha256)


@pytest.mark.parametrize("review_type", ["CODE_REVIEW", "FINAL_INDEPENDENT_AUDIT"])
def test_packet_and_freeze_identity_affect_equality_and_digest(review_type):
    base = replace(make_key(), review_type=review_type, packet_id="TP-X", freeze_sha256="f" * 64)
    assert replace(base) == base
    assert replace(base).digest == base.digest
    for changed in [replace(base, packet_id="TP-Y"), replace(base, freeze_sha256="e" * 64)]:
        assert changed != base
        assert changed.digest != base.digest


def test_optional_nonfinal_identity_is_unambiguous_and_narrows_legacy_key():
    base = make_key()
    keys = [
        base,
        replace(base, packet_id="TP-X"),
        replace(base, freeze_sha256="f" * 64),
        replace(base, packet_id="TP-X", freeze_sha256="f" * 64),
        replace(base, packet_id="TP-X\nf"),
        replace(base, packet_id="TP-X\\nf"),
    ]
    assert len(set(keys)) == len(keys)
    assert len({key.digest for key in keys}) == len(keys)


@pytest.mark.parametrize("reviewer_class", sorted(REVIEWER_CLASSES))
def test_every_reviewer_class_accepted(reviewer_class: str):
    make_key(reviewer_class=reviewer_class)


@pytest.mark.parametrize(
    "bad_head_sha",
    ["", "not-hex", "a" * 39, "a" * 41, "A" * 40, HEAD_A + "\n"],
)
def test_head_sha_pattern_rejects_bad_values(bad_head_sha: str):
    with pytest.raises(ValueError):
        make_key(head_sha=bad_head_sha)


@pytest.mark.parametrize(
    "bad_policy_digest",
    ["", "not-hex", "1" * 63, "1" * 65, "A" * 64],
)
def test_policy_digest_pattern_rejects_bad_values(bad_policy_digest: str):
    with pytest.raises(ValueError):
        make_key(policy_digest=bad_policy_digest)


# -- ReceiptRef ----------------------------------------------------------------


def test_receipt_ref_accepts_well_formed():
    ref = ReceiptRef(path="proof/w06/receipt.json", sha256=RECEIPT_DIGEST)
    assert ref.path == "proof/w06/receipt.json"


def test_receipt_ref_rejects_empty_path():
    with pytest.raises(ValueError):
        ReceiptRef(path="", sha256=RECEIPT_DIGEST)


def test_receipt_ref_rejects_bad_sha256():
    with pytest.raises(ValueError):
        ReceiptRef(path="proof/w06/receipt.json", sha256="not-hex")


# -- ReviewReceiptRecord --------------------------------------------------------


def test_record_accepts_well_formed():
    record = make_record()
    assert record.verdict == "PASS"


def test_record_rejects_non_key():
    with pytest.raises(ValueError):
        ReviewReceiptRecord(
            key="not-a-key",  # type: ignore[arg-type]
            verdict="PASS",
            issued_at="2026-01-01T00:00:00Z",
            expires_at="2026-01-02T00:00:00Z",
            invalidated=False,
            subject_head=HEAD_A,
            receipt_ref=ReceiptRef(path="p", sha256=RECEIPT_DIGEST),
        )


def test_record_rejects_empty_verdict():
    with pytest.raises(ValueError):
        make_record(verdict="")


@pytest.mark.parametrize(
    "bad_timestamp",
    ["2026-01-01", "2026-01-01T00:00:00", "not-a-time", "2026-01-01T00:00:00+00:00"],
)
def test_record_rejects_bad_issued_at(bad_timestamp: str):
    with pytest.raises(ValueError):
        make_record(issued_at=bad_timestamp)


@pytest.mark.parametrize(
    "bad_timestamp",
    ["2026-01-01", "2026-01-01T00:00:00", "not-a-time", "2026-01-01T00:00:00+00:00"],
)
def test_record_rejects_bad_expires_at(bad_timestamp: str):
    with pytest.raises(ValueError):
        make_record(expires_at=bad_timestamp)


def test_record_rejects_issued_after_expires():
    with pytest.raises(ValueError):
        make_record(
            issued_at="2026-01-02T00:00:00Z",
            expires_at="2026-01-01T00:00:00Z",
        )


def test_record_rejects_non_bool_invalidated():
    with pytest.raises(ValueError):
        make_record(invalidated="yes")  # type: ignore[arg-type]


def test_record_rejects_bad_subject_head():
    with pytest.raises(ValueError):
        make_record(subject_head="not-a-git-oid")


def test_record_rejects_non_receipt_ref():
    with pytest.raises(ValueError):
        ReviewReceiptRecord(
            key=make_key(),
            verdict="PASS",
            issued_at="2026-01-01T00:00:00Z",
            expires_at="2026-01-02T00:00:00Z",
            invalidated=False,
            subject_head=HEAD_A,
            receipt_ref={"path": "p", "sha256": RECEIPT_DIGEST},  # type: ignore[arg-type]
        )


# -- timestamp helpers -----------------------------------------------------------


def test_is_rfc3339_utc_accepts_valid():
    assert is_rfc3339_utc("2026-01-01T00:00:00Z")
    assert is_rfc3339_utc("2026-01-01T00:00:00.123Z")


@pytest.mark.parametrize(
    "value",
    ["2026-01-01T00:00:00", "2026-01-01T00:00:00+00:00", "not-a-time", 12345],
)
def test_is_rfc3339_utc_rejects_invalid(value: object):
    assert is_rfc3339_utc(value) is False


def test_parse_rfc3339_utc_round_trips_ordering():
    earlier = parse_rfc3339_utc("2026-01-01T00:00:00Z")
    later = parse_rfc3339_utc("2026-01-02T00:00:00Z")
    assert earlier < later


def test_parse_rfc3339_utc_rejects_malformed():
    with pytest.raises(ValueError):
        parse_rfc3339_utc("not-a-time")
