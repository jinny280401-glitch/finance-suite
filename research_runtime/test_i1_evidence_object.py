#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""I1 Evidence Object verification — pytest + standalone runner.

Covers the I1 acceptance criteria:
  D6:          classified research→AC / unclassified research→INF / trading→NC
  Identity:    serialize → deserialize round-trips to the same evidence_id
  Fail-closed: missing field / unknown provenance / invalid purpose / tamper
  Boundary:    admit() refuses raw dicts; purpose mismatch fails closed
"""

import contextlib
import json
from pathlib import Path

try:
    import pytest
except ImportError:  # standalone runner: minimal pytest.raises shim
    class _PytestShim:
        @staticmethod
        def raises(exc_type):
            @contextlib.contextmanager
            def _cm():
                try:
                    yield
                except exc_type:
                    return
                raise AssertionError(f"expected {exc_type.__name__} to be raised")
            return _cm()
    pytest = _PytestShim()

from evidence_object import (
    Admission,
    EvidenceObject,
    MaterializeReject,
    admit,
    from_dict,
    materialize,
)

_HERE = Path(__file__).resolve().parent
_VALID = _HERE / "fixtures" / "valid"
_INVALID = _HERE / "fixtures" / "invalid"
NOW = "2026-08-13T10:00:00Z"


def _load(name: str) -> dict:
    return json.loads((_VALID / name).read_text())


def _load_invalid(name: str) -> dict:
    payload = json.loads((_INVALID / name).read_text())
    payload.pop("_expect", None)
    return payload


# --- D6 mapping (reference path) -------------------------------------------

def test_d6_classified_research_is_attributed_claim():
    obj = from_dict(_load("i1_f1_search_result_classified_research.json"), now=NOW)
    assert obj.claim_strength_ceiling == "ATTRIBUTED_CLAIM"
    assert obj.classification == "classified:[financials]"


def test_d6_unclassified_research_is_informational():
    obj = from_dict(_load("i1_f2_search_result_unclassified_research.json"), now=NOW)
    assert obj.claim_strength_ceiling == "INFORMATIONAL"
    assert obj.content_type == "search_result"
    assert obj.classification == "unclassified"
    assert obj.purpose == "research"


def test_d6_unclassified_trading_is_no_claim():
    obj = from_dict(_load("i1_f3_search_result_unclassified_trading.json"), now=NOW)
    assert obj.claim_strength_ceiling == "NO_CLAIM"
    assert obj.purpose == "trading_signal"


# --- Identity preservation --------------------------------------------------

def test_identity_roundtrip():
    d = _load("i1_f2_search_result_unclassified_research.json")
    obj = from_dict(d, now=NOW)
    assert obj.evidence_id == d["evidence_id"]
    again = from_dict(obj.to_dict(), now=NOW)
    assert again.evidence_id == obj.evidence_id
    assert again == obj


def test_identity_is_deterministic():
    kwargs = dict(
        content_type="search_result", provenance="external",
        classification="unclassified", purpose="research",
        temporal_semantics="realtime", freshness="2026-08-13T09:55:00Z",
        allowed_use=("market_context",), now=NOW,
    )
    assert materialize(**kwargs).evidence_id == materialize(**kwargs).evidence_id


# --- Fail-closed (missing field / unknown enum / tamper) --------------------

def test_fail_closed_missing_classification():
    with pytest.raises(MaterializeReject):
        from_dict(_load_invalid("i1_f4_missing_classification.json"), now=NOW)


def test_fail_closed_missing_provenance():
    with pytest.raises(MaterializeReject):
        from_dict(_load_invalid("i1_f5_missing_provenance.json"), now=NOW)


def test_fail_closed_unknown_provenance():
    with pytest.raises(MaterializeReject):
        materialize(**_load_invalid("i1_f6_unknown_provenance.json"))


def test_fail_closed_invalid_purpose():
    with pytest.raises(MaterializeReject):
        materialize(**_load_invalid("i1_f7_invalid_purpose.json"))


def test_fail_closed_tampered_ceiling():
    d = _load("i1_f2_search_result_unclassified_research.json")
    d["claim_strength_ceiling"] = "OBSERVED_FACT"  # tamper
    with pytest.raises(MaterializeReject):
        from_dict(d, now=NOW)


def test_fail_closed_tampered_identity():
    d = _load("i1_f2_search_result_unclassified_research.json")
    d["evidence_id"] = "0" * 64
    with pytest.raises(MaterializeReject):
        from_dict(d, now=NOW)


# --- Consumer boundary ------------------------------------------------------

def test_boundary_refuses_raw_dict():
    with pytest.raises(TypeError):
        admit({"data": "raw provider output"}, consumer="Vera.ResearchSession", purpose="research")


def test_boundary_purpose_mismatch():
    obj = from_dict(_load("i1_f2_search_result_unclassified_research.json"), now=NOW)
    with pytest.raises(MaterializeReject):
        admit(obj, consumer="Vera.TradingSession", purpose="trading_signal")


def test_boundary_research_admitted_with_marker():
    obj = from_dict(_load("i1_f2_search_result_unclassified_research.json"), now=NOW)
    a = admit(obj, consumer="Vera.ResearchSession", purpose="research")
    assert a.verdict == "ALLOW_WITH_MARKER"
    assert a.claim_strength_ceiling == "INFORMATIONAL"


def test_boundary_trading_blocked():
    obj = from_dict(_load("i1_f3_search_result_unclassified_trading.json"), now=NOW)
    a = admit(obj, consumer="Vera.TradingSession", purpose="trading_signal")
    assert a.verdict == "BLOCK"


# --- D6 semantic cross-check (no drift from frozen validator) ---------------

def test_d6_ceiling_matches_frozen_validator_all_rows():
    """Every (content_type × provenance × purpose × classification) the runtime
    object produces must equal the frozen validator's d6_ceiling. Guards against
    anyone re-implementing D6 locally instead of importing it."""
    from validate_i0_schema_contract import CONTENT_TYPES, PROVENANCES, PURPOSES
    from validate_i0_schema_contract import d6_ceiling as frozen_ceiling

    cases = 0
    for ct in sorted(CONTENT_TYPES):
        for prov in sorted(PROVENANCES):
            for purpose in sorted(PURPOSES):
                for cls in ("unclassified", "classified:[financials]", "not_applicable"):
                    frozen = frozen_ceiling(ct, prov, purpose, cls)
                    if frozen is None:
                        continue  # synthesis_brief / prompt_template → N/A by design
                    got = materialize(
                        content_type=ct, provenance=prov, classification=cls,
                        purpose=purpose, temporal_semantics="realtime",
                        freshness="2026-08-13T09:55:00Z", now=NOW,
                    ).claim_strength_ceiling
                    assert got == frozen, f"{ct}×{prov}×{purpose}×{cls}: {got} != {frozen}"
                    cases += 1
    assert cases > 0


if __name__ == "__main__":
    import sys

    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS  {name}")
            except Exception as exc:  # noqa: BLE001
                failed += 1
                print(f"FAIL  {name}: {exc!r}")
    print(f"\n{ 'ALL PASS' if failed == 0 else f'{failed} FAILED' }")
    sys.exit(1 if failed else 0)
