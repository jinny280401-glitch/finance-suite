"""Task Authorization Boundary.

Contract (Owner AdJ 2026-09-29):
    requested_use × allowed_use → AUTHORIZED | BLOCKED

Position in the pipeline:
    Evidence Admission (research_runtime.evidence_bundle.build_evidence_bundle)
    → Task Authorization (this module)
    → LLM-facing Consumer (scripts.stock_data.format_stock_analysis_from_bundle)

Fail-closed semantics — the decision is BLOCKED (False) unless every
condition for authorization is met:

    - requested_use is not a non-empty str  → BLOCKED (cannot be determined safely)
    - allowed_use is empty / malformed      → BLOCKED (nothing admitted)
    - requested_use ∉ allowed_use           → BLOCKED (exceeds authorization)
    - requested_use ∈ allowed_use           → AUTHORIZED

This is a pure, deterministic, mechanical set-membership check. It:

    - does NOT call build_evidence_bundle (no second admission authority)
    - does NOT touch provider / QC / freshness / provenance policy
    - does NOT invoke any LLM or probabilistic matcher
    - does NOT mutate its inputs

Note: TRADING_DECISION_FIELDS (short_term_signal, fund_flow, position_sizing,
buy_sell_recommendation) are BLOCKED FIELDS in evidence_bundle, never
allowed_use values — so a requested_use drawn from that set can never be
authorized against a real bundle. This is what makes SYN-010 (PARTIAL QC +
position_sizing request) a BLOCK under the Task Authorization oracle.
"""
from __future__ import annotations

from typing import Any


def authorize_task(requested_use: Any, allowed_use: Any) -> bool:
    """Return True (AUTHORIZED) or False (BLOCKED).

    Fail closed: any undetermined or unauthorized input yields False.
    The decision is exact set membership — no fuzzy/embedding/substring match.
    """
    if not isinstance(requested_use, str):
        return False
    requested = requested_use.strip()
    if not requested:
        return False

    if not isinstance(allowed_use, (list, tuple, set, frozenset)):
        return False
    if not allowed_use:
        return False

    return requested in allowed_use
