# BF-JQ-01: Phantom Provider in Fallback Chain

**Status:** Finding Candidate (awaiting governance window authorization for Engram write)  
**Domain:** finance-suite  
**Date:** 2026-07-20  
**Severity:** HIGH (governance boundary violation, consumer trust risk)

---

## Finding

A provider fallback chain may **appear complete** in design while one tier is **actually unavailable** at runtime, creating a phantom provider that misleads consumers about data source availability.

---

## Case: JoinQuant Integration Audit

### Declared Chain (Design)

```
Wind → Tushare → JoinQuant → AkShare
```

### Actual Runtime Chain

```
Wind → Tushare → [PHANTOM] → AkShare
```

**Reality:**
- `jqdata_fetch.py` wrapper existed (real SDK calls, real credentials)
- Runtime expected `joinquant_data` adapter (wrong module name)
- Import failure silently swallowed by try/except
- JoinQuant tier never executed in any fallback path

**Evidence:**
- `mcp_server.py:671,842,934` — `import joinquant_data` (module not found)
- `finance_data_gateway.py:69` — `import joinquant_data` (module not found)
- `jqdata_fetch.py` — real wrapper, never imported by main chain
- `test_wind_query_optional_joinquant.py:14,34` — explicitly removes `joinquant_data`, asserts success (confirms silent degradation)

---

## Risk

**Consumer Trust Violation:**
- Consumer (LLM or human) sees provider list including JoinQuant
- Actual data never passes through JoinQuant tier
- `_qc.sources` / `fallback_source` do not expose "JoinQuant unavailable"
- Decision made under false assumption about source diversity

**Governance Gap:**
- Provider list ≠ Runtime capability
- Fallback depth claimed (4 tiers) ≠ Fallback depth executed (3 tiers)
- No provenance field surfaces the gap

---

## Root Cause

1. **Name Mismatch:** Real wrapper (`jqdata_fetch`) ≠ Expected adapter (`joinquant_data`)
2. **Silent Import Failure:** `try: import joinquant_data; except ImportError: pass`
3. **No QC Disclosure:** Missing tier not reported in `_qc` metadata
4. **Layer Collapse:** Provider selection logic embedded directly in MCP tool, bypassing Research Runtime / EvidenceBundle contract

---

## Rule (Generalizable)

Fallback providers must satisfy:

```
Provider Name
    =
Runtime Adapter Name
    =
QC Source Declaration
    =
Evidence Boundary
```

**Enforcement:**
- Silent missing imports **must not** create phantom providers
- `_qc.sources` must list **only providers actually called**
- `_qc.unavailable_providers` (or equivalent) must surface tiers skipped due to import/auth/network failure
- Provider tier count in design docs must match runtime execution count

---

## Scope

This pattern applies to **all Finance Suite multi-source providers:**
- Wind / Tushare / JoinQuant / AkShare chain
- MX-DS / IMA / Choice MCP providers
- Any future fallback architecture

---

## JoinQuant Final Status (2026-07-20)

```
╔══════════════════════════════════════╗
║ JoinQuant Integration Status          ║
╠══════════════════════════════════════╣
║ Credential            EXISTS / LOADED ║
║ Local Wrapper         EXISTS / REAL   ║
║ Tracked Provider      NOT PROVEN      ║
║ Runtime Adapter       NOT FOUND       ║
║ QC / Evidence         NOT CONNECTED   ║
║ Production Capability NOT PROVEN      ║
╚══════════════════════════════════════╝

Final: NOT READY
Reason: Integration Boundary Missing
```

---

## Next Valid Window

**Provider Integration Design** — reconcile `jqdata_fetch` ↔ `joinquant_data`, integrate with Research Runtime, add QC contract, expose unavailable tiers in `_qc`.

**Not in scope for current freeze.**

---

## Vera Roadshow Value

This finding demonstrates **what makes Vera's Trust Gate architecture enterprise-grade:**

> Real financial AI barrier is not "how many data sources we connect," but **knowing which sources actually enter the reasoning chain** and surfacing that provenance to decision-makers.

Phantom providers are the exact failure mode that Evidence Manifest + Trust Gate prevent.
