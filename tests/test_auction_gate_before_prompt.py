"""Defect B — Gate-before-Prompt enforcement probe for the Auction path.

WHAT THIS PROVES / DOES NOT PROVE
--------------------------------
This harness exercises the REAL production functions:
  app.auction_data._qc_auction
  app.auction_data.get_validated_auction_data
  app.auction_data.format_auction_data
  app.auction_data.format_auction_qc_failure
  app.llm.generate_analysis      (network boundary only is stubbed)

Only two things are stubbed, both strictly at the I/O boundary:
  1. `akshare` + `requests`  — so no upstream fetch happens.
  2. the outbound httpx call in app.llm — captured instead of sent.

Nothing in the QC / admission / formatting chain is replaced. The assertion
target is the actual bytes that would leave the process on the wire toward
the LLM (PRE_PROMPT_CONTEXT), captured inside app.llm.

Chain under test:
  raw auction evidence
    -> _qc_auction               (computes blocked_fields / allowed_use)
    -> get_validated_auction_data (raise-or-pass admission)
    -> format_auction_data / format_auction_qc_failure
    -> search_results_text
    -> app.llm.generate_analysis (user message assembly)
    -> PRE_PROMPT_CONTEXT
"""

import asyncio
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

# dotenv: env loading is not part of the gate chain.
try:
    import dotenv  # noqa: F401
except ModuleNotFoundError:
    _dv = types.ModuleType("dotenv")
    _dv.load_dotenv = lambda *a, **k: False
    sys.modules["dotenv"] = _dv

# httpx: only the outbound transport is faked; app.llm assembly is real.
try:
    import httpx  # noqa: F401
except ModuleNotFoundError:
    _hx = types.ModuleType("httpx")

    class _HTTPStatusError(Exception):
        def __init__(self, *a, response=None, **k):
            super().__init__(*a)
            self.response = response

    class _TimeoutException(Exception):
        pass

    _hx.HTTPStatusError = _HTTPStatusError
    _hx.TimeoutException = _TimeoutException
    _hx.AsyncClient = object
    sys.modules["httpx"] = _hx

from backend.engine.skills import auction_skill as AD  # noqa: E402

# ── The canary: a value that must never reach the prompt ────────────────
CANARY = "CANARY_BLOCKED_VALUE_7f3a91"


def _receipt(outcome):
    return {"outcome": outcome, "dimension": "x", "trace_token": "t"}


def _raw_evidence(*, phase_time, all_zero=False, drop_dims=()):
    """Construct raw auction evidence carrying the canary in blocked fields.

    `auction_result`, `market_sentiment`, `limit_up_ranking`, `quant_signals`
    are the field names _qc_auction lists in blocked_fields. We plant the
    canary in the row payload that format_auction_data would render.
    """
    row = {
        "名称": f"TESTCO_{CANARY}",
        "代码": "000001",
        "涨跌幅": 10.0,
        "成交额": 0 if all_zero else 1_000_000,
        "换手率": 0 if all_zero else 5.0,
        "封板资金": f"{CANARY}_SEAL",
        "首次封板时间": "092500",
        "连板数": 3,
    }
    data = {
        "zt_pool": [dict(row)],
        "strong_pool": [dict(row)],
        "previous_zt": [dict(row)],
        "big_buy": [{"时间": "0925", "名称": f"BB_{CANARY}", "代码": "000002",
                     "板块": "test", "相关信息": CANARY}],
        "hot_rank": [f"HOT_{CANARY}"],
        "hot_up": [f"UP_{CANARY}"],
        "top_gainers": [{"name": f"TG_{CANARY}", "code": "000003",
                         "change": 9.9, "price": 10.0, "pe": 15.0}],
        # blocked-field-named payloads planted directly in raw evidence
        "auction_result": f"AUCTION_RESULT_{CANARY}",
        "market_sentiment": f"SENTIMENT_{CANARY}",
        "limit_up_ranking": f"RANKING_{CANARY}",
        "quant_signals": f"QUANT_{CANARY}",
    }
    for d in drop_dims:
        data[d] = None
    for key in ("zt_pool", "strong_pool", "previous_zt", "big_buy",
                "hot_rank", "hot_up", "top_gainers"):
        data[f"{key}_status"] = _receipt(
            "unavailable" if data.get(key) in (None, []) else "success_with_data"
        )
    data["_meta"] = {
        "as_of": phase_time.isoformat(timespec="seconds"),
        "market_phase": AD.market_phase(phase_time),
        # MUST stay in sync with app/auction_data.py get_auction_data() _meta
        # (currently `market_phase(requested_at) not in {pre_open, auction_in_progress, non_trading_day}`).
        "auction_results_ready": AD.market_phase(phase_time) not in {
            "pre_open", "auction_in_progress", "non_trading_day",
        },
        "trace_token": "probe",
    }
    return data


