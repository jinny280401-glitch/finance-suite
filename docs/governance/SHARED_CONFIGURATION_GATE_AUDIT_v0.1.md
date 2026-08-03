# Shared Configuration Gate Audit v0.1

**Date:** 2026-07-31  
**Window:** Configuration & Identity Audit before Runtime Verification Execution  
**Mode:** AUDIT ONLY  
**Status:** AUDIT SPEC / EVIDENCE COLLECTION  
**Runtime:** NOT CHANGED  
**Production:** NOT TOUCHED (no writes, no restart, no deployment)  
**Secrets:** NOT EXPOSED

## 1. Purpose

This audit establishes a Shared Configuration Gate before Layer 3 / Layer 4 Runtime Verification.

The goal is not to fix configuration. The goal is to make local and production identity boundaries visible enough that future runtime failures can be classified as:

```text
Code Issue
Config Issue
Credential Issue
Provider Issue
Environment Issue
```

instead of collapsing into:

```text
Runtime failed, cause unknown.
```

Governing rule:

```text
Credential exists
  != Credential loaded
  != Provider identity proven
  != Runtime consumer proven
  != Production capability proven
```

## 2. Evidence Sources

| Area | Local evidence | Production evidence | Secret handling |
|---|---|---|---|
| Repository code | `finance-suite` working tree, code graph, `rg` scans | `/home/ubuntu/finance-suite-web` read-only source inventory | Secret values not printed |
| Dotenv files | `.env`, `.env.example`, `.env.save` metadata and key names | `/home/ubuntu/finance-suite-web/.env` metadata and key names | Values redacted; only key names and SET/EMPTY status |
| Runtime service | Local files only; demo server is not application runtime | `finance-suite.service`, `uvicorn app.main:app`, 4 workers | Process env names only |
| Nginx / systemd | `deploy/nginx/finance-suite.conf`, templates, scripts | active `/etc/nginx/sites-enabled/finance-suite`, `/etc/systemd/system/finance-suite.service` | No config mutation |
| Python packages | local `.venv` package presence / selected versions | production `venv` package presence / selected versions | No install |
| Database identity | local code paths | production SQLite metadata and aggregate counts only | No row values printed |

## 3. Credential Inventory

### 3.1 Key Presence Matrix

`SET` means a variable name exists with a non-empty value in the inspected dotenv or shell context. It does not prove that the credential is valid, current, authorized, or loaded by the active runtime.

| Item | Local | Production | Source | Status |
|---|---|---|---|---|
| `OPENROUTER_API_KEY` | SET | NOT FOUND | local `.env`; production `.env` | DRIFT |
| `QWEN_API_KEY` | NOT FOUND | SET | production `.env` | DRIFT |
| `QWEN_API_URL` | NOT FOUND | SET | production `.env` | DRIFT |
| `QWEN_MODEL` | NOT FOUND | SET | production `.env` | DRIFT |
| `SECRET_KEY` | NOT FOUND | SET | production `.env` / `app.config` | DRIFT / PRODUCTION REQUIRED |
| `ACCESS_TOKEN_EXPIRE_HOURS` | NOT FOUND | SET | production `.env` / `app.config` | DRIFT / PRODUCTION REQUIRED |
| `APP_NAME` | NOT FOUND | SET | production `.env` / `app.config` | DRIFT |
| `DEBUG` | NOT FOUND | SET | production `.env` / `app.config`, `app.main` | DRIFT |
| `JQDATA_USERNAME` | SET | SET | both dotenv files | MATCHED NAME |
| `JQDATA_PASSWORD` | SET | SET | both dotenv files | MATCHED NAME |
| `JQ_USERNAME` | SET | SET | both dotenv files | MATCHED NAME / ALIAS |
| `JQ_PASSWORD` | SET | SET | both dotenv files | MATCHED NAME / ALIAS |
| `THS_USERNAME` | SET | SET | both dotenv files | MATCHED NAME |
| `THS_PASSWORD` | SET | SET | both dotenv files | MATCHED NAME |
| `THS_TOKEN` | SET | SET | both dotenv files | MATCHED NAME |
| `THS_REFRESH_TOKEN` | SET | SET | both dotenv files | MATCHED NAME |
| `EM_USERNAME` | SET | SET | both dotenv files | MATCHED NAME |
| `EM_PASSWORD` | SET | SET | both dotenv files | MATCHED NAME |
| `BRAVE_KEYS` | shell SET / example only | SET | local shell + production `.env` | DRIFT |
| `TAVILY_KEYS` | shell SET / example only | SET | local shell + production `.env` | DRIFT |
| `SUPADATA_API_KEY` | shell SET / example only | SET | local shell + production `.env` | DRIFT |
| `TUSHARE_TOKEN` | example only | NOT FOUND | local `.env.example`; production source references absent | NOT LOADED |

