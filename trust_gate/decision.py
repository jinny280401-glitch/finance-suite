"""Trust Gate decision record — immutable, inspectable, traceable.

Integrity guarantees (F-03 remediation):
- decision_id includes microsecond + random entropy to prevent collisions
- to_dict() returns deep copies of all mutable structures — mutating the
  returned dict does NOT affect the original decision record
- from_boundaries() stores a defensive copy of the boundaries list
- _deep_freeze() recursively freezes evidence dicts AND nested lists/dicts;
  no mutation path exists after construction (C: NOT PROVEN → nested fix)
"""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any


class GateVerdict(str, Enum):
    PASS = "PASS"
    BLOCK = "BLOCK"


def _deep_freeze(value: Any) -> Any:
    """Recursively freeze all mutable containers to immutable equivalents.

    dict → MappingProxyType
    list → tuple
    set  → frozenset
    tuple → tuple (with each element recursively frozen)
    bytearray → bytes

    Idempotent on scalars and already-immutable types (str, int, float, bool,
    bytes, frozenset, MappingProxyType).
    """
    if isinstance(value, dict):
        return MappingProxyType({k: _deep_freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_deep_freeze(v) for v in value)
    if isinstance(value, set):
        return frozenset(_deep_freeze(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_deep_freeze(v) for v in value)
    if isinstance(value, bytearray):
        return bytes(value)
    return value


def _to_mutable(value: Any) -> Any:
    """Reverse _deep_freeze to produce independently-mutable copies.

    MappingProxyType → dict
    tuple → list (covers both frozen-list and frozen-tuple origins)
    frozenset → set
    bytes → bytearray

    Creates independent copies at every nesting level — mutating the returned
    structure does NOT affect the original frozen record.
    """
    if isinstance(value, MappingProxyType):
        return {k: _to_mutable(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_to_mutable(v) for v in value]
    if isinstance(value, frozenset):
        return {_to_mutable(v) for v in value}
    if isinstance(value, bytes):
        return bytearray(value)
    return value


@dataclass(frozen=True)
class BoundaryResult:
    """Single boundary check result. Deeply immutable.

    `frozen=True` prevents attribute reassignment. `__post_init__` applies
    `_deep_freeze` to evidence — nested dicts become MappingProxyType,
    nested lists become tuples. No mutation path exists after construction.
    """
    boundary_id: str          # e.g. "G2", "G3"
    boundary_label: str       # e.g. "Field Integrity"
    verdict: GateVerdict
    reason_code: str          # Machine-readable, e.g. "G2_CRITICAL_DIMENSION_MISSING"
    detail: str               # Human-readable explanation
    evidence: dict[str, Any]  # Deep-frozen in __post_init__
    evaluated_at: str         # ISO8601 timestamp

    def __post_init__(self):
        # Deep freeze evidence — prevents mutation at ANY nesting level
        object.__setattr__(self, 'evidence', _deep_freeze(dict(self.evidence)))


@dataclass(frozen=True)
class TrustGateDecision:
    """Full Trust Gate decision for a single evidence→action boundary crossing.

    Immutable. Every field is independently inspectable.
    The decision record IS the evidence that the Gate ran.
    """
    gate_version: str = "v0.1-phase1a"
    tool: str = "wind_query"
    action: str = ""          # e.g. "stock", "financials"
    code: str = ""            # Stock code
    source_used: str = ""     # Actual provider that returned data
    retrieved_at: str = ""    # When the query was made

    boundaries: list[BoundaryResult] = field(default_factory=list)
    overall_verdict: GateVerdict = GateVerdict.BLOCK
    blocked_boundaries: list[str] = field(default_factory=list)

    decision_id: str = ""
    decided_at: str = ""

    def __post_init__(self):
        # Freeze mutable collections — prevents decision.boundaries.append()
        object.__setattr__(self, 'boundaries', tuple(self.boundaries))
        object.__setattr__(self, 'blocked_boundaries', tuple(self.blocked_boundaries))

        if not self.decision_id:
            # Include microsecond + 6-char random suffix for uniqueness
            # (F-03: plain UTC-second collides under concurrent enforcement)
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
            suffix = uuid.uuid4().hex[:6]
            object.__setattr__(self, "decision_id", f"tg-{self.tool}-{ts}-{suffix}")
        if not self.decided_at:
            object.__setattr__(self, "decided_at", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))

    @property
    def passed(self) -> bool:
        return self.overall_verdict == GateVerdict.PASS

    def to_dict(self) -> dict[str, Any]:
        """Return a deep-copied dict representation.

        The returned dict is fully independent — mutating it does NOT
        affect the original TrustGateDecision or any BoundaryResult.
        (F-03: shallow to_dict() exposed mutable evidence dicts by reference.)
        """
        return {
            "gate_version": self.gate_version,
            "decision_id": self.decision_id,
            "decided_at": self.decided_at,
            "tool": self.tool,
            "action": self.action,
            "code": self.code,
            "source_used": self.source_used,
            "retrieved_at": self.retrieved_at,
            "overall_verdict": self.overall_verdict.value,
            "blocked_boundaries": list(self.blocked_boundaries),
            "boundaries": [
                {
                    "boundary_id": b.boundary_id,
                    "boundary_label": b.boundary_label,
                    "verdict": b.verdict.value,
                    "reason_code": b.reason_code,
                    "detail": b.detail,
                    "evidence": _to_mutable(b.evidence),
                    "evaluated_at": b.evaluated_at,
                }
                for b in self.boundaries
            ],
        }

    @classmethod
    def from_boundaries(
        cls,
        action: str,
        code: str,
        source_used: str,
        retrieved_at: str,
        boundaries: list[BoundaryResult],
    ) -> TrustGateDecision:
        # Defensive copy: don't share list reference with caller
        boundaries_copy = list(boundaries)
        blocked = [b.boundary_id for b in boundaries_copy if b.verdict == GateVerdict.BLOCK]
        overall = GateVerdict.BLOCK if blocked else GateVerdict.PASS
        return cls(
            action=action,
            code=code,
            source_used=source_used,
            retrieved_at=retrieved_at,
            boundaries=boundaries_copy,
            overall_verdict=overall,
            blocked_boundaries=blocked,
        )
