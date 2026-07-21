import json
import sys
from types import SimpleNamespace

import mcp_server


def _response_payload(raw: str) -> tuple[dict, dict]:
    qc_text, payload_text = raw.split("\n\n", 1)
    return json.loads(qc_text), json.loads(payload_text)


def test_connect_does_not_require_joinquant(monkeypatch):
    monkeypatch.delitem(sys.modules, "joinquant_data", raising=False)
    monkeypatch.setitem(
        sys.modules,
        "wind_data",
        SimpleNamespace(check_connection=lambda: {"connected": True}),
    )
    monkeypatch.setitem(
        sys.modules,
        "tushare_data",
        SimpleNamespace(check_connection=lambda: {"connected": False}),
    )

    qc, payload = _response_payload(mcp_server.wind_query(action="connect"))

    assert qc["_qc"]["status"] == "success"
    assert payload["connected"] is True
    assert payload["joinquant"] is False


def test_stock_uses_wind_when_joinquant_is_unavailable(monkeypatch):
    monkeypatch.delitem(sys.modules, "joinquant_data", raising=False)
    monkeypatch.setitem(
        sys.modules,
        "wind_data",
        SimpleNamespace(
            get_stock_snapshot=lambda code: {
                "code": code,
                "close": 18.88,
                "market_cap": 123456789,
            }
        ),
    )
    monkeypatch.setitem(sys.modules, "tushare_data", SimpleNamespace())

    qc, payload = _response_payload(
        mcp_server.wind_query(action="stock", code="300394.SZ")
    )

    assert qc["_qc"]["status"] == "success"
    assert payload["source"] == "wind"
    assert payload["data"]["close"] == 18.88
    assert payload["data"]["market_cap"] == 123456789
