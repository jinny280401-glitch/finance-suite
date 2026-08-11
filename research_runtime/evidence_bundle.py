"""Trust Gate Runtime v0 evidence bundle.

This module defines the narrow boundary between Gateway/QC output and prompt
construction: LLM-facing runtime code receives EvidenceBundle, never raw
provider or Gateway responses.
"""
from __future__ import annotations

import uuid
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


BLOCK_ALL = ["all"]
REALTIME_FIELDS = ["price", "volume", "amount"]
TRADING_DECISION_FIELDS = [
    "short_term_signal",
    "fund_flow",
    "position_sizing",
    "buy_sell_recommendation",
]


class ProviderClass(str, Enum):
    """Provider classification for trust gate filtering."""
    MOCK = "mock"
    FALLBACK = "fallback"
    REAL = "real"


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


def _classify_provider(gateway_response: dict[str, Any]) -> ProviderClass:
    """Classify provider as MOCK, FALLBACK, or REAL based on gateway response."""
    provider = (gateway_response.get("provider") or "").lower()
    freshness = (gateway_response.get("freshness") or "").lower()
    tier = gateway_response.get("provider_tier")

    if freshness == "mock" or "stub" in provider or provider == "":
        return ProviderClass.MOCK
    if tier == 3 or freshness in ("stale", "cached"):
        return ProviderClass.FALLBACK
    return ProviderClass.REAL


def _allowed_use(gateway_response: dict[str, Any], data_type: str) -> list[str]:
    qc = _qc(gateway_response)
    explicit = qc.get("allowed_use")
    if explicit:
        return [str(item) for item in explicit]

    status = _status(gateway_response)
    reason = _reason(gateway_response)
    missing = set(_missing_fields(gateway_response))

    # ProviderClass constraint injection
    provider_class = _classify_provider(gateway_response)
    if provider_class == ProviderClass.MOCK:
        return ["workflow_smoke", "runtime_test"]

    if status == "failure":
        return []

    if data_type == "quote":
        if status == "success":
            allowed = ["fundamental_overview", "valuation_analysis", "peer_comparison"]
        elif status == "partial" and (reason == "delayed_source" or missing.intersection(REALTIME_FIELDS)):
            allowed = ["fundamental_overview"]
        else:
            allowed = []
    elif data_type == "stock_analysis":
        if status == "partial":
            allowed = ["fundamental_overview"]
        elif status == "success":
            allowed = ["fundamental_overview", "valuation_analysis", "peer_comparison"]
        else:
            allowed = []
    elif status == "partial":
        allowed = ["fundamental_overview"]
    else:
        allowed = []

    # FALLBACK providers: restrict to overview + historical
    if provider_class == ProviderClass.FALLBACK:
        allowed = [u for u in allowed if u in ("fundamental_overview", "historical_context")]

    return allowed


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


def recursive_freeze(obj: Any) -> Any:
    """Deep-freeze nested dict/list structures to prevent mutation.

    Returns an immutable copy: dicts become recursive frozen mappings,
    lists become tuples. Non-container values pass through unchanged.

    This closes the previously observed nested dict/list mutation path
    where consumers could modify evidence after Trust Gate verification.
    """
    if isinstance(obj, dict):
        return _FrozenDict({k: recursive_freeze(v) for k, v in obj.items()})
    if isinstance(obj, list):
        return tuple(recursive_freeze(item) for item in obj)
    return obj


class _FrozenDict(dict):
    """Immutable dict proxy. Raises TypeError on mutation attempts."""

    def __setitem__(self, key, value):
        raise TypeError("_FrozenDict does not support item assignment")

    def __delitem__(self, key):
        raise TypeError("_FrozenDict does not support item deletion")

    def update(self, *args, **kwargs):
        raise TypeError("_FrozenDict does not support update")

    def pop(self, *args, **kwargs):
        raise TypeError("_FrozenDict does not support pop")

    def popitem(self):
        raise TypeError("_FrozenDict does not support popitem")

    def clear(self):
        raise TypeError("_FrozenDict does not support clear")

    def __hash__(self):
        return hash(tuple(sorted(self.items())))


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


@dataclass(frozen=True)
class BlockedEvidence:
    """Evidence rejected by Trust Gate."""
    gate_status: str = "blocked"
    reason: str = ""
    blocked_fields: list[str] = field(default_factory=lambda: ["all"])
    source: dict[str, Any] = field(default_factory=dict)
    trust_status: str = "failure"
    decision_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TrustGateResult:
    """Result of Trust Gate filtering on raw evidence."""
    allowed_bundles: list[EvidenceBundle] = field(default_factory=list)
    blocked_items: list[BlockedEvidence] = field(default_factory=list)
    passthrough_items: list[dict[str, Any]] = field(default_factory=list)
    gate_events: list[dict[str, Any]] = field(default_factory=list)
    decision_ids: list[str] = field(default_factory=list)

    @property
    def has_any_allowed(self) -> bool:
        return len(self.allowed_bundles) > 0


