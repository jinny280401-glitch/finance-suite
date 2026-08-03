# W1: Forward Observation Decision Matrix

**Date:** 2026-08-02 (prep) / 2026-08-03 09:24-09:31 (execution)  
**Window:** W1 Forward Observation (read-only production probe)  
**Status:** ARMED — launchd job loaded, will fire 2026-08-03 Mon 09:24  
**Scope:** Capture what production `/api/intel/market-context` returns inside 09:25:00-09:30:00 **right now**, with full response body + SHA-256 retained.

---

## Purpose

P0 (Historical Production Success Verification) concluded `NOT FOUND` because:
1. nginx access log showed one `2026-07-10T09:28:47` request inside the window, HTTP 200
2. But **response body was never retained** → content UNKNOWN
3. The log retention window started 2026-07-17, structurally after the target period

P0 answered "did it work **before**?" — could not be proven.  
W1 answers "does it work **now**?" — directly observable tomorrow morning.

---

## Execution Plan

**Script:** `/Users/Zhuanz/finance-suite/docs/incidents/w1_forward_probe.sh`  
**Trigger:** launchd one-shot, `~/Library/LaunchAgents/com.zhuanz.w1-auction-forward-probe.plist`  
**Fires:** 2026-08-03 (Mon) 09:24, Asia/Shanghai  
**Runs until:** 09:31:00  
**Sample interval:** every 30 seconds

**Capture window:** 09:24:30 - 09:30:59  
(Includes 09:24:xx as blocked-phase control, and 09:30:xx as post-window control, so the 09:25-09:29 samples can be compared to both boundaries.)

**Each sample:**
- Issues one `GET /api/intel/market-context` (HTTPS, 25s timeout)
- Saves full response body as `response_YYYYMMDDTHHMMSS.json`
- Saves response headers as `headers_YYYYMMDDTHHMMSS.txt`
- Computes SHA-256 of body
- Extracts decision-relevant fields inline:
  - `status`, `_qc.status`, `_qc.source_type`, `_qc.completeness`
  - Any field name containing `gate`, `phase`, `ready`, `block`, `auction`
  - `data_availability` object
- Appends one line per sample to `dimensions.txt`

**Evidence output:** `/Users/Zhuanz/finance-suite/docs/incidents/w1_evidence_20260803/`

---

## Decision Matrix (predetermined criteria)

Apply the following after execution completes. Do NOT interpret results during capture or alter criteria post-facto.

### Scenario A: Non-empty auction content inside 09:25-09:30

**Condition:** At least one response in [09:25:00, 09:30:00) contains:
- `_qc.status` is NOT `failure` or `error`
- `data_availability` or top-level keys show auction-related dimensions (涨停池 / 强势股池 / previous_zt / big_buy / hot_rank / hot_up) present and non-empty

**Verdict:**
```
Production Capability (09:25-09:30):  DEMONSTRATED
Historical Production Success:        NOT PROVEN (unchanged from P0)
Regression:                           NOT APPLICABLE
                                      (cannot regress from an unproven baseline)
```

**Implication:** The production runtime **currently** can return auction content in the target window. The "before worked / now doesn't" framing was incorrect — it may have never worked in production, or the evidence was never retained. The open question becomes a product decision: is the current capability sufficient, or does it need enhancement (dedicated endpoint, persistence, QC tightening)?

**Action:** Close W1. No implementation work authorized. Update RCA classification from "Capability Assumption vs Reality" to "Capability Assumption Mismatch — Local Success ≠ Production Capability."

---

### Scenario B: Empty / partial / degraded inside 09:25-09:30

**Condition:** All responses in [09:25:00, 09:30:00) show:
- `_qc.status = "partial"` or `"failure"`
- Auction dimensions explicitly listed as unavailable / missing / blocked
- OR: `data_availability` marks auction as unavailable
- OR: Response body is empty / error object

