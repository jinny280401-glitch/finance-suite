# AUCTION_RUNTIME_ERROR_RCA — Unexpected token '<' Investigation

**Review Mode:** READ-ONLY / Evidence First / No Fix  
**Investigation Date:** 2026-08-03 (Asia/Shanghai)  
**Scope:** New runtime incident only. This report does not reuse the prior Auction P0 Regression conclusion.

---

## 1. Incident Summary

**时间：** 2026-08-03；原始报错的精确发生时间未提供，无法从现有证据恢复。  
**错误：** Browser reported `Unexpected token '<'` while the auction page attempted to parse an API response as JSON.  
**影响：** 集合竞价分析结果未能在前端完成解析与展示。影响范围、持续时间及受影响用户数均无证据。

### Claim

某一层向集合竞价前端返回了 HTML，而前端按 JSON 解析。

### Evidence

- 任务卡记录了 `Unexpected token '<'`，并描述 response 以 `<!DOCTYPE html>` 开头。
- 生产页面的非黄金坑流程向同源 `/api/analyze` 发起请求，并直接执行 `resp.json()`。

### Evidence Gap

- 未提供事故时刻的 HAR、Network 面板导出、原始 response headers 或完整 response body。
- 未提供事故请求的 request ID / trace ID。
- 未提供与事故时间对应的 nginx access/error log、应用 access/exception log 或 traceback。
- 因此，任务卡中的 HTML 片段属于症状描述，不是可关联到某一服务层的保全网络证据。

### Risk

若仅依据首字符 `<` 推断具体根因，可能把认证页、404 fallback、网关错误页或后端异常页错误归因给 provider/runtime。

### Capability Verdict

**NOT PROVEN** — HTML 返回层未被证据链证明。

---

## 2. Observed Symptom

### Incident Symptom

```text
Unexpected token '<'
```

任务卡描述的实际 response 前缀：

```html
<!DOCTYPE html>
<html>
...
```

该症状只证明“JSON parser 收到以 `<` 开头的内容”，不能单独证明 HTML 由 API Route、Backend、Gateway、认证跳转或静态 fallback 中的哪一层产生。

### Frontend Request Evidence

| Field | Evidence |
|---|---|
| Request URL | Same-origin `/api/analyze` |
| HTTP Method | `POST` |
| Request Payload | `{"skill_type":"auction","query":"<用户输入或当日日期>"}` |
| Request headers | `Content-Type: application/json` |
| Credentials mode | `include` |
| Parser | Production page executes `resp.json()` before checking `resp.ok` |
| Incident status code | **UNKNOWN — not captured** |
| Incident Content-Type | **UNKNOWN — not captured** |

### Current Reproduction Evidence — Not the Original Incident Packet

At 2026-08-03 10:09:12 Asia/Shanghai, a read-only unauthenticated POST to the production `/api/analyze` route returned:

| Field | Observed |
|---|---|
| HTTP status | `401` |
| Content-Type | `application/json` |
| Redirect | None observed |
| Body contract | JSON error object |

At approximately 2026-08-03 10:12 Asia/Shanghai, the production page was exercised through the existing browser session. The frontend handled the current `401` response and navigated to the login page. This proves the current unauthenticated path can return JSON and be handled; it does **not** reproduce or disprove the earlier HTML response.

The production auction HTML itself returned `200 text/html`, as expected for the page document. This page response must not be confused with the `/api/analyze` API response.

---

## 3. Evidence Timeline

### Incident Timeline

```text
Time UNKNOWN
Frontend request sent to POST /api/analyze

Time UNKNOWN
Whether API route received the request is not proven

Time UNKNOWN
An HTML response was reportedly received; status, Content-Type, redirect chain,
server identity, request ID and full body were not preserved

Time UNKNOWN
Frontend JSON parse failed with Unexpected token '<'
```

### Independent Verification Timeline

```text
10:09:11
Production auction page requested; page document returned 200 text/html

10:09:12
Unauthenticated POST /api/analyze sent with auction JSON payload

10:09:12
Gateway-facing response returned 401 application/json with no observed redirect

10:12:24
Browser exercise reached the login page after the current authentication path
```

The independent verification occurred after the incident and is not the original incident packet.

---

## 4. Investigation Chain Verdict

| Layer | Claim | Evidence | Evidence Gap | Risk | Capability Verdict |
|---|---|---|---|---|---|
| Browser | JSON parsing failed on `<` | Task card records the error | No console export or HAR | Error text may be detached from exact request | PARTIAL |
| Frontend `fetch()` | Auction uses `POST /api/analyze` with JSON payload | Production HTML contains the fetch and `resp.json()` path | Exact deployed asset at incident time is not cryptographically preserved | Frontend parser masks status/body provenance | PROVEN |
| API Route | `/api/analyze` currently exists | Current request returns structured `401` JSON rather than route-level HTML | Incident request was not correlated to access logs | Current route health cannot establish incident behavior | PARTIAL |
| Gateway / Proxy | nginx is present in the current response chain | Current responses include nginx-facing headers | No incident access/error log or upstream status fields | Gateway fallback or upstream interception remains possible | NOT PROVEN |
| Backend Controller | Current unauthenticated request produces JSON contract | JSON `401` observed | No authenticated incident response, controller log, exception log or traceback | Backend exception page remains possible | NOT PROVEN |
| Provider / Runtime | No provider execution evidence exists for the failed request | None | No provider-start/provider-end markers or trace | Provider could be wrongly blamed for a pre-provider failure | NOT PROVEN |
| Response Contract | Incident response was reportedly non-JSON | Parser symptom and task-card HTML prefix | No original status, Content-Type or body artifact | Contract breach is observed only at symptom level | PARTIAL |

### Runtime Position

The failure position cannot be established as:

- before provider,
- during provider,
- after provider, or
- response serialization.

There is no evidence that the incident reached provider execution. AkShare, Wind, or any other provider must not be assigned as root cause.

### Root Cause Classification

**F. UNKNOWN (evidence insufficient)**

No available artifact identifies which layer returned the HTML. Categories A–E remain hypotheses, not findings.

---

## 5. Fix Authorization

**Fix Authorized:** NO  
**Owner:** Backend — evidence collection owner only; fix ownership remains unassigned until the returning layer is identified.  
**Reason:** The incident response packet and correlated server logs are missing. Authorizing a frontend, backend, infra, or provider fix now would be diagnosis-by-assumption and could modify the wrong layer.

### Required Next Evidence — No Fix

1. Capture one failing browser Network entry for `/api/analyze`: request URL, method, payload, status, Content-Type, redirect chain and raw response prefix/body.
2. Record request ID / trace ID and exact Asia/Shanghai timestamp.
3. Correlate that ID and timestamp across nginx access/error logs and backend access/exception logs.
4. Confirm route match, upstream status, controller entry, provider-start marker and serialization completion in order.
5. Reclassify only after the first layer that changes the contract from JSON to HTML is evidenced.

---

## Final Verdict

```text
AUCTION_RUNTIME_ERROR_RCA
Root Cause:
F. UNKNOWN (evidence insufficient) — the layer returning HTML is not identified
Evidence Confidence:
LOW
Fix Owner:
Backend evidence collection owner; implementation owner UNKNOWN
Regression Relation:
UNKNOWN
Next Action:
Capture the next failing /api/analyze network packet and correlate it to nginx and backend logs by exact timestamp/request ID; do not fix or change providers before attribution.
```

注意：本次 `Unexpected token '<'` 是新的 Runtime Incident。之前 Auction P0 Regression 的结论是 Capability NOT VERIFIED；该结论不能替代本次事故的独立证据链。
