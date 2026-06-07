"""Report Assembly Contract v0 — Contract 语义 smoke test.

验收标准：
1. Report 只能消费 SectionOutput，不得消费 Evidence / Gateway / Provider raw data
2. DONE section 才能进入正文
3. FAILED / SKIPPED section 必须进入 assembly warnings，不得静默丢弃
4. Citation Index 必须从 SectionOutput.citations 聚合
5. ReportOutput 必须带 assembly_qc
6. raw gateway response 不得出现在 ReportInput / ReportOutput

不跑真实数据，不接 LLM，不改生产。
"""
from __future__ import annotations

import sys
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ─────────────────────────────────────────────
# Contract stubs (mirrors report_assembly_contract_v0.md)
# ─────────────────────────────────────────────

class SectionStatus(str, Enum):
    DONE = "DONE"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


REPORT_FORBIDDEN = {
    "raw_evidence", "evidence_bundle", "evidence_bundles",
    "gateway_response", "provider_payload", "_qc", "raw", "payload",
}

CRITICAL_SECTIONS = [
    "section:industry_overview",
    "section:company_positioning",
]


@dataclass(frozen=True)
class Citation:
    citation_id: str
    evidence_id: str
    field_used: str
    provider: str


@dataclass
class SectionQC:
    passed: bool
    status: str


@dataclass
class SectionOutput:
    section_id: str
    status: SectionStatus
    qc: SectionQC
    body: str
    citations: list[Citation]
    used_evidence_ids: list[str]
    limitations: list[str]
    created_at: str = "2026-06-07T00:00:00Z"


@dataclass(frozen=True)
class ReportSection:
    section_id: str
    title: str
    body: str
    citation_ids: list[str]
    qc_status: str
    limitations: list[str]


@dataclass(frozen=True)
class AssemblyWarning:
    section_id: str
    status: str
    reason: str
    impact: str


@dataclass(frozen=True)
class CitationIndexEntry:
    citation_id: str
    evidence_id: str
    section_id: str
    field_used: str
    provider: str


@dataclass
class AssemblyQC:
    passed: bool
    status: str
    total_sections: int
    done_sections: int
    failed_sections: int
    skipped_sections: int
    partial_sections: int
    citation_count: int
    has_critical_section_missing: bool
    warnings: list[str]


@dataclass
class ReportInput:
    report_id: str
    symbol: str
    query: str
    section_outputs: list[SectionOutput]
    section_order: list[str]
    created_at: str = "2026-06-07T00:00:00Z"


@dataclass
class ReportOutput:
    report_id: str
    symbol: str
    title: str
    body_sections: list[ReportSection]
    assembly_warnings: list[AssemblyWarning]
    citation_index: list[CitationIndexEntry]
    assembly_qc: AssemblyQC
    created_at: str = "2026-06-07T00:00:00Z"


# ─────────────────────────────────────────────
# Assembly logic (contract validation, not runtime)
# ─────────────────────────────────────────────

def validate_report_input_no_forbidden(report_input: ReportInput) -> list[str]:
    """ReportInput 不得包含 raw Evidence / Gateway / Provider 数据"""
    violations = []
    for attr in dir(report_input):
        if attr in REPORT_FORBIDDEN:
            violations.append(f"ReportInput has forbidden attribute: {attr}")
    # Check section_outputs don't carry raw data
    for so in report_input.section_outputs:
        for attr in dir(so):
            if attr in REPORT_FORBIDDEN:
                violations.append(f"SectionOutput '{so.section_id}' has forbidden attribute: {attr}")
    return violations


