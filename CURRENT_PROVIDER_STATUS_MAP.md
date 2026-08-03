# Current Provider Status Map

**Audit date:** 2026-07-30 (Asia/Shanghai)  
**Owner role:** C - Provider Boundary Inventory  
**Input:** CC Repository Handover Audit plus current read-only repository inspection  
**Stage:** Provider Boundary Inventory  
**Mode:** Read-only; no provider, runtime, SDK, credential, or capability change  
**Verdict:** `PROVIDER INVENTORY COMPLETE / INTEGRATION NOT CHANGED`

```text
Repository Handover Audit: CC COMPLETE
Provider Boundary Inventory: COMPLETE
JQData Integration: BLOCKED / NOT VERIFIED
Implementation Authorization: NOT GRANTED
Production Capability: NOT CLAIMED
```

## 1. Status Semantics

The same field names are used for every provider. A positive state applies only to the named layer.

| State | Meaning |
|---|---|
| `VERIFIED` | Direct, scoped evidence exists for this layer. Scope and date are stated. |
| `EXISTS` | An artifact, module specification, or credential-presence receipt exists; validity and live operation are not implied. |
| `UNKNOWN` | No current evidence supports promotion at this layer. |
| `NOT FOUND` | The searched current repository/runtime boundary contains no consumer at the required layer. |
| `CLAIMED` | Repository prose makes a capability claim. It does not mean the claim is valid. |
| `NOT CLAIMED` | This map withholds the capability conclusion. |

Rules:

```text
Credential EXISTS != Credential VERIFIED
SDK EXISTS != Session VERIFIED
Direct MCP tool EXISTS != Runtime Consumer VERIFIED
Runtime Consumer VERIFIED != Evidence Integration VERIFIED
Evidence Integration VERIFIED != Production Capability
```

`JQData` means JoinQuant / 聚宽 (`jqdatasdk`). `Gildata Studio` means 聚源 Studio. They are different provider identities and cannot share a status card.

## 2. Provider Inventory Summary

| Provider | Credential | SDK | Session | Runtime Consumer | Evidence Integration | Capability Claim |
|---|---|---|---|---|---|---|
| AkShare / public Eastmoney | `VERIFIED` - inspected path requires no credential | `EXISTS` | `VERIFIED` - no authenticated session required | `VERIFIED` - scoped website/tool/runtime consumers found | `UNKNOWN` for real end-to-end manifest admission | `NOT CLAIMED` |
| Tushare Pro | `EXISTS` - credential artifact/history receipt; validity unknown | `EXISTS` | `UNKNOWN` | `VERIFIED` - gateway/tool consumers found; historical scoped connection observation | `UNKNOWN` | `NOT CLAIMED` |
| Wind | `UNKNOWN` | `UNKNOWN` in current local venv | `UNKNOWN` | `VERIFIED` - consumer code found, execution not proven | `UNKNOWN` | `NOT CLAIMED` |
| Choice / EmQuantAPI | `UNKNOWN` | `EXISTS` in current local venv | `UNKNOWN` | `NOT FOUND` beyond direct tool/shadow smoke boundary | `UNKNOWN` | `NOT CLAIMED` |
| iFinD | `UNKNOWN` | `UNKNOWN` in current local venv | `UNKNOWN` | `NOT FOUND` beyond direct tool boundary | `UNKNOWN` | `NOT CLAIMED` |
| JQData / JoinQuant (聚宽) | `EXISTS` - 2026-07-22 presence receipt; current validity unknown | `EXISTS` | `UNKNOWN` - historical auth is not a current session | `NOT FOUND` above direct MCP tool; fallback consumer is phantom | `UNKNOWN` | `NOT CLAIMED` |
| Gildata Studio / 聚源 Studio | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `NOT FOUND` in current repository runtime | `UNKNOWN` | `NOT CLAIMED` |
| Cache fallback | `VERIFIED` - no credential required | `EXISTS` - local code path | `UNKNOWN` - not applicable as provider auth | `VERIFIED` - quote gateway fallback found | `UNKNOWN` | `NOT CLAIMED` |
| Mock / local research stub | `VERIFIED` - no credential required | `EXISTS` - local code/fixtures | `UNKNOWN` - not applicable as provider auth | `VERIFIED` - smoke and local workflow consumers found | `UNKNOWN` - passthrough is not real-provider manifest proof | `NOT CLAIMED` |

