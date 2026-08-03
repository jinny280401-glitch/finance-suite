# Shared Gate Repository Status

**Audit date:** 2026-07-30 (Asia/Shanghai)  
**Owner role:** C - Runtime Boundary / Provider Status  
**Window:** Repository Shared Gate Readiness Audit  
**Mode:** Read-only audit; this document is the only created artifact  
**Shared Gate verdict:** `HOLD / NOT READY FOR HANDOVER`  
**Implementation authorization:** `NOT GRANTED`

```text
Repository Handover Audit: IN PROGRESS
Shared Gate Establishment: COMPLETE FOR CURRENT OBSERVATION
JQData Integration: DESIGN/PROTOTYPE ARTIFACTS EXIST; IMPLEMENTATION NOT VERIFIED
Code / Runtime / Provider Changes: PROHIBITED
```

## 1. Repository Identity

Two repositories have different ownership boundaries. They must not be treated as one Git baseline.

### 1.1 Website / Finance Runtime Repository

| Field | Observed state |
|---|---|
| GitHub | `https://github.com/jinny280401-glitch/finance-suite` |
| Local path | `/Users/Zhuanz/finance-suite` |
| Role | Website frontend, Finance Suite APIs/tools, data-provider scripts, Research Runtime/governance assets |
| Current branch | `feature/session-1-validation-outcomes` |
| Local HEAD | `cdac1ca7333ebfa80313f00690153961a9a0b75a0` |
| Tracking branch | `origin/feature/session-1-validation-outcomes` at `7eddfc9b40499f883ed26c90c2c4822a4e4a32d7` |
| Ahead / behind | 7 / 0 |
| Remote default | `origin/main` at locally observed `9e3906534cde94a3ab91941ae1fc8969f304d67f` |
| Remote | `origin` fetch/push points to the GitHub URL above |
| Tracked modifications | 17 files; 613 insertions and 322 deletions in unstaged diff |
| Untracked status entries | 34 top-level/file entries at audit time |
| Working tree | `DIRTY` |
| Baseline status | `NOT FROZEN` |

The seven local-only commits mix a provider finding, roadshow assets, frontend work, competition material, and memory/governance updates. They are not an approved handover unit merely because they share a branch.

The dirty tree also mixes runtime-facing pages, generated morning-brief state, deployment script changes, roadshow assets, governance records, incident records, and generated media. Asset ownership and inclusion decisions are not established.

### 1.2 Agent Repository

| Field | Observed state |
|---|---|
| GitHub | `https://github.com/jinny280401-glitch/Linmeimei-Agent` |
| Local path | `/Users/Zhuanz/Documents/New project 6/Linmeimei-Agent` |
| Role | Agent/channel service, harness, skill routing, persona/workspace, and a copied Finance Suite skill consumer |
| Current branch | `main` |
| Local/remote HEAD | `eb280b288b1e47cc0c5a8e98b08d876bc2e49da8` |
| Ahead / behind | 0 / 0 |
| Remote | `origin` fetch/push points to the GitHub URL above |
| Index state | 71 tracked files staged for deletion |
| Worktree state | 21 untracked status entries, including replacement directory trees/files |
| Working tree | `DIRTY / INDEX-WORKTREE SPLIT` |
| Baseline status | `NOT SAFE TO COMMIT OR HAND OVER` |

The Agent repository has a critical index condition: tracked content is staged as deleted while similarly named working-tree content is untracked. This is not evidence that the files should be deleted or replaced. No reset, add, restore, or commit was performed.

### 1.3 Shared-Gate Repository Rule

```text
finance-suite repository
  != Linmeimei-Agent repository

Finance provider/runtime implementation
  != Agent skill copy

Agent prompt declares a provider
  != Website runtime executes that provider
```

No repository is handover-ready while its baseline is dirty or ambiguous. The Agent repository's staged-deletion state is an immediate Git governance blocker; the Website repository's mixed local commits and untracked assets are a baseline blocker.

## 2. Runtime Boundary

### 2.1 Website / Finance Suite Observed Boundary

```text
Frontend
  app/*.html and JavaScript in repository
  production has also been observed serving static/app/*
    ->
API / Tool Entry
  server_scripts/*, mcp_server.py in repository
  production has also been observed executing app/routers/*
    ->
Runtime
  scripts/finance_data_gateway.py (quote-only v0)
  research_runtime/workflow.py + evidence_bundle.py
    ->
Provider code
  scripts/wind_data.py
  scripts/tushare_data.py
  scripts/jqdata_fetch.py
  scripts/ifind_data.py
  scripts/emquant_data.py
  scripts/choice_provider.py
  direct AkShare calls across scripts/tools
    ->
Data sources
  Wind / Tushare / JQData(JoinQuant) / iFinD / Choice / AkShare
```

