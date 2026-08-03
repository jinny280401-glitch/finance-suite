# Production PE Band Frontend Runtime Evidence

**Date:** 2026-07-31 (UTC+8)  
**Executor:** C  
**Scope:** Production Presentation Layer only  
**Target:** `https://www.touziagent.com/app/stock.html?q=600519`  
**Decision:** Production Presentation `PASS`

## Boundary

This receipt verifies that the production-served PE Band JavaScript asset loads
in a real browser and produces a non-trivial canvas from a controlled
presentation payload.

It does not call or verify `/api/analyze`. It does not verify Backend Runtime,
Provider, Research Workflow, report generation, Trust Gate, or any capability
claim.

## 1. Production Asset Receipt

The production-served asset was fetched after the change receipt:

```text
URL:
https://www.touziagent.com/app/pe-band-chart.js

SHA-256:
abc8b856c9a46358db81473e5d94bbd8c277b612815164f60910ec89a6616f19

Export binding:
global.renderPEBandChart = renderPEBandChart;
```

The served fingerprint matches the previously pinned local candidate
fingerprint. This establishes asset-byte alignment for this JavaScript file
only.

## 2. Browser Runtime Evidence

Browser: Playwright Chromium, viewport `1440 x 1000`.

The browser loaded the production stock page with HTTP `200`. A controlled PE
valuation payload was passed directly to the production-loaded
`window.renderPEBandChart` function and its returned HTML was inserted into the
page DOM. No API request was used as a substitute for this presentation check.

### Runtime observations

| Check | Observed result | Status |
|---|---|---|
| `typeof window.renderPEBandChart` | `function` | PASS |
| `.pe-band-chart` DOM node | exists | PASS |
| Child `<canvas>` | exists | PASS |
| Canvas dimensions | `720 x 140` | PASS |
| Non-transparent pixels | `16,628` | PASS |
| Browser `pageerror` | none | PASS |
| Browser console errors | none | PASS |
| `renderPEBand is not defined` | not observed | PASS |
| `renderPEBandChart is not defined` | not observed | PASS |

Rendered text included:

```text
PE 估值分位
当前 PE 20.78
处于近 5 年第 15 百分位
数据基于可用估值源，不构成买入/卖出/持有建议。
```

## 3. Screenshot Evidence

Artifact:

`docs/evidence/PRODUCTION_PE_BAND_RUNTIME_EVIDENCE_20260731.png`

```text
Size:    23,777 bytes
SHA-256: 3ba46c6bd03f273d09b22aabfff600c3351f7760876dd1cc87a0a3fef2805322
```

The screenshot visibly contains the PE band, low/reasonable/high labels,
current-value marker, median marker, percentile, and non-advisory boundary.

## 4. Status Decision

The following status promotion is supported:

```text
Production Presentation:
FAIL -> PASS
```

No other status changes:

```text
Backend Runtime:         VERIFY
Research Runtime:        NOT VERIFIED
Production Capability:   NOT CLAIMED
```

## 5. Governance Receipt

```text
Patch Applied:       acknowledged by prior change receipt
Asset Correct:       PASS for production-served pe-band-chart.js
Runtime Loaded:      PASS in production browser
Feature Rendered:    PASS with controlled Presentation Layer payload
API Verified:        NO / OUT OF SCOPE
Capability Proven:   NO
```

This closes only the Production PE Band Presentation defect evidence hold. It
does not open a Backend, Provider, Research Workflow, or Capability window.