### 2.1 SDK Observation Scope

The local Finance Suite virtual environment was checked with `importlib.util.find_spec`; packages were not imported, installed, authenticated, or called:

```text
akshare: EXISTS
tushare: EXISTS
jqdatasdk: EXISTS
EmQuantAPI: EXISTS
WindPy: UNKNOWN
iFinDPy: UNKNOWN
```

This is a local developer-environment observation only. It says nothing about production installation or provider authorization.

## 3. Provider Detail Cards

### 3.1 AkShare / Public Eastmoney

```text
Provider: AkShare / public Eastmoney
Credential: VERIFIED - no credential required by inspected client paths
SDK: EXISTS
Session: VERIFIED - no authenticated provider session is required
Runtime Consumer: VERIFIED
Evidence Integration: UNKNOWN
Capability Claim: NOT CLAIMED
```

**Observed artifacts**

- `requirements.txt` declares AkShare, and the local virtual environment resolves the package.
- Direct calls exist in `scripts/stock_data.py`, `scripts/auction_data.py`, `scripts/finance_data_gateway.py`, and multiple MCP tool paths.
- The Research Runtime quote gateway can select AkShare and wrap the result in the Finance Data Response contract.
- The 2026-07-30 Auction incident observed real AkShare/Eastmoney rows in a scoped production process and successful results from a healthy worker.

**Runtime chain**

```text
AkShare / Eastmoney
  -> direct script functions or finance_data_gateway._try_akshare
  -> MCP/API consumer or Research Runtime gateway quote
  -> QC response / EvidenceBundle consumer code
  -> research or page output
```

**Boundary**

The scoped retrieval is real, but global production reliability, every data dimension, and real Evidence Manifest generation/admission are not proven. AkShare must not be described as a verified institutional provider or universal production capability.

### 3.2 Tushare Pro

```text
Provider: Tushare Pro
Credential: EXISTS - artifact/history evidence only; current validity unknown
SDK: EXISTS
Session: UNKNOWN
Runtime Consumer: VERIFIED - scoped consumer paths exist
Evidence Integration: UNKNOWN
Capability Claim: NOT CLAIMED
```

**Observed artifacts**

- `scripts/tushare_data.py` implements connection and data functions.
- `requirements.txt` declares Tushare and the local virtual environment resolves it.
- `scripts/finance_data_gateway.py` and `mcp_server.py:wind_query` call the Tushare wrapper.
- A 2026-07-17 document recorded `tushare: true` from a scoped MCP connection response.
- Secret scans identify a credential candidate in tracked/history material. That proves sensitive residue, not current authorization or validity.

**Runtime chain**

```text
Tushare Pro
  -> scripts/tushare_data.py
  -> finance_data_gateway quote OR wind_query action chain
  -> gateway/MCP QC
  -> Research Runtime only when gateway mode selects the response
```

**Boundary**

No current authenticated session receipt, freshness check, real Evidence Manifest, production consumer receipt, or unexpired capability license was inspected.

### 3.3 Wind

```text
Provider: Wind
Credential: UNKNOWN
SDK: UNKNOWN
Session: UNKNOWN
Runtime Consumer: VERIFIED - code path exists; live execution not proven
Evidence Integration: UNKNOWN
Capability Claim: NOT CLAIMED
```

**Observed artifacts**

- `scripts/wind_data.py`, `scripts/stock_data.py`, `scripts/finance_data_gateway.py`, and `mcp_server.py:wind_query` contain Wind paths.
- The current local virtual environment does not resolve `WindPy`.
- The latest scoped status record inspected (2026-07-17) reported WindPy unavailable, Wind terminal not running, and `wind: false`.

**Runtime chain declared in code**

```text
Wind terminal / WindPy
  -> scripts/wind_data.py
  -> stock_data, finance_data_gateway, or wind_query
  -> gateway/MCP QC
  -> potential Research Runtime consumer
```

