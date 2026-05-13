# Memory

## 2026-05-12: deep-research unknown skill production fix

- User reported the message/analyze flow broke after market intel routing changes.
- First bug was local/static frontend routing in `app/xueqiu-hot.html`: clicks went to `/app/`; minimal fix routes hot discussion to `/app/deep-research.html` and stock items to `/app/stock.html`.
- Second bug was production backend skill validation: `/home/ubuntu/finance-suite-web/static/app/deep-research.html` sends `skill_type: "deep-research"`, but `/home/ubuntu/finance-suite-web/app/skills.py` only registered `auction`, `industry`, `macro`, `mckinsey`, `meeting`, `stock`, `video`.
- Live `/api/analyze` backend is on the server in `/home/ubuntu/finance-suite-web/app/routers/api.py`, not in local `/Users/Zhuanz/finance-suite`.
- Production fix applied on 2026-05-12: added `SKILL_ALIASES` in `app/skills.py` mapping `deep-research`, `deep_research`, `deepResearch`, and `research` to existing canonical `industry`; added `normalize_skill_type()`; normalized `req.skill_type` at the start of `/api/analyze`.
- Backups on server: `app/skills.py.bak_codex_deep_alias_20260512001208` and `app/routers/api.py.bak_codex_deep_alias_20260512001208`.
- Restarted `finance-suite.service`; compile check passed; unauthenticated test now returns 401 instead of 400 unknown skill, proving skill validation is fixed.
- Detailed handoff for other agents: `docs/agent_handoff_deep_research_skill_alias_20260512.md`.

## 2026-05-12: market_intel Sidebar unblock patch

- User reported Claude got stuck while mapping `/api/analyze` and Sidebar intel routing.
- Root cause: two-repo boundary caused hesitation. `/api/analyze` lives in production `finance-suite-web`, but the local `finance-suite` repo can still prepare the MCP/server_scripts side without waiting for ECS entrypoint inspection.
- Applied local unblock patch in `/Users/Zhuanz/finance-suite`:
  - `scripts/market_intel.py`: `hot_stocks()` fallback chain now includes `zt_pool` after `hot_rank/top_gainers/hot_up`.
  - `server_scripts/intel_api.py`: added direct dict routes for `/api/intel/discussions`, `/api/intel/hot-stocks`, `/api/intel/watch-alerts`, `/api/intel/research`, `/api/intel/all`.
  - `mcp_server.py`: added MCP tools `research_digest(...)` and `market_intel(...)`, both wrapping outputs with `_wrap_response`.
  - `requirements.txt`: added `fastapi` and `flask` because `server_scripts/intel_api.py` / `watchlist_api.py` already depend on them; local `.venv` had been missing FastAPI.
- Validation:
  - `py_compile` passed for `server_scripts/intel_api.py`, `mcp_server.py`, `scripts/market_intel.py`, `scripts/research_digest.py`, `scripts/digest_llm.py`.
  - `pytest tests/test_digest_llm.py tests/test_research_digest.py -q` => core research suite `14 passed`.
  - Direct MCP calls passed: `mcp_server.research_digest(action="latest", limit=1, max_llm=0)` and `mcp_server.market_intel(modules="research", limit=1)`.
  - Direct route function calls passed for `intel_research(limit=1, max_llm=0)` and `intel_all(limit=1, modules="research")`.
- Updated agent handoff doc: `docs/market_intel_sidebar_handoff_20260512.md`.

## 2026-05-12: research Sidebar local E2E demo

- Claude correctly identified a "completion illusion": schema/tests/tools were green, but nobody had seen a real dehydrated research card in the browser.
- Built a local E2E demo that bypasses production `finance-suite-web`:
  - `scripts/research_demo_api.py`: minimal FastAPI app serving `app/index.html` and exposing `/api/intel/research` via direct `research_digest.latest(...)`.
  - `app/index.html`: added fourth tab `脱水研报`, `pane-research`, `fetchResearch()`, `renderResearch()`, and `routeResearch()`.
  - Localhost auth bypass: `app/index.html` skips the `fs_auth` redirect only on `localhost` / `127.0.0.1`; production domains still require login.
  - `requirements.txt`: added `uvicorn`.
