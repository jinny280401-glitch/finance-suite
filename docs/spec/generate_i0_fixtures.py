#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
I0 fixture generator — materialize docs/spec/fixtures/{valid,invalid}/*.json.

一次性生成器：用 validator（validate_i0_schema_contract.py）同一套 jcs/sha3 实现
实算回填全部 hash 字段，保证「文档示例 / fixture / 验证器」三者同一 hash 语义
（I0 §11）。生成后由 validate_i0_schema_contract.py 验证；fixture 本体为验收
产物，不随运行动态变化——本脚本只在 fixture 修订时重跑。

用法：
    python3 generate_i0_fixtures.py

Valid fixtures：全链规范示例（normative） + F17 两条 freshness 边界（audit 旧/data 新、
EOD 跨交易日周末边界）。
Invalid fixtures：每个 fixture 精确触发其 _meta.expected_violation(s) 声明的
invariant（重叠 invariant 以并集声明，见各 fixture _meta）。
"""

import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_i0_schema_contract as v  # noqa: E402

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
VALID_DIR = os.path.join(OUT_DIR, "valid")
INVALID_DIR = os.path.join(OUT_DIR, "invalid")

PAYLOAD = '{"code": "600519", "pe": 28.3, "pb": 7.5}'

D5_DIMS = ("provider_identity", "field_integrity", "provenance", "freshness", "classification")


# ---------------------------------------------------------------- fill helpers
# 每个 fill 函数重算对应 hash 字段；skip 集合允许保留已注入的错误值。

def fill_record(r, skip=()):
    raw = v.raw_hash_of(r["_raw_payload"])
    if "records/0/raw_hash" not in skip:
        r["raw_hash"] = raw
    if "records/0/content_hash" not in skip:
        r["content_hash"] = raw
    if "normalized_content" in r and "records/0/normalized_content_hash" not in skip:
        r["normalized_content_hash"] = v.h(r["normalized_content"])
    if "records/0/id" not in skip:
        r["id"] = v.h({k: r[k] for k in ("producer_id", "evidence_class", "collected_at", "raw_hash", "schema_version")})


def fill_assessment(a, skip=()):
    dims = {k: a[k] for k in D5_DIMS}
    dims["classification"] = v.norm_classification(dims["classification"])
    if "assessments/0/assessment_result_hash" not in skip:
        a["assessment_result_hash"] = v.h(dims)
    a["assessment_id"] = v.h({k: a[k] for k in ("record_id", "assessment_policy_version", "assessed_at", "assessor_id")})


def fill_decision(d, skip=()):
    d["decision_id"] = v.h({k: d[k] for k in ("record_id", "assessment_ref", "consumer", "purpose", "policy_family", "policy_version")})


def fill_receipt(r, skip=()):
    if "_assessment_result_hash_src" in r and "receipts/0/assessment_result_hash" not in skip:
        r["assessment_result_hash"] = r["_assessment_result_hash_src"]
    if "receipts/0/receipt_id" not in skip:
        r["receipt_id"] = v.h({k: r[k] for k in ("receipt_schema_version", "decision_id", "timestamp")})


def fill_manifest_bundle(m, b, skip=()):
    m["curated_content_hash"] = v.h(b["curated_content"])
    if "manifests/0/bundle_hash" not in skip:
        m["bundle_hash"] = v.h({k: m[k] for k in ("bundle_schema_version", "consumer", "purpose", "admitted_record_ids", "member_decision_ids", "curated_content_hash")})
    m["bundle_id"] = m["bundle_hash"]
    b["bundle_id"] = m["bundle_id"]


# ---------------------------------------------------------------- base components

def base_components():
    record = {
        "id": None, "content_hash": None, "raw_hash": None,
        "producer_id": "S11.wind_query",
        "evidence_class": "structured_financial",
        "collected_at": "2026-08-13T02:15:00Z",
        "raw_reference": {"reference": "wind://daily/600519", "object_hash": "ref-600519-v1"},
        "schema_version": "0.1",
        "content_type": "structured_financial",
        "source_type": "internal_provider",
        "retrieval_mode": "direct_api",
        "temporal_semantics": "realtime",
        "normalized_content": {"code": "600519", "pe": 28.3, "pb": 7.5},
        "normalized_content_hash": None,
        "normalization_version": "1.0",
        "_raw_payload": PAYLOAD,
    }
    assessment = {
        "assessment_id": None, "record_id": None,
        "assessed_at": "2026-08-13T02:15:01Z",
        "assessor_id": "gate.assessor.v1",
        "assessment_policy_version": "v0.1",
        "assessment_result_hash": None,
        "provider_identity": "VERIFIED",
        "field_integrity": "PASS",
        "provenance": "real",
        "freshness": "2026-08-13T02:14:59Z",
        "classification": "classified:[valuation]",
    }
    decision = {
        "decision_id": None, "record_id": None, "assessment_ref": None,
        "consumer": "stock-analyst.md",
        "purpose": "trading_signal",
        "policy_family": "P1",
        "policy_version": "v0.1",
        "verdict": "ALLOW",
        "allowed_use": ["fundamental_overview", "valuation_judgment"],
        "blocked_use": [],
        "max_claim_strength": "OBSERVED_FACT",
    }
    receipt = {
        "receipt_id": None, "receipt_schema_version": "1.0",
        "decision_id": None, "assessment_id": None, "assessment_result_hash": None,
        "producer_id": None, "evidence_record_id": None,
        "consumer": None, "purpose": None, "policy_family": None, "policy_version": None,
        "verdict": None, "allowed_use": None, "blocked_use": None, "max_claim_strength": None,
        "assessment_dimensions": None, "evidence_hash": None,
        "timestamp": "2026-08-13T02:15:02Z",
        "audit_trail": {"bypass_detected": False},
    }
    manifest = {
        "bundle_id": None, "bundle_schema_version": "1.0",
        "consumer": "stock-analyst.md", "purpose": "trading_signal",
        "admitted_record_ids": None, "member_decision_ids": None,
        "curated_content_hash": None,
        "generated_at": "2026-08-13T02:15:03Z",
        "bundle_hash": None,
    }
    bundle = {
        "bundle_id": None,
        "curated_content": None,
    }
    return record, assessment, decision, receipt, manifest, bundle


def link_and_fill(comp, skip=()):
    """link_and_fill 顺序：record → assessment → decision → receipt → manifest/bundle。

    前置引用（assessment.record_id 等）在 fill 之后写入；receipt 镜像字段从
    decision 复制（F13 改 decision.verdict 后 receipt.verdict 自动跟随）。
    """
    record, assessment, decision, receipt, manifest, bundle = comp
    fill_record(record, skip)
    assessment["record_id"] = record["id"]
    fill_assessment(assessment, skip)
    decision["record_id"] = record["id"]
    decision["assessment_ref"] = assessment["assessment_id"]
    fill_decision(decision, skip)
    receipt["decision_id"] = decision["decision_id"]
    receipt["assessment_id"] = assessment["assessment_id"]
    receipt["evidence_record_id"] = record["id"]
    receipt["evidence_hash"] = record["raw_hash"]
    receipt["producer_id"] = record["producer_id"]
    for f in ("consumer", "purpose", "policy_family", "policy_version", "verdict",
              "allowed_use", "blocked_use", "max_claim_strength"):
        receipt[f] = copy.deepcopy(decision[f])
    receipt["assessment_dimensions"] = {d: assessment[d] for d in D5_DIMS}
    receipt["_assessment_result_hash_src"] = assessment["assessment_result_hash"]
    fill_receipt(receipt, skip)
    manifest["admitted_record_ids"] = [record["id"]]
    manifest["member_decision_ids"] = [decision["decision_id"]]
    bundle["curated_content"] = [{
        "fragment_id": "frag-1",
        "decision_id": decision["decision_id"],
        "evidence_record_id": record["id"],
        "content": {"code": "600519", "pe": 28.3, "pb": 7.5},
    }]
    fill_manifest_bundle(manifest, bundle, skip)
    for r in (receipt,):
        r.pop("_assessment_result_hash_src", None)
    return {
        "records": [record], "assessments": [assessment], "decisions": [decision],
        "receipts": [receipt], "manifests": [manifest], "bundles": [bundle],
    }


def world(*lists, **kw):
    d = {k: v for k, v in zip(("records", "assessments", "decisions", "receipts", "manifests", "bundles"), lists)}
    d["_meta"] = kw.get("meta", {})
    return d


def dump(path, data, force_ascii=False):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=force_ascii, indent=2)
        f.write("\n")


# ---------------------------------------------------------------- search 类组件

def search_record():
    return {
        "id": None, "content_hash": None, "raw_hash": None,
        "producer_id": "S2.search.stock",
        "evidence_class": "external_search",
        "collected_at": "2026-08-13T02:15:00Z",
        "raw_reference": {"reference": "web://search/600519-news", "object_hash": "ref-s-1"},
        "schema_version": "0.1",
        "content_type": "search_result",
        "source_type": "external_search",
        "retrieval_mode": "search_fetch",
        "temporal_semantics": "realtime",
        "_raw_payload": '{"title": "600519 news"}',
    }


def search_assessment(classification):
    return {
        "assessment_id": None, "record_id": None,
        "assessed_at": "2026-08-13T02:15:01Z",
        "assessor_id": "gate.assessor.v1",
        "assessment_policy_version": "v0.1",
        "assessment_result_hash": None,
        "provider_identity": "NOT_APPLICABLE",
        "field_integrity": "NOT_APPLICABLE",
        "provenance": "external",
        "freshness": "2026-08-13T02:14:59Z",
        "classification": classification,
    }


def search_decision(purpose, family, verdict, strength):
    return {
        "decision_id": None, "record_id": None, "assessment_ref": None,
        "consumer": "stock-analyst.md",
        "purpose": purpose,
        "policy_family": family,
        "policy_version": "v0.1",
        "verdict": verdict,
        "allowed_use": ["market_context"],
        "blocked_use": [],
        "max_claim_strength": strength,
    }


def link_rd(record, assessment, skip=(), decision=None):
    fill_record(record, skip)
    assessment["record_id"] = record["id"]
    fill_assessment(assessment, skip)
    if decision is None:
        return {"records": [record], "assessments": [assessment]}
    decision["record_id"] = record["id"]
    decision["assessment_ref"] = assessment["assessment_id"]
    fill_decision(decision, skip)
    return {"records": [record], "assessments": [assessment], "decisions": [decision]}


# ---------------------------------------------------------------- fixtures

def main():
    os.makedirs(VALID_DIR, exist_ok=True)
    os.makedirs(INVALID_DIR, exist_ok=True)

    # ---------- valid ----------

    # normative_full_chain：全链规范示例（§11），零 violation
    comp = base_components()
    data = link_and_fill(comp)
    data["_meta"] = {"name": "normative_full_chain",
                     "context": {"consumer": "stock-analyst.md", "purpose": "trading_signal",
                                 "context_time": "2026-08-13T02:25:00Z"}}
    dump(os.path.join(VALID_DIR, "normative_full_chain.json"), data)

    # f17_audit_old_data_fresh：receipt.timestamp 旧（audit-only），data_as_of 新 → PASS
    comp = base_components()
    comp[3]["timestamp"] = "2026-01-01T00:00:00Z"
    data = link_and_fill(comp)
    data["_meta"] = {"name": "f17_audit_old_data_fresh",
                     "context": {"consumer": "stock-analyst.md", "purpose": "trading_signal",
                                 "context_time": "2026-08-13T02:25:00Z"}}
    dump(os.path.join(VALID_DIR, "f17_audit_old_data_fresh.json"), data)

    # f17_eod_weekend_boundary：EOD/trading 跨交易日边界 — 周五 EOD，周六上午 admission
    # duration = 17h = 61200s ≤ 86400s → PASS（证明 duration 计算，非 date 相等判定）
    comp = base_components()
    record, assessment, decision, receipt, manifest, bundle = comp
    record["temporal_semantics"] = "eod"
    record["collected_at"] = "2026-08-14T15:00:01Z"
    assessment["assessed_at"] = "2026-08-14T15:00:01Z"
    assessment["freshness"] = "2026-08-14T15:00:00Z"
    receipt["timestamp"] = "2026-08-15T08:00:00Z"
    manifest["generated_at"] = "2026-08-15T08:00:01Z"
    data = link_and_fill(comp)
    data["_meta"] = {"name": "f17_eod_weekend_boundary",
                     "context": {"consumer": "stock-analyst.md", "purpose": "trading_signal",
                                 "context_time": "2026-08-15T08:00:00Z"}}
    dump(os.path.join(VALID_DIR, "f17_eod_weekend_boundary.json"), data)

    # f27：D6 research×search_result×unclassified = INF (M25 positive discriminator)
    srecord = search_record()
    sassessment = search_assessment("unclassified")
    sdecision = search_decision("research", "P2", "ALLOW_WITH_MARKER", "INFORMATIONAL")
    sdecision["consumer"] = "Vera.ResearchSession"
    data = link_rd(srecord, sassessment, decision=sdecision)
    data["_meta"] = {"name": "f27_d6_research_unclassified_inf",
                     "description": "M25 positive: search_result + unclassified + research → ceiling=INF",
                     "context": {"consumer": "Vera.ResearchSession", "purpose": "research",
                                 "context_time": "2026-08-13T09:30:02Z"}}
    dump(os.path.join(VALID_DIR, "f27_d6_research_unclassified_inf.json"), data)

    # ---------- invalid ----------

    # f01：L1-I5 — record 携带 fact-purity 禁用字段
    comp = base_components()
    comp[0]["allowed_use"] = []
    data = link_and_fill(comp)
    data["_meta"] = {"name": "f01", "expected_violation": "L1-I5"}
    dump(os.path.join(INVALID_DIR, "f01_l1_i5_forbidden_field.json"), data)

    # f02：L1-I2 — id 非公式值
    comp = base_components()
    comp[0]["id"] = "<wrong>"
    data = link_and_fill(comp, skip=("records/0/id",))
    data["_meta"] = {"name": "f02", "expected_violation": "L1-I2"}
    dump(os.path.join(INVALID_DIR, "f02_l1_i2_id_formula.json"), data)

    # f03：L1-I3 — raw_hash ≠ content_hash ≠ SHA3(raw bytes)
    comp = base_components()
    comp[0]["raw_hash"] = "<wrong>"
    data = link_and_fill(comp, skip=("records/0/raw_hash",))
    data["_meta"] = {"name": "f03", "expected_violation": "L1-I3"}
    dump(os.path.join(INVALID_DIR, "f03_l1_i3_content_raw_hash.json"), data)

    # f04：L1-I1 — normalized triad 不齐（缺 normalization_version）
    comp = base_components()
    comp[0].pop("normalization_version")
    data = link_and_fill(comp)
    data["_meta"] = {"name": "f04", "expected_violation": "L1-I1"}
    dump(os.path.join(INVALID_DIR, "f04_l1_i1_normalized_triad.json"), data)

    # f05：L2-I4 — search_result 的 provider_identity 必须是 NOT_APPLICABLE（D5 ✗）
    record = search_record()
    assessment = search_assessment("classified:[news_event]")
    assessment["provider_identity"] = "VERIFIED"
    data = link_rd(record, assessment)
    data["_meta"] = {"name": "f05", "expected_violation": "L2-I4"}
    dump(os.path.join(INVALID_DIR, "f05_l2_i4_d5_na.json"), data)

    # f06：L2-I2 — assessment_result_hash 非公式值
    comp = base_components()
    comp[1]["assessment_result_hash"] = "<wrong>"
    data = link_and_fill(comp, skip=("assessments/0/assessment_result_hash",))
    data["_meta"] = {"name": "f06", "expected_violation": "L2-I2"}
    dump(os.path.join(INVALID_DIR, "f06_l2_i2_result_hash_formula.json"), data)

    # f07：L2-I6 — 同 (record, assessor, policy) 两条评估 hash 不同（应上报，非静默）
    comp = base_components()
    a2 = copy.deepcopy(comp[1])
    a2["provenance"] = "derived"
    record, assessment = comp[0], comp[1]
    fill_record(record)
    assessment["record_id"] = record["id"]
    a2["record_id"] = record["id"]
    fill_assessment(assessment)
    fill_assessment(a2)
    data = world([record], [assessment, a2])
    data["_meta"] = {"name": "f07", "expected_violation": "L2-I6"}
    dump(os.path.join(INVALID_DIR, "f07_l2_i6_conflicting_assessments.json"), data)

    # f08：L3-I1 + X-I1 — assessment_ref 悬空（receipt.assessment_id 同步悬空避免镜像误伤；
    # 无 manifest/bundle——member 覆盖是 F14 的靶位，此处不携带避免 L4-I11 级联）
    comp = base_components()
    data = link_and_fill(comp)
    decision, receipt = data["decisions"][0], data["receipts"][0]
    decision["assessment_ref"] = "f" * 64
    receipt["assessment_id"] = "f" * 64
    fill_decision(decision)  # decision_id 公式含 assessment_ref → 重算
    receipt["decision_id"] = decision["decision_id"]
    fill_receipt(receipt)
    del data["manifests"]; del data["bundles"]
    data["_meta"] = {"name": "f08", "expected_violations": ["L3-I1", "X-I1"]}
    dump(os.path.join(INVALID_DIR, "f08_l3_i1_dangling_assessment_ref.json"), data)

    # f09：L3-I5 — search_result(classified) ceiling=AC，DI 升级违反
    record = search_record()
    assessment = search_assessment("classified:[news_event]")
    decision = search_decision("trading_signal", "P2", "ALLOW", "DERIVED_INDICATOR")
    data = link_rd(record, assessment, decision=decision)
    data["_meta"] = {"name": "f09", "expected_violation": "L3-I5"}
    dump(os.path.join(INVALID_DIR, "f09_l3_i5_ceiling_search.json"), data)

    # f10：L3-I5 — structured_financial/fallback ceiling=INF，OF 升级违反
    comp = base_components()
    comp[1]["provenance"] = "fallback"
    data = link_and_fill(comp)
    data["_meta"] = {"name": "f10", "expected_violation": "L3-I5"}
    dump(os.path.join(INVALID_DIR, "f10_l3_i5_ceiling_fallback.json"), data)

    # f11：L3-I4 — unclassified + trading + financial_signal → 应为 BLOCK，给了 ALLOW
    record = search_record()
    assessment = search_assessment("unclassified")
    decision = search_decision("trading_signal", "P2", "ALLOW", "NO_CLAIM")
    data = link_rd(record, assessment, decision=decision)
    data["_meta"] = {"name": "f11", "expected_violation": "L3-I4", "financial_signal": True}
    dump(os.path.join(INVALID_DIR, "f11_l3_i4_unclassified_trading.json"), data)

    # f28：D6 search_result×unclassified×trading = NC 边界 (M25 判别) — strength=AC 升级违反
    # 注意：research 行 M25 = INF，但 trading 行冻结 = NC；不得因 research=INF 传播到 trading。
    record = search_record()
    assessment = search_assessment("unclassified")
    decision = search_decision("trading_signal", "P2", "ALLOW_WITH_MARKER", "ATTRIBUTED_CLAIM")
    data = link_rd(record, assessment, decision=decision)
    data["_meta"] = {"name": "f28", "expected_violation": "L3-I5"}
    dump(os.path.join(INVALID_DIR, "f28_d6_boundary_trading_unclassified.json"), data)

    # f12：L4-I2 — receipt 携带 bundle 字段（bundle 未成型）
    comp = base_components()
    data = link_and_fill(comp)
    data["receipts"][0]["bundle_hash"] = "a" * 64
    del data["manifests"]; del data["bundles"]
    data["_meta"] = {"name": "f12", "expected_violation": "L4-I2"}
    dump(os.path.join(INVALID_DIR, "f12_l4_i2_receipt_bundle_field.json"), data)

    # f13：L4-I16 — BLOCK verdict 出现在 bundle（不会到达 consumer）
    comp = base_components()
    comp[2]["verdict"] = "BLOCK"  # receipt 镜像字段经 link_and_fill 自动跟随
    data = link_and_fill(comp)
    data["_meta"] = {"name": "f13", "expected_violation": "L4-I16"}
    dump(os.path.join(INVALID_DIR, "f13_l4_i16_block_in_bundle.json"), data)

    # f14：L4-I11 — member_decision_ids 覆盖检查失败（fragment 同步移除，避免 L4-I15 误伤）
    comp = base_components()
    data = link_and_fill(comp)
    data["manifests"][0]["member_decision_ids"] = []
    data["bundles"][0]["curated_content"] = []
    fill_manifest_bundle(data["manifests"][0], data["bundles"][0])
    data["_meta"] = {"name": "f14", "expected_violation": "L4-I11"}
    dump(os.path.join(INVALID_DIR, "f14_l4_i11_member_coverage.json"), data)

    # f15：L4-I9 — manifest.consumer 与 member receipt 不一致
    comp = base_components()
    data = link_and_fill(comp)
    data["manifests"][0]["consumer"] = "other-consumer"
    fill_manifest_bundle(data["manifests"][0], data["bundles"][0])
    data["_meta"] = {"name": "f15", "expected_violation": "L4-I9"}
    dump(os.path.join(INVALID_DIR, "f15_l4_i9_consumer_mismatch.json"), data)

    # f16：L4-I3 + X-I1 — receipt.decision_id 悬空
    comp = base_components()
    data = link_and_fill(comp)
    data["receipts"][0]["decision_id"] = "f" * 64
    fill_receipt(data["receipts"][0])
    del data["manifests"]; del data["bundles"]
    data["_meta"] = {"name": "f16", "expected_violations": ["L4-I3", "X-I1"]}
    dump(os.path.join(INVALID_DIR, "f16_l4_i3_dangling_decision.json"), data)

    # f18：X-I4 — synthesis 单调性：OF > glb(constituents)=DI
    srecord = {
        "id": None, "content_hash": None, "raw_hash": None,
        "producer_id": "R5.assembly",
        "evidence_class": "synthesis",
        "collected_at": "2026-08-13T02:15:00Z",
        "raw_reference": {"reference": "internal://assembly/2026-08-13", "object_hash": "ref-a-1"},
        "schema_version": "0.1",
        "content_type": "synthesis_brief",
        "source_type": "derived",
        "retrieval_mode": "pipeline_assembly",
        "temporal_semantics": "rolling",
        "_raw_payload": '{"brief": "valuation"}',
    }
    sassessment = {
        "assessment_id": None, "record_id": None,
        "assessed_at": "2026-08-13T02:15:01Z",
        "assessor_id": "gate.assessor.v1",
        "assessment_policy_version": "v0.1",
        "assessment_result_hash": None,
        "provider_identity": "NOT_APPLICABLE",
        "field_integrity": "NOT_APPLICABLE",
        "provenance": "derived",
        "freshness": "2026-08-13T02:14:59Z",
        "classification": "classified:[valuation]",
    }
    sdecision = search_decision("research", "P6", "ALLOW", "OBSERVED_FACT")
    sdecision["allowed_use"] = ["background_context"]
    sdecision["_constituent_strengths"] = ["DERIVED_INDICATOR", "DERIVED_INDICATOR"]
    data = link_rd(srecord, sassessment, decision=sdecision)
    data["_meta"] = {"name": "f18", "expected_violation": "X-I4"}
    dump(os.path.join(INVALID_DIR, "f18_x_i4_synthesis_monotonicity.json"), data)

    # f19：L4-I8 — bypass_detected != false
    comp = base_components()
    data = link_and_fill(comp)
    data["receipts"][0]["audit_trail"]["bypass_detected"] = True
    data["_meta"] = {"name": "f19", "expected_violation": "L4-I8"}
    dump(os.path.join(INVALID_DIR, "f19_l4_i8_bypass_detected.json"), data)

    # f20：L1-I7 — collected_at 非 UTC ISO 8601
    comp = base_components()
    comp[0]["collected_at"] = "2026-08-13 02:15:00"
    data = link_and_fill(comp)
    data["_meta"] = {"name": "f20", "expected_violation": "L1-I7"}
    dump(os.path.join(INVALID_DIR, "f20_l1_i7_bad_iso.json"), data)

    # f21：L1-I2 — id 为字符串拼接 hash（违规 hash 输入形态；全链引用同步使用该 id）
    comp = base_components()
    record = comp[0]
    raw = v.raw_hash_of(PAYLOAD)
    concat_id = v.SHA3("".join([record["producer_id"], record["evidence_class"],
                                record["collected_at"], raw, record["schema_version"]]).encode())
    record["id"] = concat_id
    data = link_and_fill(comp, skip=("records/0/id",))
    data["_meta"] = {"name": "f21", "expected_violation": "L1-I2"}
    dump(os.path.join(INVALID_DIR, "f21_l1_i2_string_concat_hash.json"), data)

    # f22：L4-I10 — bundle_hash 非 canonical rep 公式值
    comp = base_components()
    data = link_and_fill(comp)
    data["manifests"][0]["bundle_hash"] = "<wrong>"
    fill_manifest_bundle(data["manifests"][0], data["bundles"][0],
                         skip=("manifests/0/bundle_hash",))
    data["_meta"] = {"name": "f22", "expected_violation": "L4-I10"}
    dump(os.path.join(INVALID_DIR, "f22_l4_i10_bundle_hash_formula.json"), data)

    # f23：L4-I15 — fragment 缺 decision_id provenance trace
    comp = base_components()
    data = link_and_fill(comp)
    data["bundles"][0]["curated_content"][0].pop("decision_id")
    fill_manifest_bundle(data["manifests"][0], data["bundles"][0])
    data["_meta"] = {"name": "f23", "expected_violation": "L4-I15"}
    dump(os.path.join(INVALID_DIR, "f23_l4_i15_fragment_trace.json"), data)

    # f24：L4-I6 + V8 — receipt.assessment_result_hash 与 L2 不一致（CR2 绑定链断）
    comp = base_components()
    data = link_and_fill(comp)
    data["receipts"][0]["assessment_result_hash"] = "<wrong>"
    fill_receipt(data["receipts"][0], skip=("receipts/0/assessment_result_hash",))
    data["_meta"] = {"name": "f24", "expected_violations": ["L4-I6", "V8"]}
    dump(os.path.join(INVALID_DIR, "f24_l4_i6_v8_assessment_binding.json"), data)

    # f25_realtime_15min：V5 — realtime/trading 900s：duration 2701s → FAIL
    comp = base_components()
    data = link_and_fill(comp)
    data["_meta"] = {"name": "f25_realtime_15min", "expected_violation": "V5",
                     "context": {"consumer": "stock-analyst.md", "purpose": "trading_signal",
                                 "context_time": "2026-08-13T03:00:00Z"}}
    dump(os.path.join(INVALID_DIR, "f25_realtime_15min.json"), data)

    # f25_eod_cross_trading_day：V5 — eod/trading 86400s 跨交易日：周五 EOD，周一开盘
    # duration = 66h = 237600s > 86400s → FAIL。
    # 判别性：date(data_as_of)=周五 == previous_trading_day(周一) → 错误的 date 规则会 PASS；
    # duration 规则必须 FAIL。这正是 ACR-3 解释规则锁定的场景。
    comp = base_components()
    record, assessment, decision, receipt, manifest, bundle = comp
    record["temporal_semantics"] = "eod"
    record["collected_at"] = "2026-08-14T15:00:01Z"
    assessment["assessed_at"] = "2026-08-14T15:00:01Z"
    assessment["freshness"] = "2026-08-14T15:00:00Z"
    receipt["timestamp"] = "2026-08-17T09:00:00Z"
    manifest["generated_at"] = "2026-08-17T09:00:01Z"
    data = link_and_fill(comp)
    data["_meta"] = {"name": "f25_eod_cross_trading_day", "expected_violation": "V5",
                     "context": {"consumer": "stock-analyst.md", "purpose": "trading_signal",
                                 "context_time": "2026-08-17T09:00:00Z"}}
    dump(os.path.join(INVALID_DIR, "f25_eod_cross_trading_day.json"), data)

    # f26：JCS REJECT — lone surrogate（CR5 受限 profile 拒绝；expect_reject，非 violation）
    record = base_components()[0]
    record["normalized_content"] = {"x": "\ud800"}
    record["normalized_content_hash"] = "<placeholder>"
    record["id"] = "<placeholder>"
    record["content_hash"] = "<placeholder>"
    record["raw_hash"] = "<placeholder>"
    data = {"records": [record],
            "_meta": {"name": "f26", "expect_reject": True}}
    dump(os.path.join(INVALID_DIR, "f26_jcs_lone_surrogate_reject.json"), data, force_ascii=True)

    print("fixtures written: %d valid, %d invalid"
          % (len(os.listdir(VALID_DIR)), len(os.listdir(INVALID_DIR))))


if __name__ == "__main__":
    main()
