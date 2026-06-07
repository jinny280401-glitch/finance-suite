"""Evidence Manifest Contract v0 — Contract 语义 smoke test.

验收标准：
1. Evidence 不得包含 forbidden fields（_qc / raw / payload / raw_response / gateway_response / provider_payload）
2. Evidence Manifest 不得包含 qc_status=="failure" 且 allowed_use==[] 的 Evidence
3. Citation 必须通过 evidence_id 回溯到 Manifest 中的 Evidence
4. Citation 不得引用 qc_status=="failure" 的 Evidence
5. Evidence Lineage 必须存在：任意 Evidence 必须有对应 Lineage 记录
6. Lineage 链路完整：Citation → Evidence → Lineage → Provider 无断裂
7. Section 不得绕过 Manifest 直接使用 raw dict

不跑真实数据，不接 LLM，不改生产。
"""
from __future__ import annotations

import sys
import uuid
from dataclasses import dataclass, field
from typing import Any


# ─────────────────────────────────────────────
# Contract stubs (mirrors contract v0 docs)
# ─────────────────────────────────────────────

FORBIDDEN_FIELDS = {"raw_response", "gateway_response", "provider_payload", "_qc", "raw", "payload"}


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    title: str
    summary: str
    provider: str
    provider_tier: int
    qc_status: str
    allowed_use: list[str]
    blocked_fields: list[str]
    data: dict[str, Any]
    as_of: str | None = None
    created_at: str = "2026-06-07T00:00:00Z"

    def __post_init__(self) -> None:
        violations = FORBIDDEN_FIELDS.intersection(self.data.keys())
        if violations:
            raise ValueError(
                f"Evidence.data contains forbidden fields: {violations}"
            )


@dataclass
class EvidenceManifest:
    manifest_id: str
    section_id: str
    evidences: list[Evidence]
    created_at: str = "2026-06-07T00:00:00Z"

    def __post_init__(self) -> None:
        seen_ids: set[str] = set()
        for ev in self.evidences:
            if ev.evidence_id in seen_ids:
                raise ValueError(f"Duplicate evidence_id: {ev.evidence_id}")
            seen_ids.add(ev.evidence_id)


@dataclass(frozen=True)
class Citation:
    citation_id: str
    evidence_id: str
    field_used: str
    provider: str


@dataclass(frozen=True)
class EvidenceLineage:
    evidence_id: str
    provider: str
    provider_tier: int
    gateway_timestamp: str
    trust_gate_status: str
    trust_gate_reason: str | None
    trust_gate_blocked_fields: list[str]
    allowed_use: list[str]
    as_of: str | None = None


@dataclass
class LineageStore:
    records: dict[str, EvidenceLineage] = field(default_factory=dict)

    def add(self, lineage: EvidenceLineage) -> None:
        if lineage.evidence_id in self.records:
            raise ValueError(f"Duplicate lineage for {lineage.evidence_id}")
        self.records[lineage.evidence_id] = lineage

    def get(self, evidence_id: str) -> EvidenceLineage | None:
        return self.records.get(evidence_id)

    def trace_back(self, citation: Citation) -> EvidenceLineage | None:
        return self.get(citation.evidence_id)


# ─────────────────────────────────────────────
# Validators
# ─────────────────────────────────────────────

def validate_no_forbidden_fields(evidence: Evidence) -> None:
    violations = FORBIDDEN_FIELDS.intersection(evidence.data.keys())
    if violations:
        raise ValueError(f"Evidence contains forbidden fields: {violations}")


def validate_manifest_no_blocked_evidence(manifest: EvidenceManifest) -> list[str]:
    violations = []
    for ev in manifest.evidences:
        if ev.qc_status == "failure" and ev.allowed_use == []:
            violations.append(ev.evidence_id)
    return violations


def validate_citations(
    citations: list[Citation],
    manifest: EvidenceManifest,
) -> list[str]:
    manifest_ids = {ev.evidence_id for ev in manifest.evidences}
    manifest_map = {ev.evidence_id: ev for ev in manifest.evidences}
    violations = []

    for cite in citations:
        if cite.evidence_id not in manifest_ids:
            violations.append(f"{cite.citation_id}: evidence_id not in manifest")
            continue
        ev = manifest_map[cite.evidence_id]
        if cite.field_used not in ev.data:
            violations.append(f"{cite.citation_id}: field_used '{cite.field_used}' not in evidence.data")
        if ev.qc_status == "failure":
            violations.append(f"{cite.citation_id}: references failure evidence")

    return violations


def validate_lineage_completeness(
    manifest: EvidenceManifest,
    lineage_store: LineageStore,
) -> list[str]:
    missing = []
    for ev in manifest.evidences:
        if lineage_store.get(ev.evidence_id) is None:
            missing.append(ev.evidence_id)
    return missing


