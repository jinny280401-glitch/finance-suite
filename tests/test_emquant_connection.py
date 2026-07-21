import sys
from types import SimpleNamespace

from scripts import emquant_data


def test_connection_calls_emquant_client_start(monkeypatch):
    calls = []
    client = SimpleNamespace(
        start=lambda: calls.append("start")
        or SimpleNamespace(ErrorCode=0, ErrorMsg="")
    )
    monkeypatch.setitem(sys.modules, "EmQuantAPI", SimpleNamespace(c=client))
    monkeypatch.setattr(emquant_data, "_EM_USERNAME", "configured-user")
    monkeypatch.setattr(emquant_data, "_EM_PASSWORD", "configured-password")
    monkeypatch.setattr(emquant_data, "_em_connected", None)

    assert emquant_data.check_connection()["connected"] is True
    assert calls == ["start"]