**Boundary**

Consumer code existence does not establish SDK, credential, session, evidence retrieval, or research capability.

### 3.4 Choice / EmQuantAPI

```text
Provider: Choice / EmQuantAPI
Credential: UNKNOWN
SDK: EXISTS
Session: UNKNOWN
Runtime Consumer: NOT FOUND beyond direct tool/shadow smoke boundary
Evidence Integration: UNKNOWN
Capability Claim: NOT CLAIMED
```

**Observed artifacts**

- `scripts/emquant_data.py` contains a direct Choice SDK wrapper.
- `mcp_server.py:emquant_query` exposes a direct MCP tool.
- `scripts/choice_provider.py` normalizes already-fetched Choice table payloads but explicitly does not call Choice.
- `scripts/smoke_choice_provider_shadow.py` is smoke/shadow evidence, not a production consumer.
- The current local environment resolves `EmQuantAPI`; no current session was opened.

**Boundary chain**

```text
Choice SDK path
  -> scripts/emquant_data.py
  -> direct emquant_query MCP tool
  -> no verified Research Runtime consumer

Choice shadow path
  -> already-fetched/mock table
  -> scripts/choice_provider.normalize_choice_table
  -> smoke contract only
```

The direct tool and shadow normalizer are two different boundaries. Neither proves current Research Runtime or production capability.

### 3.5 iFinD

```text
Provider: iFinD
Credential: UNKNOWN
SDK: UNKNOWN
Session: UNKNOWN
Runtime Consumer: NOT FOUND beyond direct tool boundary
Evidence Integration: UNKNOWN
Capability Claim: NOT CLAIMED
```

**Observed artifacts**

- `scripts/ifind_data.py` contains SDK and HTTP modes.
- `mcp_server.py:ths_query` exposes a direct MCP tool.
- The local environment does not resolve `iFinDPy`; no HTTP credential or authenticated session was inspected.

**Boundary chain**

```text
iFinD SDK/HTTP
  -> scripts/ifind_data.py
  -> direct ths_query MCP tool
  -> no verified Research Runtime consumer
```

Documentation that calls iFinD integrated exceeds the current evidence boundary.

### 3.6 JQData / JoinQuant (聚宽)

```text
Provider: JQData / JoinQuant (聚宽)
Credential: EXISTS - historical scoped presence receipt; no value inspected
SDK: EXISTS
Session: UNKNOWN
Runtime Consumer: NOT FOUND above direct MCP tool
Evidence Integration: UNKNOWN
Capability Claim: NOT CLAIMED
```

**Observed artifacts and evidence**

- `scripts/jqdata_fetch.py` is a real SDK wrapper.
- `requirements.txt` declares `jqdatasdk`; the current local environment resolves it.
- `mcp_server.py:jqdata_query` correctly imports `scripts.jqdata_fetch`.
- The read-only 2026-07-22 audit recorded credential presence, SDK import, authentication, and historical real rows. It also recorded exhausted quota and stale/permission-limited data. This is historical scoped evidence, not a current session.
- `scripts/finance_data_gateway.py`, `wind_query`, monitoring, and factor paths expect `joinquant_data`, which is absent.
- No frontend, automation, scheduled pipeline, or Research Runtime consumer of `jqdata_query` was found by the prior full-stack audit.

**Runtime boundary map**

```text
Path A - direct tool (historically functional, constrained)
JQData
  -> scripts/jqdata_fetch.py
  -> mcp_server.jqdata_query
  -> human/LLM direct caller only
  -> no verified downstream Research Runtime consumer

Path B - declared fallback (phantom)
JQData
  -> import joinquant_data
  -> module NOT FOUND
  -> silent skip to next provider
```

**Boundary decision**

```text
Credential artifact: EXISTS
SDK artifact: EXISTS
Historical direct MCP retrieval: VERIFIED WITH STALENESS/QUOTA CAVEATS
Current session: UNKNOWN
Fallback adapter: NOT FOUND
Runtime consumer: NOT FOUND
Evidence Manifest binding: UNKNOWN
Provider integration: NOT VERIFIED
Production capability: NOT CLAIMED
```