def validate_citation_lineage(
    citations: list[Citation],
    manifest: EvidenceManifest,
    lineage_store: LineageStore,
) -> list[str]:
    breaks = []
    manifest_map = {ev.evidence_id: ev for ev in manifest.evidences}

    for cite in citations:
        # Citation → Evidence
        if cite.evidence_id not in manifest_map:
            breaks.append(f"{cite.citation_id}: Citation→Evidence break")
            continue
        # Evidence → Lineage
        lineage = lineage_store.get(cite.evidence_id)
        if lineage is None:
            breaks.append(f"{cite.citation_id}: Evidence→Lineage break")
            continue
        # Lineage → Provider
        if not lineage.provider:
            breaks.append(f"{cite.citation_id}: Lineage→Provider break (empty provider)")
        # Lineage → Trust Gate
        if not lineage.trust_gate_status:
            breaks.append(f"{cite.citation_id}: Lineage→TrustGate break (empty status)")

    return breaks


def validate_section_uses_manifest_only(manifest_or_raw: Any) -> None:
    """Section must receive EvidenceManifest, not raw dict."""
    if not isinstance(manifest_or_raw, EvidenceManifest):
        raise TypeError(
            f"Section requires EvidenceManifest, got {type(manifest_or_raw).__name__}"
        )


# ─────────────────────────────────────────────
# Test helpers
# ─────────────────────────────────────────────

def _eid() -> str:
    return f"evidence:{uuid.uuid4().hex[:8]}"


def _make_evidence(
    qc_status: str = "success",
    allowed_use: list[str] | None = None,
    data: dict[str, Any] | None = None,
) -> Evidence:
    if allowed_use is None:
        allowed_use = ["fundamental_overview", "valuation_analysis"]
    return Evidence(
        evidence_id=_eid(),
        title="Test Evidence",
        summary="Test summary",
        provider="wind",
        provider_tier=1,
        qc_status=qc_status,
        allowed_use=allowed_use,
        blocked_fields=[],
        data=data if data is not None else {"pe": 20, "revenue": 1000, "net_profit": 200},
    )


def _make_lineage(evidence_id: str, provider: str = "wind") -> EvidenceLineage:
    return EvidenceLineage(
        evidence_id=evidence_id,
        provider=provider,
        provider_tier=1,
        gateway_timestamp="2026-06-07T10:00:00Z",
        trust_gate_status="success",
        trust_gate_reason=None,
        trust_gate_blocked_fields=[],
        allowed_use=["fundamental_overview", "valuation_analysis"],
        as_of="2026-06-06",
    )


# ─────────────────────────────────────────────
# Test cases
# ─────────────────────────────────────────────

def case_1_forbidden_fields_rejected() -> None:
    """Evidence.data 不得包含 forbidden fields"""
    try:
        Evidence(
            evidence_id=_eid(),
            title="Bad",
            summary="Contains raw",
            provider="wind",
            provider_tier=1,
            qc_status="success",
            allowed_use=["fundamental_overview"],
            blocked_fields=[],
            data={"pe": 20, "_qc": {"status": "success"}, "payload": {"raw": True}},
        )
        raise AssertionError("Should reject forbidden fields in data")
    except ValueError as e:
        assert "forbidden" in str(e).lower()


def case_1b_clean_evidence_accepted() -> None:
    """Clean Evidence.data 被接受"""
    ev = _make_evidence()
    validate_no_forbidden_fields(ev)


def case_2_manifest_rejects_blocked_evidence() -> None:
    """Manifest 不得包含 qc_status=failure + allowed_use=[] 的 Evidence"""
    blocked_ev = _make_evidence(qc_status="failure", allowed_use=[])
    good_ev = _make_evidence()
    manifest = EvidenceManifest(
        manifest_id=f"manifest:{uuid.uuid4().hex[:8]}",
        section_id="section:test",
        evidences=[good_ev, blocked_ev],
    )
    violations = validate_manifest_no_blocked_evidence(manifest)
    assert len(violations) == 1
    assert violations[0] == blocked_ev.evidence_id


def case_3_citation_traces_to_evidence() -> None:
    """Citation 必须通过 evidence_id 回溯到 Manifest 中的 Evidence"""
    ev = _make_evidence()
    manifest = EvidenceManifest(
        manifest_id=f"manifest:{uuid.uuid4().hex[:8]}",
        section_id="section:test",
        evidences=[ev],
    )
    # Valid citation
    good_cite = Citation(
        citation_id=f"cite:{uuid.uuid4().hex[:8]}",
        evidence_id=ev.evidence_id,
        field_used="pe",
        provider="wind",
    )
    violations = validate_citations([good_cite], manifest)
    assert violations == []

    # Invalid citation (evidence_id not in manifest)
    bad_cite = Citation(
        citation_id=f"cite:{uuid.uuid4().hex[:8]}",
        evidence_id="evidence:nonexistent",
        field_used="pe",
        provider="wind",
    )
    violations = validate_citations([bad_cite], manifest)
    assert len(violations) == 1