### 3.2 Loaded Location

| Component | Local loaded location | Production loaded location | Status |
|---|---|---|---|
| Static demo server | None; static files only | N/A | NOT APPLICATION RUNTIME |
| `research_demo_api.py` | `load_dotenv(ROOT / ".env")` | Not production route | LOCAL DEMO ONLY |
| Production FastAPI app | Not present locally as active app runtime | `app/main.py` loads `/home/ubuntu/finance-suite-web/.env` | PRODUCTION ONLY |
| Production settings | Local equivalent exists, not active runtime | `app/config.py`, `settings = Settings()` | PRODUCTION ACTIVE |
| MCP server | local `.env` through root `mcp_server.py` | production `mcp_server.py` exists, not the web service entrypoint | SEPARATE RUNTIME |
| Provider scripts | local `.env` for JQData / iFinD scripts | production `.env` for JQData / iFinD scripts | SHARED NAMES, DIFFERENT ENVIRONMENTS |

### 3.3 Used By

| Credential / Config family | Used by | Current evidence |
|---|---|---|
| Qwen LLM config | production `app/llm.py`, `app/config.py` | Production has Qwen variables; local `.env` has OpenRouter instead |
| OpenRouter key | `scripts/research_demo_api.py` / research demo path | Local-only demo path; production `.env` does not expose this key name |
| Search keys (`TAVILY_KEYS`, `BRAVE_KEYS`) | `app/search.py`, `scripts/search.py`, config | Production and local shell/example names observed; validity not tested |
| Video key (`SUPADATA_API_KEY`) | `app/video_data.py`, docs/scripts | Production and local shell/example names observed; validity not tested |
| JWT/session (`SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_HOURS`) | production `app/auth.py`, `app/config.py` | Production required; local `.env` missing these production names |
| JQData (`JQDATA_*`, `JQ_*`) | `scripts/jqdata_fetch.py` | Names present both sides; session/provider capability not proven here |
| iFinD (`THS_*`) | `scripts/ifind_data.py` | Names present both sides; session/provider capability not proven here |
| Choice / EmQuant (`EM_*`) | local `scripts/emquant_data.py`; MCP documentation | Production `.env` has names, but production `scripts/emquant_data.py` was not found |
| AkShare | `app/stock_data.py`, `app/auction_data.py`, `app/routers/intel.py` | SDK present in production and local; no credential required |
| Tushare | local `scripts/tushare_data.py` | Local SDK exists; production SDK and script not found |

### 3.4 Rotation Status

Rotation age/status was not verified. No key values, creation dates, provider dashboards, or secret-manager records were inspected.

```text
Rotation Status: UNKNOWN
Reason: no secret-management source of truth was available in this audit.
```

## 4. Provider Identity Mapping