def assemble_report(report_input: ReportInput) -> ReportOutput:
    """Contract-compliant report assembly."""
    if not isinstance(report_input, ReportInput):
        raise TypeError("assemble_report requires ReportInput")

    body_sections: list[ReportSection] = []
    assembly_warnings: list[AssemblyWarning] = []
    citation_index: list[CitationIndexEntry] = []
    done_count = 0
    failed_count = 0
    skipped_count = 0
    partial_count = 0

    output_map = {so.section_id: so for so in report_input.section_outputs}

    for section_id in report_input.section_order:
        so = output_map.get(section_id)
        if so is None:
            assembly_warnings.append(AssemblyWarning(
                section_id=section_id,
                status="MISSING",
                reason="section_id in section_order but not in section_outputs",
                impact="Section content unavailable",
            ))
            continue

        if so.status == SectionStatus.DONE:
            done_count += 1
            if so.qc.status == "partial":
                partial_count += 1
                assembly_warnings.append(AssemblyWarning(
                    section_id=section_id,
                    status="PARTIAL",
                    reason="Section completed with partial evidence",
                    impact="Some data may be incomplete",
                ))

            body_sections.append(ReportSection(
                section_id=so.section_id,
                title=so.section_id.replace("section:", "").replace("_", " ").title(),
                body=so.body,
                citation_ids=[c.citation_id for c in so.citations],
                qc_status=so.qc.status,
                limitations=so.limitations,
            ))

            # Aggregate citations
            for cite in so.citations:
                citation_index.append(CitationIndexEntry(
                    citation_id=cite.citation_id,
                    evidence_id=cite.evidence_id,
                    section_id=so.section_id,
                    field_used=cite.field_used,
                    provider=cite.provider,
                ))

        elif so.status == SectionStatus.FAILED:
            failed_count += 1
            assembly_warnings.append(AssemblyWarning(
                section_id=section_id,
                status="FAILED",
                reason="Section execution failed",
                impact="Section content unavailable in report",
            ))

        elif so.status == SectionStatus.SKIPPED:
            skipped_count += 1
            assembly_warnings.append(AssemblyWarning(
                section_id=section_id,
                status="SKIPPED",
                reason="Section skipped due to dependency failure",
                impact="Section content unavailable in report",
            ))

    # Check critical sections
    done_section_ids = {s.section_id for s in body_sections}
    has_critical_missing = any(
        cs not in done_section_ids for cs in CRITICAL_SECTIONS
    )

    total = len(report_input.section_order)
    if has_critical_missing or done_count == 0:
        qc_status = "failure"
        qc_passed = False
    elif failed_count > 0 or skipped_count > 0 or partial_count > 0:
        qc_status = "partial"
        qc_passed = True
    else:
        qc_status = "success"
        qc_passed = True

    assembly_qc = AssemblyQC(
        passed=qc_passed,
        status=qc_status,
        total_sections=total,
        done_sections=done_count,
        failed_sections=failed_count,
        skipped_sections=skipped_count,
        partial_sections=partial_count,
        citation_count=len(citation_index),
        has_critical_section_missing=has_critical_missing,
        warnings=[w.reason for w in assembly_warnings],
    )

    return ReportOutput(
        report_id=report_input.report_id,
        symbol=report_input.symbol,
        title=f"Research Report: {report_input.symbol}",
        body_sections=body_sections,
        assembly_warnings=assembly_warnings,
        citation_index=citation_index,
        assembly_qc=assembly_qc,
    )


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _rid() -> str:
    return f"report:{uuid.uuid4().hex[:8]}"


def _cid() -> str:
    return f"cite:{uuid.uuid4().hex[:8]}"


def _eid() -> str:
    return f"evidence:{uuid.uuid4().hex[:8]}"


def _make_done_section(section_id: str, qc_status: str = "success") -> SectionOutput:
    eid = _eid()
    return SectionOutput(
        section_id=section_id,
        status=SectionStatus.DONE,
        qc=SectionQC(passed=True, status=qc_status),
        body=f"Content for {section_id}",
        citations=[Citation(
            citation_id=_cid(),
            evidence_id=eid,
            field_used="pe",
            provider="wind",
        )],
        used_evidence_ids=[eid],
        limitations=[] if qc_status == "success" else ["partial data"],
    )


def _make_failed_section(section_id: str) -> SectionOutput:
    return SectionOutput(
        section_id=section_id,
        status=SectionStatus.FAILED,
        qc=SectionQC(passed=False, status="failure"),
        body="",
        citations=[],
        used_evidence_ids=[],
        limitations=[],
    )


