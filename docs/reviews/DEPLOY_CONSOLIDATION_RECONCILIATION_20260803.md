# deploy.sh Main Consolidation Reconciliation Note

**Date:** 2026-08-03  
**Repository:** finance-suite  
**Final Main Commit:** b327540  

---

## Context

During selective consolidation from `feature/session-1-validation-outcomes` into `main`, `deploy.sh` required manual review.

The feature branch contained additional deployment-related changes. These changes were **not automatically promoted** into `main`.

---

## Decision

- Retain current `main` production deployment path.
- Do **not** replace `main` `deploy.sh` with the feature branch version.
- Preserve current production entry behavior.
- Require independent validation before introducing additional deployment assets.

---

## Reviewed Candidates

Potential additions observed from `stash@{0}`:

| Candidate | Status | Reason |
|---|---|---|
| `pe-band-chart.js` | **NOT PROMOTED** | No independent runtime validation completed. |
| `workbench-config` | **NOT PROMOTED** | No independent runtime validation completed. |
| `market-temperature-mini` | **NOT PROMOTED** | No independent runtime validation completed. |
| Post-deploy curl verification assets | **NOT PROMOTED** | No independent runtime validation completed. |

---

## Generated Artifacts

The following remain non-source artifacts:

- `data/morning_brief/latest.html`
- `data/morning_brief/latest.json`
- `data/morning_brief/loop_state.json`

**Disposition:** Discard after review.

---

## Final Boundary

**Main branch represents:**

```
Runtime + Governance baseline
```

**Main branch does not include:**

- Unverified deployment assets
- Generated runtime outputs
- Research / demo / competition artifacts
- Personal agent extensions

---

## Audit Trail

- Selective consolidation commit: `58d6fe7`
- Remote main integration merge: `b327540`
- Stash reviewed: `stash@{0}` (`pre-main-consolidation-runtime-assets`)
- Stash disposition: Dropped after review

---

**End of Note**
