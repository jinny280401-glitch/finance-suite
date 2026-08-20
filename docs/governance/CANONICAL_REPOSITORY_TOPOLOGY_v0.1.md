# Canonical Repository Topology — v0.1

**Date:** 2026-08-20  
**Status:** Phase 4 sampled identity PROVEN/CLOSED; Phase 2 ownership 4/5 DECIDED（见 `PHASE2_CANONICAL_OWNERSHIP_DECISION_v0.1.md`，独立于 Phase 4 receipt）; REPOSITORY_MANIFEST.yaml pending (backlog)  
**Authority:** Repository Handoff Closure v0.1

## Three-Repository Model

Finance Suite operates as three distinct entities with clear boundaries:

### 1. Frontend / Orchestration Canonical

**Repository:** `finance-suite`  
**GitHub:** `github.com/jinny280401-glitch/finance-suite`  
**Current anchor:** `faa01d4` (main branch)  
**Role:** Frontend pages, MCP server, trust-gate enforcement, user entry points

**Canonical ownership:**
- `app/` — Workbench frontend application
- `index.html` — Hero homepage template
- `mcp_server.py` — MCP server（canonical owner FRONTEND；production identity = backend e266213 copy，production/owner drift OPEN）
- `trust_gate/` — Trust gate validation rules
- `docs/` — Governance, evidence, architecture documentation
- `tests/` — Trust gate, MCP, frontend integration tests
- `deploy.sh` — Frontend deployment script
- `.env.example` — Environment variable template

**Responsibilities:**
- User-facing HTML/JS/CSS
- MCP tool orchestration
- Context admission and search enforcement
- Trust-gate runtime validation
- Governance documentation
- Frontend deployment only (does not deploy backend services)

---

### 2. Backend Canonical

**Repository:** `finance-suite-backend`  
**GitHub:** `github.com/jinny280401-glitch/finance-suite-backend`  
**Current anchor:** `e266213` (main branch)  
**Role:** Backend API server, data providers, production-hardened runtime

**Canonical ownership:**
- `app/main.py` — FastAPI application entry point
- `app/routers/` — API route handlers
- `app/auction_data.py` — Auction data provider（canonical owner BACKEND）
- `app/stock_data.py` — Stock snapshot provider（canonical owner BACKEND）
- `app/config.py` — Backend configuration
- `.env.example` — Backend environment variable template
- `tests/` — Backend provider and API tests
- `scripts/deploy-backend.sh` — Backend deployment orchestration
- `docs/API_CONTRACTS.md` — Backend API specifications

**Responsibilities:**
- FastAPI + uvicorn runtime
- Data provider implementations（auction/stock canonical owner BACKEND；fund flow 归 backend）
- Backend-specific QC and error taxonomy
- Production data adapter logic
- Backend deployment and service management

---

### 3. Production Landing Directory

**Path:** `<landing>` on `<prod-host>`  
**Role:** DEPLOYMENT TARGET ONLY  
**NOT a Git repository**

**Constraints:**
- No `git init`
- No direct source editing on server
- No development branches on server
- Only receives deployed artifacts via `deploy.sh` / `deploy-backend.sh`

**Purpose:**
- Runtime landing directory for deployed frontend and backend files
- Serves live production traffic
- Must match frozen canonical commits for production baselines

---

## Boundary Rules

### Frontend ↔ Backend

| Concern | Canonical Owner |
|---|---|
| User-facing HTML/CSS/JS | Frontend |
| MCP server process | **FRONTEND**（canonical owner；production identity = backend e266213 copy，drift OPEN） |
| Trust-gate enforcement | Frontend |
| Backend API server | Backend |
| Data provider implementations | **BACKEND**（auction_data.py / stock_data.py，Phase 2 DECIDED——见 `PHASE2_CANONICAL_OWNERSHIP_DECISION_v0.1.md`；§Current Known Violations 3-4） |
| Provider QC/taxonomy | Backend |

**Communication:** Frontend → Backend via HTTP API (documented in `finance-suite-backend/docs/API_CONTRACTS.md`)

### Repository ↔ Production

**Deployment flow:**
```
[canonical repo commit] → [deploy script] → [production landing directory]
```

**NOT allowed:**
```
[production edit] → [commit to repo]
```

Production is a read-only deployment target, not a development environment.

### Mirror Policy

Files that appear in both repositories must follow one of these patterns:

1. **CANONICAL + STALE MIRROR** — One repo owns it, the other has an outdated copy that must be removed or synced
2. **CANONICAL + DEPLOYMENT ARTIFACT** — One repo owns the source, the other receives it via deployment
3. **ACTIVE FORK (temporary)** — Intentional divergence during transition; must converge to single canonical owner before handoff

**NOT allowed:**
- Permanent "both are canonical"
- "Whichever is newer"
- "Both actively maintained"

Every runtime file has exactly one canonical owner.

---

## Current Known Violations

These must be resolved before HUMAN PROGRAMMER READY:

1. **`mcp_server.py`** — canonical owner FRONTEND（production identity = backend e266213 copy，production/owner drift OPEN；backend copy = stale mirror 1325 行，非 canonical）

2. **`index.html`** — Frontend is canonical; backend byte-identical copy in `templates/` = deploy artifact / mirror（no ownership conflict）

3. **`auction_data.py`** — `app/auction_data.py` canonical owner BACKEND（production identity = e266213 MATCH）；`scripts/auction_data.py` = historical frontend `fcafa4d` orphan（disposition pending，不重开 app/auction_data.py ownership）

4. **`stock_data.py`** — `app/stock_data.py` canonical owner BACKEND（production identity = e266213 MATCH）

5. **`deploy-backend.sh`** — SPLIT / UNDECIDED（同名不同职责：frontend legacy helper vs backend orchestration；production use unproven OBS-5）

6. **`skills.py`** — Only in backend repo, but duplicated within that repo (`/skills.py` vs `/app/skills.py`) → in-repo duplication must be resolved

---

## Verification

To confirm this topology:

```bash
# Frontend canonical exists
cd /Users/Zhuanz/finance-suite
git cat-file -t faa01d4  # should return: commit

# Backend canonical exists
cd /Users/Zhuanz/finance-suite-backend
git cat-file -t e266213  # should return: commit

# Production landing directory exists (SSH required)
ssh <prod-host> 'ls -d <landing>'
```

---

## Next Steps

1. ~~Resolve duplicate files (Phase 2)~~ → DONE（4/5 DECIDED，见 `PHASE2_CANONICAL_OWNERSHIP_DECISION_v0.1.md`；deploy-backend.sh SPLIT，scripts/auction_data.py orphan）
2. ~~Establish production ↔ repository identity proof (Phase 4)~~ → DONE（sampled identity PROVEN/CLOSED；full-tree + deployment contract NOT_PROVEN）
3. Pick single developer branch → A = canonical `main`（preferred candidate）
4. Materialize onboarding docs（README / .env.example / handoff allowlist）

---

**Status:** Phase 4 sampled identity PROVEN/CLOSED · Phase 2 ownership 4/5 DECIDED（`PHASE2_CANONICAL_OWNERSHIP_DECISION_v0.1.md`） · A = preferred branch  
**Last verified:** 2026-08-20  
**Authority:** Repository Handoff Closure v0.1