- Validation:
  - Demo server runs with `.venv/bin/uvicorn scripts.research_demo_api:app --host 127.0.0.1 --port 8765`.
  - `curl http://127.0.0.1:8765/api/intel/research?limit=2&max_llm=1` returned real Eastmoney research items.
  - First observed item: `中国综合能源装备制造龙头，燃机&新能源构筑第二增长曲线`.
  - Without LLM key, `digest_status=fallback`; this proves the product loop is alive but the differentiation still depends on `OPENROUTER_API_KEY` or `ANTHROPIC_API_KEY`.
  - `py_compile` passed and `pytest tests/test_digest_llm.py tests/test_research_digest.py -q` => core research suite `14 passed`.
- Handoff doc updated: `docs/market_intel_sidebar_handoff_20260512.md`.

## 2026-05-12: ECS intel research route fact check

- Ran read-only SSH checks against `ubuntu@touziagent.com`.
- Production FastAPI entrypoint is `/home/ubuntu/finance-suite-web/app/main.py`; it includes `pages`, `api`, `admin`, `intel`, and `watchlist` routers.
- systemd service is `finance-suite.service`: `uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4`.
- nginx `/api/` proxies to `127.0.0.1:8000`; `/app/` serves `/home/ubuntu/finance-suite-web/static`.
- Production `/home/ubuntu/finance-suite-web/app/routers/intel.py` has `/api/intel/research`, but it is a compatibility stub returning HTTP 200 with `_qc.status=failure` and error `research route is not connected to a live upstream yet`.
- Production `static/app/index.html` does not contain `脱水研报`, `fetchResearch`, or `pane-research`, so the 4-tab research UI is not deployed.
- Conclusion: production `/api/intel/research` being 200 does not mean live `research_digest` is deployed. It is a safe placeholder. Docs updated: `docs/backend_api_architecture_20260512.md` and `docs/production_stability_guard_20260512.md`.

## 2026-05-12: production stability guard before next release

- User asked Codex to finish after Claude hit daily limit, with the priority: keep tomorrow's website basic functions online.
- Decision: freeze feature expansion. Do not deploy local research Sidebar demo or connect live research routes until deployment window; ECS §九 has since confirmed production router/static facts.
- Production observations from unauthenticated smoke checks:
  - `https://www.touziagent.com/app/index.html` => 200
  - `https://www.touziagent.com/app/stock.html` => 200
  - `https://www.touziagent.com/app/deep-research.html` => 200
  - `POST /api/analyze` without login => 401, healthy guard behavior
  - Initial `GET /api/intel/research?limit=1` was 404; later ECS confirmation found it now returns HTTP 200 from a compatibility stub with `_qc.status=failure` and `research route is not connected to a live upstream yet`.
- Added `scripts/site_smoke_check.py`: conservative production smoke check requiring no credentials. It treats static app pages and unauthenticated `/api/analyze` guard as critical, and treats `/api/intel/research` as optional but validates that any 200 remains the known `_qc.status=failure` stub until live deployment.
- Added `docs/production_stability_guard_20260512.md`: tomorrow morning checklist, hard freeze rules, and failure triage.
- 2026-05-13 verifier update: full pytest discovery currently returns `16 passed`; the original research-focused pair remains `14 passed`.
- Long-term guard rule: never accept HTTP 200 alone as proof of launch. Verify response body, `_qc.status`, production path, router source, production static drift, and update the fact-source docs for any status change.
- Reminder: quote URLs containing `?` in zsh, e.g. `curl -i 'https://www.touziagent.com/api/intel/research?limit=1'`.

