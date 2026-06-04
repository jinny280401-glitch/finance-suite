"""Trust Gate Runtime v0 evidence bundle.

This module defines the narrow boundary between Gateway/QC output and prompt
construction: LLM-facing runtime code receives EvidenceBundle, never raw
provider or Gateway responses.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from typing import Any


BLOCK_ALL = ["all"]
REALTIME_FIELDS = ["price", "volume", "amount"]
TRADING_DECISION_FIELDS = [
    "short_term_signal",
    "fund_flow",
    "position_sizing",
    "buy_sell_recommendation",
]


@dataclass(frozen=True)
class EvidenceBundle:
    evidence: dict[str, Any]
    allowed_use: list[str]
    blocked_fields: list[str]
    trust_status: str
    reason: str | None = None
    source: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _qc(gateway_response: dict[str, Any]) -> dict[str, Any]:
    qc = gateway_response.get("_qc") or gateway_response.get("qc") or {}
    return qc if isinstance(qc, dict) else {}


def _status(gateway_response: dict[str, Any]) -> str:
    return str(_qc(gateway_response).get("status") or "failure").lower()


def _reason(gateway_response: dict[str, Any]) -> str | None:
    reason = _qc(gateway_response).get("reason")
    return str(reason) if reason else None


def _missing_fields(gateway_response: dict[str, Any]) -> list[str]:
    fields = _qc(gateway_response).get("missing_fields") or _qc(gateway_response).get("missing_dimensions") or []
    return [str(field) for field in fields]


def _base_blocked_fields(gateway_response: dict[str, Any]) -> list[str]:
    blocked = list(_qc(gateway_response).get("blocked_fields") or [])
    for field in _missing_fields(gateway_response):
        if field not in blocked:
            blocked.append(field)
    return blocked


def _allowed_use(gateway_response: dict[str, Any], data_type: str) -> list[str]:
    qc = _qc(gateway_response)
    explicit = qc.get("allowed_use")
    if explicit:
        return [str(item) for item in explicit]

    status = _status(gateway_response)
    reason = _reason(gateway_response)
    missing = set(_missing_fields(gateway_response))

    if status == "failure":
        return []

    if data_type == "quote":
        if status == "success":
            return ["fundamental_overview", "valuation_analysis", "peer_comparison"]
        if status == "partial" and (reason == "delayed_source" or missing.intersection(REALTIME_FIELDS)):
            return ["fundamental_overview"]

    if data_type == "stock_analysis":
        if status == "partial":
            return ["fundamental_overview"]
        if status == "success":
            return ["fundamental_overview", "valuation_analysis", "peer_comparison"]

    if status == "partial":
        return ["fundamental_overview"]

    return []


def _runtime_blocked_fields(gateway_response: dict[str, Any], data_type: str) -> list[str]:
    status = _status(gateway_response)
    reason = _reason(gateway_response)
    missing = set(_missing_fields(gateway_response))
    blocked = _base_blocked_fields(gateway_response)

    if status == "failure":
        return BLOCK_ALL.copy()

    if data_type == "quote" and status == "partial" and (reason == "delayed_source" or missing.intersection(REALTIME_FIELDS)):
        for field in [*REALTIME_FIELDS, *TRADING_DECISION_FIELDS]:
            if field not in blocked:
                blocked.append(field)

    if data_type == "stock_analysis" and status == "partial":
        for field in TRADING_DECISION_FIELDS:
            if field not in blocked:
                blocked.append(field)

    return blocked


def _strip_blocked_fields(data: dict[str, Any], blocked_fields: list[str]) -> dict[str, Any]:
    if "all" in blocked_fields:
        return {}
    evidence = deepcopy(data)
    for field in blocked_fields:
        evidence.pop(field, None)
    return evidence


def build_evidence_bundle(gateway_response: dict[str, Any]) -> EvidenceBundle:
    """Convert a Gateway response into an LLM-facing evidence bundle."""
    data_type = str(gateway_response.get("data_type") or "unknown")
    trust_status = _status(gateway_response)
    blocked_fields = _runtime_blocked_fields(gateway_response, data_type)
    allowed_use = _allowed_use(gateway_response, data_type)
    raw_data = gateway_response.get("data") if isinstance(gateway_response.get("data"), dict) else {}

    return EvidenceBundle(
        evidence=_strip_blocked_fields(raw_data, blocked_fields),
        allowed_use=allowed_use,
        blocked_fields=blocked_fields,
        trust_status=trust_status,
        reason=_reason(gateway_response),
        source={
            "symbol": gateway_response.get("symbol"),
            "data_type": data_type,
            "provider": gateway_response.get("provider"),
            "provider_tier": gateway_response.get("provider_tier"),
            "freshness": gateway_response.get("freshness"),
            "as_of": gateway_response.get("as_of"),
        },
    )


def generate_section_body(evidence_bundle: EvidenceBundle) -> dict[str, Any]:
    """Minimal prompt-boundary stand-in for smoke tests.

    A real section generator should accept this type and never accept raw
    Gateway responses.
    """
    if not isinstance(evidence_bundle, EvidenceBundle):
        raise TypeError("generate_section_body only accepts EvidenceBundle")
    return {
        "allowed_use": evidence_bundle.allowed_use,
        "evidence": evidence_bundle.evidence,
        "trust_status": evidence_bundle.trust_status,
    }
