"""Auction Cache Admission Repair — regression probes.

Locks the P0 fix: a stale L3 analysis cached before the current admission ladder
must NOT be served to an auction request whose evidence has since degraded to
L2/L1. The fix disables analysis cache read AND write for skill_type="auction"
so every auction request must re-run:

    fetch -> QC -> admission -> allowed_use -> L1/L2 direct response OR L3 LLM

Probes (full-path against the real app.routers.api.analyze, deps mocked):
  C1  old L3 cache + current L2 -> cached analysis NOT returned
  C1b L2 -> generate_analysis NOT called
  C1c auction cache write disabled (cache_set never called)
  C1d auction cache read disabled  (cache_get never called)
  C2  old L3 cache + current L1 -> cached analysis NOT returned
  C2b L1 -> generate_analysis NOT called
  C3  non-auction skill cache read/write behavior unchanged

Only network/db/user/llm boundaries are mocked; the admission logic under test
(_qc_auction -> auction_allows_llm -> branch guard) is the real production code.
"""

import asyncio
import sys
import types
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

# akshare is transitively imported by app.auction_data; stub if absent so the
# module can load in an env without the full dependency tree.
for _name in ("akshare",):
    if _name not in sys.modules:
        sys.modules[_name] = types.ModuleType(_name)

from app.routers import api as API  # noqa: E402
from app import auction_data as AD  # noqa: E402


class _DB:
    def add(self, *a, **k):
        pass

    def commit(self):
        pass


class _User:
    id = 1
    tier = "vip"


# A stale L3 auction analysis already sitting in the cache before evidence drops.
STALE_L3 = {
    "success": True,
    "result": "CACHED_L3_AUCTION_ANALYSIS",
    "sources": [],
    "kline": None,
    "report_as_of": None,
    "_qc": {"status": "success"},
}

# Current evidence degraded to L2 (morning, zt_pool unavailable -> bundle short).
L2_DATA = {
    "_meta": {
        "as_of": "2026-08-10T10:30:00+08:00",
        "market_phase": "morning_session",
        "auction_results_ready": True,
        "trace_token": "t",
    },
    "_qc": {
        "status": "success",
        "allowed_use": ["market_structure_overview"],
        "invalid_dimensions": [],
        "unavailable_dimensions": ["zt_pool"],
        "blocked_fields": ["zt_pool"],
    },
    "zt_pool": None,
    "strong_pool": [{"名称": "TEST", "代码": "000001",
                    "涨跌幅": 5.0, "成交额": 1_000_000, "换手率": 5.0}],
    "previous_zt": [],
    "big_buy": [], "hot_rank": [], "hot_up": [], "top_gainers": [],
}

# Current evidence degraded to L1 (pre-open / auction window -> observation only).
L1_QC = {
    "status": "failure",
    "gate_reason": "auction_results_not_ready",
    "allowed_use": ["pre_auction_observation"],
    "market_phase": "auction_in_progress",
    "auction_results_ready": False,
    "invalid_dimensions": [],
    "blocked_fields": [],
}


def _run_auction(auction_fetch):
    """Call the real analyze() for skill_type=auction with cache/admission deps mocked."""
    with mock.patch.object(API, "check_usage_allowed", return_value=(True, 0, 100)), \
         mock.patch.object(API, "cache_get", return_value=dict(STALE_L3)) as cache_get, \
         mock.patch.object(API, "cache_set") as cache_set, \
         mock.patch.object(API, "generate_analysis") as gen, \
         mock.patch.object(AD, "get_validated_auction_data", new=auction_fetch):
        req = API.AnalyzeRequest(skill_type="auction", query="测试竞价")
        resp = asyncio.run(API.analyze(req, user=_User(), db=_DB()))
    return resp, cache_get, cache_set, gen


RESULTS = []


def check(name, cond, detail):
    RESULTS.append((name, bool(cond), detail))
    if not cond:
        raise AssertionError(f"[{name}] {detail}")


def main():
    # ── C1: old L3 cache + current L2 ────────────────────────────────────
    resp, cache_get, cache_set, gen = _run_auction(mock.AsyncMock(return_value=L2_DATA))
    body = str(resp.get("result", ""))
    check("C1", "CACHED_L3_AUCTION_ANALYSIS" not in body,
          "stale L3 cache must NOT be served under L2 (got cache hit)")
    check("C1b", gen.call_count == 0,
          f"L2 must NOT call generate_analysis (called {gen.call_count}x)")
    check("C1c", cache_set.call_count == 0,
          f"auction must NOT write cache (cache_set called {cache_set.call_count}x)")
    check("C1d", cache_get.call_count == 0,
          f"auction must NOT read cache (cache_get called {cache_get.call_count}x)")

    # ── C2: old L3 cache + current L1 ────────────────────────────────────
    resp2, cache_get2, cache_set2, gen2 = _run_auction(
        mock.AsyncMock(side_effect=AD.AuctionDataQualityError(L1_QC))
    )
    body2 = str(resp2.get("result", ""))
    check("C2", "CACHED_L3_AUCTION_ANALYSIS" not in body2,
          "stale L3 cache must NOT be served under L1 (got cache hit)")
    check("C2b", gen2.call_count == 0,
          f"L1 must NOT call generate_analysis (called {gen2.call_count}x)")
    check("C2c", cache_set2.call_count == 0,
          f"auction must NOT write cache (cache_set called {cache_set2.call_count}x)")
    check("C2d", cache_get2.call_count == 0,
          f"auction must NOT read cache (cache_get called {cache_get2.call_count}x)")

    # ── C3: non-auction cache behavior unchanged ─────────────────────────
    with mock.patch.object(API, "check_usage_allowed", return_value=(True, 0, 100)), \
         mock.patch.object(API, "cache_get", return_value=dict(STALE_L3)) as cg, \
         mock.patch.object(API, "cache_set") as cs:
        req = API.AnalyzeRequest(skill_type="industry", query="半导体行业")
        resp3 = asyncio.run(API.analyze(req, user=_User(), db=_DB()))
    check("C3", cg.call_count == 1,
          f"non-auction must still read cache (cache_get called {cg.call_count}x)")
    check("C3b", "CACHED_L3_AUCTION_ANALYSIS" in str(resp3.get("result", "")),
          "non-auction cache hit must still be served")
    check("C3c", cs.call_count == 0,
          f"cache hit must early-return without rewriting (cache_set called {cs.call_count}x)")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)
    for name, ok, detail in RESULTS:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}  {detail}")
    print(f"\n{len(RESULTS)} checks all PASS")