## 2026-05-12: production watchlist 404 follow-up

- Production logs showed repeated `GET /api/watchlist/list` 404s after the deep-research fix.
- Cause: production `finance-suite-web/static/app/index.html` polls `/api/watchlist/list`, and `stock.html` posts `/api/watchlist/add`, but FastAPI had no watchlist router registered. Local `server_scripts/watchlist_api.py` is Flask Blueprint style and was not mounted.
- Production fix applied: created `/home/ubuntu/finance-suite-web/app/routers/watchlist.py`, registered it in `/home/ubuntu/finance-suite-web/app/main.py`, and also mounted existing `intel.router` which existed but was not included.
- Watchlist router uses existing `/home/ubuntu/finance-suite/scripts/watchlist.py` and `~/.finance-suite/watchlist.json`.
- Verified `GET /api/watchlist/list -> 200 OK` with empty success payload; `POST /api/watchlist/add {}` returns expected 400 `query 不能为空`.
- While mounting intel, `/api/intel/xueqiu-hot-stock` exposed an AkShare upstream parse failure. Adjusted intel exception contract to HTTP 200 + `_qc.status=failure` + empty `data`, so frontend fallback works without 5xx log noise.
- Additional backups on server: `app/main.py.bak_codex_watchlist_20260512011010`, `app/routers/intel.py.bak_codex_status_contract_20260512011113`.

## 2026-05-12: canonical deep-research frontend and intel helper

- Chose to do A+B from the follow-up list.
- Production `/home/ubuntu/finance-suite-web/static/app/deep-research.html` now sends canonical `skill_type: "industry"` instead of legacy `deep-research`.
- Local source `/Users/Zhuanz/finance-suite/app/deep-research.html` now sends canonical `skill_type: "industry"` instead of `deep_research`, so future deploys should not reintroduce legacy aliases.
- Alias layer remains in production backend for backward compatibility.
- Production `app/routers/intel.py` now documents the intel contract and uses `_intel_failure(error)` helper for HTTP 200 + `_qc.status=failure` + empty `data`.
- Verified production `GET /api/intel/xueqiu-hot-stock -> 200 OK` with `_qc.failure` and `GET /api/watchlist/list -> 200 OK`.
- Additional backups on server: `static/app/deep-research.html.bak_codex_canonical_skill_20260512012127`, `app/routers/intel.py.bak_codex_failure_helper_20260512012127`.

## 2026-05-12: final production stabilization before handoff

- Goal: make sure core website functions will not drop tomorrow.
- Added production `GET /api/check-auth` in `/home/ubuntu/finance-suite-web/app/routers/api.py`; logged-out requests now return expected 401 instead of 404, and authenticated admin-token check returns 200 with `{authenticated, username, tier}`.
- Added production intel compatibility routes in `/home/ubuntu/finance-suite-web/app/routers/intel.py`: `/api/intel/discussions`, `/api/intel/hot-stocks`, `/api/intel/watch-alerts`, `/api/intel/research`, `/api/intel/all`.
- Unconnected intel modules use the `_intel_failure` contract: HTTP 200 + `_qc.status=failure` + empty payload.
- Added local deprecation warning to `/Users/Zhuanz/finance-suite/server_scripts/watchlist_api.py`: old Flask watchlist API is not mounted in production; production uses `finance-suite-web/app/routers/watchlist.py`.
- Final public smoke passed: `/`, `/app/index.html`, `/app/deep-research.html`, `/app/stock.html`, `/api/health`, `/api/watchlist/list`, `/api/intel/xueqiu-hot`, `/api/intel/xueqiu-hot-stock`, `/api/intel/research`, `/api/intel/all` all return 200; `/api/check-auth` returns expected 401 when logged out.
- Additional production backups: `app/routers/api.py.bak_codex_check_auth_20260512020447`, `app/routers/intel.py.bak_codex_intel_stubs_20260512020548`.
