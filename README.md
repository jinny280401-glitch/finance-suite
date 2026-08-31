# Finance Suite / Vera — Trusted Research Runtime

**Repository:** `finance-suite`  
**Canonical Branch:** `main`  
**Status:** Runtime Governance **Target / Partial Implementation** — the governance architecture below is a design target, not a verified production runtime fact. Research artifacts live elsewhere. See §1.1 for the per-stage evidence boundary.

---

## Production Identity — Read This First

- **Canonical source repository:** `finance-suite`; **canonical source branch:** `main`.
- **Production runtime landing:** `/home/ubuntu/finance-suite-web`. It is a deployment/runtime directory, **not** a Git source of truth.
- Server-side `finance-suite` checkouts, including historical OpenClaw skill locations, are **non-canonical**. Their current deployment use is **NOT PROVEN**; do not copy code back from them without an explicit handoff decision.
- Start new development from a fresh clone of the canonical repository's `main` branch, not from a server directory or another local worktree.
- `deploy.sh` and `deploy-backend.sh` are deployment helpers; they do not establish canonical ownership. `deploy-backend.sh` may probe historical locations, and its current production use is **NOT PROVEN**.

### `deploy.sh` — what it is, and what it cannot prove

`deploy.sh` is a **production landing populator**. It is not a build, not a source of truth, and not an ownership decision.

| Question | Answer |
|---|---|
| Where does it take source from? | `raw.githubusercontent.com/jinny280401-glitch/finance-suite/main/...` — GitHub canonical `main`, fetched over the network at run time. Never from the local checkout it is invoked from. |
| Where does it write? | `/home/ubuntu/finance-suite-web/static/app/` and `/home/ubuntu/finance-suite-web/templates/index.html`; it also rewrites `/etc/nginx/sites-available/finance-suite` and reloads nginx. |
| Does it build? | **No.** It is `curl` of static HTML/JS/CSS assets. No compile, bundle, or transform step. |
| Does it define canonical ownership? | **No.** It *consumes* an already-decided canonical branch. It records no ownership and resolves no ambiguity. |

What it proves: the **frontend landing** under `/home/ubuntu/finance-suite-web/static/app/` is intended to be a copy of GitHub `main`'s `app/` assets, as of whenever the script last ran.

What it cannot prove:

- **Backend production checkout identity.** `deploy.sh` touches only static frontend assets plus nginx. The API is proxied to `127.0.0.1:8000`; which checkout or revision serves that port is **outside this script's evidence** and remains **UNKNOWN** from the script alone.
- **That production currently matches `main`.** The script pins no revision and writes no receipt. It fetches whatever `main` pointed to at run time. Absent a run log, deployed content identity is establishable only by `path` + `sha256` of the landed files, not by a revision.
- **That any local worktree is what shipped.** Because source is pulled from GitHub rather than the invoking checkout, a clean local tree is not evidence about production, and a dirty one is not counter-evidence.

### Choosing a checkout to work from

Do **not** assume a local directory is the canonical checkout. Before using one, confirm branch, HEAD, cleanliness, and upstream. Specifically:

- A tree that is **dirty** is not a handoff baseline.
- Being **on `main`** is not the same as being **published**. A local `main` may sit ahead of `origin/main` with unpushed commits.
- `origin/*` refs are only as fresh as the last `git fetch` in that clone. A stale `origin/main` will silently understate divergence.
- Prefer a fresh clone of canonical `main` over reusing any existing local worktree.

---

## 1. Project Overview

Finance Suite is the runtime repository for **Vera**, a trusted AI research infrastructure for Chinese A-share and macro analysis.

It is not a general-purpose chatbot. It is a bounded research runtime that separates:

- **What the system can prove** (Evidence)
- **What the system can claim** (Capability Claim Governance)
- **What the system may decide** (Trust Gate)

### Core Design — Target Architecture

The following is the **intended** pipeline. It is a design target. Do **not** read it as a description of what every production request currently executes; see §1.1 for what is actually proven.

```
Provider Layer (Wind / Choice / iFinD / Tushare / AkShare)
        ↓
Provider Normalization
        ↓
Trust Evaluation (freshness + completeness + provenance + confidence)
        ↓
Authorization Decision (allowed_use / blocked_use / claim_strength)
        ↓
Context Assembly
        ↓
Agent / LLM Consumption
```

