# Finance Suite / Vera — Trusted Research Runtime

**Repository:** `finance-suite`  
**Canonical Branch:** `main`  
**Status:** Runtime Governance Baseline — Research artifacts live elsewhere.

---

## 1. Project Overview

Finance Suite is the runtime repository for **Vera**, a trusted AI research infrastructure for Chinese A-share and macro analysis.

It is not a general-purpose chatbot. It is a bounded research runtime that separates:

- **What the system can prove** (Evidence)
- **What the system can claim** (Capability Claim Governance)
- **What the system may decide** (Trust Gate)

### Core Design

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

# 4. Install frontend dependencies (if applicable)
npm install
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

## 5. Trust Gate Workflow

1. A provider returns raw data.
2. The data is normalized into an **Evidence Object** with provenance, freshness, and completeness.
3. The **Trust Gate** evaluates validity.
4. An **Authorization Decision** scopes allowed uses.
5. Only governed evidence reaches the agent layer.

For details, see `docs/governance/EVIDENCE_GOVERNANCE_v1.0.md` §1.2.

---

## 6. License

MIT
