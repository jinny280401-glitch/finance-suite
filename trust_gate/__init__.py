"""Trust Gate Enforcement Layer.

Phase 1a: wind_query single-tool enforcement.
Boundaries active: G2 (Field Integrity), G3 (Phase-aware Freshness).
Contract G1 (Source Identity): planned, not yet implemented.

Evidence → Gate → Decision → Action chain.
"""

from trust_gate.decision import TrustGateDecision, BoundaryResult, GateVerdict
from trust_gate.enforcer import enforce_wind_query

__all__ = [
    "TrustGateDecision",
    "BoundaryResult",
    "GateVerdict",
    "enforce_wind_query",
]
