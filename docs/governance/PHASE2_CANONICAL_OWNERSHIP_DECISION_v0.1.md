# Phase 2 Canonical Ownership Decision — v0.1

**Decision authority:** G
**Decision date:** 2026-08-20

---

## Relationship to Phase 4 Production Receipt

`PHASE4_PRODUCTION_RECEIPT_v0.1.md` proves **sampled production/file identity only**. It MUST NOT be used to infer canonical ownership. Its historical statement that Phase 2 was paused at receipt time (`Phase 2 继续暂停`) remains valid **as a statement about that receipt's own scope and authority** — the receipt itself never adjudicated ownership, before or after this decision.

Phase 2 ownership was **subsequently** adjudicated by G as a separate governance decision, distinct from and later than the receipt's "Phase 2 paused" state. Production identity evidence (Phase 4) and ownership authority (Phase 2) are two separate evidence layers and remain separate.

---

## Frozen Phase 2 Ownership Matrix

| # | Item | Canonical Owner |
|---|---|---|
| 1 | `mcp_server.py` | FRONTEND |
| 2 | `index.html` | FRONTEND |
| 3 | `app/auction_data.py` | BACKEND |
| 4 | `app/stock_data.py` | BACKEND |
| 5 | `deploy-backend.sh` | SPLIT / NAMING COLLISION / FINAL DISPOSITION PENDING |

**Denominator:**
- 5/5 REVIEWED
- 4/5 canonical ownership DECIDED
- 1/5 SPLIT

`scripts/auction_data.py` = historical orphan / disposition pending; **not part of** the five-item ownership denominator above.

---

## Boundaries

This decision does NOT:
- upgrade production runtime-loaded-code proof
- authorize convergence of backend `mcp_server.py`
- authorize deletion / rename / move / cleanup
- resolve `deploy-backend.sh` final disposition

Production identity evidence and ownership authority remain separate. The Phase 4 receipt must not be rewritten to pretend it made this ownership decision.

---

**Authority:** G (Phase 2 governance decision, 2026-08-20)
