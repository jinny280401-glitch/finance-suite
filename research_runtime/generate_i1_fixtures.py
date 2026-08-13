#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate I1 Evidence Object fixtures (I1-F1 .. I1-F7).

Valid fixtures (F1/F2/F3) are the FULL serialized EvidenceObject (to_dict()),
with evidence_id / claim_strength_ceiling / max_age baked in by actually
materializing. Invalid fixtures (F4..F7) are inputs that must fail closed.

Mapping to the I1 task card:
  I1-F1  classified search_result + research  → I0 frozen mapping (AC)
  I1-F2  unclassified search_result + research → INF (D6 / M25)
  I1-F3  unclassified search_result + trading  → NC (trading counterpart)
  I1-F4  missing classification / provenance  → fail closed
  I1-F5  serialize → deserialize               → identity preserved (test-level)
  (F6/F7  extra fail-closed: unknown provenance / invalid purpose)

Usage:
    python3 research_runtime/generate_i1_fixtures.py

Writes research_runtime/fixtures/{valid,invalid}/i1_f*.json
"""

import json
from pathlib import Path

from evidence_object import EvidenceObject, materialize

_HERE = Path(__file__).resolve().parent
_VALID = _HERE / "fixtures" / "valid"
_INVALID = _HERE / "fixtures" / "invalid"

# Pinned timestamps → deterministic staleness + identity.
NOW = "2026-08-13T10:00:00Z"
FRESH = "2026-08-13T09:55:00Z"


def _search_result(purpose: str, classification: str = "unclassified") -> EvidenceObject:
    """Reference path: search_result × {classified|unclassified} × purpose."""
    return materialize(
        content_type="search_result",
        provenance="external",
        classification=classification,
        purpose=purpose,
        temporal_semantics="realtime",
        freshness=FRESH,
        qc_status="success",
        provider_identity="NOT_APPLICABLE",
        field_integrity="NOT_APPLICABLE",
        allowed_use=("market_context",),
        blocked_use=(),
        now=NOW,
    )


def main() -> None:
    _VALID.mkdir(parents=True, exist_ok=True)
    _INVALID.mkdir(parents=True, exist_ok=True)

    # F1: I1-F1 — classified search_result + research → I0 frozen mapping (AC).
    f1 = _search_result("research", classification="classified:[financials]")
    assert f1.claim_strength_ceiling == "ATTRIBUTED_CLAIM", f1.claim_strength_ceiling

    # F2: I1-F2 — D6 research discriminator → INF (M25), admitted WITH marker.
    f2 = _search_result("research")
    assert f2.claim_strength_ceiling == "INFORMATIONAL", f2.claim_strength_ceiling

    # F3: I1-F3 — D6 trading counterpart → NO_CLAIM (NC), blocked.
    f3 = _search_result("trading_signal")
    assert f3.claim_strength_ceiling == "NO_CLAIM", f3.claim_strength_ceiling

    valid = {
        "i1_f1_search_result_classified_research.json": f1,
        "i1_f2_search_result_unclassified_research.json": f2,
        "i1_f3_search_result_unclassified_trading.json": f3,
    }
    for name, obj in valid.items():
        (_VALID / name).write_text(json.dumps(obj.to_dict(), indent=2, ensure_ascii=False))

    # Invalid fixtures. F4 (missing field) fixtures are otherwise-complete
    # serialized objects with exactly ONE required field removed, so the only
    # failure is the missing field (distinguishes the error).
    f4_missing_classification = f2.to_dict()
    del f4_missing_classification["classification"]
    f4_missing_classification["_expect"] = "MaterializeReject: missing classification"

    f5_missing_provenance = f2.to_dict()
    del f5_missing_provenance["provenance"]
    f5_missing_provenance["_expect"] = "MaterializeReject: missing provenance"

    invalid = {
        # I1-F4 — missing classification (from_dict boundary).
        "i1_f4_missing_classification.json": f4_missing_classification,
        # I1-F4 — missing provenance (from_dict boundary).
        "i1_f5_missing_provenance.json": f5_missing_provenance,
        # Extra fail-closed: unknown provenance (not in PROVENANCES).
        "i1_f6_unknown_provenance.json": {
            "_expect": "MaterializeReject: unknown provenance",
            "content_type": "search_result",
            "provenance": "mystery",
            "classification": "unclassified",
            "purpose": "research",
            "temporal_semantics": "realtime",
            "freshness": FRESH,
        },
        # Extra fail-closed: invalid purpose (not in PURPOSES).
        "i1_f7_invalid_purpose.json": {
            "_expect": "MaterializeReject: invalid purpose",
            "content_type": "search_result",
            "provenance": "external",
            "classification": "unclassified",
            "purpose": "gambling",
            "temporal_semantics": "realtime",
            "freshness": FRESH,
        },
    }
    for name, payload in invalid.items():
        (_INVALID / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    print(f"wrote {len(valid)} valid + {len(invalid)} invalid fixtures to {_HERE / 'fixtures'}")


if __name__ == "__main__":
    main()