**Verdict:**
```
Production Capability (09:25-09:30):  NOT DEMONSTRATED
Historical Production Success:        NOT PROVEN (unchanged)
Regression:                           NOT APPLICABLE
Current Baseline:                     No capability observed
```

**Implication:** Production does not currently return auction content in the target window. This is consistent with P0 findings (no historical evidence either). The problem is not a regression but a **capability gap** — the 09:25-09:30 auction chain was a design intent that was never implemented in production, or was implemented in a non-operational state.

**Action:** Close W1. This establishes the factual baseline ("currently does not work"). The next decision is whether to **build** the capability (W3, requires implementation) or **withdraw** the capability assumption (W0, documentation only). Do NOT proceed to W3 without explicit authorization — W1 finding "does not work now" does not imply "should be fixed."

---

### Scenario C: gate_reason appears inside 09:25-09:30

**Condition:** Any response in [09:25:00, 09:30:00) contains:
- `gate_reason = "auction_not_complete_before_09_25"` or similar
- `auction_results_ready = false`
- `market_phase` indicates blocking

**Verdict:**
```
Production app/auction_data.py:       DIVERGED FROM BRANCH
W2 Inference:                         INVALIDATED
H4 (Gate blocks window):              REOPENED for production path
```

**Implication:** Production gate segmentation differs from the branch implementation read in W2. The branch allows 09:25-09:30 (`auction_complete`), but production blocks it. This would be a **production-specific gate misconfiguration**, not present in the MCP branch.

**Action:** Read production `app/auction_data.py` lines 18-60 (requires SSH or you executing the command). Determine the actual `hhmmss < ???` threshold. If confirmed blocking, this is a **fixable defect** (change one threshold literal), not a capability gap. Authorization for fix would be straightforward, as the gate exists and only needs threshold correction.

---

### Scenario D: No samples captured (technical failure)

**Condition:**
- Zero response files in output directory
- OR: all curl attempts returned `CURL_FAIL`
- OR: launchd job did not fire

**Verdict:**
```
W1 Execution:  FAILED
Result:        INCONCLUSIVE
```

**Action:** Retry on 2026-08-04 (Tue). Check:
1. launchd job loaded: `launchctl list | grep w1-auction`
2. Network reachable: `curl -I https://www.touziagent.com/`
3. Clash interference: same DNS hijack that blocked SSH might block HTTPS

If retry also fails, fall back to manual capture (you run the curl loop while present at 09:25).

---

## Expected Timeline

| Time | Event |
|------|-------|
| 2026-08-02 21:44 | W1 prep complete, launchd armed |
| 2026-08-03 09:24 | Probe script fires (unattended) |
| 2026-08-03 09:31 | Probe script exits |
| 2026-08-03 ~10:00 | Review evidence, apply decision matrix |

---

## Boundaries

**W1 does:**
- Observe production behavior in the target window
- Retain full response bodies (solving P0's missing-content problem)
- Establish current capability baseline

**W1 does NOT:**
- Modify production
- Change code, config, triggers, or providers
- Prove historical success (P0 already closed that as NOT PROVABLE)
- Authorize implementation (that requires separate decision after W1 result)

**W1 output feeds into:**
- Final Auction RCA classification (Scenario A vs B changes the "Capability Assumption" verdict)
- Go/no-go decision for W3 (building the chain) — W3 is NOT auto-authorized
- Possible H4 reopening (Scenario C only)

---

## What happens after W1

W1 is **the last read-only window**. After its result:

- **If Scenario A** → close all Auction windows, file as "capability assumption mismatch, current capability acceptable"
- **If Scenario B** → product decision required: build (W3) or withdraw (W0)
- **If Scenario C** → quick fix window opens (threshold change), separate from W1/W3
- **If Scenario D** → retry once, then manual fallback

In all cases, **implementation is not automatic**. W1 establishes facts; you decide what to build.

---

**Probe script SHA-256 (for evidence chain):**
```
shasum -a 256 /Users/Zhuanz/finance-suite/docs/incidents/w1_forward_probe.sh
```
(will be appended to this doc after tomorrow's run)