This inventory does not authorize connection, SDK installation, adapter work, credential use, or JQData design.

### 3.7 Gildata Studio / 聚源 Studio

```text
Provider: Gildata Studio / 聚源 Studio
Credential: UNKNOWN
SDK: UNKNOWN
Session: UNKNOWN
Runtime Consumer: NOT FOUND
Evidence Integration: UNKNOWN
Capability Claim: NOT CLAIMED
```

**Observed artifacts**

- D27 governance and institutional-provider architecture documents describe the required lifecycle and evidence semantics.
- Governance fact-check records refer to a Gildata adapter/smoke/schema artifact set, but those implementation files are absent from the current Finance Suite worktree.
- No current Gildata provider module, route, Research Runtime consumer, or real Evidence Manifest artifact was found.

**Boundary**

This is design/governance state only in the current repository. It must not be merged with JQData/JoinQuant status.

### 3.8 Cache Fallback

```text
Provider: Local cache fallback
Credential: VERIFIED - not required
SDK: EXISTS - repository code
Session: UNKNOWN - not applicable to provider authentication
Runtime Consumer: VERIFIED
Evidence Integration: UNKNOWN
Capability Claim: NOT CLAIMED
```

`scripts/finance_data_gateway.py` includes cache as the final quote fallback and assigns cached/stale freshness. No cache freshness, persistence integrity, or production Evidence Manifest admission was tested here.

### 3.9 Mock / Local Stub

```text
Provider: Mock / local_research_stub
Credential: VERIFIED - not required
SDK: EXISTS - repository code and fixtures
Session: UNKNOWN - not applicable to provider authentication
Runtime Consumer: VERIFIED
Evidence Integration: UNKNOWN
Capability Claim: NOT CLAIMED
```

The Research Runtime can select `local_research_stub`, and smoke suites contain mock/fallback/real-class fixtures. `_run_trust_gate()` passes non-gateway evidence through unchanged. That passthrough is not provider verification and must never be counted as real financial evidence.

## 4. Runtime Consumer Mapping

### 4.1 Actual Code Consumer Matrix

| Provider | Adapter / wrapper | Direct consumer found | Research Runtime consumer | Classification |
|---|---|---|---|---|
| AkShare | Direct calls plus gateway normalization | Website API/MCP tools and scripts | Gateway quote can feed Research Runtime | Real code path; scoped runtime evidence exists |
| Tushare | `scripts/tushare_data.py` | `wind_query`, gateway quote | Indirect through gateway selection | Real code path; current session unknown |
| Wind | `scripts/wind_data.py` | `stock_data`, `wind_query`, gateway | Indirect through gateway selection | Consumer code only; provider unavailable in latest scoped record |
| Choice | `emquant_data.py`; shadow `choice_provider.py` | Direct `emquant_query`; shadow smoke | `NOT FOUND` | Direct tool / smoke boundary only |
| iFinD | `scripts/ifind_data.py` | Direct `ths_query` | `NOT FOUND` | Direct tool boundary only |
| JQData | `scripts/jqdata_fetch.py` | Direct `jqdata_query`; deep stock fallback | `NOT FOUND` for direct tool; gateway import is phantom | Direct MCP boundary, not integrated consumer chain |
| Gildata | Current implementation artifact `NOT FOUND` | `NOT FOUND` | `NOT FOUND` | Governance/design only |
| Cache | Gateway cache helper | Gateway quote | Indirect through gateway | Fallback code path; evidence admission unknown |
| Mock/stub | Fixtures / `local_research_stub` | Smoke/local workflow | Local Research Runtime | Mock/stub only |

### 4.2 Research Output Boundary

```text
Provider wrapper exists
  -> does not prove it was selected

Provider selected by gateway/tool
  -> does not prove its fields passed QC

QC response exists
  -> does not prove Evidence Manifest binding

EvidenceBundle code exists
  -> does not prove a real provider bundle reached a report

Research output rendered
  -> does not prove Production Capability
```

Only AkShare has current scoped production retrieval evidence in this audit context. That observation does not promote the entire provider catalog or the full Research Runtime.

## 5. Capability Claim Findings