**Boundary status:** `OBSERVED IN CODE`, not a single verified production chain.

The repository and observed production layout diverge. The Auction incident proved that production used `/home/ubuntu/finance-suite-web/app/routers/*`, `app/auction_data.py`, and `static/app/*`, while the Git repository carries `server_scripts/*`, `scripts/auction_data.py`, and `app/*`. Therefore the canonical production runtime path remains `UNKNOWN` until deployment hashes map to a reviewed commit.

### 2.2 Gateway and Trust Boundary

The code graph establishes this current Research Runtime path:

```text
run_research_workflow
  -> _select_provider
  -> _retrieve_evidence
       -> finance_data_gateway.get_finance_data("quote")
       OR local_research_stub
  -> _run_trust_gate
       -> build_evidence_bundle for gateway_* evidence
  -> downstream research artifacts
```

Observed limitations:

- `finance_data_gateway.py` is quote-only v0.
- Its declared provider chain includes `joinquant`, but `_try_joinquant()` imports absent module `joinquant_data`; the real wrapper is named `scripts/jqdata_fetch.py`.
- `local_research_stub` is a smoke/stub source, not real provider evidence.
- Non-gateway evidence is passed through by `_run_trust_gate`; passthrough must not be interpreted as provider verification.
- Evidence Bundle and Trust Gate consumer code exists. End-to-end production consumption of institutional provider evidence is not established.

### 2.3 Agent Repository Observed Boundary

```text
Channel request (Feishu / WeCom / other bridge)
  -> app/routers/*
  -> app/harness or app/services/agent
  -> skill router / prompt selection
  -> skills/finance-suite copy
  -> external MCP/tool execution (declared)
```

The Agent repository contains routing, service, and Finance Suite skill code, but its current Git index cannot reproduce the working tree. No live deployment, MCP binding, real provider retrieval, Evidence Manifest admission, or end-user runtime chain was tested in this audit. Its runtime status is `UNKNOWN`; its code shape is `OBSERVED`.

### 2.4 Boundary Status Legend

| Label | Meaning in this Shared Gate |
|---|---|
| `VERIFIED` | A scoped assertion has reproducible runtime evidence and a named verifier |
| `OBSERVED` | Code, document, process, response, or file state was directly inspected |
| `UNKNOWN` | Required runtime evidence was not collected or cannot be bound to a reproducible baseline |
| `NOT CLAIMED` | This gate explicitly withholds a capability conclusion |

## 3. Provider Status

Provider status is recorded per layer. A wrapper, SDK declaration, credential artifact, or successful historical smoke does not establish Research Capability.

| Provider | Code/design observation | Current runtime evidence | Shared Gate state | Capability claim |
|---|---|---|---|---|
| AkShare / public Eastmoney | Direct calls exist across website runtime; package declared | Real rows were observed in the scoped 2026-07-30 Auction diagnosis, but one worker degraded independently | `OBSERVED` for scoped retrieval; global runtime `UNKNOWN` | `NOT CLAIMED` |
| Tushare | `scripts/tushare_data.py`, requirements entry, gateway/tool references exist | No current authenticated session or end-to-end Evidence Manifest inspected; credential-history risk exists | `UNKNOWN` | `NOT CLAIMED` |
| Wind | Wrapper and route logic exist; requires local Wind terminal/client | No current session or production consumer receipt inspected | `UNKNOWN` | `NOT CLAIMED` |
| JQData / JoinQuant (聚宽) | `scripts/jqdata_fetch.py`, `jqdatasdk` requirement, direct `jqdata_query` MCP tool, historical audit/design exist | Gateway and fallback code expect missing `joinquant_data`; no Research Runtime consumer proof | `DESIGN/PROTOTYPE OBSERVED`; integration `NOT VERIFIED` | `NOT CLAIMED` |
| Choice / EmQuantAPI | Direct wrapper/tool and a shadow normalizer exist | No current production session, manifest admission, or consumer receipt inspected | `OBSERVED IN CODE`; runtime `UNKNOWN` | `NOT CLAIMED` |
| iFinD | Direct wrapper/tool design exists | No current SDK/session/evidence/consumer receipt inspected | `OBSERVED IN CODE`; runtime `UNKNOWN` | `NOT CLAIMED` |
| Gildata Studio / 聚源 Studio | D27 institutional-provider architecture and governance records exist | Adapter/smoke/schema artifacts referenced by governance records are absent from this repository worktree; no real evidence retrieval is established | `DESIGN/GOVERNANCE ONLY` in current repo | `NOT CLAIMED` |
| Cache | Gateway fallback code exists | Cache freshness and production admission not audited here | `OBSERVED IN CODE`; runtime `UNKNOWN` | `NOT CLAIMED` |
| Mock / local stub | Smoke fixtures and `local_research_stub` exist | Synthetic/local behavior only | `MOCK/STUB` | Real-provider capability explicitly prohibited |

