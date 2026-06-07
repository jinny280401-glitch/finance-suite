"""Section Workflow Contract v0 — Contract 语义 smoke test.

验收标准：
1. section 无 evidence manifest 不得进入 ANALYZE
2. depends_on 失败时 section 必须 SKIPPED
3. section output 必须带 qc/status/citations 占位
4. raw gateway response 不得出现在 section input
5. 所有事件必须能追踪 section_id

不跑真实数据，不接 LLM，不改生产。
"""
from __future__ import annotations

import sys
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ─────────────────────────────────────────────
# Minimal contract stubs (mirrors section_workflow_contract_v0.md)
# ─────────────────────────────────────────────

class SectionStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    RETRIEVING = "RETRIEVING"
    ANALYZE = "ANALYZE"
    QC = "QC"
    DONE = "DONE"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"


# Import EvidenceBundle from research_runtime to avoid re-defining
try:
    from research_runtime.evidence_bundle import EvidenceBundle, build_evidence_bundle
except ImportError:
    # Minimal stub if research_runtime not on path
    @dataclass(frozen=True)
    class EvidenceBundle:  # type: ignore[no-redef]
        evidence: dict[str, Any]
        allowed_use: list[str]
        blocked_fields: list[str]
        trust_status: str
        reason: str | None = None
        source: dict[str, Any] = field(default_factory=dict)

    def build_evidence_bundle(gateway_response: dict) -> EvidenceBundle:
        qc = gateway_response.get("_qc", {})
        return EvidenceBundle(
            evidence=gateway_response.get("data", {}),
            allowed_use=["fundamental_overview"] if qc.get("status") == "partial" else [],
            blocked_fields=qc.get("missing_fields", []),
            trust_status=qc.get("status", "failure"),
            reason=qc.get("reason"),
            source={"provider": gateway_response.get("provider")},
        )


@dataclass(frozen=True)
class EvidenceManifestEntry:
    manifest_id: str
    evidence_bundle: EvidenceBundle
    evidence_type: str
    as_of: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_bundle, EvidenceBundle):
            raise TypeError(
                "EvidenceManifestEntry.evidence_bundle must be EvidenceBundle, "
                f"got {type(self.evidence_bundle).__name__}"
            )


@dataclass
class SectionInput:
    section_id: str
    symbol: str
    query: str
    evidence_manifest: list[EvidenceManifestEntry]
    allowed_use_filter: list[str]
    required_evidence_types: list[str]
    optional_evidence_types: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SectionCitation:
    citation_id: str
    manifest_id: str
    field_used: str
    allowed_use_observed: str


@dataclass
class SectionQC:
    passed: bool
    status: str
    evidence_count: int
    evidence_all_real: bool
    has_fallback_evidence: bool
    has_mock_evidence: bool
    missing_required_types: list[str]
    blocked_evidence_count: int
    limitations: list[str]


@dataclass
class SectionOutput:
    section_id: str
    status: SectionStatus
    qc: SectionQC
    body: str
    citations: list[SectionCitation]
    used_evidence_ids: list[str]
    limitations: list[str]
    created_at: str

    def __post_init__(self) -> None:
        # citations must not be None
        if self.citations is None:
            raise TypeError("SectionOutput.citations must not be None")
        # used_evidence_ids must not reference unknown manifest_ids
        # (checked externally in validation)


@dataclass
class SectionEvent:
    event_id: str
    section_id: str
    type: str
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        if "section_id" not in self.payload:
            raise ValueError(
                f"Event '{self.type}' payload must include section_id"
            )


# ─────────────────────────────────────────────
# Contract validators
# ─────────────────────────────────────────────

def validate_no_raw_gateway_in_manifest(manifest: list[EvidenceManifestEntry]) -> None:
    """Red line: raw gateway response must not appear in evidence manifest."""
    for entry in manifest:
        if not isinstance(entry.evidence_bundle, EvidenceBundle):
            raise TypeError(
                f"manifest entry {entry.manifest_id}: evidence_bundle must be "
                f"EvidenceBundle, got {type(entry.evidence_bundle).__name__}"
            )


def validate_section_can_enter_analyze(section_input: SectionInput) -> None:
    """Contract §2: section without evidence manifest must not enter ANALYZE."""
    if not section_input.evidence_manifest:
        raise ValueError(
            f"Section '{section_input.section_id}' cannot enter ANALYZE: "
            "evidence_manifest is empty"
        )


def validate_depends_on(
    section_id: str,
    dependencies: list[str],
    section_statuses: dict[str, SectionStatus],
) -> SectionStatus:
    """Contract §4: returns READY or SKIPPED based on dependency statuses."""
    for dep_id in dependencies:
        dep_status = section_statuses.get(dep_id)
        if dep_status in (SectionStatus.SKIPPED, SectionStatus.FAILED):
            return SectionStatus.SKIPPED
        if dep_status != SectionStatus.DONE:
            raise ValueError(
                f"Section '{section_id}' dependency '{dep_id}' is not yet DONE "
                f"(current status: {dep_status})"
            )
    return SectionStatus.READY


