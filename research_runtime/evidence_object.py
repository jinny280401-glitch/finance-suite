"""I1 — Evidence Object Materialization (local runtime reference).

Materializes the I0 Schema Contract's semantic cells into a runtime-creatable,
carriable, verifiable Evidence Object.

Scope (user-decreed 2026-08-13, Option A):
  LOCAL ONLY — no production wiring, no /api/analyze, no MCP/Agent tool result,
  no Search-bypass repair, no admission-enforced claim, no deployment.

Semantic source of truth = frozen I0 validator
  docs/spec/validate_i0_schema_contract.py (31/31 PASS).
  This module imports the frozen D6 ceiling, §1.8 freshness matrix, enum sets,
  and restricted-JCS/SHA3-256 hashing directly from it. The runtime object MUST
  NOT re-implement those semantics (drift is forbidden). I1 adds only the
  *carrier*: a typed, immutable, serializable object + materialization,
  fail-closed, and consumer-boundary behavior.

Field mapping (task label → I0 frozen name):
  EVIDENCE_TYPE          → L1 content_type
  PROVENANCE             → L2 provenance
  CLASSIFICATION         → L2 classification
  PURPOSE                → L3 purpose
  PROVIDER_STATE         → L2 provider_identity + field_integrity
  TEMPORAL_METADATA      → L1 temporal_semantics + L2 freshness + §1.8 max_age
  QC_STATUS              → runtime _qc status (success/partial/failure)
  ALLOWED_USE            → L3 allowed_use
  BLOCKED_FIELDS         → L3 blocked_use
  CLAIM_STRENGTH_CEILING → L3 max_claim_strength (D6 d6_ceiling)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Frozen I0 semantics live in docs/spec. Import them; do NOT re-implement.
_SPEC = Path(__file__).resolve().parents[1] / "docs" / "spec"
if str(_SPEC) not in sys.path:
    sys.path.insert(0, str(_SPEC))

from validate_i0_schema_contract import (  # noqa: E402
    MATRIX,
    CLAIM_STRENGTHS,
    CONTENT_TYPES,
    FI_VALUES,
    PI_VALUES,
    PROVENANCES,
    PURPOSES,
    TEMPORAL_SEMANTICS,
    USE_CLASSES,
    classification_valid,
    d6_ceiling,
    h,
    is_utc_iso,
)

SCHEMA_VERSION = "i1.v0.1"
QC_STATUSES = {"success", "partial", "failure"}


class MaterializeReject(ValueError):
    """Fail-closed: input state cannot be materialized into a valid Evidence
    Object (unknown provenance, invalid purpose, missing field, etc.)."""


@dataclass(frozen=True)
class ProviderState:
    """I0 L2 provider-dimension assessment (D5-applicable dimensions)."""

    provider_identity: str  # PI_VALUES: VERIFIED / UNVERIFIED / NOT_APPLICABLE
    field_integrity: str    # FI_VALUES: PASS / PARTIAL / FAIL / NOT_APPLICABLE


@dataclass(frozen=True)
class TemporalMetadata:
    """I0 L1+L2 temporal cells + §1.8 max_age."""

    temporal_semantics: str        # TEMPORAL_SEMANTICS
    freshness: str                 # UTC ISO 8601 (L2 freshness timestamp)
    max_age_seconds: int | None    # MATRIX[purpose][temporal_semantics]; None = ∞
    stale: bool                    # derived: now - freshness > max_age (when bounded)


@dataclass(frozen=True)
class EvidenceObject:
    """Immutable I0-conformant Evidence Object.

    The identity (`evidence_id`) is the SHA3-256 of the restricted-JCS canonical
    serialization of the semantic fields below (max_age_seconds/stale are
    derived caches and excluded). Two objects with identical semantics share an
    identity; any tamper of a carried field breaks the round-trip.
    """

    evidence_id: str
    schema_version: str
    content_type: str
    provenance: str
    classification: str
    purpose: str
    provider_state: ProviderState
    temporal: TemporalMetadata
    qc_status: str
    allowed_use: tuple[str, ...]
    blocked_use: tuple[str, ...]
    claim_strength_ceiling: str  # CLAIM_STRENGTHS (D6)

    def to_dict(self) -> dict[str, Any]:
        """Serializable form (fully self-describing, round-trips via from_dict)."""
        return {
            "evidence_id": self.evidence_id,
            "schema_version": self.schema_version,
            "content_type": self.content_type,
            "provenance": self.provenance,
            "classification": self.classification,
            "purpose": self.purpose,
            "provider_identity": self.provider_state.provider_identity,
            "field_integrity": self.provider_state.field_integrity,
            "qc_status": self.qc_status,
            "temporal_semantics": self.temporal.temporal_semantics,
            "freshness": self.temporal.freshness,
            "max_age_seconds": self.temporal.max_age_seconds,
            "stale": self.temporal.stale,
            "allowed_use": list(self.allowed_use),
            "blocked_use": list(self.blocked_use),
            "claim_strength_ceiling": self.claim_strength_ceiling,
        }


def _canonical_semantics(obj: EvidenceObject) -> dict[str, Any]:
    """The semantic cells that define identity (jcs sorts keys; lists sorted at
    construction). max_age_seconds/stale are derived caches → excluded."""
    return {
        "schema_version": obj.schema_version,
        "content_type": obj.content_type,
        "provenance": obj.provenance,
        "classification": obj.classification,
        "purpose": obj.purpose,
        "provider_identity": obj.provider_state.provider_identity,
        "field_integrity": obj.provider_state.field_integrity,
        "qc_status": obj.qc_status,
        "temporal_semantics": obj.temporal.temporal_semantics,
        "freshness": obj.temporal.freshness,
        "allowed_use": list(obj.allowed_use),
        "blocked_use": list(obj.blocked_use),
        "claim_strength_ceiling": obj.claim_strength_ceiling,
    }


def _now_or_default(now: str | None) -> datetime:
    if now is None:
        return datetime.now(timezone.utc)
    if not is_utc_iso(now):
        raise MaterializeReject(f"now is not UTC ISO 8601: {now!r}")
    return datetime.fromisoformat(now.replace("Z", "+00:00"))


def materialize(
    *,
    content_type: str,
    provenance: str,
    classification: str,
    purpose: str,
    temporal_semantics: str,
    freshness: str,
    qc_status: str = "success",
    provider_identity: str = "NOT_APPLICABLE",
    field_integrity: str = "NOT_APPLICABLE",
    allowed_use: tuple[str, ...] = (),
    blocked_use: tuple[str, ...] = (),
    now: str | None = None,
) -> EvidenceObject:
    """Deterministically map I0 semantic cells → an immutable EvidenceObject.

    Fail-closed: any out-of-contract value raises MaterializeReject rather than
    producing a bogus object.
    """
    # --- enum / shape validation (fail-closed, in dependency order) ---
    if content_type not in CONTENT_TYPES:
        raise MaterializeReject(f"unknown content_type: {content_type!r}")
    if provenance not in PROVENANCES:
        raise MaterializeReject(f"unknown provenance: {provenance!r}")
    if purpose not in PURPOSES:
        raise MaterializeReject(f"invalid purpose: {purpose!r}")
    if temporal_semantics not in TEMPORAL_SEMANTICS:
        raise MaterializeReject(f"unknown temporal_semantics: {temporal_semantics!r}")
    if not classification_valid(classification):
        raise MaterializeReject(f"invalid classification: {classification!r}")
    if provider_identity not in PI_VALUES:
        raise MaterializeReject(f"invalid provider_identity: {provider_identity!r}")
    if field_integrity not in FI_VALUES:
        raise MaterializeReject(f"invalid field_integrity: {field_integrity!r}")
    if qc_status not in QC_STATUSES:
        raise MaterializeReject(f"invalid qc_status: {qc_status!r}")
    if not is_utc_iso(freshness):
        raise MaterializeReject(f"freshness is not UTC ISO 8601: {freshness!r}")
    for u in allowed_use:
        if u not in USE_CLASSES:
            raise MaterializeReject(f"unknown allowed_use class: {u!r}")
    for b in blocked_use:
        if b not in USE_CLASSES:
            raise MaterializeReject(f"unknown blocked_use class: {b!r}")

    # --- D6 claim ceiling (fail-closed on undeterminable) ---
    ceiling = d6_ceiling(content_type, provenance, purpose, classification)
    if ceiling is None or ceiling not in CLAIM_STRENGTHS:
        raise MaterializeReject(
            f"claim ceiling undeterminable for "
            f"{content_type}×{provenance}×{purpose}×{classification}"
        )

    # --- §1.8 max_age + staleness ---
    max_age = MATRIX[purpose][temporal_semantics]
    stale = False
    if max_age is not None:
        stale = (_now_or_default(now) - datetime.fromisoformat(
            freshness.replace("Z", "+00:00")
        )).total_seconds() > max_age

    obj = EvidenceObject(
        evidence_id="",  # filled below (identity depends on all fields)
        schema_version=SCHEMA_VERSION,
        content_type=content_type,
        provenance=provenance,
        classification=classification,
        purpose=purpose,
        provider_state=ProviderState(
            provider_identity=provider_identity,
            field_integrity=field_integrity,
        ),
        temporal=TemporalMetadata(
            temporal_semantics=temporal_semantics,
            freshness=freshness,
            max_age_seconds=max_age,
            stale=stale,
        ),
        qc_status=qc_status,
        allowed_use=tuple(sorted(set(allowed_use))),
        blocked_use=tuple(sorted(set(blocked_use))),
        claim_strength_ceiling=ceiling,
    )
    evidence_id = h(_canonical_semantics(obj))
    return EvidenceObject(
        evidence_id=evidence_id,
        schema_version=obj.schema_version,
        content_type=obj.content_type,
        provenance=obj.provenance,
        classification=obj.classification,
        purpose=obj.purpose,
        provider_state=obj.provider_state,
        temporal=obj.temporal,
        qc_status=obj.qc_status,
        allowed_use=obj.allowed_use,
        blocked_use=obj.blocked_use,
        claim_strength_ceiling=obj.claim_strength_ceiling,
    )


def from_dict(d: dict[str, Any], *, now: str | None = None) -> EvidenceObject:
    """Deserialize a to_dict() output back into an EvidenceObject.

    Recomputes every derived field (ceiling / max_age / stale) and verifies the
    stored evidence_id and claim_strength_ceiling match — a tampered object
    fails closed rather than round-tripping.
    """
    missing = [k for k in (
        "evidence_id", "schema_version", "content_type", "provenance",
        "classification", "purpose", "provider_identity", "field_integrity",
        "qc_status", "temporal_semantics", "freshness", "allowed_use",
        "blocked_use", "claim_strength_ceiling",
    ) if k not in d]
    if missing:
        raise MaterializeReject(f"missing field(s): {missing}")

    obj = materialize(
        content_type=d["content_type"],
        provenance=d["provenance"],
        classification=d["classification"],
        purpose=d["purpose"],
        temporal_semantics=d["temporal_semantics"],
        freshness=d["freshness"],
        qc_status=d["qc_status"],
        provider_identity=d["provider_identity"],
        field_integrity=d["field_integrity"],
        allowed_use=tuple(d["allowed_use"]),
        blocked_use=tuple(d["blocked_use"]),
        now=now,
    )
    if d["schema_version"] != obj.schema_version:
        raise MaterializeReject(f"schema_version mismatch: {d['schema_version']!r}")
    if d["evidence_id"] != obj.evidence_id:
        raise MaterializeReject(
            f"identity mismatch: stored {d['evidence_id']!r} != recomputed {obj.evidence_id!r}"
        )
    if d["claim_strength_ceiling"] != obj.claim_strength_ceiling:
        raise MaterializeReject(
            f"claim_strength_ceiling tamper: stored {d['claim_strength_ceiling']!r} "
            f"!= D6 recomputation {obj.claim_strength_ceiling!r}"
        )
    return obj


@dataclass(frozen=True)
class Admission:
    """Local consumer-boundary result (reference path)."""

    consumer: str
    purpose: str
    verdict: str          # ALLOW / ALLOW_WITH_MARKER / BLOCK
    claim_strength_ceiling: str
    allowed_use: tuple[str, ...]


def admit(obj: Any, *, consumer: str, purpose: str) -> Admission:
    """Local consumer boundary: accepts ONLY an EvidenceObject, never a raw
    provider dict. Fail-closes on purpose mismatch.

    Verdict (reference path, minimal):
      ceiling == NO_CLAIM       → BLOCK
      ceiling == INFORMATIONAL  → ALLOW_WITH_MARKER
      otherwise                 → ALLOW
    """
    if not isinstance(obj, EvidenceObject):
        raise TypeError("admit() only accepts EvidenceObject (not raw provider dict)")
    if purpose != obj.purpose:
        raise MaterializeReject(
            f"purpose mismatch: consumer {purpose!r} vs object {obj.purpose!r}"
        )
    ceiling = obj.claim_strength_ceiling
    if ceiling == "NO_CLAIM":
        verdict = "BLOCK"
    elif ceiling == "INFORMATIONAL":
        verdict = "ALLOW_WITH_MARKER"
    else:
        verdict = "ALLOW"
    return Admission(
        consumer=consumer,
        purpose=obj.purpose,
        verdict=verdict,
        claim_strength_ceiling=ceiling,
        allowed_use=obj.allowed_use,
    )