### 5.1 Claim Greater Than Evidence

| ID | Location | Claim observed | Evidence boundary | Finding |
|---|---|---|---|---|
| PC-01 | `mcp_server.py` header and server description | Declares `Wind -> Tushare -> JoinQuant -> AkShare` as the multi-source architecture | JoinQuant fallback imports absent `joinquant_data` | `Claim > Evidence` - phantom tier |
| PC-02 | `docs/ifind_emquant_integration.md` | Says Finance Suite has integrated iFinD and Choice | Direct tools/wrappers exist; no current Research Runtime consumer or production receipt | `Claim > Evidence` |
| PC-03 | `docs/source_fallback_12_level_workplan_20260604.md` | Marks Wind/iFinD and Tier-2 sources as connected/integrated | Current Capability Matrix states no provider is Runtime Verified | `Claim > Evidence` |
| PC-04 | Agent repository `skills/finance-suite/SKILL.md` | Describes Wind priority and automatic AkShare fallback | Skill copy is a consumer declaration; live MCP/provider execution is not established by it | `Claim > Evidence` if read as runtime status |
| PC-05 | Agent `docs/architecture-v2.md` | Marks Finance Suite skills complete | Feature/prompt completeness does not establish provider evidence or production runtime | Ambiguous claim requiring scope |
| PC-06 | `docs/joinquant-integration-audit-20260722.md` | Calls direct MCP path real and functional | The same audit explicitly finds no consumer/UI and a phantom fallback | Accept only at direct MCP boundary; reject broad integration reading |

### 5.2 Claims That Respect the Boundary

- `docs/governance/INSTITUTIONAL_PROVIDER_ARCHITECTURE_v0.1.md` explicitly says design only, runtime not established, production capability not claimed.
- `docs/governance/CAPABILITY_CLAIM_MATRIX_v1.md` withholds Runtime Verified and Production Capable status.
- `docs/findings/BF-JQ-01-phantom-provider.md` separates wrapper/credential artifacts from runtime consumer proof.
- Evidence and Trust governance documents explicitly state that smoke, design, transport, and credentials cannot authorize production capability.

### 5.3 Hygiene Verdict

```text
Capability Claim Hygiene: FAIL / CONFLICTING DOCUMENTS
Controlling State: LOWEST EVIDENCED LAYER
Provider Integrated: NOT A PERMITTED GLOBAL CLAIM
Institutional Data Connected: NOT A PERMITTED GLOBAL CLAIM
Production Ready: NOT CLAIMED
```

Legacy prose must not be silently rewritten in this window. It is recorded as Shared Gate input for a future, separately authorized claim-reconciliation decision.

## 6. Shared Gate Provider Card

```text
Provider Inventory: COMPLETE
Provider Code Changes: NONE
Provider Integration: NOT CHANGED
Current Auth/Session Probes: NOT RUN
JQData: NOT VERIFIED
Gildata / 聚源: DESIGN/GOVERNANCE ONLY IN CURRENT REPO
Real Evidence Manifest Admission: UNKNOWN
Research Runtime Provider Capability: NOT CLAIMED
Production Capability: NOT CLAIMED
Implementation Authorization: NOT GRANTED
```

This map answers the Shared Gate questions:

1. **What providers exist?** AkShare, Tushare, Wind, Choice, iFinD, JQData, cache, and mock/stub have code or declared paths; Gildata has governance/design references but no current implementation artifact.
2. **Which have evidence?** AkShare has current scoped production retrieval evidence; JQData has historical direct-MCP evidence with staleness/quota limitations; Tushare has historical scoped connection evidence. These facts remain layer- and date-bound.
3. **Which are only design, script, demo, or smoke?** Gildata is governance/design in the current repo; Choice shadow normalization and mock/stub paths are smoke/design boundaries; iFinD and Choice lack verified Research Runtime consumers.
4. **Which cannot be claimed?** No provider may be globally claimed as integrated, Research Runtime capable, institutional-data connected, production ready, or production capable from the evidence in this map.

No JQData connection, SDK installation, adapter implementation, provider/runtime modification, Capability Matrix edit, credential storage, commit, or deployment was performed.
