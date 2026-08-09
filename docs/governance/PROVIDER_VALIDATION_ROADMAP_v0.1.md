# Provider Validation Roadmap v0.1

**Status:** ADVISORY DRAFT — NOT PROVEN (C Review 2026-08-07)
**Effective date:** 2026-08-07
**Scope:** Institutional provider verification sequence for Phase 1b and beyond
**Anchored to:** [Provider Capability Matrix v0.1](PROVIDER_CAPABILITY_MATRIX_v0.1.md), [Provider Trust Gate Alignment v0.1](PROVIDER_TRUST_GATE_ALIGNMENT_v0.1.md), [Auction Provider Capability Review v0.1](../evidence/AUCTION_PROVIDER_CAPABILITY_REVIEW_v0.1.md)
**Review:** [Provider Capability Matrix v0.1 §11](PROVIDER_CAPABILITY_MATRIX_v0.1.md#11-c-independent-review-2026-08-07) — C Independent Review: finding F6 (unsupported feasibility claims), overall NOT PROVEN

---

## 1. Purpose

Define the priority, preconditions, and acceptance criteria for verifying institutional provider capabilities. This roadmap answers: **which provider should be verified next, in what order, and what must be true before verification can begin.**

**This roadmap does NOT authorize implementation.** It is an input to the Phase 1b planning window. All verification requires a separate Implementation Window with explicit authorization.

**Entry gate (v0.1-amended):** No provider in §4 may enter runtime capability validation until the five Phase 1b Entry Criteria in **§3** all return PASS. The priority tiers in §4 define *order*; §3 defines *admissibility*. Order does not confer admissibility.

---

## 2. Current State Summary

| Provider | Capability Level | Blockers | Closest to Operational? |
|----------|-----------------|----------|------------------------|
| 东方财富 (direct) | **L3** REAL_CONNECTED | — | Already operational |
| AkShare | **L2** RUNTIME_VERIFIED | Completeness (0.43 for market_pulse) | Already operational |
| Tushare | **L1** FIXTURE_VERIFIED | Staleness (T+3), freshness gate needed | Operational but stale |
| **Choice (EmQuantAPI)** | **L0** MOCK_ONLY | SDK not configured | **YES — credentials exist, SDK available** |
| **iFinD (THS)** | **L0** MOCK_ONLY | HTTP mode query=fail | **YES — connect succeeds, data path broken** |
| **Wind** | **L0** MOCK_ONLY | SDK not connected | NO — requires Wind terminal/SDK setup |
| JQData | **L0** MOCK_ONLY | Module unavailable | NO — module missing from environment |
| Barchart | **L0** MOCK_ONLY | Not probed | Unknown |
| factor_scan | **L0** MOCK_ONLY | Not probed | Unknown |
| stock_analysis | **L0** MOCK_ONLY | Symbol resolution broken | Blocked by underlying providers |

**Key insight:** 2 institutional providers (Choice, iFinD) show partial signs of life — Choice has env var references in code, iFinD HTTP connect succeeds. Whether either is close to L2 is UNKNOWN without first verifying credential validity, SDK availability, and the root cause of iFinD's query failure. The gap between "code references an env var" and "live data flows" may be a simple config change or a multi-week infrastructure blocker — current evidence cannot distinguish these cases.

---

## 3. Phase 1b Entry Criteria — Runtime Path Identity Gate

**Amendment date:** 2026-08-09
**Amendment status:** ADVISORY — tightens admissibility. Grants no authorization.
**Trigger:** Trust Gate Validation v0.1 was BLOCKED, then reclassified as RUNTIME PATH MISMATCH — the validated path (`mcp_server.py` stdio MCP) was not the production path (nginx → Flask HTTP). A validation run had already started before anyone established which runtime it was validating. This gate exists so that cannot recur.

### 3.1 The Gate

Runtime capability validation for a provider MAY begin only after **all five** criteria below return `PASS` for **that specific provider**. This is a conjunctive gate: four PASS and one non-PASS is not partial entry — it is `NOT ADMITTED`.

| # | Criterion | Question it answers | PASS requires |
|---|-----------|--------------------|---------------|
| **E-1** | **Provider identity identified** | Which provider, reached over which route, under which credential alias? | Provider name + SDK/API route + credential alias, all three named. A tool name is not a provider identity (`wind_query` ≠ Wind). |
| **E-2** | **Runtime consumer identified** | Who consumes this provider's output downstream? | A named consumer: frontend route / backend route / research runtime / MCP tool / script. "The MCP tool exists" is not a consumer — a tool with no downstream reader consumes nothing. |
| **E-3** | **Production path identified** | Which runtime will the validation actually exercise, and is it the production one? | The invocation path named end to end (entrypoint → transport → handler → provider adapter), plus an explicit statement of whether that path is production, and if not, what differs. |
| **E-4** | **Trust Gate insertion point identified** | Where would the Gate sit on *this* path? | A concrete insertion point on the path named in E-3, referencing the option set in [Trust Gate Enforcement Authorization v0.1 §2](../evidence/TRUST_GATE_ENFORCEMENT_AUTHORIZATION_v0.1.md) (A: tool decorator / B: server middleware / C: context assembly filter), or a declaration that none exists on this path. |
| **E-5** | **Evidence owner identified** | Who owns the evidence this run produces, and who may read verdicts from it? | A named owner per [Owner Assignment Schema v0.1](OWNER_ASSIGNMENT_SCHEMA_v0.1.md). Producer and verdict-reader must be distinguishable; unowned evidence is not admissible input to a closure review. |

### 3.2 Rule

```
E-1 Provider identity identified
  ↓ PASS
E-2 Runtime consumer identified
  ↓ PASS
E-3 Production path identified
  ↓ PASS
E-4 Trust Gate insertion point identified
  ↓ PASS
E-5 Evidence owner identified
  ↓ PASS
  ⇒ Runtime capability validation MAY start

Any criterion not PASS
  ⇒ NOT ADMITTED — validation MUST NOT start
```

**Only after all five prerequisites PASS may runtime capability validation start.**

### 3.3 Verdict values

Each criterion takes exactly one value. There is no partial credit.

| Verdict | Meaning | Consequence |
|---------|---------|-------------|
| `PASS` | Identified, and the identification is checkable by a reader who was not present | Counts toward entry |
| `UNKNOWN` | Not established | Blocks entry. Does not escalate with time or repetition. |
| `MISMATCH` | Established, and it is not the intended target (E-3's failure mode: the reachable path is not the production path) | Blocks entry. Record as a finding, not as a retry. |

`UNKNOWN` and `MISMATCH` are both non-PASS. They differ in what they tell the next window: `UNKNOWN` means go look; `MISMATCH` means the target itself is wrong.

### 3.4 What a non-PASS permits

A provider that fails this gate is not idle — it is scoped down. Consistent with [Runtime Verification Framework v0.2 §7.6](RUNTIME_VERIFICATION_FRAMEWORK_v0.2.md), when any field is unresolved the work may proceed **only as scoped evidence collection, never as capability validation**.

| Permitted under non-PASS | Forbidden under non-PASS |
|-------------------------|--------------------------|
| Reading source to establish E-1 … E-5 | Invoking the provider to see if it works |
| Recording that a path is UNKNOWN or MISMATCH | Recording a capability level |
| Producing a finding that names the missing criterion | Producing a verdict of PASS / FAIL on capability |

A run that starts before the gate clears does not yield weak evidence. It yields evidence about an unidentified runtime, which cannot be attributed to any provider — the Trust Gate Validation v0.1 outcome.

### 3.5 Naming discipline

When a run is stopped by this gate, the correct statement is **"Not admitted — entry criteria not met"**, naming which criterion. It is not "Validation Failed". A blocked entry says nothing about whether the provider works or whether the Gate works; it says the run was never in a position to find out. Reporting it as a capability failure would inject a false negative into the capability record.

### 3.6 Amendment scope

This amendment:

- ✅ Adds an admissibility gate ahead of §4's priority tiers
- ✅ Supersedes the per-provider ad-hoc "Step 0" in §4 (Choice only) with a gate applying to every tier
- ❌ Does not modify the Trust Gate implementation
- ❌ Does not modify any provider capability level or status
- ❌ Does not start, authorize, or schedule any validation run
- ❌ Does not authorize deployment of anything

Provider levels in §2 remain exactly as recorded on the 2026-08-07 baseline.

---

## 4. Verification Priority Tiers

**Admissibility precondition:** every provider below is subject to §3. Tier position (P0…P3) is priority only; it grants no entry.

### P0: Choice (EmQuantAPI) + iFinD (THS)

**Rationale:**
- Both are institutional-tier providers (source_confidence=HIGH under Evidence Governance v1.0 §2.4)
- Both show partial signs of life: Choice has env var references in code; iFinD HTTP connect succeeds
- Bringing either online would be the first institutional provider at L2+ since the system was built
- The current system operates entirely on AkShare + 东方财富 (retail/public tier, source_confidence=LOW/MEDIUM)
- **Caveat:** The gap between "code references exist" and "live data flows" is UNKNOWN. Credential validity, SDK availability, and root cause of iFinD query failure must be verified before any "close to L2" claim.

**Current state per provider:**

#### Choice (EmQuantAPI)

| Checkpoint | Status | Evidence |
|-----------|--------|----------|
| Credential exists | ❓ UNKNOWN | `EM_USERNAME` + `EM_PASSWORD` env vars referenced in code. Env var reference ≠ credential file exists with valid content. |
| SDK installed | ❓ Unknown | EmQuantAPI SDK must be installed from quantapi.eastmoney.com. Installation status not verified. |
| Transport verified | ❌ | Not probed |
| Session established | ❌ | Not probed |
| Data retrieved | ❌ | Not probed |
| Tool endpoint | `emquant_query` (MCP tool #18) | Code path exists |

**Step 0 (infrastructure precondition check):**
1. Verify EmQuantAPI SDK is installable on the target platform (Mac ARM compatibility unknown)
2. Verify credentials exist at the expected paths and are valid (not expired, not revoked)
3. If either fails: document as BLOCKED BY INFRASTRUCTURE, do not proceed to verification steps

**Note (v0.1-amended):** Step 0 checks *infrastructure availability*. It does not substitute for the §3 Entry Criteria, which check *runtime path identity*. Both must clear, and §3 comes first — an installable SDK on an unidentified runtime still yields unattributable evidence.

**Minimum viable verification (if preconditions pass):**
1. Install SDK
2. Load credentials
3. Establish session (emquant_query `action=connect`)
4. Retrieve one data point (emquant_query `action=stock`, code="600519.SH")
5. Validate schema against expected contract
6. Classify capability level (L2 RUNTIME_VERIFIED on first success, with single-probe caveat)

#### iFinD (THS)

| Checkpoint | Status | Evidence |
|-----------|--------|----------|
| Credential exists | ✅ | `THS_USERNAME` + `THS_PASSWORD` or `THS_TOKEN` referenced |
| Transport verified | ⚠️ Partial | HTTP mode `connect` returns success |
| Session established | ❌ | `connect=ok` but `stock` query fails |
| Data retrieved | ❌ | "iFinD 连接失败或查询无结果" |
| Tool endpoint | `ths_query` (MCP tool #19) | Code path exists |

**Minimum viable verification:**
1. Diagnose HTTP mode query failure (connect succeeds, query fails)
2. Try iFinDPy SDK path as alternative to HTTP mode
3. Retrieve one data point (ths_query `action=stock`, code="600519.SH")
4. Validate schema
5. Classify capability level

**Risk:** iFinD HTTP mode may be intermittently broken. If the failure is server-side (iFinD API instability), this may not be fixable from the Finance Suite side. Fallback: document as KNOWN LIMITATION and move to P1.

### P1: Wind

**Rationale:**
- Wind is the declared primary provider in the `wind_query` chain (name carries provenance weight)
- Current `wind_query` tool name is misleading — it says "Wind" but returns Tushare/AkShare data
- Source confidence HIGH (institutional, direct exchange feed)
- The multi-source fallback chain (Wind→Tushare→JQ→AkShare) was designed for Wind as primary

**Current state:**

| Checkpoint | Status | Evidence |
|-----------|--------|----------|
| Credential exists | ❓ Unknown | Wind terminal credentials not verified this session |
| SDK installed | ❓ Unknown | Wind SDK (WindPy) availability not verified |
| Transport verified | ❌ | "Wind SDK not connected" |
| Tool endpoint | `wind_query` (MCP tool #15) | Wind is first in fallback chain |

**Preconditions for P1 verification:**
- Wind SDK (WindPy) installed and importable
- Wind terminal running and accessible
- Credentials loaded and valid
- These are infrastructure prerequisites — they may require Wind account/subscription changes outside the Finance Suite codebase

**Risk:** Wind verification may be blocked by infrastructure/licensing constraints. If Wind SDK cannot be made available, the `wind_query` tool SHOULD be renamed to reflect its actual primary provider (Tushare or AkShare).

### P2: JQData + Tushare Upgrade

#### JQData (JoinQuant)

| Checkpoint | Status |
|-----------|--------|
| Module available | ❌ "No module named 'scripts.jqdata_fetch'" |
| Credential exists | ❓ Unknown |

**Verification path:** Install `jqdatac` SDK, configure credentials, verify module import, probe one data point.

**Value:** JQData is tier-2 (licensed retail, source_confidence=MEDIUM). It provides a middle tier between AkShare (free/public) and Wind/Choice (institutional). Having JQData operational would improve the fallback chain quality.

#### Tushare Upgrade (L1 → L2)

Tushare is L1 (FIXTURE_VERIFIED) because it returns stale T+3 data. This is not a connectivity issue — Tushare is connected and responding. The issue is data freshness.

**Upgrade path:**
1. Verify Tushare Pro tier (tier-2 in provider hierarchy, but free tier returns delayed data)
2. If free tier: document max staleness as a known constraint
3. If Pro tier: verify real-time data availability
4. Set G3 freshness policy per actual data timeliness

**Risk:** Tushare free tier is inherently delayed. Upgrade to Pro tier requires token upgrade on tushare.pro. This may not be a code fix.

### P3: Barchart + factor_scan (Triage)

These providers have never been probed. They are L0 by default. Before investing in verification:

1. **Barchart:** Requires Chrome extension connection. Determine if this dependency is acceptable for production use. If not, mark as EXPERIMENTAL and deprioritize.
2. **factor_scan:** Depends on trading-system → JQ → Wind → Tushare → AkShare chain. Blocked by JQ and Wind being offline. Triage after P0–P2 complete.

---

## 5. Acceptance Criteria Per Tier

These are **exit** criteria. They apply only to a provider that has already been admitted under §3.

### P0 Completion Criteria

- [ ] Choice (EmQuantAPI) at **L2 RUNTIME_VERIFIED** minimum
  - [ ] SDK installed and importable
  - [ ] Session established (connect returns success)
  - [ ] At least one stock data query returns valid, non-stale data
  - [ ] Schema validated against expected contract
  - [ ] Capability level updated in Provider Capability Matrix

- [ ] iFinD (THS) at **L2 RUNTIME_VERIFIED** OR **DOCUMENTED AS BLOCKED**
  - [ ] Root cause of query failure diagnosed
  - [ ] If fixable: data query succeeds → L2
  - [ ] If not fixable: documented as infrastructure limitation, capability level remains L0 with explicit reason

### P1 Completion Criteria

- [ ] Wind at **L2 RUNTIME_VERIFIED** OR **TOOL RENAMED**
  - [ ] If Wind SDK available: data query succeeds → L2
  - [ ] If Wind SDK unavailable: `wind_query` tool renamed to `multi_query` or similar, provenance documented

### P2 Completion Criteria

- [ ] JQData module installed and importable
- [ ] At least one data query succeeds → L2
- [ ] Tushare freshness policy defined (max_age per data type)
- [ ] Tushare capability level re-evaluated (L1→L2 if freshness policy met)

---

## 6. What Each Tier Unlocks

| Tier Complete | Unlocks |
|--------------|---------|
| **P0** | First institutional provider (source_confidence=HIGH) at L2+. The `stock_analysis` multi-source tool may become functional if underlying providers are online. |
| **P0 + P1** | Multi-institutional provider coverage. The `wind_query` fallback chain has a real primary. Source diversity meets governance minimums. |
| **P0 + P1 + P2** | Full provider tier coverage: institutional (Wind/Choice/iFinD, tier-1) + licensed retail (Tushare/JQ, tier-2) + public (AkShare, tier-3). Source confidence can be properly assigned per provider. |

---

## 7. Verification Governance

### 7.1 Rules

1. **Each provider verification is a separate Implementation Window.** Do not verify multiple providers in one window — the evidence chains must be independent.
2. **Verification is read-only until L2 is proven.** Do not modify provider adapters during verification. If the adapter is broken, document the breakage; fix it in a separate window.
3. **Capability claims follow the Chain.** A single successful probe → L2 (RUNTIME_VERIFIED), not L3 (REAL_CONNECTED). L3 requires multi-session reliability evidence.
4. **Negative results are evidence.** "iFinD query failed after 3 attempts" is a valid verification outcome. It prevents false capability claims.
5. **Builder ≠ Declarer for L3+.** A Builder who fixes a provider adapter MAY declare L2 (Succeeded). L3 (Authorized) requires Governance Owner sign-off. L4 (Claimable) is exclusively Governance Owner.
6. **Entry criteria precede probes.** §3 (E-1 … E-5) is evaluated by reading and declaring, not by invoking. A probe run to discover which runtime is reachable is itself a validation start and is therefore out of order.

### 7.2 Evidence Package Per Provider

Every provider verification must produce:

| Artifact | Content |
|----------|---------|
| Probe log | Timestamp, request parameters, response (redacted if contains credentials) |
| Raw response hash | SHA-256 of raw provider response |
| Schema validation | Field mapping verified against expected contract |
| Capability classification | Provider Capability Matrix level assigned with evidence |
| QC report | Status, completeness, freshness, missing dimensions |
| Limitation declaration | What this verification does NOT prove |

### 7.3 No Implementation Authorization

This roadmap is an ADVISORY document. It does NOT authorize:

- ❌ Installing SDKs on production
- ❌ Modifying provider adapters
- ❌ Changing `wind_query` fallback chain
- ❌ Deploying code changes
- ❌ Writing new mock data or fixtures
- ❌ Upgrading any capability claim
- ❌ Starting runtime capability validation — including for a provider that passes §3. Passing the entry gate makes a provider *admissible*; authorization is still a separate act.

All of the above require separate, explicitly authorized Implementation Windows.

---

## 8. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Choice SDK not installable (Mac ARM compatibility) | MEDIUM | Blocks P0 | Verify SDK platform support before attempting installation |
| iFinD HTTP mode fundamentally unstable | MEDIUM | Downgrades iFinD to DOCUMENTED BLOCKED | Try iFinDPy SDK path; if both fail, document as infrastructure limitation |
| Wind SDK requires paid license/subscription | HIGH | Blocks P1, may require tool rename | Verify license status; if unavailable, rename `wind_query` |
| JQData free tier has severe rate limits | MEDIUM | Limits P2 value | Document rate limits; evaluate Pro tier cost |
| Verification effort reveals more broken providers than fixable ones | LOW | Delays institutional provider coverage | Each negative result is valid governance evidence — it prevents false claims |

---

## 9. Timeline (Not Committed)

This is an advisory sequence, not a schedule. Windows open based on authorization, not calendar.

```
Phase 1b Planning Window
  → Review this Roadmap
  → Run §3 Entry Criteria per candidate provider (E-1 … E-5)
  → Admitted set = providers with all five PASS
      (non-PASS → scoped evidence collection only, per §3.4)
  → Authorize P0 Implementation Windows — from the admitted set only
  → P0: Choice Verification Window
  → P0: iFinD Verification Window
  → Re-evaluate: did P0 change the provider landscape?
  → Authorize P1 (if warranted)
  → P1: Wind Verification Window
  → Re-evaluate
  → Authorize P2 (if warranted)
```

---

## 10. Relationship to Trust Gate Implementation

Provider verification (this Roadmap) and Trust Gate MCP→LLM enforcement (Provider Trust Gate Alignment v0.1) are **independent but mutually reinforcing workstreams:**

- **Verification without Gate:** Providers are verified but data still reaches LLM unguarded. Value: accurate capability claims, no enforcement.
- **Gate without Verification:** Gate enforces on all providers but only G2+G3 exist. Value: freshness/completeness enforced, provider classification limited to 3-state enum.
- **Both together:** Providers verified to L2+ → classified in 5-level Matrix → Gate enforces per-level rules → LLM receives only authorized data.

The Roadmap defines WHAT to verify. The Trust Gate Alignment defines HOW to enforce. Both are required for the target state.

---

## 11. Window Declaration

**Window mode:** Governance Roadmap — no code modified, no providers probed, no verification executed.

**Status after C Independent Review (2026-08-07):** ADVISORY DRAFT. NOT PROVEN. Finding F6: Choice/iFinD "one fix away" and "closest to operational" claims not supported by evidence (env var reference ≠ credential valid; connect=ok/query=fail ≠ one fix away). Corrected to acknowledge uncertainty; added Step 0 precondition checks.

---

## 12. Version History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| v0.1 | 2026-08-07 | CC | Initial draft |
| v0.1-reviewed | 2026-08-07 | CC (after C review) | Status downgraded to ADVISORY DRAFT; Choice/iFinD feasibility claims corrected (UNKNOWN gap, not "one fix away"); Step 0 preconditions added; credential status corrected (UNKNOWN not ✅) |
| v0.1-amended | 2026-08-09 | CC | **Phase 1b Entry Criteria Amendment.** Added §3 Runtime Path Identity Gate (E-1 Provider identity / E-2 Runtime consumer / E-3 Production path / E-4 Trust Gate insertion point / E-5 Evidence owner), conjunctive, with PASS/UNKNOWN/MISMATCH verdicts and non-PASS scoping rule. Sections 3–11 renumbered to 4–12. Step 0 scoped to infrastructure only, subordinated to §3. Timeline updated to route through the gate. No Trust Gate implementation change, no provider status change, no validation started, no deployment. |

---

*Governance Design Window — Provider Capability Governance Alignment v0.1*
*Anchored to: Provider Capability Matrix v0.1 + Provider Capability Chain v0.1 + Provider Trust Gate Alignment v0.1*
*Review: C Independent Review 2026-08-07 — NOT PROVEN (F6: unsupported feasibility claims)*