def validate_section_output(output: SectionOutput) -> None:
    """Contract §3.2: output must have qc, status, and citations placeholder."""
    assert output.qc is not None, "SectionOutput.qc must not be None"
    assert output.status is not None, "SectionOutput.status must not be None"
    assert output.citations is not None, "SectionOutput.citations must not be None"


def validate_event_has_section_id(event: SectionEvent) -> None:
    """Contract §6.2: all events must carry section_id."""
    assert "section_id" in event.payload, (
        f"Event '{event.type}' missing section_id in payload"
    )


# ─────────────────────────────────────────────
# Smoke test cases
# ─────────────────────────────────────────────

def _make_evidence_bundle(trust_status: str = "success") -> EvidenceBundle:
    return EvidenceBundle(
        evidence={"pe": 20, "revenue": 1000},
        allowed_use=["fundamental_overview", "valuation_analysis"],
        blocked_fields=[],
        trust_status=trust_status,
        reason=None,
        source={"provider": "wind", "provider_tier": 1},
    )


def _make_manifest_entry(
    evidence_type: str = "quote",
    trust_status: str = "success",
) -> EvidenceManifestEntry:
    return EvidenceManifestEntry(
        manifest_id=f"manifest:{uuid.uuid4().hex[:8]}",
        evidence_bundle=_make_evidence_bundle(trust_status),
        evidence_type=evidence_type,
        as_of="2026-06-07",
    )


def _make_section_event(section_id: str, event_type: str, extra: dict | None = None) -> SectionEvent:
    payload = {"section_id": section_id}
    if extra:
        payload.update(extra)
    return SectionEvent(
        event_id=str(uuid.uuid4()),
        section_id=section_id,
        type=event_type,
        payload=payload,
    )


RESULTS: list[tuple[str, bool, str]] = []


def run(name: str, fn) -> None:  # type: ignore[type-arg]
    try:
        fn()
        RESULTS.append((name, True, ""))
    except Exception as e:
        RESULTS.append((name, False, str(e)))


# ─────────────────────────────────────────────
# Case 1: section 无 evidence manifest 不得进入 ANALYZE
# ─────────────────────────────────────────────

def case_empty_manifest_blocks_analyze() -> None:
    section_input = SectionInput(
        section_id="section:revenue_structure",
        symbol="600519.SH",
        query="revenue analysis",
        evidence_manifest=[],          # empty — must block ANALYZE
        allowed_use_filter=["fundamental_overview"],
        required_evidence_types=["financials"],
    )
    try:
        validate_section_can_enter_analyze(section_input)
        raise AssertionError("Should have raised ValueError for empty manifest")
    except ValueError as e:
        assert "cannot enter ANALYZE" in str(e), f"Unexpected error: {e}"


# ─────────────────────────────────────────────
# Case 2: depends_on 失败时 section 必须 SKIPPED
# ─────────────────────────────────────────────

def case_depends_on_failed_becomes_skipped() -> None:
    section_statuses = {
        "section:industry_overview": SectionStatus.FAILED,
    }
    result = validate_depends_on(
        section_id="section:company_positioning",
        dependencies=["section:industry_overview"],
        section_statuses=section_statuses,
    )
    assert result == SectionStatus.SKIPPED, (
        f"Expected SKIPPED, got {result}"
    )


def case_depends_on_skipped_becomes_skipped() -> None:
    section_statuses = {
        "section:industry_overview": SectionStatus.SKIPPED,
    }
    result = validate_depends_on(
        section_id="section:company_positioning",
        dependencies=["section:industry_overview"],
        section_statuses=section_statuses,
    )
    assert result == SectionStatus.SKIPPED, (
        f"Expected SKIPPED when dependency is SKIPPED, got {result}"
    )


def case_depends_on_done_becomes_ready() -> None:
    section_statuses = {
        "section:industry_overview": SectionStatus.DONE,
    }
    result = validate_depends_on(
        section_id="section:company_positioning",
        dependencies=["section:industry_overview"],
        section_statuses=section_statuses,
    )
    assert result == SectionStatus.READY, (
        f"Expected READY when dependency is DONE, got {result}"
    )


# ─────────────────────────────────────────────
# Case 3: section output 必须带 qc/status/citations 占位
# ─────────────────────────────────────────────

def case_output_must_have_qc_status_citations() -> None:
    manifest_entry = _make_manifest_entry()
    qc = SectionQC(
        passed=True,
        status="partial",
        evidence_count=1,
        evidence_all_real=True,
        has_fallback_evidence=False,
        has_mock_evidence=False,
        missing_required_types=[],
        blocked_evidence_count=0,
        limitations=["macro_snapshot unavailable"],
    )
    output = SectionOutput(
        section_id="section:industry_overview",
        status=SectionStatus.DONE,
        qc=qc,
        body="Industry overview content here.",
        citations=[
            SectionCitation(
                citation_id=f"cite:{uuid.uuid4().hex[:8]}",
                manifest_id=manifest_entry.manifest_id,
                field_used="pe",
                allowed_use_observed="fundamental_overview",
            )
        ],
        used_evidence_ids=[manifest_entry.manifest_id],
        limitations=["macro_snapshot unavailable"],
        created_at="2026-06-07T00:00:00Z",
    )
    validate_section_output(output)
    assert output.qc is not None
    assert output.status == SectionStatus.DONE
    assert isinstance(output.citations, list)


