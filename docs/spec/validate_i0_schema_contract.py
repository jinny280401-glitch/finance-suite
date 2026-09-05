#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
I0 Schema Contract validator — machine validation of I0_SCHEMA_CONTRACT_v0.1.md.

stdlib only（json / hashlib / re / sys / datetime），零第三方依赖，不 import 任何生产代码。
自实现受限 JCS profile（CR5），明确声明 ≠ 完整 RFC 8785。

用法：
    python3 validate_i0_schema_contract.py

读取 docs/spec/fixtures/{valid,invalid}/*.json，逐一断言：
  - valid fixture：零 violation；
  - invalid fixture：reported violations 恰等于 _meta.expected_violation(s) 声明的集合。
    声明集合机制：部分 frozen invariants 存在天然重叠（悬空引用同时违反 X-I1 与
    所在层 invariant；V8 与 L4-I4/L4-I6 同源），fixture 在 _meta 中声明实际触发的
    全集，验证器断言「恰为声明集合」——不允许少报（漏检）也不允许多报（误伤）。
  - _meta.expect_reject（F26）：断言验证过程中产生 JCS REJECT（CR5 受限 profile 拒绝）。

实现说明（相对 §13 PLAN 的具体化）：
  - hash 类 invariant（L1-I2/I3/I4、L2-I1/I2、L3-I8、L4-I5、L4-I10/I10b）以
    「fixture 存储值 vs 本验证器重算值」方式检查；fixture 由
    generate_i0_fixtures.py 用同一套 jcs/sha3 实现实算生成。
  - 设计级 invariant（L1-I9 / L2-I7 append-only）在单 world fixture 内不可机器判定，
    注册为 design-level，文档化跳过。
  - L3-I8 同时校验 §4.1 FROZEN 的 decision_id 公式（OPC #3）——冻结不变量表中无独立
    公式检查项，此为实现侧补齐，见交付说明（候选 OBS-8，待用户裁决）。
  - V5 使用 §1.8 冻结矩阵（ACR-3 CLOSED）：86400s 等值均为 duration threshold，
    非"上一交易日数据天然有效"业务规则；跨交易日边界由 F17eod / F25b 覆盖。
  - X-I1 负责引用闭合（L2.record_id→L1、L3.assessment_ref→L2、receipt 三引用、
    manifest.member_decision_ids→receipts）；fragment 引用由 L4-I15 专属检查，
    避免双重上报。
  - D6 research×search_result×unclassified 行为 TBD（§1.6 冻结行缺 research 值），
    验证器跳过该组合并注明。
  - P3 trading 未分类的"S9 个股对照 baseline"分支需要 baseline 数据，fixture 层
    不实现，fail-closed 为 BLOCK。

退出码：0 = 全部断言成立；非 0 = 存在 unexpected pass/fail。
"""

import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

SHA3 = lambda b: hashlib.sha3_256(b).hexdigest()

MAX_SAFE_INT = 2 ** 53


class JcsReject(ValueError):
    """受限 JCS profile 拒绝（CR5）：输入错误，不算 PASS。"""


def jcs(obj):
    """Restricted JCS profile（CR5）— key 字典序 / UTF-8 / 有限数字。

    明确声明：≠ 完整 RFC 8785。数字规则：±2^53 内整数精确序列化；
    非整数必须可经 Python repr 最短往返（否则 REJECT）；lone surrogate REJECT。
    """
    if obj is None:
        return "null"
    if isinstance(obj, bool):
        return "true" if obj else "false"
    if isinstance(obj, int):
        if not (-MAX_SAFE_INT <= obj <= MAX_SAFE_INT):
            raise JcsReject("integer out of ±2^53: %r" % obj)
        return str(obj)
    if isinstance(obj, float):
        if obj != obj or obj in (float("inf"), float("-inf")):
            raise JcsReject("non-finite float: %r" % obj)
        text = repr(obj)
        if float(text) != obj:
            raise JcsReject("float does not round-trip via repr: %r" % obj)
        return text
    if isinstance(obj, str):
        out = ['"']
        for ch in obj:
            cp = ord(ch)
            if 0xD800 <= cp <= 0xDFFF:
                raise JcsReject("lone surrogate in string")
            if ch == '"':
                out.append('\\"')
            elif ch == "\\":
                out.append("\\\\")
            elif cp < 0x20:
                out.append("\\u%04x" % cp)
            else:
                out.append(ch)
        out.append('"')
        return "".join(out)
    if isinstance(obj, list):
        return "[" + ",".join(jcs(x) for x in obj) + "]"
    if isinstance(obj, dict):
        for k in obj:
            if not isinstance(k, str):
                raise JcsReject("non-string object key: %r" % k)
        return "{" + ",".join(jcs(k) + ":" + jcs(obj[k]) for k in sorted(obj)) + "}"
    raise JcsReject("unsupported type: %r" % type(obj))


def h(obj):
    """SHA3-256 of restricted-JCS canonical serialization（M9：canonical object 输入）。"""
    return SHA3(jcs(obj).encode("utf-8"))


def raw_hash_of(payload_text):
    """content_hash / raw_hash = SHA3-256(raw_payload_bytes)（M9 唯一例外）。"""
    return SHA3(payload_text.encode("utf-8"))


ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")


def parse_utc(text):
    if not isinstance(text, str) or not ISO_RE.match(text):
        raise ValueError("not UTC ISO 8601: %r" % text)
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def is_utc_iso(text):
    try:
        parse_utc(text)
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------- frozen enums

CONTENT_TYPES = {
    "structured_financial", "search_result", "news_article", "macro_indicator",
    "market_pulse", "media_transcript", "institutional_research_full_text",
    "institutional_research_excerpt", "synthesis_brief", "prompt_template",
}
SOURCE_TYPES = {"internal_provider", "external_search", "institutional_kb",
                "media_platform", "derived"}
RETRIEVAL_MODES = {"direct_api", "search_fetch", "kb_lookup", "url_extract",
                   "media_extract", "pipeline_assembly"}
TEMPORAL_SEMANTICS = {"realtime", "eod", "historical", "static_reference",
                      "periodic_indicator", "rolling"}
PROVENANCES = {"real", "derived", "fallback", "external", "institutional", "transcript"}
EVIDENCE_CLASSES = {"structured_financial", "external_search", "market_indicator",
                    "media_transcript", "institutional_research", "synthesis"}
CLAIM_STRENGTHS = {"OBSERVED_FACT", "DERIVED_INDICATOR", "ATTRIBUTED_CLAIM",
                   "ANALYST_OPINION", "INFORMATIONAL", "NO_CLAIM"}
VERDICTS = {"ALLOW", "ALLOW_WITH_MARKER", "DOWNGRADE", "BLOCK"}
PURPOSES = {"research", "trading_signal", "portfolio_review", "market_monitor",
            "brief_assembly"}
POLICY_FAMILIES = {"P1", "P2", "P3", "P4", "P5", "P6"}
POLICY_VERSIONS = {"v0.1"}
PI_VALUES = {"VERIFIED", "UNVERIFIED", "NOT_APPLICABLE"}
FI_VALUES = {"PASS", "PARTIAL", "FAIL", "NOT_APPLICABLE"}
CLASSIFICATION_DOMAINS = {
    "capital_flow", "valuation", "management", "financials",
    "news_event", "sentiment", "macro", "industry", "regulatory",
    "company_profile", "other",
}
USE_CLASSES = {"fundamental_overview", "market_context", "valuation_judgment",
               "trading_signal", "price_reference", "background_context",
               "attribution_source"}

PRODUCER_RE = re.compile(r"^(S[1-9]|S1[01]|R[1235])\.[A-Za-z0-9_.-]+$")
PREFIX_FAMILY = {
    "S1": "P1", "S11": "P1", "R1": "P1",
    "S2": "P2", "S3": "P2", "S4": "P2", "S5": "P2", "S6": "P2", "S7": "P2",
    "S8": "P3", "S9": "P3",
    "S10": "P4",
    "R2": "P5", "R3": "P5",
    "R5": "P6",
}

COARSE = {
    "structured_financial": "structured_financial",
    "search_result": "external_search",
    "news_article": "external_search",
    "macro_indicator": "market_indicator",
    "market_pulse": "market_indicator",
    "media_transcript": "media_transcript",
    "institutional_research_full_text": "institutional_research",
    "institutional_research_excerpt": "institutional_research",
    "synthesis_brief": "synthesis",
}

# D5 适用矩阵（§1.5）：✓ = 必须判定；✗ = 必须 NOT_APPLICABLE
D5 = {
    "structured_financial": {"provider_identity": True, "field_integrity": True, "provenance": True, "freshness": True, "classification": True},
    "search_result": {"provider_identity": False, "field_integrity": False, "provenance": True, "freshness": True, "classification": True},
    "news_article": {"provider_identity": False, "field_integrity": False, "provenance": True, "freshness": True, "classification": True},
    "macro_indicator": {"provider_identity": True, "field_integrity": True, "provenance": True, "freshness": True, "classification": False},
    "market_pulse": {"provider_identity": True, "field_integrity": True, "provenance": True, "freshness": True, "classification": True},
    "media_transcript": {"provider_identity": False, "field_integrity": False, "provenance": True, "freshness": True, "classification": True},
    "institutional_research_full_text": {"provider_identity": True, "field_integrity": False, "provenance": True, "freshness": True, "classification": True},
    "institutional_research_excerpt": {"provider_identity": True, "field_integrity": False, "provenance": True, "freshness": True, "classification": True},
    "synthesis_brief": {"provider_identity": False, "field_integrity": False, "provenance": True, "freshness": True, "classification": True},
    "prompt_template": {"provider_identity": False, "field_integrity": False, "provenance": False, "freshness": False, "classification": False},
}

D5_DIMS = ("provider_identity", "field_integrity", "provenance", "freshness", "classification")


# D6 Claim Ceiling（§1.6，含 OBS-4 / CR6）
def d6_ceiling(content_type, provenance, purpose, classification):
    if content_type == "structured_financial":
        return {"real": "OBSERVED_FACT", "derived": "DERIVED_INDICATOR",
                "fallback": "INFORMATIONAL"}.get(provenance)
    if content_type == "search_result":
        if classification == "unclassified":
            # §1.6 行 206 + M25 (2026-08-13): trading=NC, research=INF
            return "NO_CLAIM" if purpose == "trading_signal" else "INFORMATIONAL"
        return "ATTRIBUTED_CLAIM"
    if content_type == "news_article":
        return "ATTRIBUTED_CLAIM"
    if content_type in ("macro_indicator", "market_pulse"):
        return "OBSERVED_FACT"
    if content_type == "media_transcript":
        return "ATTRIBUTED_CLAIM" if purpose == "research" else "INFORMATIONAL"
    if content_type == "institutional_research_full_text":
        return "ANALYST_OPINION" if purpose == "research" else "INFORMATIONAL"
    if content_type == "institutional_research_excerpt":
        return "INFORMATIONAL" if purpose == "research" else "NO_CLAIM"
    return None  # synthesis_brief → X-I4 glb 检查；prompt_template → N/A（无 L1/L3）


# Claim strength lattice（M16）：≤ 关系
LOWER = {
    "OBSERVED_FACT": {"DERIVED_INDICATOR", "ATTRIBUTED_CLAIM", "ANALYST_OPINION", "INFORMATIONAL", "NO_CLAIM"},
    "DERIVED_INDICATOR": {"ATTRIBUTED_CLAIM", "ANALYST_OPINION", "INFORMATIONAL", "NO_CLAIM"},
    "ATTRIBUTED_CLAIM": {"INFORMATIONAL", "NO_CLAIM"},
    "ANALYST_OPINION": {"INFORMATIONAL", "NO_CLAIM"},
    "INFORMATIONAL": {"NO_CLAIM"},
    "NO_CLAIM": set(),
}


def le(a, b):
    return a == b or a in LOWER[b]


def pair_glb(a, b):
    if le(a, b):
        return a
    if le(b, a):
        return b
    if {a, b} == {"ATTRIBUTED_CLAIM", "ANALYST_OPINION"}:
        return "INFORMATIONAL"
    return "NO_CLAIM"


def glb(strengths):
    acc = None
    for s in strengths:
        acc = s if acc is None else pair_glb(acc, s)
    return acc


# §1.8 冻结 6×5 max_age 矩阵（ACR-3 CLOSED 2026-08-13；单位：秒；None = ∞）
MATRIX = {
    "trading_signal": {"realtime": 900, "eod": 86400, "rolling": 86400,
                       "periodic_indicator": 5184000, "historical": 604800,
                       "static_reference": 2592000},
    "market_monitor": {"realtime": 1800, "eod": 172800, "rolling": 604800,
                       "periodic_indicator": 5184000, "historical": 2592000,
                       "static_reference": 7776000},
    "portfolio_review": {"realtime": 86400, "eod": 604800, "rolling": 2592000,
                         "periodic_indicator": 10368000, "historical": 10368000,
                         "static_reference": 15552000},
    "research": {"realtime": 2592000, "eod": 2592000, "rolling": 7776000,
                 "periodic_indicator": 31536000, "historical": 31536000,
                 "static_reference": 31536000},
    "brief_assembly": {"realtime": None, "eod": None, "rolling": None,
                       "periodic_indicator": None, "historical": None,
                       "static_reference": None},
}


def unclassified_expected_verdict(family, purpose, financial_signal):
    """§1.7 未分类默认策略表（P3 trading 的 baseline 对照分支 fixture 层不实现，fail-closed）。"""
    research = {"P2": "ALLOW_WITH_MARKER", "P3": "ALLOW_WITH_MARKER",
                "P4": "ALLOW_WITH_MARKER", "P5": "ALLOW_WITH_MARKER", "P6": "BLOCK"}
    trading = {
        "P2": "BLOCK" if financial_signal else "ALLOW_WITH_MARKER",
        "P3": "BLOCK",
        "P4": "BLOCK" if financial_signal else "ALLOW_WITH_MARKER",
        "P5": "BLOCK",
        "P6": "BLOCK",
    }
    if purpose == "research":
        return research.get(family)
    if purpose == "trading_signal":
        return trading.get(family)
    return None


def norm_classification(val):
    """CR5：hash 输入中的 classification domain list 先按字典序排序。"""
    if isinstance(val, str) and val.startswith("classified:[") and val.endswith("]"):
        inner = val[len("classified:["):-1]
        return "classified:[" + ",".join(sorted(inner.split(","))) + "]"
    return val


def classification_valid(val):
    if val in ("unclassified", "not_applicable"):
        return True
    if isinstance(val, str) and val.startswith("classified:[") and val.endswith("]"):
        inner = val[len("classified:["):-1]
        doms = inner.split(",")
        return (all(d in CLASSIFICATION_DOMAINS for d in doms)
                and doms == sorted(doms))
    return False


L1_REQUIRED = ["id", "content_hash", "raw_hash", "producer_id", "evidence_class",
               "collected_at", "raw_reference", "schema_version", "content_type",
               "source_type", "retrieval_mode", "temporal_semantics"]
L1_FORBIDDEN = {"allowed_use", "blocked_use", "max_claim_strength", "trust_status", "verdict"}
L2_REQUIRED = ["assessment_id", "record_id", "assessed_at", "assessor_id",
               "assessment_policy_version", "assessment_result_hash",
               "provider_identity", "field_integrity", "provenance", "freshness",
               "classification"]
L3_REQUIRED = ["decision_id", "record_id", "assessment_ref", "consumer", "purpose",
               "policy_family", "policy_version", "verdict", "allowed_use",
               "blocked_use", "max_claim_strength"]
RECEIPT_REQUIRED = ["receipt_id", "receipt_schema_version", "decision_id",
                    "assessment_id", "assessment_result_hash", "producer_id",
                    "evidence_record_id", "consumer", "purpose", "policy_family",
                    "policy_version", "verdict", "allowed_use", "blocked_use",
                    "max_claim_strength", "assessment_dimensions", "evidence_hash",
                    "timestamp", "audit_trail"]
MANIFEST_REQUIRED = ["bundle_id", "bundle_schema_version", "consumer", "purpose",
                     "admitted_record_ids", "member_decision_ids",
                     "curated_content_hash", "generated_at", "bundle_hash"]
BUNDLE_VERDICTS = {"ALLOW", "ALLOW_WITH_MARKER", "DOWNGRADE"}


# ---------------------------------------------------------------- world model

class World:
    def __init__(self, data):
        self.meta = data.get("_meta", {})
        self.records = data.get("records", [])
        self.assessments = data.get("assessments", [])
        self.decisions = data.get("decisions", [])
        self.receipts = data.get("receipts", [])
        self.manifests = data.get("manifests", [])
        self.bundles = data.get("bundles", [])
        self.record_by_id = {}
        for r in self.records:
            self.record_by_id[r.get("id")] = r
        self.assessment_by_id = {}
        for a in self.assessments:
            self.assessment_by_id[a.get("assessment_id")] = a
        self.decision_by_id = {}
        for d in self.decisions:
            self.decision_by_id[d.get("decision_id")] = d
        self.receipt_by_decision = {}
        for r in self.receipts:
            self.receipt_by_decision[r.get("decision_id")] = r
        self.bundle_by_id = {}
        for b in self.bundles:
            self.bundle_by_id[b.get("bundle_id")] = b


# ---------------------------------------------------------------- checks（L1）

def ck_l1_i1(w):
    for i, r in enumerate(w.records):
        missing = [f for f in L1_REQUIRED if f not in r]
        if missing:
            yield "L1-I1", "records[%d]: missing %s" % (i, missing)
        has_n = "normalized_content" in r
        has_h = "normalized_content_hash" in r
        has_v = "normalization_version" in r
        if not (has_n == has_h == has_v):
            yield "L1-I1", "records[%d]: normalized triad mismatch (content=%s hash=%s version=%s)" % (i, has_n, has_h, has_v)


def ck_l1_i2(w):
    for i, r in enumerate(w.records):
        if r.get("id") != h({k: r.get(k) for k in ("producer_id", "evidence_class", "collected_at", "raw_hash", "schema_version")}):
            yield "L1-I2", "records[%d]: id != SHA3-256(JCS{producer_id,evidence_class,collected_at,raw_hash,schema_version})" % i


def ck_l1_i3(w):
    for i, r in enumerate(w.records):
        payload = r.get("_raw_payload")
        if not isinstance(payload, str):
            yield "L1-I3", "records[%d]: missing _raw_payload fixture meta (cannot verify content_hash)" % i
            continue
        expected = raw_hash_of(payload)
        if r.get("content_hash") != expected or r.get("raw_hash") != expected or r.get("content_hash") != r.get("raw_hash"):
            yield "L1-I3", "records[%d]: content_hash/raw_hash != SHA3-256(raw_payload_bytes)" % i


def ck_l1_i4(w):
    for i, r in enumerate(w.records):
        if "normalized_content_hash" in r:
            if r.get("normalized_content_hash") != h(r.get("normalized_content")):
                yield "L1-I4", "records[%d]: normalized_content_hash != SHA3-256(JCS(normalized_content))" % i


def ck_l1_i5(w):
    for i, r in enumerate(w.records):
        bad = [f for f in L1_FORBIDDEN if f in r]
        if bad:
            yield "L1-I5", "records[%d]: forbidden fields %s (fact purity)" % (i, bad)


def ck_l1_i6(w):
    for i, r in enumerate(w.records):
        if r.get("content_type") not in CONTENT_TYPES:
            yield "L1-I6", "records[%d]: content_type %r not in enum" % (i, r.get("content_type"))
        if r.get("source_type") not in SOURCE_TYPES:
            yield "L1-I6", "records[%d]: source_type %r not in enum" % (i, r.get("source_type"))
        if r.get("retrieval_mode") not in RETRIEVAL_MODES:
            yield "L1-I6", "records[%d]: retrieval_mode %r not in enum" % (i, r.get("retrieval_mode"))
        if r.get("temporal_semantics") not in TEMPORAL_SEMANTICS:
            yield "L1-I6", "records[%d]: temporal_semantics %r not in enum" % (i, r.get("temporal_semantics"))
        if r.get("evidence_class") not in EVIDENCE_CLASSES:
            yield "L1-I6", "records[%d]: evidence_class %r not in enum" % (i, r.get("evidence_class"))
        if not (isinstance(r.get("producer_id"), str) and PRODUCER_RE.match(r.get("producer_id"))):
            yield "L1-I6", "records[%d]: producer_id %r not in 15-entry set (S1-S11,R1,R2,R3,R5)" % (i, r.get("producer_id"))
        elif COARSE.get(r.get("content_type")) != r.get("evidence_class"):
            yield "L1-I6", "records[%d]: evidence_class %r != coarse(content_type=%r)" % (i, r.get("evidence_class"), r.get("content_type"))


def ck_l1_i7(w):
    for i, r in enumerate(w.records):
        if not is_utc_iso(r.get("collected_at")):
            yield "L1-I7", "records[%d]: collected_at %r not UTC ISO 8601" % (i, r.get("collected_at"))


def ck_l1_i8(w):
    for i, r in enumerate(w.records):
        ref = r.get("raw_reference")
        if not isinstance(ref, dict) or "reference" not in ref or "object_hash" not in ref:
            yield "L1-I8", "records[%d]: raw_reference must carry reference + object_hash (immutable ref)" % i


# ---------------------------------------------------------------- checks（L2）

def ck_l2_i1(w):
    for i, a in enumerate(w.assessments):
        if a.get("assessment_id") != h({k: a.get(k) for k in ("record_id", "assessment_policy_version", "assessed_at", "assessor_id")}):
            yield "L2-I1", "assessments[%d]: assessment_id != SHA3-256(JCS{record_id,assessment_policy_version,assessed_at,assessor_id})" % i


def ck_l2_i2(w):
    for i, a in enumerate(w.assessments):
        dims = {k: a.get(k) for k in D5_DIMS}
        dims["classification"] = norm_classification(dims["classification"])
        if a.get("assessment_result_hash") != h(dims):
            yield "L2-I2", "assessments[%d]: assessment_result_hash != SHA3-256(JCS(5 dims, classification sorted))" % i


def ck_l2_i3(w):
    for i, a in enumerate(w.assessments):
        if a.get("record_id") not in w.record_by_id:
            yield "L2-I3", "assessments[%d]: record_id %r not in L1 set" % (i, a.get("record_id"))


def ck_l2_i4(w):
    for i, a in enumerate(w.assessments):
        rec = w.record_by_id.get(a.get("record_id"))
        if not rec:
            continue  # L2-I3 / X-I1 负责
        ct = rec.get("content_type")
        d5 = D5.get(ct)
        if d5 is None:
            yield "L2-I4", "assessments[%d]: no D5 row for content_type %r" % (i, ct)
            continue
        for dim in D5_DIMS:
            val = a.get(dim)
            if d5[dim] and val == "NOT_APPLICABLE":
                yield "L2-I4", "assessments[%d]: dim %s must be assessed (D5 ✓), got NOT_APPLICABLE" % (i, dim)
            if not d5[dim] and val != "NOT_APPLICABLE":
                yield "L2-I4", "assessments[%d]: dim %s must be NOT_APPLICABLE (D5 ✗), got %r" % (i, dim, val)


def ck_l2_i5(w):
    for i, a in enumerate(w.assessments):
        if a.get("provider_identity") not in PI_VALUES:
            yield "L2-I5", "assessments[%d]: provider_identity %r invalid" % (i, a.get("provider_identity"))
        if a.get("field_integrity") not in FI_VALUES:
            yield "L2-I5", "assessments[%d]: field_integrity %r invalid" % (i, a.get("field_integrity"))
        if a.get("provenance") not in PROVENANCES:
            yield "L2-I5", "assessments[%d]: provenance %r invalid" % (i, a.get("provenance"))
        fresh = a.get("freshness")
        if fresh not in ("STALE", "UNKNOWN") and not is_utc_iso(fresh):
            yield "L2-I5", "assessments[%d]: freshness %r invalid (ISO data_as_of / STALE / UNKNOWN)" % (i, fresh)
        if not classification_valid(a.get("classification")):
            yield "L2-I5", "assessments[%d]: classification %r invalid (CR5 sorted closed list)" % (i, a.get("classification"))


def ck_l2_i6(w):
    groups = {}
    for i, a in enumerate(w.assessments):
        key = (a.get("record_id"), a.get("assessor_id"), a.get("assessment_policy_version"))
        groups.setdefault(key, []).append((i, a.get("assessment_result_hash")))
    for key, items in groups.items():
        if len({h_ for _, h_ in items}) > 1:
            yield "L2-I6", "conflict: %d assessments share (record_id=%r, assessor_id=%r, policy=%r) with different result hashes (must be reported, not silent)" % (len(items), key[0], key[1], key[2])


# ---------------------------------------------------------------- checks（L3）

def ck_l3_i1(w):
    for i, d in enumerate(w.decisions):
        if d.get("assessment_ref") not in w.assessment_by_id:
            yield "L3-I1", "decisions[%d]: assessment_ref %r dangling (must be literal assessment_id, no 'latest')" % (i, d.get("assessment_ref"))


def ck_l3_i2(w):
    for i, d in enumerate(w.decisions):
        a = w.assessment_by_id.get(d.get("assessment_ref"))
        if a and d.get("record_id") != a.get("record_id"):
            yield "L3-I2", "decisions[%d]: record_id != assessment.record_id" % i


def ck_l3_i3(w):
    groups = {}
    for i, d in enumerate(w.decisions):
        key = (d.get("record_id"), d.get("consumer"), d.get("purpose"), d.get("policy_version"))
        groups.setdefault(key, []).append(i)
    for key, items in groups.items():
        if len(items) > 1:
            yield "L3-I3", "duplicate decision for (record_id=%r, consumer=%r, purpose=%r, policy_version=%r): %d decisions" % (key + (len(items),))


def ck_l3_i4(w):
    financial_signal = bool(w.meta.get("financial_signal", False))
    for i, d in enumerate(w.decisions):
        if d.get("verdict") not in VERDICTS:
            yield "L3-I4", "decisions[%d]: verdict %r not in enum" % (i, d.get("verdict"))
        for field in ("allowed_use", "blocked_use"):
            lst = d.get(field)
            if not isinstance(lst, list) or not all(u in USE_CLASSES for u in lst):
                yield "L3-I4", "decisions[%d]: %s %r outside 7-value closed list (§1.3.2)" % (i, field, lst)
        a = w.assessment_by_id.get(d.get("assessment_ref"))
        if not a or a.get("classification") != "unclassified":
            continue
        expected = unclassified_expected_verdict(d.get("policy_family"), d.get("purpose"), financial_signal)
        if expected is not None and d.get("verdict") != expected:
            yield "L3-I4", "decisions[%d]: unclassified %s/%s verdict %r != §1.7 default %r (financial_signal=%s)" % (i, d.get("policy_family"), d.get("purpose"), d.get("verdict"), expected, financial_signal)


def ck_l3_i5(w):
    for i, d in enumerate(w.decisions):
        a = w.assessment_by_id.get(d.get("assessment_ref"))
        rec = w.record_by_id.get(d.get("record_id"))
        if not a or not rec:
            continue  # X-I1 负责悬空
        ct = rec.get("content_type")
        if ct == "synthesis_brief":
            continue  # synthesis ceiling 由 X-I4 glb 检查负责
        ceiling = d6_ceiling(ct, a.get("provenance"), d.get("purpose"), a.get("classification"))
        if ceiling is None:
            continue  # research×search_result×unclassified TBD（§1.6）
        strength = d.get("max_claim_strength")
        if strength not in CLAIM_STRENGTHS:
            yield "L3-I5", "decisions[%d]: max_claim_strength %r not in lattice enum" % (i, strength)
        elif not le(strength, ceiling):
            yield "L3-I5", "decisions[%d]: %s > D6 ceiling %s (content_type=%s, provenance=%s, purpose=%s) — upgrade violates" % (i, strength, ceiling, ct, a.get("provenance"), d.get("purpose"))


def ck_l3_i6(w):
    for i, d in enumerate(w.decisions):
        rec = w.record_by_id.get(d.get("record_id"))
        if not rec:
            continue  # X-I1 负责
        m = PRODUCER_RE.match(rec.get("producer_id") or "")
        if not m:
            continue  # L1-I6 负责
        family = PREFIX_FAMILY[m.group(1)]
        if d.get("policy_family") != family:
            yield "L3-I6", "decisions[%d]: policy_family %r != entry family %r (producer %r)" % (i, d.get("policy_family"), family, rec.get("producer_id"))


def ck_l3_i7(w):
    for i, d in enumerate(w.decisions):
        if d.get("policy_version") not in POLICY_VERSIONS:
            yield "L3-I7", "decisions[%d]: policy_version %r not in registry {v0.1}" % (i, d.get("policy_version"))


def ck_l3_i8(w):
    # 唯一性 + §4.1 FROZEN 公式（OPC #3）。冻结不变量表仅写"全集合内唯一"，
    # 公式检查为实现侧补齐（交付说明：候选 OBS-8，待用户裁决）。
    seen = set()
    for i, d in enumerate(w.decisions):
        did = d.get("decision_id")
        if did in seen:
            yield "L3-I8", "decisions[%d]: duplicate decision_id %r" % (i, did)
        seen.add(did)
        if did != h({k: d.get(k) for k in ("record_id", "assessment_ref", "consumer", "purpose", "policy_family", "policy_version")}):
            yield "L3-I8", "decisions[%d]: decision_id != SHA3-256(JCS{record_id,assessment_ref,consumer,purpose,policy_family,policy_version}) (§4.1 FROZEN)" % i


# ---------------------------------------------------------------- checks（L4 receipt）

def ck_l4_i1(w):
    for i, r in enumerate(w.receipts):
        missing = [f for f in RECEIPT_REQUIRED if f not in r]
        if missing:
            yield "L4-I1", "receipts[%d]: missing %s" % (i, missing)


def ck_l4_i2(w):
    for i, r in enumerate(w.receipts):
        bad = [f for f in ("bundle_hash", "bundle_id") if f in r]
        if bad:
            yield "L4-I2", "receipts[%d]: forbidden fields %s (receipt is per-decision, bundle 未成型)" % (i, bad)


def ck_l4_i3(w):
    for i, r in enumerate(w.receipts):
        if r.get("decision_id") not in w.decision_by_id:
            yield "L4-I3", "receipts[%d]: decision_id %r not in L3 set" % (i, r.get("decision_id"))
        if r.get("evidence_record_id") not in w.record_by_id:
            yield "L4-I3", "receipts[%d]: evidence_record_id %r not in L1 set" % (i, r.get("evidence_record_id"))
        rec = w.record_by_id.get(r.get("evidence_record_id"))
        if rec and r.get("evidence_hash") != rec.get("raw_hash"):
            yield "L4-I3", "receipts[%d]: evidence_hash != record.raw_hash" % i


def ck_l4_i4(w):
    for i, r in enumerate(w.receipts):
        d = w.decision_by_id.get(r.get("decision_id"))
        if not d:
            continue  # L4-I3 / X-I1 负责
        for f in ("consumer", "purpose", "policy_family", "policy_version", "verdict", "allowed_use", "blocked_use", "max_claim_strength"):
            if r.get(f) != d.get(f):
                yield "L4-I4", "receipts[%d]: %s %r != decision %r (mirror)" % (i, f, r.get(f), d.get(f))
        rec = w.record_by_id.get(r.get("evidence_record_id"))
        if rec and r.get("producer_id") != rec.get("producer_id"):
            yield "L4-I4", "receipts[%d]: producer_id != record.producer_id" % i
        if r.get("assessment_id") != d.get("assessment_ref"):
            yield "L4-I4", "receipts[%d]: assessment_id != decision.assessment_ref (CR2)" % i


def ck_l4_i5(w):
    for i, r in enumerate(w.receipts):
        if r.get("receipt_id") != h({k: r.get(k) for k in ("receipt_schema_version", "decision_id", "timestamp")}):
            yield "L4-I5", "receipts[%d]: receipt_id != SHA3-256(JCS{receipt_schema_version,decision_id,timestamp}) (CR1)" % i


def ck_l4_i6(w):
    for i, r in enumerate(w.receipts):
        a = w.assessment_by_id.get(r.get("assessment_id"))
        if not a:
            continue  # X-I1 负责
        if r.get("assessment_result_hash") != a.get("assessment_result_hash"):
            yield "L4-I6", "receipts[%d]: assessment_result_hash != L2.assessment_result_hash (CR2)" % i
        dims = r.get("assessment_dimensions")
        if not isinstance(dims, dict):
            yield "L4-I6", "receipts[%d]: assessment_dimensions missing" % i
            continue
        for dim in D5_DIMS:
            if dims.get(dim) != a.get(dim):
                yield "L4-I6", "receipts[%d]: assessment_dimensions.%s %r != L2 %r (snapshot)" % (i, dim, dims.get(dim), a.get(dim))


def ck_l4_i7(w):
    for i, r in enumerate(w.receipts):
        if not is_utc_iso(r.get("timestamp")):
            yield "L4-I7", "receipts[%d]: timestamp %r not UTC ISO 8601" % (i, r.get("timestamp"))


def ck_l4_i8(w):
    for i, r in enumerate(w.receipts):
        trail = r.get("audit_trail")
        if not isinstance(trail, dict) or "bypass_detected" not in trail:
            yield "L4-I8", "receipts[%d]: audit_trail missing bypass_detected" % i
        elif trail.get("bypass_detected") is not False:
            yield "L4-I8", "receipts[%d]: bypass_detected == %r (must be false)" % (i, trail.get("bypass_detected"))


# ---------------------------------------------------------------- checks（L4 bundle/manifest）

def ck_l4_i9(w):
    for i, m in enumerate(w.manifests):
        missing = [f for f in MANIFEST_REQUIRED if f not in m]
        if missing:
            yield "L4-I9", "manifests[%d]: missing %s" % (i, missing)
        for r in w.receipts:
            if r.get("decision_id") not in m.get("member_decision_ids", []):
                continue
            if r.get("consumer") != m.get("consumer") or r.get("purpose") != m.get("purpose"):
                yield "L4-I9", "manifests[%d]: consumer/purpose mismatch with member receipt (must match)" % i


def ck_l4_i10(w):
    for i, m in enumerate(w.manifests):
        if m.get("bundle_hash") != h({k: m.get(k) for k in ("bundle_schema_version", "consumer", "purpose", "admitted_record_ids", "member_decision_ids", "curated_content_hash")}):
            yield "L4-I10", "manifests[%d]: bundle_hash != SHA3-256(JCS of no-self-reference canonical rep) (CR4)" % i


def ck_l4_i10b(w):
    for i, m in enumerate(w.manifests):
        b = w.bundle_by_id.get(m.get("bundle_id"))
        if not b:
            continue  # L4-I13 负责（bundle 缺失）
        if m.get("curated_content_hash") != h(b.get("curated_content")):
            yield "L4-I10b", "manifests[%d]: curated_content_hash != SHA3-256(JCS(curated_content)) (两级 hash)" % i


def ck_l4_i11(w):
    for i, m in enumerate(w.manifests):
        expected_ids = [r.get("decision_id") for r in w.receipts]
        if m.get("member_decision_ids") != expected_ids:
            yield "L4-I11", "manifests[%d]: member_decision_ids %r != receipts 有序集合 %r (覆盖检查)" % (i, m.get("member_decision_ids"), expected_ids)
        expected_records = []
        for r in w.receipts:
            e = r.get("evidence_record_id")
            if e not in expected_records:
                expected_records.append(e)
        if m.get("admitted_record_ids") != expected_records:
            yield "L4-I11", "manifests[%d]: admitted_record_ids %r != receipts 有序去重 %r (覆盖检查)" % (i, m.get("admitted_record_ids"), expected_records)


def ck_l4_i12(w):
    if not w.receipts:
        return
    max_ts = max(parse_utc(r["timestamp"]) for r in w.receipts)
    for i, m in enumerate(w.manifests):
        if parse_utc(m.get("generated_at")) < max_ts:
            yield "L4-I12", "manifests[%d]: generated_at < max(receipt.timestamp) (finalization ordering)" % i


def ck_l4_i13(w):
    seen = set()
    for i, m in enumerate(w.manifests):
        bid = m.get("bundle_id")
        if bid in seen:
            yield "L4-I13", "manifests[%d]: duplicate bundle_id %r" % (i, bid)
        seen.add(bid)
        if bid != m.get("bundle_hash"):
            yield "L4-I13", "manifests[%d]: bundle_id != bundle_hash (content-addressed, OPC #4)" % i
        b = w.bundle_by_id.get(bid)
        if not b:
            yield "L4-I13", "manifests[%d]: no CuratedEvidenceBundle with bundle_id %r" % (i, bid)
        elif b.get("bundle_id") != bid:
            yield "L4-I13", "bundle.bundle_id != manifest.bundle_id"


def _find_bad_keys(obj, bad, path):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in bad:
                return True, path + "." + k
            found, p = _find_bad_keys(v, bad, path + "." + k)
            if found:
                return found, p
    elif isinstance(obj, list):
        for idx, v in enumerate(obj):
            found, p = _find_bad_keys(v, bad, path + "[%d]" % idx)
            if found:
                return found, p
    return False, None


def ck_l4_i14(w):
    for i, b in enumerate(w.bundles):
        for j, frag in enumerate(b.get("curated_content", [])):
            content = frag.get("content")
            found, p = _find_bad_keys(content, {"raw_payload", "raw_reference"}, "content")
            if found:
                yield "L4-I14", "bundles[%d].curated_content[%d]: raw payload/reference at %s (consumer 只见 stripped 内容)" % (i, j, p)


def ck_l4_i15(w):
    for i, b in enumerate(w.bundles):
        m = None
        for mm in w.manifests:
            if mm.get("bundle_id") == b.get("bundle_id"):
                m = mm
                break
        if not m:
            continue  # L4-I13 负责
        members = m.get("member_decision_ids", [])
        admitted = m.get("admitted_record_ids", [])
        for j, frag in enumerate(b.get("curated_content", [])):
            did = frag.get("decision_id")
            rid = frag.get("evidence_record_id")
            if did not in members:
                yield "L4-I15", "bundles[%d].curated_content[%d]: decision_id %r not in member_decision_ids (provenance trace)" % (i, j, did)
            if rid not in admitted:
                yield "L4-I15", "bundles[%d].curated_content[%d]: evidence_record_id %r not in admitted_record_ids" % (i, j, rid)
            r = w.receipt_by_decision.get(did)
            if r and r.get("evidence_record_id") != rid:
                yield "L4-I15", "bundles[%d].curated_content[%d]: receipt(decision).evidence_record_id != fragment.evidence_record_id" % (i, j)


def ck_l4_i16(w):
    for i, m in enumerate(w.manifests):
        members = m.get("member_decision_ids", [])
        for r in w.receipts:
            if r.get("decision_id") in members and r.get("verdict") not in BUNDLE_VERDICTS:
                yield "L4-I16", "receipt verdict %r in bundle (BLOCK 不会到达 consumer)" % r.get("verdict")


# ---------------------------------------------------------------- checks（跨对象 X / V）

def ck_x_i1(w):
    for i, a in enumerate(w.assessments):
        if a.get("record_id") not in w.record_by_id:
            yield "X-I1", "assessments[%d]: record_id %r dangling" % (i, a.get("record_id"))
    for i, d in enumerate(w.decisions):
        if d.get("assessment_ref") not in w.assessment_by_id:
            yield "X-I1", "decisions[%d]: assessment_ref %r dangling" % (i, d.get("assessment_ref"))
    for i, r in enumerate(w.receipts):
        if r.get("decision_id") not in w.decision_by_id:
            yield "X-I1", "receipts[%d]: decision_id %r dangling" % (i, r.get("decision_id"))
        if r.get("assessment_id") not in w.assessment_by_id:
            yield "X-I1", "receipts[%d]: assessment_id %r dangling" % (i, r.get("assessment_id"))
        if r.get("evidence_record_id") not in w.record_by_id:
            yield "X-I1", "receipts[%d]: evidence_record_id %r dangling" % (i, r.get("evidence_record_id"))
    for i, m in enumerate(w.manifests):
        for did in m.get("member_decision_ids", []):
            if did not in w.receipt_by_decision:
                yield "X-I1", "manifests[%d]: member_decision_id %r has no receipt" % (i, did)


def ck_x_i2(w):
    for i, r in enumerate(w.receipts):
        for f in ("consumer", "purpose", "assessment_id", "policy_version"):
            if f not in r:
                yield "X-I2", "receipts[%d]: 四元组授权缺 %r（receipt 必须自包含可独立验证）" % (i, f)


def ck_x_i4(w):
    for i, d in enumerate(w.decisions):
        rec = w.record_by_id.get(d.get("record_id"))
        if not rec or rec.get("content_type") != "synthesis_brief":
            continue
        constituents = d.get("_constituent_strengths")
        if not isinstance(constituents, list):
            continue  # fixture 未提供 constituent 信息 → 无法验证（文档化）
        g = glb(constituents)
        strength = d.get("max_claim_strength")
        if not le(strength, g):
            yield "X-I4", "decisions[%d]: synthesis strength %s > glb(constituents %r)=%s (单调性)" % (i, strength, constituents, g)


def ck_v3(w):
    ctx = w.meta.get("context")
    if not ctx:
        return
    for i, r in enumerate(w.receipts):
        if r.get("consumer") != ctx.get("consumer") or r.get("purpose") != ctx.get("purpose"):
            yield "V3", "receipts[%d]: (consumer=%r, purpose=%r) != context (%r, %r)" % (i, r.get("consumer"), r.get("purpose"), ctx.get("consumer"), ctx.get("purpose"))


def ck_v5(w):
    ctx = w.meta.get("context")
    if not ctx:
        return
    ctx_time = parse_utc(ctx.get("context_time"))
    for i, r in enumerate(w.receipts):
        if r.get("consumer") != ctx.get("consumer") or r.get("purpose") != ctx.get("purpose"):
            continue  # V3 负责
        dims = r.get("assessment_dimensions") or {}
        fresh = dims.get("freshness")
        purpose = r.get("purpose")
        if fresh == "STALE":
            if purpose != "brief_assembly":
                yield "V5", "receipts[%d]: STALE → FAIL for purpose=%r" % (i, purpose)
            continue
        if fresh == "UNKNOWN":
            if purpose in ("trading_signal", "market_monitor", "portfolio_review"):
                yield "V5", "receipts[%d]: UNKNOWN → FAIL (fail-closed) for purpose=%r" % (i, purpose)
            continue
        if not is_utc_iso(fresh):
            continue  # L2-I5 / L4-I6 负责
        rec = w.record_by_id.get(r.get("evidence_record_id"))
        ts = rec.get("temporal_semantics") if rec else None
        max_age = MATRIX.get(purpose, {}).get(ts)
        if max_age is None:
            continue  # brief_assembly 跨会话 / 未知组合
        duration = (ctx_time - parse_utc(fresh)).total_seconds()
        if duration > max_age:
            yield "V5", "receipts[%d]: context_time − data_as_of = %.0fs > max_age %ds (purpose=%r, temporal_semantics=%r) — duration threshold，非上一交易日判定" % (i, duration, max_age, purpose, ts)


def ck_v8(w):
    for i, r in enumerate(w.receipts):
        d = w.decision_by_id.get(r.get("decision_id"))
        a = w.assessment_by_id.get(r.get("assessment_id"))
        if not d or not a:
            continue  # X-I1 负责悬空
        if r.get("assessment_id") != d.get("assessment_ref"):
            yield "V8", "receipts[%d]: assessment_id != decision.assessment_ref" % i
        if r.get("evidence_record_id") != d.get("record_id"):
            yield "V8", "receipts[%d]: evidence_record_id != decision.record_id" % i
        if d.get("record_id") != a.get("record_id"):
            yield "V8", "receipts[%d]: decision.record_id != assessment.record_id" % i
        if r.get("assessment_result_hash") != a.get("assessment_result_hash"):
            yield "V8", "receipts[%d]: assessment_result_hash != assessment.assessment_result_hash" % i
        dims = r.get("assessment_dimensions") or {}
        for dim in D5_DIMS:
            if dims.get(dim) != a.get(dim):
                yield "V8", "receipts[%d]: assessment_dimensions.%s != L2 (绑定链)" % (i, dim)


# ---------------------------------------------------------------- registry

# None = design-level / composition（文档化跳过）：
#   L1-I9 / L2-I7：append-only，单 world fixture 内不可机器判定
#   X-I3：结构组合（L3 必经 L2 = L3-I1；receipt 必经 L3 = L4-I3）
# 别名：V1→L4-I5；V2→X-I1；V4→L4-I16；V6→L4-I9/I10/I10b/I11；V7→L4-I8
CHECKS = [
    ("L1-I1", ck_l1_i1), ("L1-I2", ck_l1_i2), ("L1-I3", ck_l1_i3),
    ("L1-I4", ck_l1_i4), ("L1-I5", ck_l1_i5), ("L1-I6", ck_l1_i6),
    ("L1-I7", ck_l1_i7), ("L1-I8", ck_l1_i8), ("L1-I9", None),
    ("L2-I1", ck_l2_i1), ("L2-I2", ck_l2_i2), ("L2-I3", ck_l2_i3),
    ("L2-I4", ck_l2_i4), ("L2-I5", ck_l2_i5), ("L2-I6", ck_l2_i6),
    ("L2-I7", None),
    ("L3-I1", ck_l3_i1), ("L3-I2", ck_l3_i2), ("L3-I3", ck_l3_i3),
    ("L3-I4", ck_l3_i4), ("L3-I5", ck_l3_i5), ("L3-I6", ck_l3_i6),
    ("L3-I7", ck_l3_i7), ("L3-I8", ck_l3_i8),
    ("L4-I1", ck_l4_i1), ("L4-I2", ck_l4_i2), ("L4-I3", ck_l4_i3),
    ("L4-I4", ck_l4_i4), ("L4-I5", ck_l4_i5), ("L4-I6", ck_l4_i6),
    ("L4-I7", ck_l4_i7), ("L4-I8", ck_l4_i8), ("L4-I9", ck_l4_i9),
    ("L4-I10", ck_l4_i10), ("L4-I10b", ck_l4_i10b), ("L4-I11", ck_l4_i11),
    ("L4-I12", ck_l4_i12), ("L4-I13", ck_l4_i13), ("L4-I14", ck_l4_i14),
    ("L4-I15", ck_l4_i15), ("L4-I16", ck_l4_i16),
    ("X-I1", ck_x_i1), ("X-I2", ck_x_i2), ("X-I3", None), ("X-I4", ck_x_i4),
    ("V1", ck_l4_i5), ("V2", ck_x_i1), ("V3", ck_v3), ("V4", ck_l4_i16),
    ("V5", ck_v5), ("V6", [ck_l4_i9, ck_l4_i10, ck_l4_i10b, ck_l4_i11]),
    ("V7", ck_l4_i8), ("V8", ck_v8),
]


def run_world(data):
    w = World(data)
    meta = data.get("_meta", {})
    violations = {}
    try:
        for inv, fn in CHECKS:
            if fn is None:
                continue
            fns = fn if isinstance(fn, list) else [fn]
            for f in fns:
                for iid, msg in f(w):
                    violations.setdefault(iid, []).append(msg)
    except JcsReject as e:
        if meta.get("expect_reject"):
            return ("REJECT-OK", str(e))
        return ("ERROR", "JcsReject without expect_reject: %s" % e)
    if meta.get("expect_reject"):
        return ("FAIL", "expected JCS REJECT (CR5) but none raised")
    reported = sorted(violations)
    declared = sorted(set(meta.get("expected_violations", [])
                          + ([meta["expected_violation"]] if meta.get("expected_violation") else [])))
    if declared:
        if reported == declared:
            return ("PASS", "violations exactly %s" % reported)
        return ("FAIL", "expected %s, got %s %s" % (declared, reported,
                 {k: v[0] for k, v in violations.items()} if violations else ""))
    if not reported:
        return ("PASS", "no violations")
    return ("FAIL", "unexpected violations %s %s" % (reported,
            {k: v[0] for k, v in violations.items()}))


def main():
    base = Path(__file__).resolve().parent
    results = []
    for kind in ("valid", "invalid"):
        for path in sorted((base / "fixtures" / kind).glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                results.append((kind, path.name, "ERROR", "cannot parse: %s" % e))
                continue
            status, detail = run_world(data)
            results.append((kind, path.name, status, detail))

    n_fail = 0
    for kind, name, status, detail in results:
        print("[%s] %s/%s — %s" % (status, kind, name, detail))
        if status not in ("PASS", "REJECT-OK"):
            n_fail += 1

    n_checked = sum(1 for _, fn in CHECKS if fn is not None)
    print("----")
    print("fixtures: %d checked, %d unexpected" % (len(results), n_fail))
    print("invariant registry: %d IDs, %d machine-checked (design-level: L1-I9, L2-I7, X-I3)" % (len(CHECKS), n_checked))
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