| Provider identity | Local evidence | Production evidence | Runtime route / consumer | Status |
|---|---|---|---|---|
| AkShare / Eastmoney | SDK exists; local scripts exist | SDK exists; `app/stock_data.py`, `app/auction_data.py`, `app/routers/intel.py` import/use AkShare | Production API routes under `/api/analyze` and `/api/intel/*` | MATCHED PROVIDER FAMILY |
| Qwen | Local `.env` does not carry Qwen names | Production `.env` carries `QWEN_*`; `app/llm.py` identifies Qwen | Production LLM path | PRODUCTION ONLY |
| OpenRouter | Local `.env` carries `OPENROUTER_API_KEY`; demo script references it | Production `.env` does not carry OpenRouter name | local research demo only | LOCAL DEMO ONLY |
| JQData | local credential names and SDK exist | production credential names and SDK exist | MCP/script path, not proven production research consumer | CREDENTIAL NAME MATCH / CAPABILITY NOT CLAIMED |
| iFinD | local credential names exist; local SDK not found | production credential names and SDK exist | script/MCP path; production research consumer not proven | DRIFT |
| Choice / EmQuant | local script and SDK exist | production credential names and SDK exist, but production `scripts/emquant_data.py` not found | MCP documentation references Choice, production script path missing | DRIFT |
| Tushare | local script and SDK exist; example token exists | production SDK/script not found | local script path only | LOCAL ONLY |
| Search (`Tavily`, `Brave`) | key names in local shell/example; scripts exist | key names in production `.env`; app config references them | search layer | NAME DRIFT / VALIDITY UNKNOWN |
| Supadata | key name in local shell/example | key name in production `.env`; `app/video_data.py` references it | video extraction path | NAME DRIFT / VALIDITY UNKNOWN |
| Research Runtime stub / gateway | `local_research_stub`, `finance_data_gateway` in local research runtime | Not proven as active production path | local `research_runtime/workflow.py` | DESIGN / LOCAL WORKFLOW ONLY |

Gate rule for provider identity:

```text
Provider code entry
  != SDK present
  != credential present
  != session established
  != evidence generated
  != research runtime consumer proven
```

## 5. Identity / ID Mapping Audit

### 5.1 Production Web Identity

| Layer | Evidence | Status |
|---|---|---|
| User | production ORM has `User.id`, `User.username`, `User.tier` | FOUND |
| Account ID | no separate `account_id` field found in inspected production app identity path | NOT FOUND |
| UUID | no hardcoded UUID literal found in production `app/*.py` scan | NOT FOUND |
| Session | JWT token carries `user_id`; request auth resolves current user | FOUND |
| Research Run ID | not found in production web app route identity path | NOT FOUND |
| Provider Identity | provider strings exist per module (`akshare`, `qwen`, `jqdata`, `ifind`) | FOUND / NOT CENTRALIZED |

Production aggregate DB checks, without printing user records:

| Check | Result |
|---|---|
| DB driver | SQLite |
| DB basename | `finance_suite.db` |
| DB password present | False |
| User count | 59 |
| Duplicate username groups | 0 |
| Usage rows | 507 |
| Orphan usage user IDs | 0 |

This proves basic user/usage referential consistency, not correctness of every user identity.

### 5.2 Local Research Runtime Identity

| Layer | Evidence | Status |
|---|---|---|
| Research session | `ResearchSession.session_id = research-{uuid}` | FOUND |
| Runtime event ID | incrementing `event_id` in `ResearchSession.add_event` | FOUND |
| Provider selection | `_select_provider(mode)` returns `finance_data_gateway` or `local_research_stub` | FOUND |
| User/account binding | no user/account binding in local `research_runtime` workflow | NOT FOUND |
| Production binding | no proof local research session maps to production request/session | NOT PROVEN |

### 5.3 Hardcoded / Historical ID Risk

No hardcoded UUID or numeric `user_id/account_id/session_id/run_id` literals were found in the inspected production `app` Python files.

Local `server_scripts` contain a legacy Flask-style `session['user_id']` auth path and a `finance_suite.db` path. Existing project memory states `server_scripts/` is not the active online runtime. This should stay classified as legacy/local unless a later runtime trace proves otherwise.

## 6. Local vs Production Drift Audit

| Area | Local | Production | Result |
|---|---|---|---|
| Git revision | local HEAD `16fc7da...`, branch `feature/session-1-validation-outcomes` | production has no `.git` metadata | DRIFT / TRACEABILITY PARTIAL |
| Web backend entry | no local `app/main.py` active app runtime in static demo | `uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4` | DRIFT |
| Static demo | `python3 -m http.server 8765` for pages only | N/A | LOCAL ONLY |
| Systemd | deploy templates/scripts exist locally | active service file hash `07c8ce...`; no `EnvironmentFile`; `Environment=PATH` only | DRIFT |
| Nginx | `deploy/nginx/finance-suite.conf` hash matches active nginx symlink hash | active nginx serves `touziagent.com`, `www`, `api`; proxies to backend upstream | MATCHED FILE HASH |
| Deploy scripts | local `deploy.sh`, `deploy-backend.sh` exist | production root does not contain these deploy scripts | DRIFT |
| Requirements file | local hash `245dae...` | production hash `e47f1a...` | DRIFT |
| Python package versions | newer local FastAPI/Uvicorn/SQLAlchemy/PyJWT/AkShare | older production versions; production lacks Tushare | DRIFT |
| Dotenv key set | OpenRouter + institutional providers; lacks production web `SECRET_KEY/QWEN_*` names | Qwen + JWT + institutional providers; lacks OpenRouter | DRIFT |
| Database | no local application DB evidence established | production SQLite `finance_suite.db` active | PRODUCTION ONLY |
| Provider SDKs | local has AkShare/Tushare/JQData/EmQuant; iFinD SDK not found | production has AkShare/JQData/iFinD/EmQuant; Tushare not found | DRIFT |
| Choice script path | local `scripts/emquant_data.py` exists | production `scripts/emquant_data.py` not found | DRIFT |
| JQData script path | local exists | production exists | MATCHED PATH |
| iFinD script path | local exists | production exists | MATCHED PATH |

