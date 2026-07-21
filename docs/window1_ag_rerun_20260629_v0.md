# Window 1 A-G Re-run Report

Date: 2026-06-29

Owner: CB

Scope: Reality -> Presentation A-G checklist re-run.

Verdict: PARTIAL / HOLD

Acceptance PASS: NOT CLAIMED

Production Ready: NOT CLAIMED

Deploy Authorization: NOT CLAIMED

Runtime Full Recovered: NOT CLAIMED

## Input Claim From CA/C

CA/C reported:

- `/api/health` PASS
- `finance-suite.service` active
- `nginx` active
- Three case raw API all HTTP 200 / `success=true`
- Three cases include:
  - `data_availability`
  - `_qc.data_availability`
  - `section_data_usage`
  - `_qc.section_data_usage`
- `600036 cached=true` includes Trust Data
- `600036 live rendered smoke` PASS
- Rendered page shows `可信度说明` and `数据完整性摘要`
- Rendered page is not fallback trust presentation

CB could not locate the raw evidence pack in the local repository and could not independently fetch authenticated `/api/analyze` bodies via unauthenticated curl.

## Direct CB Re-run Attempt

Endpoint:

`https://www.touziagent.com/api/analyze`

Requests:

- `{"skill_type":"stock","query":"贵州茅台"}`
- `{"skill_type":"stock","query":"600519.SH"}`
- `{"skill_type":"stock","query":"招商银行"}`
- `{"skill_type":"stock","query":"600036.SH"}`
- `{"skill_type":"stock","query":"苏美达"}`
- `{"skill_type":"stock","query":"600710.SH"}`

Observed by CB:

```text
HTTP/2 401
{"detail":"401: 未登录，请先登录"}
```

Second CB re-run at 2026-06-29 17:20 CST observed the same result for:

- `600519.SH`
- `600036.SH`
- `600710.SH`
- Chinese-name query attempts

```text
HTTP/2 401
{"detail":"401: 未登录，请先登录"}
```

Interpretation:

This is an authentication gate for CB's direct curl path. It does not disprove CA/C's authenticated evidence, but it prevents CB from independently validating all three raw API bodies.

## Live Shell Check

Live pages:

- `https://www.touziagent.com/app/stock.html`
- `https://www.touziagent.com/app/deep-research.html`

Observed:

- HTTP 200
- `stock.html` last-modified: `Mon, 29 Jun 2026 05:08:27 GMT`
- `deep-research.html` last-modified: `Mon, 29 Jun 2026 05:08:28 GMT`
- Both pages include:
  - `可信度说明`
  - `数据完整性摘要`
  - `renderTrustPresentation`
  - `data_availability`
  - `section_data_usage`
  - `暂不可用`

Live Shell:

PASS

## A-G Checklist

| Check | Result | Reason |
|---|---|---|
| A. 数据完整性摘要是否出现 | PARTIAL | Live shell contains the blocks. CB could not independently render all three authenticated case reports. |
| B. 暂不可用统一展示 | PARTIAL | Live shell sanitizer is present and visible static DOM has no raw missing token leak. Three rendered reports not independently captured by CB. |
| C. Partial 是否说明缺什么 | HOLD | Requires rendered reports with real `Partial` data. CA/C claims Trust Data exists, but raw bodies/rendered HTML were not available to CB. |
| D. 章节级数据说明是否展示 | HOLD | Requires rendered reports with `section_data_usage`. CB could not inspect the three authenticated rendered outputs. |
| E. UI 是否只消费 Runtime/QC 字段 | PASS for shell | Live shell consumes `trust_presentation`, `presentation`, `data_availability`, `_qc.data_availability`, `section_data_usage`, `_qc.section_data_usage`. |
| F. realtime / valuation unavailable 是否没有进入确定结论 | HOLD | Requires rendered report text. CB could not inspect all three authenticated outputs. |
| G. 页面是否无 nan/null/None/N/A 泄漏 | PASS for shell visible DOM | Live static visible DOM does not leak `nan/null/None/N/A`. Three rendered reports not independently captured by CB. |

## Raw Leak Check

Method:

- Fetch live static pages.
- Strip `script`, `style`, `noscript`.
- Inspect visible text for `nan`, `null`, `None`, `N/A`.

Result:

| Page | nan | null | None | N/A |
|---|---:|---:|---:|---:|
| stock.html | false | false | false | false |
| deep-research.html | false | false | false | false |

Note:

Raw HTML source contains missing-value tokens inside sanitizer code and regex. Those are not user-visible leaks.

## Traceability Mapping

Live UI shell consumes:

- `data.trust_presentation`
- `data.presentation`
- `data.data_availability`
- `data._qc.data_availability`
- `section_data_usage`
- `data.section_data_usage`
- `data._qc.section_data_usage`

No Provider-specific field consumption was observed in the live shell.

## Remaining Gaps

1. CB direct `/api/analyze` path still returns 401.
2. Raw three-case API bodies were not available to CB in repository evidence.
3. Three-case rendered HTML evidence was not available to CB, except the CA/C summary claim for `600036`.
4. A-G cannot be fully closed from shell evidence alone.

## Final Verdict

Reality -> Presentation:

PARTIAL / HOLD

Reason:

Live Presentation Shell is deployed and traceable, but CB cannot independently validate the three authenticated raw API bodies and rendered outputs. The window should remain open until CA/C provides the raw three-case API bodies and rendered HTML artifacts, or CB receives an authenticated test path.

Not claimed:

- Acceptance PASS
- Production Ready
- Deploy Authorization
- Runtime Full Recovered
