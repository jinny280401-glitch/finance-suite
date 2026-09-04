"""Trust Gate boundary checks.

Phase 1a active boundaries (with contract mapping):
- G2: Field Integrity (contract G2 — critical dimension presence)
- G3: Phase-aware Freshness (contract G3 — data age check)

Contract G1 (Source Identity): planned, not yet implemented in Phase 1a.
"""

from trust_gate.boundaries.g2_field_integrity import check_g2_field_integrity
from trust_gate.boundaries.g3_freshness import check_g3_freshness

__all__ = ["check_g2_field_integrity", "check_g3_freshness"]