def _enforce_trust_gate_or_block(
    payload: dict[str, Any],
    provider_name: str = "unknown",
) -> tuple[EvidenceBundle | BlockedEvidence, str]:
    """Enforce Trust Gate on a single gateway payload.

    Generates a unique decision_id for every enforcement decision.
    Missing-code and top-level exception paths build QC and enter
    enforcement — they never bypass the gate.

    Returns (bundle_or_blocked, decision_id).
    """
    decision_id = f"tg-{provider_name}-{uuid.uuid4().hex[:12]}"

    # Missing-code path: build QC from available fields, then enforce
    if not payload or not isinstance(payload, dict):
        synthetic_qc = {
            "status": "failure",
            "reason": "missing_payload",
            "missing_dimensions": ["all"],
        }
        payload = {"_qc": synthetic_qc, "data_type": "unknown"}

    # Build the bundle through the standard gate
    try:
        bundle = build_evidence_bundle(payload)
    except Exception as exc:
        # Top-level exception path: build QC, enter enforcement
        synthetic_qc = {
            "status": "failure",
            "reason": f"build_exception: {exc}",
            "missing_dimensions": ["all"],
        }
        payload = {"_qc": synthetic_qc, "data_type": "unknown"}
        bundle = build_evidence_bundle(payload)

    if bundle.trust_status == "failure" or not bundle.allowed_use:
        blocked = BlockedEvidence(
            gate_status="blocked",
            reason=(
                bundle.reason or "qc_failure"
                if bundle.trust_status == "failure"
                else "no_allowed_use"
            ),
            blocked_fields=bundle.blocked_fields if bundle.blocked_fields else ["all"],
            source=bundle.source,
            trust_status=bundle.trust_status,
            decision_id=decision_id,
        )
        return (blocked, decision_id)

    return (bundle, decision_id)


def _run_trust_gate(raw_evidence: list[dict[str, Any]]) -> TrustGateResult:
    """Run Trust Gate filter on raw evidence items from workflow.

    Gateway evidence (kind=gateway_*) is converted to EvidenceBundle or BlockedEvidence.
    Non-gateway evidence (kind=research_scope, skeleton) passes through unchanged.
    """
    result = TrustGateResult()

    for item in raw_evidence:
        kind = item.get("kind", "")

        # Non-gateway evidence: passthrough
        if not kind.startswith("gateway_"):
            result.passthrough_items.append(item)
            result.gate_events.append({
                "type": "trust_gate_passthrough",
                "message": f"Non-gateway evidence passed through: {kind}",
                "payload": {"kind": kind, "source": item.get("source")},
            })
            continue

        # Gateway evidence: run through Trust Gate
        payload = item.get("payload")
        provider_name = kind.replace("gateway_", "") if kind.startswith("gateway_") else "unknown"

        bundle_or_blocked, decision_id = _enforce_trust_gate_or_block(payload, provider_name)
        result.decision_ids.append(decision_id)

        if isinstance(bundle_or_blocked, BlockedEvidence):
            result.blocked_items.append(bundle_or_blocked)
            result.gate_events.append({
                "type": "evidence_blocked",
                "message": f"Evidence blocked: {bundle_or_blocked.source.get('symbol')} {bundle_or_blocked.source.get('data_type')}",
                "payload": {
                    "reason": bundle_or_blocked.reason,
                    "trust_status": bundle_or_blocked.trust_status,
                    "symbol": bundle_or_blocked.source.get("symbol"),
                    "data_type": bundle_or_blocked.source.get("data_type"),
                    "decision_id": decision_id,
                },
            })
        else:
            result.allowed_bundles.append(bundle_or_blocked)
            result.gate_events.append({
                "type": "evidence_allowed",
                "message": f"Evidence allowed: {bundle_or_blocked.source.get('symbol')} {bundle_or_blocked.source.get('data_type')}",
                "payload": {
                    "trust_status": bundle_or_blocked.trust_status,
                    "allowed_use": bundle_or_blocked.allowed_use,
                    "symbol": bundle_or_blocked.source.get("symbol"),
                    "data_type": bundle_or_blocked.source.get("data_type"),
                    "decision_id": decision_id,
                },
            })

    result.gate_events.insert(0, {
        "type": "trust_gate_started",
        "message": "Trust Gate filter started",
        "payload": {
            "raw_evidence_count": len(raw_evidence),
            "gateway_count": sum(1 for item in raw_evidence if item.get("kind", "").startswith("gateway_")),
        },
    })
    result.gate_events.append({
        "type": "trust_gate_completed",
        "message": "Trust Gate filter completed",
        "payload": {
            "allowed_count": len(result.allowed_bundles),
            "blocked_count": len(result.blocked_items),
            "passthrough_count": len(result.passthrough_items),
        },
    })

    return result
