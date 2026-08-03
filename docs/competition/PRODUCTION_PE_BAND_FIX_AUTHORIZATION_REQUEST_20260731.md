# Production PE Band Fix Authorization Request

**Date:** 2026-07-31  
**Classification:** Production Presentation Layer Defect  
**Authorization status:** REQUESTED / NOT GRANTED  
**Production change:** NOT APPLIED  
**Runtime activation:** NOT APPLICABLE UNTIL AUTHORIZED  

## Authorization Readiness Review

| Pre-authorization requirement | Status | Evidence |
|---|---|---|
| Current production fingerprint recorded | PASS | Production-served SHA-256 is pinned in §4. It must be rechecked before the first production write. |
| Backup and rollback method defined | PASS | A timestamped single-file backup is required by §6; rollback conditions and restoration evidence are defined in §8. |
| Post-change verification defined | PASS | Served/on-disk fingerprints, browser global, console error, and query-routing checks are fixed in §7. |
| Change window identified | **PENDING** | No date, time, named operator, or execution window has been authorized. |
| Rollback triggers defined | PASS | Fingerprint mismatch, missing global function, attributable JavaScript error, or route regression triggers rollback under §8. |

```text
Authorization Readiness: PARTIAL
Blocking Item: CHANGE WINDOW NOT IDENTIFIED
Execution Window: NOT OPEN
Apply Permission: NOT GRANTED
```

This review does not approve the change. A specific production change window
and operator authorization must be recorded before execution can begin.

## 1. Confirmed Defect

The production workbench entry is reachable and routes a stock query from
`/app/index.html` to `/app/stock.html?q=...`. The destination page then loads a
production JavaScript asset with an invalid export binding.

Observed production binding:

```javascript
global.renderPEBandChart = renderPEBand;
```

The file defines `renderPEBandChart`, not `renderPEBand`. Browser observation on
`https://www.touziagent.com/app/stock.html` produced:

```text
ReferenceError: renderPEBand is not defined
```

The local candidate binding is:

```javascript
global.renderPEBandChart = renderPEBandChart;
```

Local browser observation confirmed:

```text
typeof window.renderPEBandChart === "function"
```

## 2. Classification Boundary

```text
Production Presentation:       FAIL
Production Backend:            UNKNOWN
Production Research Runtime:   NOT VERIFIED
Production Capability:         NOT CLAIMED

Local fixed source:            PASS
Local presentation check:      PASS
Production synchronization:    NOT APPLIED
```

This evidence establishes a deterministic presentation-layer defect only. It
does not establish an API, backend, provider, research-runtime, report-pipeline,
or production-capability failure.

## 3. Requested Change

Authorize a one-line correction in the production static asset only.

**Production target:**

```text
/home/ubuntu/finance-suite-web/static/app/pe-band-chart.js
```

**Change:**

```diff
-  global.renderPEBandChart = renderPEBand;
+  global.renderPEBandChart = renderPEBandChart;
```

No other line or file is authorized by this request.

## 4. Fingerprint Baseline

Read-only fingerprints captured before authorization:

| Asset | SHA-256 | State |
|---|---|---|
| Production-served `https://www.touziagent.com/app/pe-band-chart.js` | `462a940acd7387b508034f5c8ed0f9653dcb6d6574142dd5d93510a3e980a626` | Defective baseline |
| Local candidate `/Users/Zhuanz/finance-suite/app/pe-band-chart.js` | `abc8b856c9a46358db81473e5d94bbd8c277b612815164f60910ec89a6616f19` | Locally verified candidate |

Authorization must stop if the production pre-change fingerprint no longer
matches the defective baseline. The candidate fingerprint is an integrity
reference, not permission to copy or deploy the local file wholesale.

## 5. Explicit Exclusions

- No `/api/analyze` or other API change.
- No backend, database, authentication, or service restart.
- No Provider, Research Runtime, Trust Gate, Evidence, or QC change.
- No Auction or Golden Pit change.
- No modification to `stock.html`, `index.html`, or the Demo Source Decision.
- No capability, readiness, or production claim promotion.
- No synchronization or deployment before explicit authorization.

## 6. Authorized-Window Procedure

Only after explicit approval:

1. Re-read and record the production target fingerprint.
2. Stop if it differs from the pinned production baseline.
3. Create a timestamped backup of the single target file.
4. Apply only the one-line export-binding correction.
5. Record the new on-disk and served-asset fingerprints.
6. Perform the narrow browser verification in §7.
7. Roll back immediately if any required check fails.

This request does not authorize a service restart because the target is a
static JavaScript asset. Any cache invalidation or nginx action beyond ordinary
file serving requires separate approval if it becomes necessary.

## 7. Required Post-Fix Verification

The verification scope is intentionally narrow:

1. Record the updated production file fingerprint and the fingerprint of the
   asset served at `/app/pe-band-chart.js`; they must match.
2. In the production browser, verify:

   ```javascript
   typeof window.renderPEBandChart
   ```

   Expected result:

   ```text
   function
   ```

3. Load `/app/stock.html` and confirm that no `ReferenceError` involving
   `renderPEBand` or `renderPEBandChart` occurs.
4. Confirm `/app/index.html` still routes a stock query to
   `/app/stock.html?q=...` with the query preserved.
5. Do not expand the smoke into API, backend, provider, Auction, or report
   pipeline validation.

Passing these checks closes only the production presentation defect. It does
not establish Production Demo Ready, backend readiness, Research Runtime
readiness, or production capability.

## 8. Rollback Trigger

Rollback the single static asset from its timestamped backup if:

- the served fingerprint does not match the post-change on-disk fingerprint;
- `window.renderPEBandChart` is not a function;
- the page emits a new JavaScript error attributable to this change; or
- the workbench-to-stock route no longer preserves the query.

After rollback, record the restored fingerprint and retain the defect as open.

## 9. Decision Requested

```text
Requested authorization:
  ONE-FILE PRODUCTION PRESENTATION FIX

Requested target:
  /home/ubuntu/finance-suite-web/static/app/pe-band-chart.js

Requested semantic change:
  renderPEBand -> renderPEBandChart export binding only

Current decision:
  NOT GRANTED

Production behavior:
  UNCHANGED
```