## 7. Shared Configuration Gate Variables

Variables and identities that must enter the Shared Configuration Gate before Runtime Verification:

| Gate item | Why it enters the gate | Required decision before runtime verification |
|---|---|---|
| `SECRET_KEY` | controls JWT/session validity | define local/prod handling; never default silently |
| `ACCESS_TOKEN_EXPIRE_HOURS` | changes auth behavior | record expected value source and environment |
| `QWEN_API_KEY`, `QWEN_API_URL`, `QWEN_MODEL` | production LLM identity | define production LLM provider identity and expected model |
| `OPENROUTER_API_KEY` | local demo LLM identity | keep separated from production Qwen identity |
| `TAVILY_KEYS`, `BRAVE_KEYS` | search provider identity | define rotation/load source and runtime consumer |
| `SUPADATA_API_KEY` | video provider identity | define runtime scope; avoid claiming if not tested |
| `JQDATA_USERNAME`, `JQDATA_PASSWORD`, `JQ_USERNAME`, `JQ_PASSWORD` | JQData credential aliases | decide canonical alias and adapter ownership |
| `THS_USERNAME`, `THS_PASSWORD`, `THS_TOKEN`, `THS_REFRESH_TOKEN` | iFinD identity variants | decide SDK vs token route and active identity |
| `EM_USERNAME`, `EM_PASSWORD` | Choice identity | resolve production script-path drift before capability claims |
| `TUSHARE_TOKEN` | local/example only | do not claim production availability |
| `MARKET_CONTEXT_TOP_GAINERS_TIMEOUT` | auction/market-context runtime behavior | define expected default and override policy |
| `CC_POOL_LOG` | runtime instrumentation output | classify as observability-only, not product config |
| `finance_suite.db` | production identity/account/usage store | define DB source and backup/read-only verification policy |
| `uvicorn app.main:app` service identity | active production runtime entrypoint | treat as production runtime SOT |
| `research_demo_api.py` | local demo API identity | keep out of production capability claims |

## 8. Answers Required by Task Card

### 1. 本地运行依赖哪些 Key？

Observed local dependencies:

```text
OPENROUTER_API_KEY
JQDATA_USERNAME / JQDATA_PASSWORD
JQ_USERNAME / JQ_PASSWORD
THS_USERNAME / THS_PASSWORD / THS_TOKEN / THS_REFRESH_TOKEN
EM_USERNAME / EM_PASSWORD
BRAVE_KEYS / TAVILY_KEYS / SUPADATA_API_KEY (present in shell/example context)
TUSHARE_TOKEN (example/script reference only)
```

Local static demo (`python3 -m http.server 8765`) does not require these keys for page delivery.

### 2. 生产运行依赖哪些 Key？

Observed production `.env` and app source dependencies:

```text
SECRET_KEY
ACCESS_TOKEN_EXPIRE_HOURS
APP_NAME
DEBUG
QWEN_API_KEY / QWEN_API_URL / QWEN_MODEL
TAVILY_KEYS / BRAVE_KEYS
SUPADATA_API_KEY
JQDATA_USERNAME / JQDATA_PASSWORD
JQ_USERNAME / JQ_PASSWORD
THS_USERNAME / THS_PASSWORD / THS_TOKEN / THS_REFRESH_TOKEN
EM_USERNAME / EM_PASSWORD
MARKET_CONTEXT_TOP_GAINERS_TIMEOUT (source reference, not observed in .env)
CC_POOL_LOG (instrumentation reference)
```