### 3.1 Identity Guard

`JQData` is the JoinQuant/聚宽 SDK (`jqdatasdk`). `Gildata Studio` is 聚源 Studio. They are different provider identities and must not share a credential, adapter state, or capability claim. The phrase `JQData / 聚源` is ambiguous and must be resolved before any implementation authorization card is issued.

### 3.2 Required JQData State Card

```text
Credential: UNKNOWN
SDK: UNKNOWN at active handover runtime
Session: UNKNOWN
Direct Wrapper: OBSERVED
Direct MCP Tool: OBSERVED
Gateway Adapter: NOT FOUND (phantom module boundary)
Evidence Manifest Binding: NOT VERIFIED
Research Runtime Consumer: NOT VERIFIED
Provider Integration: NOT VERIFIED
Capability: NOT CLAIMED
```

The dependency line `jqdatasdk>=1.9.8` proves only a declared dependency. No SDK installation, authentication, query, production-data run, or credential inspection was performed in this window.

## 4. Capability Status

### 4.1 Claim-Hygiene Findings

The repository contains both careful governance language and broader legacy claims. The coexistence is a Shared Gate conflict.

| Location | Observed statement pattern | Evidence conflict | Gate treatment |
|---|---|---|---|
| `mcp_server.py` header/tool description | Declares `Wind -> Tushare -> JoinQuant -> AkShare` multi-source architecture | JoinQuant fallback imports missing `joinquant_data`; historical finding classifies it as phantom | Treat as design/intended chain, not executed chain |
| `docs/ifind_emquant_integration.md` | Says Finance Suite has integrated iFinD and Choice | Current session, manifest, consumer, and production receipts were not inspected | Overbroad; capability withheld |
| `docs/source_fallback_12_level_workplan_20260604.md` | Marks Wind/iFinD and Tier-2 sources as connected/integrated | Governance matrix says no provider is Runtime Verified; current baseline is not reproducible | Historical/design claim only |
| Agent `skills/finance-suite/SKILL.md` | States Wind priority and automatic AkShare degradation | Skill text is a consumer declaration; it does not prove live MCP/provider behavior | Documentation claim only |
| Agent `docs/architecture-v2.md` | Marks five Finance Suite skills complete | Skill completeness does not establish provider evidence or production runtime | Feature/design status only |
| Website `README.md` | Lists AkShare-backed user features and online site | Does not claim Production Ready, but lacks current runtime/evidence qualifications | Product description; not provider verification |

**Capability Claim Hygiene:** `FAIL / CONFLICTING SOURCES`.

The normative governance documents correctly state:

```text
Credential Exists != Credential Loaded
Provider Connected != Evidence Retrieved
Evidence Retrieved != Research Runtime Consumer Proven
Design != Production Capability
PoC != Production
```

Until legacy claims are reconciled in an authorized governance window, the Shared Gate uses the lowest evidenced state, not the strongest prose statement.

### 4.2 Current Capability Card

```text
Repository Baseline: NOT FROZEN
Canonical Production Runtime: UNKNOWN
Finance Data Gateway: OBSERVED / QUOTE-ONLY V0
Trust Gate Consumer Logic: OBSERVED IN CODE
Evidence Manifest Design: DEFINED
Institutional Provider Runtime: NOT VERIFIED
JQData Integration: NOT VERIFIED
Agent-to-Provider End-to-End Runtime: UNKNOWN
Production Capability: NOT CLAIMED
Implementation Authorization: NOT GRANTED
```

## 5. Security Status

This section records findings only. No credential value is reproduced, opened for handoff, rotated, deleted, or changed.