def case_4_citation_rejects_failure_evidence() -> None:
    """Citation 不得引用 qc_status=failure 的 Evidence"""
    ev = _make_evidence(qc_status="failure", allowed_use=["fundamental_overview"])
    manifest = EvidenceManifest(
        manifest_id=f"manifest:{uuid.uuid4().hex[:8]}",
        section_id="section:test",
        evidences=[ev],
    )
    cite = Citation(
        citation_id=f"cite:{uuid.uuid4().hex[:8]}",
        evidence_id=ev.evidence_id,
        field_used="pe",
        provider="wind",
    )
    violations = validate_citations([cite], manifest)
    assert any("failure" in v for v in violations)


def case_5_lineage_must_exist() -> None:
    """任意 Evidence 必须有对应 Lineage 记录"""
    ev = _make_evidence()
    manifest = EvidenceManifest(
        manifest_id=f"manifest:{uuid.uuid4().hex[:8]}",
        section_id="section:test",
        evidences=[ev],
    )

    # Empty lineage store → missing
    empty_store = LineageStore()
    missing = validate_lineage_completeness(manifest, empty_store)
    assert ev.evidence_id in missing

    # With lineage → complete
    store = LineageStore()
    store.add(_make_lineage(ev.evidence_id))
    missing = validate_lineage_completeness(manifest, store)
    assert missing == []


def case_6_full_lineage_chain() -> None:
    """Citation → Evidence → Lineage → Provider 无断裂"""
    ev = _make_evidence()
    manifest = EvidenceManifest(
        manifest_id=f"manifest:{uuid.uuid4().hex[:8]}",
        section_id="section:test",
        evidences=[ev],
    )
    store = LineageStore()
    store.add(_make_lineage(ev.evidence_id, provider="wind"))

    cite = Citation(
        citation_id=f"cite:{uuid.uuid4().hex[:8]}",
        evidence_id=ev.evidence_id,
        field_used="pe",
        provider="wind",
    )
    breaks = validate_citation_lineage([cite], manifest, store)
    assert breaks == []

    # Verify trace_back works
    lineage = store.trace_back(cite)
    assert lineage is not None
    assert lineage.provider == "wind"
    assert lineage.trust_gate_status == "success"


def case_6b_lineage_break_detected() -> None:
    """Lineage 断裂必须被检测"""
    ev = _make_evidence()
    manifest = EvidenceManifest(
        manifest_id=f"manifest:{uuid.uuid4().hex[:8]}",
        section_id="section:test",
        evidences=[ev],
    )
    empty_store = LineageStore()

    cite = Citation(
        citation_id=f"cite:{uuid.uuid4().hex[:8]}",
        evidence_id=ev.evidence_id,
        field_used="pe",
        provider="wind",
    )
    breaks = validate_citation_lineage([cite], manifest, empty_store)
    assert len(breaks) == 1
    assert "Lineage break" in breaks[0]


def case_7_section_rejects_raw_dict() -> None:
    """Section 不得绕过 Manifest 直接使用 raw dict"""
    raw_dict = {"pe": 20, "provider": "wind"}
    try:
        validate_section_uses_manifest_only(raw_dict)
        raise AssertionError("Should reject raw dict")
    except TypeError as e:
        assert "EvidenceManifest" in str(e)


def case_7b_section_accepts_manifest() -> None:
    """Section 接受 EvidenceManifest"""
    ev = _make_evidence()
    manifest = EvidenceManifest(
        manifest_id=f"manifest:{uuid.uuid4().hex[:8]}",
        section_id="section:test",
        evidences=[ev],
    )
    validate_section_uses_manifest_only(manifest)  # must not raise


# ─────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────

def main() -> int:
    cases = [
        ("case_1a: forbidden fields rejected in Evidence.data", case_1_forbidden_fields_rejected),
        ("case_1b: clean evidence accepted", case_1b_clean_evidence_accepted),
        ("case_2:  manifest rejects blocked evidence", case_2_manifest_rejects_blocked_evidence),
        ("case_3:  citation traces to manifest evidence", case_3_citation_traces_to_evidence),
        ("case_4:  citation rejects failure evidence", case_4_citation_rejects_failure_evidence),
        ("case_5:  lineage must exist for all evidence", case_5_lineage_must_exist),
        ("case_6a: full lineage chain (no breaks)", case_6_full_lineage_chain),
        ("case_6b: lineage break detected", case_6b_lineage_break_detected),
        ("case_7a: section rejects raw dict", case_7_section_rejects_raw_dict),
        ("case_7b: section accepts manifest", case_7b_section_accepts_manifest),
    ]

    passed = 0
    failed = 0
    for name, fn in cases:
        try:
            fn()
            print(f"  PASS  {name}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {name}: {e}")
            failed += 1

    print()
    print(f"Evidence Manifest Contract v0 smoke: {passed}/{passed + failed} PASS")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
