# Production Incident RCA Status Board — 2026-07-30

**Date**: 2026-07-30
**SOT**: `/Users/Zhuanz/finance-suite/` (working tree at HEAD `cdac1ca`)
**Scope**: Status snapshot only. No code change. No deploy. No architecture change.

---

## INC-01 Auction

| Field | Value |
|---|---|
| Status | **OPEN** · RCA COMPLETE · Remediation Pending |
| RCA card | `docs/incidents/INCIDENT_RCA_CARD_AUCTION_20260730.md` |
| Remediation plan | `docs/incidents/AUCTION_REMEDIATION_PLAN.md` |
| Classification | `EXTERNAL_PROVIDER_DEGRADED` + `ARCHITECTURE_DRIFT` (legacy) |
| Layer 1 cause | AkShare single-source provider with no fallback; QC correctly downgrades `_qc.status=partial` when data degrades |
| Layer 2 cause | Historical dual-path drift between `app/auction_data.py` and `scripts/auction_data.py` (per 2026-07-17 hotfix memory). `app/auction_data.py` no longer exists in current SOT; single canonical `scripts/auction_data.py` retained |
| Next step | Awaiting user authorization for one of: (A) document Tier 1/2/3 fallback contract in SPEC, (B) open D27-B window for W1–W3, (C) defer to separate window |
| Forbidden actions | No new API, no AkShare modification, no new data source addition |

## INC-02 Invoice

| Field | Value |
|---|---|
| Status | **CLOSED** · Reason: `FEATURE_NOT_FOUND_IN_TARGET_SYSTEM` |
| RCA card | `docs/incidents/INCIDENT_RCA_CARD_INVOICE_20260730.md` (retained, not deleted) |
| Classification | `USER_SYMPTOM_MISMATCH` / `FEATURE_NOT_DEPLOYED` |
| Evidence | Exhaustive SOT search: 0 invoice-related files in `app/`, `server_scripts/`, `mcp_server.py`, `scripts/`; 0 commits in git history matching invoice/fapiao/报销/发票; only roadshow marketing material mentions 报销 as a future Skill |
| Next step | Awaiting user symptom source confirmation. Possible resolutions: (1) symptom refers to 报销 Skill (separate Claude Skill, not finance-suite); (2) symptom refers to a different system; (3) symptom refers to a finance-suite feature under a different name |
| Note | RCA card intentionally retained as a `User Symptom → Product Boundary Mismatch` artifact for future audit reference |

---

## Production SOT Context

- **D27 Phase 1**: FROZEN (`docs/governance/D27_INSTITUTIONAL_EVIDENCE_PROVIDER_LAYER_STATUS.md`). Phase A Architecture Design CLOSED 2026-07-30; Phase B Integration Validation BLOCKED by W1/W2/W3.
- **D27-A1 closure**: 2026-07-30 (additive only; original Phase 1 byte-level unchanged).
- **Active governance windows**: OPC material closure (P0, deadline 2026-08-03); Golden Pit Simulation Evidence Collection (P1, separate window); D27-B (P2, blocked).
- **Capability vocabulary audit rule** (effective 2026-07-30): semantic-positive claim detection, not string match. Boundary markers (`≠ Provider Available`, `: NOT CLAIMED`) are allowed; positive assertions without evidence are forbidden.

---

## What this board does NOT do

- Does not authorize any code or deployment change.
- Does not merge INC-01 into D27-B Implementation Window.
- Does not promote INC-02 from `FEATURE_NOT_FOUND_IN_TARGET_SYSTEM` to `BUG`.
- Does not commit or push any file in the SOT.

---

## Sign-off

| Aspect | Statement |
|---|---|
| Scope | Status snapshot only. |
| Source | Two RCA cards + one remediation plan, all written today. |
| Boundary | D27-A1 governance layer respected. Production SOT invariants respected. No implementation entered. |
