"""Auction L2 no-LLM + golden-pit ladder unification — enforcement probes.

Locks the two user-approved follow-up fixes (2026-08-13):
  golden-pit 统一到 _qc_auction 阶梯   — Path B reuses phase/bundle ladder.
  L2 不调用 LLM                        — only L3 auction_analysis calls the LLM.

Exercises the REAL production functions in app.auction_data:
  _qc_auction               (ladder derivation)
  auction_allows_llm        (L1/L2 → False, L3 → True)
  golden_pit_authorization  (L1 → observe-only; L2/L3 → structure-overview cap)
  format_auction_data       (L2 degradation annotation)
  format_auction_qc_failure (L1 "wait until 09:25")

Only upstream network (akshare/requests/dotenv/httpx) is stubbed.
"""

import sys
import types
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

SHANGHAI = ZoneInfo("Asia/Shanghai")

for _name in ("akshare",):
    if _name not in sys.modules:
        sys.modules[_name] = types.ModuleType(_name)

if "requests" not in sys.modules:
    _req = types.ModuleType("requests")
    _req.get = lambda *a, **k: None
    _req.post = lambda *a, **k: None
    sys.modules["requests"] = _req

try:
    import dotenv  # noqa: F401
except ModuleNotFoundError:
    _dv = types.ModuleType("dotenv")
    _dv.load_dotenv = lambda *a, **k: False
    sys.modules["dotenv"] = _dv

try:
    import httpx  # noqa: F401
except ModuleNotFoundError:
    _hx = types.ModuleType("httpx")
    _hx.HTTPStatusError = type("HTTPStatusError", (Exception,), {})
    _hx.TimeoutException = type("TimeoutException", (Exception,), {})
    _hx.AsyncClient = object
    sys.modules["httpx"] = _hx

from app import auction_data as AD  # noqa: E402

DIMS = ["zt_pool", "strong_pool", "previous_zt", "big_buy",
        "hot_rank", "hot_up", "top_gainers"]


def _mk(phase_time, outcomes):
    row = {"名称": "TEST", "代码": "000001", "涨跌幅": 5.0,
           "成交额": 1_000_000, "换手率": 5.0}
    data = {}
    for dim in DIMS:
        outcome = outcomes.get(dim, "success_with_data")
        if outcome == "success_with_data":
            data[dim] = [dict(row)]
        elif outcome == "valid_empty":
            data[dim] = []
        else:
            data[dim] = None
        data[f"{dim}_status"] = {"outcome": outcome}
    data["_meta"] = {
        "as_of": phase_time.isoformat(timespec="seconds"),
        "market_phase": AD.market_phase(phase_time),
        "auction_results_ready": AD.market_phase(phase_time) not in {
            "pre_open", "auction_in_progress", "non_trading_day",
        },
        "trace_token": "t",
    }
    return data


MON = datetime(2026, 8, 10, tzinfo=SHANGHAI)
T_IN_AUCTION = MON.replace(hour=9, minute=20)   # auction_in_progress → L1
T_MORNING = MON.replace(hour=10, minute=30)     # morning_session → L2/L3

RESULTS = []


def check(name, cond, detail):
    RESULTS.append((name, bool(cond), detail))
    if not cond:
        raise AssertionError(f"[{name}] {detail}")


def main():
    # ── L1: auction window, rich data ──────────────────────────────────
    qc = AD._qc_auction(_mk(T_IN_AUCTION, {}))
    check("G1", qc["allowed_use"] == ["pre_auction_observation"],
          f"allowed_use={qc['allowed_use']} (want L1)")
    check("G1b", AD.auction_allows_llm(qc["allowed_use"]) is False,
          "L1 must NOT call LLM")
    g1 = AD.golden_pit_authorization(qc)
    check("G1c", g1["build_candidates"] is False,
          "L1 golden-pit must NOT build candidates")
    check("G1d", g1["allowed_use"] == ["pre_auction_observation"],
          f"golden-pit L1 allowed_use={g1['allowed_use']}")
    check("G1e", "候选池构造" in g1["forbidden_use"],
          f"golden-pit L1 forbidden_use={g1['forbidden_use']} must forbid candidate construction")

    # ── L2: post-09:25, bundle missing zt_pool ─────────────────────────
    qc2 = AD._qc_auction(_mk(T_MORNING, {"zt_pool": "timeout"}))
    check("G2", qc2["allowed_use"] == ["market_structure_overview"],
          f"allowed_use={qc2['allowed_use']} (want L2)")
    check("G2b", AD.auction_allows_llm(qc2["allowed_use"]) is False,
          "L2 must NOT call LLM")
    g2 = AD.golden_pit_authorization(qc2)
    check("G2c", g2["build_candidates"] is True,
          "L2 golden-pit MAY build (degraded) candidates")
    check("G2d", g2["allowed_use"] == ["market_structure_overview"],
          f"golden-pit L2 allowed_use={g2['allowed_use']}")
    check("G2e", "auction_analysis" in g2["forbidden_use"],
          f"golden-pit L2 forbidden_use={g2['forbidden_use']} must forbid auction_analysis")

    # ── L3: post-09:25, full 7/7 ────────────────────────────────────────
    qc3 = AD._qc_auction(_mk(T_MORNING, {}))
    check("G3", qc3["allowed_use"] == ["auction_analysis"],
          f"allowed_use={qc3['allowed_use']} (want L3)")
    check("G3b", AD.auction_allows_llm(qc3["allowed_use"]) is True,
          "L3 MAY call LLM")
    g3 = AD.golden_pit_authorization(qc3)
    check("G3c", g3["build_candidates"] is True,
          "L3 golden-pit builds full candidates")
    check("G3d", g3["allowed_use"] == ["market_structure_overview"],
          f"golden-pit caps at market_structure_overview even at L3: {g3['allowed_use']}")
    check("G3e", "auction_analysis" in g3["forbidden_use"],
          f"golden-pit NEVER authorizes auction_analysis: {g3['forbidden_use']}")

    # ── L1 failure body: explicit wait-until-09:25 ─────────────────────
    l1_text = AD.format_auction_qc_failure(qc)
    check("G4", "09:25" in l1_text,
          f"L1 failure body must name 09:25: {l1_text[:60]!r}")

    # ── L2 body: degradation annotation + blocked dim absent ───────────
    data2 = _mk(T_MORNING, {"zt_pool": "timeout", "hot_rank": "timeout"})
    qc2b = AD._qc_auction(data2)
    data2["_qc"] = qc2b
    data2["hot_rank"] = ["HOT_LEAK_4f2c"]
    text2 = AD.format_auction_data(data2)
    check("G5", "HOT_LEAK_4f2c" not in text2,
          "L2 blocked hot_rank data must not reach body")
    check("G5b", "数据降级" in text2,
          "L2 body must carry explicit degradation annotation")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)
    for name, ok, detail in RESULTS:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}  {detail}")
    print(f"\n{len(RESULTS)} checks all PASS")
