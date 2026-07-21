#!/usr/bin/env python3
"""Smoke test for Realtime Quote Integration Window.

Verifies that stock reports can source realtime/quote metadata from the
Finance Data Gateway instead of relying only on the optional in-memory cache.
"""
from __future__ import annotations

import asyncio
import sys

sys.path.insert(0, "scripts")

import stock_data  # noqa: E402
from mcp_server import _qc_stock  # noqa: E402


async def main() -> int:
    code = "600519"
    data = await stock_data.get_stock_full_data(code)
    availability = data.get("realtime_availability") or {}
    quote = data.get("realtime_quote") or {}

    assert "realtime_quote" in data, "get_stock_full_data must include realtime_quote gateway response"
    assert availability, "get_stock_full_data must include realtime_availability"
    assert availability.get("status") in {"available", "partial", "unavailable"}

    if availability["status"] == "partial" and availability.get("freshness") in {"daily", "delayed", "cached", "stale"}:
        assert availability.get("allowed_use") == ["daily_reference", "historical_context"]
        for field in (
            "current_price_judgment",
            "intraday_strength",
            "support_resistance",
            "short_term_breakout",
            "position_advice",
        ):
            assert field in availability.get("blocked_fields", []), f"{field} must be blocked"

    if quote.get("ok") is False:
        assert availability["status"] == "unavailable"
        assert not availability.get("allowed_use")

    qc = _qc_stock(data, stock_data.get_active_source(), realtime_stale=stock_data._is_realtime_stale())
    assert qc.get("data_availability", {}).get("realtime"), "MCP QC must expose realtime data_availability"
    assert "realtime" in qc.get("allowed_use", {}), "MCP QC must expose realtime allowed_use"
    assert "realtime" in qc.get("blocked_fields", {}), "MCP QC must expose realtime blocked_fields"

    print("Realtime Quote Integration Smoke: PASS")
    print(f"status={availability.get('status')}")
    print(f"source={availability.get('source')}")
    print(f"freshness={availability.get('freshness')}")
    print(f"allowed_use={availability.get('allowed_use')}")
    print(f"blocked_fields={availability.get('blocked_fields')}")
    print(f"quote_qc={quote.get('_qc')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
