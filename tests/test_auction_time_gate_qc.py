from datetime import datetime
from zoneinfo import ZoneInfo

import mcp_server
from scripts.auction_data import format_auction_data, market_phase


SHANGHAI = ZoneInfo("Asia/Shanghai")


def _data(as_of: str, ready: bool, previous_zt=None):
    row = {"名称": "样本", "成交额": 1000, "换手率": 0.1}
    return {
        "_meta": {
            "as_of": as_of,
            "market_phase": "auction_complete" if ready else "auction_in_progress",
            "auction_results_ready": ready,
        },
        "zt_pool": [row],
        "strong_pool": [row],
        "previous_zt": previous_zt or [row],
        "big_buy": [row],
        "hot_rank": [row],
        "hot_up": [row],
        "top_gainers": [row],
    }


def test_market_phase_boundary_at_0925():
    assert market_phase(datetime(2026, 7, 17, 9, 24, 59, tzinfo=SHANGHAI)) == "auction_in_progress"
    assert market_phase(datetime(2026, 7, 17, 9, 25, 0, tzinfo=SHANGHAI)) == "auction_complete"


def test_qc_blocks_auction_conclusions_before_0925():
    data = _data("2026-07-17T09:19:00+08:00", False)
    qc = mcp_server._qc_auction(data)
    data["_qc"] = qc
    content = format_auction_data(data)

    assert qc["status"] == "partial"
    assert qc["gate_reason"] == "auction_not_complete_before_09_25"
    assert "market_sentiment" in qc["blocked_fields"]
    assert "quant_signals" in qc["blocked_fields"]
    assert "时间门阻断" in content
    assert "今日涨停池" not in content


def test_qc_rejects_nonempty_but_zero_liquidity_rows():
    zero_rows = [
        {"名称": "样本A", "成交额": 0, "换手率": 0},
        {"名称": "样本B", "成交额": 0, "换手率": 0},
    ]
    data = _data("2026-07-17T09:25:05+08:00", True, previous_zt=zero_rows)
    qc = mcp_server._qc_auction(data)
    data["_qc"] = qc
    content = format_auction_data(data)

    assert qc["status"] == "partial"
    assert "previous_zt" in qc["invalid_dimensions"]
    assert qc["gate_reason"] == "zero_liquidity_rows"
    assert "liquidity_assessment" in qc["blocked_fields"]
    assert "昨日涨停今日表现" not in content


def test_qc_allows_valid_post_auction_data():
    qc = mcp_server._qc_auction(_data("2026-07-17T09:25:05+08:00", True))

    assert qc["status"] == "success"
    assert qc["auction_results_ready"] is True
    assert qc["blocked_fields"] == []