### 5.1 Website Repository

| Check | State | Evidence |
|---|---|---|
| Local `.env` | `FOUND` | `.env` exists and is ignored; contents were not read in this audit |
| Local `.env.save` | `FOUND` | ignored backup-style credential file exists; contents were not read |
| Tracked `.env.example` | `FOUND` | example file is tracked; safety requires value-level review before sharing |
| Tracked account material | `FOUND` | `docs/internal/reference_finance_suite_accounts.md`, auth/import documentation exist |
| Secret scan | `FOUND / FAIL` | 2026-07-29 gitleaks report recorded four history findings; two were reachable from `origin/main` |
| Rotation/revocation proof | `UNKNOWN` | no issuer-backed rotation receipt inspected |
| Public-share readiness | `FAIL` | prior repository share gate remains hard blocked |

### 5.2 Agent Repository

| Check | State | Evidence |
|---|---|---|
| Local `.env` | `FOUND` | contents were not manually read; gitleaks scanned with redaction |
| Git history scan | `FOUND / FAIL` | current redacted gitleaks run scanned 19 commits and reported 15 findings |
| Finding classes | `FOUND` | history includes a WeCom secret candidate, API-token examples, and a Tushare token candidate; values intentionally omitted |
| Rotation/revocation proof | `UNKNOWN` | no issuer-backed receipt inspected |
| Index safety | `FAIL` | 71 staged deletions plus untracked replacement content create accidental-loss/commit risk |

### 5.3 Security Verdict

```text
Sensitive Local Files: FOUND
Historical Secret Candidates: FOUND
Credential Validity: UNKNOWN
Rotation Status: UNKNOWN
History Remediation Authorization: NOT GRANTED
Credential Handover: PROHIBITED
Repository Share Security: FAIL
```

A `.gitignore` rule prevents future ordinary tracking but does not remove a value from Git history. Staged deletion similarly does not remediate public history.

## 6. Current Restrictions

The Shared Gate is fail-closed. Until a separate authorization card names scope, owner, baseline, and validation evidence:

- **Do not** connect JQData or Gildata.
- **Do not** write or rename a provider adapter.
- **Do not** modify provider routes, fallback chains, Research Runtime, Trust Gate, Evidence Manifest, or Capability Matrix.
- **Do not** install SDKs or inspect/share plaintext credentials.
- **Do not** change pool, runtime, deployment, or production configuration.
- **Do not** merge, rebase, push, commit, stage, unstage, restore, or clean either repository.
- **Do not** treat the Agent skill copy as the canonical Finance Suite runtime.
- **Do not** treat a direct MCP tool, wrapper, smoke, or credential as Provider Integration.
- **Do not** invite a handover owner or Builder under the assumption that either worktree is reproducible.

### 6.1 Required Next Gates

| Gate | Required evidence | Current state |
|---|---|---|
| Repository ownership | Named owner for each repository and asset class | `UNKNOWN` |
| Website baseline | Approved commit/file set; dirty/untracked disposition | `NOT FROZEN` |
| Agent baseline | Owner decision on 71 staged deletions and untracked replacements | `HARD BLOCKED` |
| Deployment identity | Production hashes mapped to an approved website commit | `UNKNOWN` |
| Claim reconciliation | Legacy provider claims aligned to Capability Matrix and runtime evidence | `PENDING` |
| Security remediation | Issuer review, rotation/revocation receipts, authorized history decision, clean rescan | `FAIL / PENDING AUTHORIZATION` |
| Implementation authorization | Provider identity, change scope, consumer, validation gate | `NOT GRANTED` |

### 6.2 Shared Gate Handover Card

```text
Website Repository Identity: OBSERVED
Agent Repository Identity: OBSERVED
Website Worktree: DIRTY
Agent Worktree: DIRTY / INDEX-WORKTREE SPLIT
Runtime Boundary: OBSERVED IN CODE / PRODUCTION CANONICAL UNKNOWN
Provider Status Inventory: COMPLETE FOR CURRENT OBSERVATION
Capability Claim Hygiene: FAIL / CONFLICTING SOURCES
Security Status: FAIL / FINDINGS PRESENT
JQData Integration: NOT VERIFIED
Production Capability: NOT CLAIMED
Shared Gate: HOLD
Handover Ready: NO
```

This document establishes a common fact boundary. It does not authorize repository cleanup, credential remediation, provider work, runtime changes, or implementation.