def _make_skipped_section(section_id: str) -> SectionOutput:
    return SectionOutput(
        section_id=section_id,
        status=SectionStatus.SKIPPED,
        qc=SectionQC(passed=False, status="failure"),
        body="",
        citations=[],
        used_evidence_ids=[],
        limitations=[],
    )


# ─────────────────────────────────────────────
# Test cases
# ─────────────────────────────────────────────

def case_1_report_only_consumes_section_output() -> None:
    """Report 只能消费 SectionOutput，不得消费 raw data"""
    report_input = ReportInput(
        report_id=_rid(),
        symbol="600519.SH",
        query="test",
        section_outputs=[_make_done_section("section:industry_overview")],
        section_order=["section:industry_overview"],
    )
    violations = validate_report_input_no_forbidden(report_input)
    assert violations == [], f"Unexpected violations: {violations}"

    # Reject raw dict
    try:
        assemble_report({"sections": []})  # type: ignore[arg-type]
        raise AssertionError("Should reject raw dict")
    except TypeError as e:
        assert "ReportInput" in str(e)


def case_2_only_done_enters_body() -> None:
    """DONE section 才能进入正文"""
    sections = [
        _make_done_section("section:industry_overview"),
        _make_done_section("section:company_positioning"),
        _make_failed_section("section:revenue_structure"),
        _make_skipped_section("section:scenario_analysis"),
    ]
    report_input = ReportInput(
        report_id=_rid(),
        symbol="600519.SH",
        query="test",
        section_outputs=sections,
        section_order=[so.section_id for so in sections],
    )
    report = assemble_report(report_input)

    body_ids = {s.section_id for s in report.body_sections}
    assert "section:industry_overview" in body_ids
    assert "section:company_positioning" in body_ids
    assert "section:revenue_structure" not in body_ids
    assert "section:scenario_analysis" not in body_ids


def case_3_failed_skipped_must_warn() -> None:
    """FAILED / SKIPPED section 必须进入 assembly warnings，不得静默丢弃"""
    sections = [
        _make_done_section("section:industry_overview"),
        _make_done_section("section:company_positioning"),
        _make_failed_section("section:revenue_structure"),
        _make_skipped_section("section:scenario_analysis"),
    ]
    report_input = ReportInput(
        report_id=_rid(),
        symbol="600519.SH",
        query="test",
        section_outputs=sections,
        section_order=[so.section_id for so in sections],
    )
    report = assemble_report(report_input)

    warning_ids = {w.section_id for w in report.assembly_warnings}
    assert "section:revenue_structure" in warning_ids, "FAILED section missing from warnings"
    assert "section:scenario_analysis" in warning_ids, "SKIPPED section missing from warnings"

    # Verify status is preserved
    warning_map = {w.section_id: w for w in report.assembly_warnings}
    assert warning_map["section:revenue_structure"].status == "FAILED"
    assert warning_map["section:scenario_analysis"].status == "SKIPPED"


def case_4_citation_index_from_section_citations() -> None:
    """Citation Index 必须从 SectionOutput.citations 聚合"""
    done1 = _make_done_section("section:industry_overview")
    done2 = _make_done_section("section:company_positioning")
    failed = _make_failed_section("section:revenue_structure")

    report_input = ReportInput(
        report_id=_rid(),
        symbol="600519.SH",
        query="test",
        section_outputs=[done1, done2, failed],
        section_order=[done1.section_id, done2.section_id, failed.section_id],
    )
    report = assemble_report(report_input)

    # Citation index should only contain citations from DONE sections
    assert len(report.citation_index) == 2  # one per DONE section
    index_section_ids = {entry.section_id for entry in report.citation_index}
    assert "section:industry_overview" in index_section_ids
    assert "section:company_positioning" in index_section_ids
    assert "section:revenue_structure" not in index_section_ids

    # Each entry should have valid fields
    for entry in report.citation_index:
        assert entry.citation_id.startswith("cite:")
        assert entry.evidence_id.startswith("evidence:")
        assert entry.field_used == "pe"
        assert entry.provider == "wind"