### 1.1 Evidence Boundary — Target vs Present vs Proven

Three distinct levels. A claim at one level does not imply the level to its right.

| Stage | Target Architecture | Statically Present in `main` | Runtime / Production Proven |
|---|---|---|---|
| Provider Layer | Yes | *Not assessed by this README correction* | *Not assessed by this README correction* |
| Provider Normalization | Yes | *Not assessed by this README correction* | *Not assessed by this README correction* |
| Trust Evaluation | Yes | Yes — `_run_trust_gate()` in `research_runtime/evidence_bundle.py`, called unconditionally inside `research_runtime/workflow.py` | **NOT PROVEN** for the production request path — see boundary note below |
| Authorization Decision | Yes | Partial — `allowed_use` / `blocked_fields` emitted by *some* `_qc_*` helpers in `mcp_server.py`, not all | **NOT PROVEN** as a uniform stage |
| Context Assembly | Yes | *Not assessed by this README correction* | *Not assessed by this README correction* |
| Agent / LLM Consumption | Yes | *Not assessed by this README correction* | *Not assessed by this README correction* |

*Not assessed by this README correction* means exactly that: this correction made no finding either way. It is **not** a claim of absence, and **not** a downgrade of any separately evidenced status. Only the two Trust Gate rows were verified in the window that produced this section; their evidence is the boundary note below.

**Boundary note — two different things are called "Trust Gate":**

1. `research_runtime/`'s `_run_trust_gate()` — the staged gate matching the diagram above. On `main`, `research_runtime` has **no non-test importer**; `mcp_server.py` does not import it. Its presence in the tree therefore does **not** establish that the served API executes it.
2. An **inline, per-tool** completeness/freshness check inside `mcp_server.py` (the `_qc_*` helpers), which produces the `_qc` envelope. This is a narrower mechanism, applied unevenly across tools, and is **not** the staged Trust Evaluation → Authorization Decision pipeline drawn above.

Conflating (1) and (2) overstates the runtime. Treat production consumption of the staged gate as **NOT PROVEN** until a runtime evidence receipt exists.

### Key Concepts

| Concept | Purpose |
|---|---|
| **Trust Gate** | Decide whether a piece of evidence is valid and what it may be used for. |
| **Evidence Governance** | Define how provider output becomes trustworthy evidence. |
| **Capability Claim Ladder** | Prevent capability claims from exceeding verified evidence maturity. |
| **Research Runtime** | Execute scoped research workflows with observable evidence trails. |

---

## 2. Repository Structure

