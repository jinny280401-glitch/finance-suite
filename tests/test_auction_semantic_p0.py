"""Auction Semantic P0 — acceptance fixtures F1–F7.

Locks the three AUTHORIZED design decisions (2026-08-13):

  Decision 1  Capability-Bundle Fail-Closed  — minimum_analysis_bundle.
  Decision 2  Allowed Use Ladder             — L1/L2/L3 三层授权。
  Decision 3  Repair Scope                   — revert auction_in_progress→ready,
                                              decouple market_phase / data_readiness / allowed_use.

Exercises the REAL production functions:
  app.auction_data._qc_auction        (allowed_use / blocked_fields derivation)
  app.auction_data.format_auction_data (blocked-evidence → absent from pre-prompt)

Only upstream network (akshare/requests/dotenv/httpx) is stubbed; the QC and
formatting chain is untouched.

Fixtures:
  F1 auction_in_progress + rich data        → pre_auction_observation (NOT auction_analysis)
  F2 auction_in_progress + only previous_zt → pre_auction_observation, blocked_fields != []  (counterexample)
  F3 post-09:25 + bundle not satisfied      → market_structure_overview
  F4 post-09:25 + critical dim missing      → no full auction_analysis
  F5 post-09:25 + valid bundle              → auction_analysis, blocked_fields == []
  F6 parse_error/unavailable                → explicit blocked_fields (never empty)
  F7 blocked-capability evidence            → absent from formatted pre-prompt text
"""

import sys
import types
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

SHANGHAI = ZoneInfo("Asia/Shanghai")

# ── Boundary stubs: upstream network only ───────────────────────────────
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

from backend.engine.skills import auction_skill as AD  # noqa: E402

DIMS = ["zt_pool", "strong_pool", "previous_zt", "big_buy",
        "hot_rank", "hot_up", "top_gainers"]


def _mk(phase_time, outcomes):
    """Construct raw auction evidence for a given phase + per-dimension outcome."""
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


MON = datetime(2026, 8, 10, tzinfo=SHANGHAI)          # Monday
T_IN_AUCTION = MON.replace(hour=9, minute=20)         # auction_in_progress
T_MORNING = MON.replace(hour=10, minute=30)           # morning_session


def _qc(outcomes, phase_time):
    data = _mk(phase_time, outcomes)
    qc = AD._qc_auction(data)
    data["_qc"] = qc
    return data, qc


RESULTS = []


def check(name, cond, detail):
    RESULTS.append((name, bool(cond), detail))
    if not cond:
        raise AssertionError(f"[{name}] {detail}")


def main():
    # F1 — auction_in_progress + rich data → L1 (NOT auction_analysis)
    _, qc = _qc({}, T_IN_AUCTION)
    check("F1", qc["allowed_use"] == ["pre_auction_observation"],
          f"allowed_use={qc['allowed_use']} (want L1 even with rich data)")
    check("F1b", "auction_analysis" not in qc["allowed_use"],
          "auction_analysis must not appear during auction window")

    # F2 — counterexample closure: auction_in_progress + only previous_zt (completeness 0.14)
    only_prev = {d: "timeout" for d in DIMS}
    only_prev["previous_zt"] = "success_with_data"
    _, qc = _qc(only_prev, T_IN_AUCTION)
    check("F2", qc["allowed_use"] == ["pre_auction_observation"],
          f"allowed_use={qc['allowed_use']} (counterexample must be L1, not auction_analysis)")
    check("F2b", qc["blocked_fields"] != [],
          f"blocked_fields={qc['blocked_fields']} must be non-empty")
    check("F2c", qc["completeness"] == 0.14,
          f"completeness={qc['completeness']} (fixture sanity: only 1/7 present)")
    check("F2d", qc["auction_results_ready"] is False,
          "auction_in_progress → auction_results_ready must be False (3A revert)")

    # F3 — post-09:25 + bundle not satisfied (zt_pool timeout) → L2
    partial = {"zt_pool": "timeout"}
    _, qc = _qc(partial, T_MORNING)
    check("F3", qc["allowed_use"] == ["market_structure_overview"],
          f"allowed_use={qc['allowed_use']} (bundle missing zt_pool → L2)")
    check("F3b", "zt_pool" in qc["blocked_fields"],
          f"blocked_fields={qc['blocked_fields']} must list zt_pool")

    # F4 — post-09:25 + critical (bundle) dim missing → no full auction_analysis
    crit = {"strong_pool": "provider_error"}
    _, qc = _qc(crit, T_MORNING)
    check("F4", "auction_analysis" not in qc["allowed_use"],
          f"allowed_use={qc['allowed_use']} (critical strong_pool missing → no L3)")
    check("F4b", "strong_pool" in qc["blocked_fields"],
          f"blocked_fields={qc['blocked_fields']} must list strong_pool")

    # F5 — post-09:25 + valid bundle → L3, no spurious blocking
    _, qc = _qc({}, T_MORNING)
    check("F5", qc["allowed_use"] == ["auction_analysis"],
          f"allowed_use={qc['allowed_use']} (full 7/7 → L3)")
    check("F5b", qc["blocked_fields"] == [],
          f"blocked_fields={qc['blocked_fields']} must be empty on clean success")

    # F6 — parse_error/unavailable → explicit blocked_fields (never empty, even at L3)
    err = {"hot_rank": "parse_error", "top_gainers": "unavailable"}
    _, qc = _qc(err, T_MORNING)
    check("F6", qc["allowed_use"] == ["auction_analysis"],
          f"allowed_use={qc['allowed_use']} (bundle intact → L3)")
    check("F6b", "hot_rank" in qc["blocked_fields"] and "top_gainers" in qc["blocked_fields"],
          f"blocked_fields={qc['blocked_fields']} must list both failed dims")

    # F7 — blocked-capability evidence absent from formatted pre-prompt text
    leak = {"hot_rank": "timeout"}
    data, qc = _qc(leak, T_MORNING)
    data["hot_rank"] = ["HOT_CANARY_LEAK_9d31"]          # plant data that would leak if not gated
    text = AD.format_auction_data(data)
    check("F7", "HOT_CANARY_LEAK_9d31" not in text,
          "unavailable dim's data must not reach formatted prompt")
    check("F7b", "人气排行" not in text,
          "unavailable hot_rank section must be absent")
    check("F7c", "数据降级" in text,
          "degraded state must be explicitly annotated in prompt text")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)
    for name, ok, detail in RESULTS:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}  {detail}")
    print(f"\n{len(RESULTS)} checks all PASS")