def case_output_citations_not_none_for_skipped() -> None:
    """SKIPPED section output must still have citations as empty list, not None."""
    qc = SectionQC(
        passed=False,
        status="failure",
        evidence_count=0,
        evidence_all_real=False,
        has_fallback_evidence=False,
        has_mock_evidence=False,
        missing_required_types=[],
        blocked_evidence_count=0,
        limitations=[],
    )
    output = SectionOutput(
        section_id="section:company_positioning",
        status=SectionStatus.SKIPPED,
        qc=qc,
        body="",
        citations=[],           # empty list, not None
        used_evidence_ids=[],
        limitations=[],
        created_at="2026-06-07T00:00:00Z",
    )
    validate_section_output(output)
    assert output.citations is not None
    assert output.citations == []


# ─────────────────────────────────────────────
# Case 4: raw gateway response 不得出现在 section input
# ─────────────────────────────────────────────

def case_raw_gateway_response_blocked_in_manifest() -> None:
    raw_gateway_response = {
        "ok": True,
        "symbol": "600519.SH",
        "data": {"pe": 20},
        "_qc": {"status": "success"},
    }
    try:
        # Attempt to create a manifest entry with raw dict instead of EvidenceBundle
        entry = EvidenceManifestEntry(
            manifest_id="manifest:bad",
            evidence_bundle=raw_gateway_response,  # type: ignore[arg-type]
            evidence_type="quote",
            as_of="2026-06-07",
        )
        # __post_init__ should raise
        raise AssertionError("Should have raised TypeError for raw gateway dict")
    except TypeError as e:
        assert "EvidenceBundle" in str(e), f"Unexpected error: {e}"


def case_valid_evidence_bundle_accepted_in_manifest() -> None:
    bundle = _make_evidence_bundle()
    entry = EvidenceManifestEntry(
        manifest_id="manifest:good",
        evidence_bundle=bundle,
        evidence_type="quote",
        as_of="2026-06-07",
    )
    validate_no_raw_gateway_in_manifest([entry])  # must not raise


# ─────────────────────────────────────────────
# Case 5: 所有事件必须能追踪 section_id
# ─────────────────────────────────────────────

def case_events_carry_section_id() -> None:
    section_id = "section:industry_overview"
    events = [
        _make_section_event(section_id, "section_state_entered", {"state": "ANALYZE"}),
        _make_section_event(section_id, "section_manifest_built", {"manifest_count": 1, "blocked_count": 0}),
        _make_section_event(section_id, "section_qc_passed", {"status": "partial", "evidence_count": 1}),
        _make_section_event(section_id, "section_output_written", {"citation_count": 1, "limitation_count": 0}),
    ]
    for event in events:
        validate_event_has_section_id(event)
        assert event.payload["section_id"] == section_id


def case_event_missing_section_id_rejected() -> None:
    try:
        bad_event = SectionEvent(
            event_id=str(uuid.uuid4()),
            section_id="section:foo",
            type="section_state_entered",
            payload={"state": "ANALYZE"},  # missing section_id
        )
        raise AssertionError("Should have raised ValueError for missing section_id")
    except ValueError as e:
        assert "section_id" in str(e), f"Unexpected error: {e}"


def case_section_skipped_event_has_failed_dependency() -> None:
    event = _make_section_event(
        "section:company_positioning",
        "section_skipped",
        {
            "reason": "dependency_skipped",
            "failed_dependency": "section:industry_overview",
        },
    )
    assert event.payload["failed_dependency"] == "section:industry_overview"
    assert event.payload["section_id"] == "section:company_positioning"


# ─────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────

def main() -> int:
    cases = [
        ("case_1a: empty manifest blocks ANALYZE", case_empty_manifest_blocks_analyze),
        ("case_2a: depends_on FAILED → SKIPPED", case_depends_on_failed_becomes_skipped),
        ("case_2b: depends_on SKIPPED → SKIPPED", case_depends_on_skipped_becomes_skipped),
        ("case_2c: depends_on DONE → READY", case_depends_on_done_becomes_ready),
        ("case_3a: output must have qc/status/citations", case_output_must_have_qc_status_citations),
        ("case_3b: SKIPPED output citations not None", case_output_citations_not_none_for_skipped),
        ("case_4a: raw gateway response blocked", case_raw_gateway_response_blocked_in_manifest),
        ("case_4b: valid EvidenceBundle accepted", case_valid_evidence_bundle_accepted_in_manifest),
        ("case_5a: events carry section_id", case_events_carry_section_id),
        ("case_5b: event missing section_id rejected", case_event_missing_section_id_rejected),
        ("case_5c: section_skipped event has failed_dependency", case_section_skipped_event_has_failed_dependency),
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
    print(f"Section Workflow Contract v0 smoke: {passed}/{passed + failed} PASS")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