```
finance-suite/
├── app/                          # Frontend pages and research interfaces
│   ├── index.html                # Main dashboard
│   ├── stock.html                # Stock analysis interface
│   ├── deep-research.html        # Deep research workspace
│   ├── d13_midday_pulse.html     # Midday market pulse
│   ├── auction.html              # Auction signal view
│   ├── macro.html                # Macro research view
│   └── *.js / *.css              # Supporting assets
│
├── research_runtime/             # Research workflow runtime
│   └── workflow.py               # Orchestration layer
│
├── mcp_server.py                 # MCP server entry point
├── deploy.sh                     # Production deployment script
├── deploy-backend.sh             # Backend deployment helper
├── deploy/                       # Deployment assets
│
├── docs/
│   ├── governance/               # Runtime governance specifications
│   │   ├── EVIDENCE_GOVERNANCE_v1.0.md
│   │   ├── NEWS_EVIDENCE_PROVIDER_BOUNDARY_v0.1.md
│   │   ├── Vera_Capability_Claim_Governance_Framework_v1.md
│   │   └── ...
│   ├── evidence/                 # Evidence manifest and verification artifacts
│   ├── incidents/                # Production incident RCA and learning records
│   └── signal-validation-v0.1/   # Validated signal evidence pack
│
├── data/                         # Runtime generated artifacts
│   └── morning_brief/            # Generated briefs (not source-controlled)
│
├── prompts/                      # Analyst prompts and instructions
│   └── stock-analyst.md
│
├── scripts/                      # Utility scripts
├── .env.example                  # Required environment variables template
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

### Boundary Notice

This repository is the **canonical runtime repository**. It does **not** contain:

- Roadshow or presentation materials
- Competition filing drafts
- External architecture reconnaissance reports
- Personal agent extensions (e.g., LinMeimei-specific skills)

Those assets live in separate repositories or working trees to preserve the runtime boundary.

---

## 3. Local Reproduction

### 3.1 Requirements

- **Python:** 3.11+
- **Node.js:** 18+ (for frontend build tooling, if used)
- **OS:** macOS or Linux recommended
- **Database:** SQLite (default), or PostgreSQL for production-like setups

### 3.2 Installation

```bash
# 1. Clone the canonical runtime repository
git clone https://github.com/jinny280401-glitch/finance-suite.git
cd finance-suite

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# Note: Frontend is static HTML/JS — no npm install needed
```

### 3.3 Configuration Parameters

Copy `.env.example` to `.env` and fill in required values:

```bash
cp .env.example .env
```

#### Required Environment Variables

| Variable | Purpose | Required |
|---|---|---|
| `DATABASE_URL` | Database connection string | Yes |
| `SECRET_KEY` | Application secret key | Yes |
| `OPENAI_API_KEY` | LLM inference (if using OpenAI) | Yes* |
| `TAVILY_API_KEY` | Web search provider | Yes* |

`*` At least one search provider and one LLM provider must be configured.

#### Data Provider Credentials (at least one required)

| Variable | Provider | Notes |
|---|---|---|
| `TUSHARE_TOKEN` | Tushare Pro | A-share fundamentals |
| `AKSHARE_NO_TOKEN` | AkShare | Free, no token required |
| `WIND_API_USER` / `WIND_API_PASSWORD` | Wind | Institutional only |
| `CHOICE_USERNAME` / `CHOICE_PASSWORD` | Choice EmQuant | Institutional only |
| `IFIND_USERNAME` / `IFIND_PASSWORD` | iFinD | Institutional only |
| `JQDATA_USERNAME` / `JQDATA_PASSWORD` | JoinQuant | Factor and valuation data |

#### Optional Environment Variables

| Variable | Purpose |
|---|---|
| `LOG_LEVEL` | Logging verbosity (default: INFO) |
| `MCP_PORT` | MCP server port (default: 8766) |
| `FRONTEND_PORT` | Frontend dev server port |

### 3.4 Runtime Start

```bash
# Start backend / MCP server
python mcp_server.py

# Or start the backend service directly
bash deploy-backend.sh

# Serve frontend (static)
# Open app/index.html in a browser or use a static server
python -m http.server 8080
```

---

## 4. Production Boundary

> **Production capability depends on configured providers.**  
> Missing credentials or providers result in degraded capability, not runtime failure.  
> Research artifacts and governance documents do not imply runtime capability.

### Capability Claim Rule

A capability may be claimed only at the lowest verified maturity level of any required component.

```
UNKNOWN → SHELL_VERIFIED → TRANSPORT_VERIFIED → AUTH_BOUNDARY_VERIFIED
  → RUNTIME_VERIFIED → EVIDENCE_VERIFIED → LIVE_VERIFIED
```

See `docs/governance/Vera_Capability_Claim_Governance_Framework_v1.md` for the full ladder.

### Governance Baseline

The following documents define the trust boundary of this runtime:

- `docs/governance/EVIDENCE_GOVERNANCE_v1.0.md`
- `docs/governance/NEWS_EVIDENCE_PROVIDER_BOUNDARY_v0.1.md`
- `docs/governance/INSTITUTIONAL_PROVIDER_ARCHITECTURE_v0.1.md`
- `docs/governance/Vera_Capability_Claim_Governance_Framework_v1.md`

---

## 5. Trust Gate Workflow — Designed Sequence

The sequence below is the **designed** flow, stated in the specification. It is not a statement that every production request performs these steps; see §1.1.

1. A provider returns raw data.
2. The data is normalized into an **Evidence Object** with provenance, freshness, and completeness.
3. The **Trust Gate** evaluates validity.
4. An **Authorization Decision** scopes allowed uses.
5. Only governed evidence reaches the agent layer.

Step 5 ("only governed evidence reaches the agent layer") is a **design intent, NOT PROVEN** as an enforced production invariant: the staged gate lives in `research_runtime/`, which no production entry point imports on `main`.

For details, see `docs/governance/EVIDENCE_GOVERNANCE_v1.0.md` §1.2.

---

## 6. License

MIT