### 3. 是否存在本地有、生产无？

Yes.

```text
OPENROUTER_API_KEY
TUSHARE_TOKEN
Tushare SDK/script runtime presence
local scripts/emquant_data.py path
local static/demo API path
```

### 4. 是否存在生产有、本地无？

Yes.

```text
SECRET_KEY
ACCESS_TOKEN_EXPIRE_HOURS
APP_NAME
DEBUG
QWEN_API_KEY / QWEN_API_URL / QWEN_MODEL
production app.main:app runtime
production SQLite app database
production iFinD SDK
```

### 5. Provider Identity 是否一致？

Partially.

```text
AkShare / Eastmoney: MATCHED provider family
JQData: MATCHED credential names and script path, capability not proven
iFinD: credential names matched, SDK presence drifts local vs production
Choice / EmQuant: credential names present, production script path missing
Tushare: local/example only, production not found
LLM: local OpenRouter vs production Qwen, DRIFT
```

Provider identity is not centrally registered. It is distributed across config, scripts, module literals, and runtime paths.

### 6. 哪些变量进入 Shared Configuration Gate？

Minimum gate set:

```text
SECRET_KEY
ACCESS_TOKEN_EXPIRE_HOURS
QWEN_API_KEY
QWEN_API_URL
QWEN_MODEL
OPENROUTER_API_KEY
TAVILY_KEYS
BRAVE_KEYS
SUPADATA_API_KEY
JQDATA_USERNAME
JQDATA_PASSWORD
JQ_USERNAME
JQ_PASSWORD
THS_USERNAME
THS_PASSWORD
THS_TOKEN
THS_REFRESH_TOKEN
EM_USERNAME
EM_PASSWORD
TUSHARE_TOKEN
MARKET_CONTEXT_TOP_GAINERS_TIMEOUT
CC_POOL_LOG
```

### 7. 哪些问题阻塞 Runtime Verification？

Hard blockers for broad Runtime Verification:

1. Local and production are not the same application runtime. Local static server / demo API cannot prove production backend runtime.
2. LLM provider identity drifts: local OpenRouter vs production Qwen.
3. Production has no git metadata, so source revision mapping is partial unless sha256-pinned.
4. Requirements/package versions drift materially between local and production.
5. Provider identity is distributed and not centrally declared.
6. Choice / EmQuant production path is inconsistent: credential names exist, SDK exists, but `scripts/emquant_data.py` was not found in production.
7. Tushare is local/example only and must not enter production capability claims.
8. Credential rotation and owner status are unknown.

Non-blockers for narrow production presentation verification:

1. Static asset fingerprinting can still prove a loaded frontend asset.
2. Browser runtime evidence can still prove presentation behavior.
3. Fixture rendering can still prove UI rendering only, as long as it is not upgraded into data-pipeline evidence.

## 9. Runtime Verification Entry Rule

Before a Runtime Verification case enters Layer 3 / Layer 4, it must state:

```text
Target runtime:
  local static demo / local demo API / production FastAPI / MCP / script

Credential source:
  dotenv / shell / systemd / none / unknown

Provider identity:
  provider name + SDK/API route + credential alias

Data source:
  AkShare / Qwen / OpenRouter / JQData / iFinD / Choice / Tushare / other

Runtime consumer:
  frontend route / backend route / research runtime / MCP tool / script

Capability claim:
  NOT CLAIMED until evidence reaches runtime consumer
```

If any field is `UNKNOWN`, the case may proceed only as a scoped evidence collection, not as a capability validation.

## 10. Final Audit State

```text
Shared Configuration Gate:
  ESTABLISHED v0.1

Credential Inventory:
  COMPLETE (names/presence only, no values)

Identity / ID Mapping:
  PARTIAL

Local vs Production Drift:
  CONFIRMED

Provider Identity:
  PARTIAL / DISTRIBUTED

Runtime:
  NOT CHANGED

Production:
  NOT TOUCHED (no writes, no restart, no deployment)

Secrets:
  NOT EXPOSED

Runtime Verification:
  MAY PROCEED ONLY WITH EXPLICIT TARGET RUNTIME AND GATE VARIABLES DECLARED
```
