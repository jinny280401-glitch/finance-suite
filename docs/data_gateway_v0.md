# Finance Data Gateway v0

Finance Data Gateway v0 is the smallest Finance Suite version of OpenBB's
"connect once, consume everywhere" idea.

It does not attempt to rebuild OpenBB's ODP, plugin system, Workspace, Excel
integration, or MCP architecture. The goal for v0 is narrower: put one unified
JSON contract in front of the existing Finance Suite quote data path so REST,
MCP, frontend, and agents can eventually consume the same structure.

## Scope

v0 adds:

- `scripts/finance_data_contract.py`
  - `build_response()`
  - standard fields: `ok`, `symbol`, `data_type`, `provider`, `freshness`,
    `as_of`, `data`, `qc`
- `scripts/finance_data_gateway.py`
  - `get_finance_data(data_type, symbol=None, params=None)`
  - only supports `data_type="quote"`
  - wraps the existing provider chain without changing business tools
- `GET /api/data/query`
  - parameters: `data_type`, `symbol`
  - returns the unified contract
- `scripts/smoke_data_gateway.py`
  - checks `/api/data/query?data_type=quote&symbol=600519.SH`
  - verifies the response contains `ok/provider/freshness/as_of/data/qc`

## Provider Chain

For `quote`, v0 tries:

```text
Wind -> Tushare -> JoinQuant -> AkShare -> cache
```

The first provider that returns data wins. The response records the selected
provider and attempted providers in `qc`.

## Contract

Example shape:

```json
{
  "ok": true,
  "symbol": "600519.SH",
  "data_type": "quote",
  "provider": "akshare",
  "freshness": "realtime",
  "as_of": "2026-05-26T13:20:00Z",
  "data": {},
  "qc": {
    "status": "success",
    "completeness": 1.0,
    "sources": ["akshare"],
    "fallback_source": "akshare",
    "missing_dimensions": [],
    "stale_data": [],
    "attempted_sources": [],
    "provider_chain": ["wind", "tushare", "joinquant", "akshare", "cache"]
  }
}
```

## Local Run

Start the local FastAPI demo:

```bash
cd /Users/Zhuanz/finance-suite
.venv/bin/uvicorn scripts.research_demo_api:app --host 127.0.0.1 --port 8765
```

Query:

```bash
curl 'http://127.0.0.1:8765/api/data/query?data_type=quote&symbol=600519.SH'
```

Smoke test:

```bash
python scripts/smoke_data_gateway.py
```

## Non-Goals

v0 intentionally does not:

- refactor the MCP server
- change the frontend
- add more `data_type` values
- add a plugin system
- touch production deployment

This is the first stable data exit, not a platform rewrite.