def case_5_report_must_have_assembly_qc() -> None:
    """ReportOutput 必须带 assembly_qc"""
    sections = [
        _make_done_section("section:industry_overview"),
        _make_done_section("section:company_positioning"),
    ]
    report_input = ReportInput(
        report_id=_rid(),
        symbol="600519.SH",
        query="test",
        section_outputs=sections,
        section_order=[so.section_id for so in sections],
    )
    report = assemble_report(report_input)

    assert report.assembly_qc is not None
    assert isinstance(report.assembly_qc, AssemblyQC)
    assert report.assembly_qc.passed is True
    assert report.assembly_qc.status == "success"
    assert report.assembly_qc.total_sections == 2
    assert report.assembly_qc.done_sections == 2
    assert report.assembly_qc.has_critical_section_missing is False


def case_5b_critical_section_missing_fails_qc() -> None:
    """关键 Section 缺失时 assembly_qc.passed = False"""
    sections = [
        _make_failed_section("section:industry_overview"),  # critical!
        _make_done_section("section:company_positioning"),
    ]
    report_input = ReportInput(
        report_id=_rid(),
        symbol="600519.SH",
        query="test",
        section_outputs=sections,
        section_order=[so.section_id for so in sections],
    )
    report = assemble_report(report_input)

    assert report.assembly_qc.passed is False
    assert report.assembly_qc.status == "failure"
    assert report.assembly_qc.has_critical_section_missing is True


def case_6_no_raw_gateway_in_report() -> None:
    """raw gateway response 不得出现在 ReportInput / ReportOutput"""
    # ReportInput rejects raw dict
    try:
        assemble_report({"gateway_response": {}, "sections": []})  # type: ignore[arg-type]
        raise AssertionError("Should reject raw dict with gateway_response")
    except TypeError:
        pass

    # Valid assembly doesn't leak raw data
    sections = [_make_done_section("section:industry_overview")]
    report_input = ReportInput(
        report_id=_rid(),
        symbol="600519.SH",
        query="test",
        section_outputs=sections,
        section_order=[so.section_id for so in sections],
    )
    report = assemble_report(report_input)

    # Verify no forbidden fields in output
    output_attrs = set(dir(report))
    leaked = output_attrs.intersection(REPORT_FORBIDDEN)
    assert leaked == set(), f"ReportOutput has forbidden attributes: {leaked}"


def case_6b_partial_section_triggers_warning() -> None:
    """DONE + partial QC 的 section 进入正文但同时生成 warning"""
    sections = [
        _make_done_section("section:industry_overview", qc_status="partial"),
        _make_done_section("section:company_positioning"),
    ]
    report_input = ReportInput(
        report_id=_rid(),
        symbol="600519.SH",
        query="test",
        section_outputs=sections,
        section_order=[so.section_id for so in sections],
    )
    report = assemble_report(report_input)

    # Should be in body
    body_ids = {s.section_id for s in report.body_sections}
    assert "section:industry_overview" in body_ids

    # Should also be in warnings
    warning_ids = {w.section_id for w in report.assembly_warnings}
    assert "section:industry_overview" in warning_ids

    # QC should be partial, but passed
    assert report.assembly_qc.status == "partial"
    assert report.assembly_qc.passed is True


# ─────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────

def main() -> int:
    cases = [
        ("case_1:  report only consumes SectionOutput", case_1_report_only_consumes_section_output),
        ("case_2:  only DONE enters body_sections", case_2_only_done_enters_body),
        ("case_3:  FAILED/SKIPPED must enter warnings", case_3_failed_skipped_must_warn),
        ("case_4:  citation index from section citations", case_4_citation_index_from_section_citations),
        ("case_5a: report must have assembly_qc", case_5_report_must_have_assembly_qc),
        ("case_5b: critical section missing fails QC", case_5b_critical_section_missing_fails_qc),
        ("case_6a: no raw gateway in report", case_6_no_raw_gateway_in_report),
        ("case_6b: partial section triggers warning", case_6b_partial_section_triggers_warning),
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
    print(f"Report Assembly Contract v0 smoke: {passed}/{passed + failed} PASS")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
