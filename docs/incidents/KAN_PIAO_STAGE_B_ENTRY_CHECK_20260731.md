# 看票分析 Stage B Entry Check

**Date:** 2026-07-31  
**Window:** Stage A Evidence Hold Point  
**Mode:** READ-ONLY  
**Stage B decision:** `HOLD / ENTRY CONDITION NOT PROVEN`  
**Code or production change:** `NONE`

```text
KAN_PIAO Runtime Stabilization
Stage A: COMPLETE
Instrumentation: RUNTIME ACTIVE
Evidence Hold Point: NOT SATISFIED
Stage B: BLOCKED / NOT AUTHORIZED
Production Fix: NOT PROVEN
```

## 1. Entry Rule

Stage B may open only when both statements are proven:

```text
Stage A instrumentation runtime: ACTIVE
AND
/api/analyze owns a DB checkout for tens or 100+ seconds
```

An instrumented restart, a healthy endpoint, or an old QueuePool timeout does not by itself satisfy the second statement.

## 2. Read-only Production Snapshot

Observed through the production jump host at approximately `2026-07-31 00:45-00:47 +08:00`:

```text
finance-suite.service: active / running
service active since: 2026-07-30 16:48:43 +08:00
health: GET /api/health -> HTTP 200
database.py sha256: d932177900a1f8066ca300e5b4ce13b1dbecba30f50c583930ded4000f32d06e
auth.py sha256: d5151409431e4384be97ceae29ad968e6b4c041e591233342d8c791d7cf3a804
api.py sha256: 2f78db6f78b85e3083efe0582868d5799cf6197075c049c43097888aea127889
```

The live service start time and the pool-event records beginning at `16:48:44` prove that the prepared `database.py` instrumentation was loaded by the restarted workers. The Stage B patches to `auth.py` and `api.py` are not active.

## 3. Instrumentation Evidence

`logs/pool_instrument.log` contains, after the restart:

```text
checkout events: 8
checkin events: 8
held_s > 5 seconds: 0
observed held_s range: 0.003-0.013 seconds
```

All eight pairs occurred at `2026-07-30 16:48:44 +08:00`, during worker startup. They are not accompanied by a `/api/analyze` request.

The instrumentation records `pid`, `tid`, pool counters, action, and `held_s`. It does not record a route or request identifier. Association with `/api/analyze` therefore requires a qualifying request in the service/access log and temporal plus worker correlation. No such post-restart request exists in the inspected interval.

## 4. Fault-time Comparison

### Pre-instrumentation failure interval

The production journal and nginx access log agree on repeated `/api/analyze` failures on `2026-07-30`, including:

| HTTP 500 time (+08:00) | Worker | QueuePool timeout at same time | Instrumented held_s |
|---|---:|---|---|
| 09:35:35 | 2907242 | YES | NOT AVAILABLE |
| 09:36:30 | 2907242 | YES | NOT AVAILABLE |
| 09:36:37 | 2907242 | YES | NOT AVAILABLE |
| 14:43:15 | 2907242 | YES | NOT AVAILABLE |
| 14:43:55 | 2907242 | YES | NOT AVAILABLE |
| 15:28:06 | 2907242 | YES | NOT AVAILABLE |
| 15:29:01 | 2907242 | YES | NOT AVAILABLE |
| 15:31:34 | 2907242 | YES | NOT AVAILABLE |
| 15:33:05 | 2907242 | YES | NOT AVAILABLE |

These failures preceded the `16:48:43` instrumentation restart. They prove that HTTP 500 and QueuePool timeout coincided on the degraded worker, but they cannot prove the duration or route ownership of any checkout because `held_s` did not yet exist in the serving runtime.

### Post-instrumentation interval

From `2026-07-30 16:48:43` through the read-only check:

```text
/api/analyze requests in service journal: 0
QueuePool timeout records: 0
HTTP 500 records: 0
held_s > 5 seconds: 0
```

This is an absence of a qualifying observation, not evidence that `/api/analyze` releases its DB connection quickly.

**No qualifying runtime event does not invalidate the root cause hypothesis; it only means Stage B entry criteria has not been met.**

## 5. Decision

```text
Stage A Runtime Activation: PASS
Instrumentation Active: VERIFIED
Qualifying /api/analyze Observation: NOT FOUND
Long DB Hold Owned By /api/analyze: NOT PROVEN
Case A: NOT ESTABLISHED
Case B: NOT ESTABLISHED
Stage B Entry: HOLD
Stage B Authorization: NOT GRANTED
Production Fix: NOT APPLIED / NOT PROVEN
```

Case A cannot be selected because no instrumented `/api/analyze` request produced a tens/100+ second `held_s`. Case B also cannot be selected: the only short holds are startup operations, so they do not contradict the request-lifetime hypothesis.

## 6. Required Evidence To Re-evaluate

Wait for one approved or naturally occurring authenticated `/api/analyze` request while instrumentation is active. It must be a non-cached, complete analysis path that reaches Provider/Search/LLM; a cache hit can produce only short quota and usage operations and therefore does not test the long-hold hypothesis. Then collect read-only evidence for:

1. request timestamp, completion status, and serving worker PID;
2. checkout/checkin events for the same PID and time window;
3. `held_s` duration;
4. any QueuePool timeout or HTTP 500 in the same window.

Only a correlated long hold permits a Stage B authorization request. No request was generated in this check, and no code, pool configuration, Provider, model, process, or service was changed.

The follow-up classification is:

```text
Case A
  Complete non-cached analysis + held_s in tens/100+ seconds
  -> Long DB Hold CONFIRMED
  -> Stage B may request authorization

Case B
  Complete non-cached analysis proven + held_s < 1 second
  -> Long DB Hold NOT OBSERVED
  -> Re-evaluate the RCA

Case C
  No attributable event, cache path, or incomplete logging
  -> UNABLE TO ATTRIBUTE
  -> Evidence Hold Point remains unsatisfied
```

## 7. Recheck

A second read-only check at `2026-07-31 00:47:57 +08:00` found no state change:

```text
new /api/analyze request: 0
new pool event after worker startup: 0
new QueuePool timeout: 0
new HTTP 500: 0
Stage B decision: HOLD
```

The evidence hold point remains open; silence during an idle interval is not Case B evidence.

A third read-only check at `2026-07-31 00:48:31 +08:00` again found:

```text
/api/analyze since restart: 0
held_s > 5 seconds: 0
pool events after the startup second: 0
QueuePool timeout since restart: 0
```

The entry audit is now waiting on an external runtime event: an authenticated `/api/analyze` request. Further polling without such traffic cannot strengthen either Case A or Case B.