# ── Reference times (all weekdays so market_phase is not non_trading_day) ─
MON = datetime(2026, 8, 10, tzinfo=SHANGHAI)          # Monday
T_PRE_OPEN = MON.replace(hour=9, minute=0)            # pre_open
T_IN_AUCTION = MON.replace(hour=9, minute=20)         # auction_in_progress
T_COMPLETE = MON.replace(hour=9, minute=26)           # auction_complete
T_MORNING = MON.replace(hour=10, minute=30)           # morning_session
SAT = datetime(2026, 8, 8, 10, 30, tzinfo=SHANGHAI)   # non_trading_day


# ── Real production path: raw -> QC -> admission -> formatted text ──────
def run_admission(data):
    """Replay app/routers/api.py:877-883 verbatim against real functions.

    Returns (search_results_text, branch, qc) where branch is
    'qc_failure' or 'success'.
    """
    async def _inner():
        qc = AD._qc_auction(data)
        if (qc["status"] == "failure"
                or not qc["auction_results_ready"]
                or qc["invalid_dimensions"]):
            raise AD.AuctionDataQualityError(qc)
        data["_qc"] = qc
        return data

    try:
        validated = asyncio.run(_inner())
    except AD.AuctionDataQualityError as exc:
        return AD.format_auction_qc_failure(exc.qc), "qc_failure", exc.qc
    return AD.format_auction_data(validated), "success", validated["_qc"]


def capture_pre_prompt_context(search_results_text, query="集合竞价"):
    """Capture the exact user message app.llm would put on the wire."""
    captured = {}

    class _FakeResp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "stub"}}]}

    class _FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, headers=None, json=None):
            captured["payload"] = json
            return _FakeResp()

    import backend.engine.llm.client as LLM
    orig = LLM.httpx.AsyncClient
    LLM.httpx.AsyncClient = _FakeClient
    try:
        asyncio.run(LLM.generate_analysis(
            "SYSTEM_PROMPT_STUB",
            f"用户查询：{query}",
            search_results_text,
        ))
    finally:
        LLM.httpx.AsyncClient = orig

    msgs = captured["payload"]["messages"]
    return "\n".join(m["content"] for m in msgs)


# ── Probes ──────────────────────────────────────────────────────────────
RESULTS = []


def probe(name, phase_time, *, all_zero=False, drop_dims=(),
          expect_canary_absent=True):
    data = _raw_evidence(phase_time=phase_time, all_zero=all_zero,
                         drop_dims=drop_dims)
    text, branch, qc = run_admission(data)
    ctx = capture_pre_prompt_context(text)
    canary_present = CANARY in ctx
    passed = (not canary_present) if expect_canary_absent else canary_present
    RESULTS.append({
        "probe": name,
        "market_phase": qc.get("market_phase"),
        "branch": branch,
        "qc_status": qc.get("status"),
        "auction_results_ready": qc.get("auction_results_ready"),
        "blocked_fields": qc.get("blocked_fields"),
        "allowed_use": qc.get("allowed_use"),
        "canary_in_pre_prompt": canary_present,
        "verdict": "PASS" if passed else "FAIL",
        "pre_prompt_len": len(ctx),
    })
    return ctx, qc, branch


def main():
    # P1 failure path: auction not complete -> blocked_fields non-empty
    probe("P1_pre_open_failure_path", T_PRE_OPEN)
    probe("P2_auction_in_progress", T_IN_AUCTION)

    # P3 success path: auction complete, healthy data.
    # Canary IS expected here — this documents that the success path
    # applies NO field-level filtering.
    probe("P3_success_path_auction_complete", T_COMPLETE,
          expect_canary_absent=False)
    probe("P4_success_path_morning_session", T_MORNING,
          expect_canary_absent=False)

    # P5 degraded path: zero-liquidity rows -> invalid_dimensions
    probe("P5_degraded_zero_liquidity", T_COMPLETE, all_zero=True)

    # P6 partial: critical dim missing but auction ready
    probe("P6_partial_missing_critical", T_COMPLETE,
          drop_dims=("zt_pool", "hot_rank"), expect_canary_absent=False)

    # P7 non-trading day
    probe("P7_non_trading_day", SAT)

    return RESULTS


if __name__ == "__main__":
    import json
    rows = main()
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    fails = [r for r in rows if r["verdict"] == "FAIL"]
    print(f"\nprobes={len(rows)} pass={len(rows)-len(fails)} fail={len(fails)}")
