# Three Case Evidence Pack

Date: 2026-06-29 17:30 CST

Owner: CA/C

Scope: Window 1 three-case evidence pack for live production `stock.html`.

Production Ready: NOT CLAIMED

## Environment

- Site: `https://www.touziagent.com`
- Page: `https://www.touziagent.com/app/stock.html`
- Browser: user Chrome profile, logged-in session
- Chrome session: yes
- Local page substitution: no
- Synthetic payload: no
- Proxy observed on local machine: yes, `HTTP_PROXY/HTTPS_PROXY/ALL_PROXY=http://127.0.0.1:7897`
- Direct origin check: `--resolve www.touziagent.com:443:119.28.156.125` returned HTTP 200 for static page
- DNS observed: `www.touziagent.com -> 198.18.1.66`
- Unauthenticated `/api/analyze`: HTTP 401, treated as expected auth gate, not business failure

## Live UI Mapping

Live `stock.html`:

- `/api/analyze` request: line 773
- request payload shape: line 776, `{ skill_type: 'stock', query }`
- `getTrustMeta(data)`: line 962
- consumes `data_availability`: lines 964, 968
- `renderTrustPresentation(data)`: line 984
- `getSectionUsage(data)`: line 1026
- consumes `section_data_usage`: line 1028

Mapping verdict:

- The page consumes trust fields when a real API response reaches `formatResult(data)`.
- This is stronger than shell-only evidence because each case below rendered real report body plus populated availability items.
- Raw API bodies were not captured in this run, so top-level vs `_qc` trust-field source cannot be proven per case.

## Case 1: 贵州茅台 / 600519.SH

Request payload:

```json
{"skill_type":"stock","query":"600519.SH"}
```

### Raw API Evidence

| Field | Evidence |
|---|---|
| HTTP status | UNKNOWN |
| success | UNKNOWN |
| cached | UNKNOWN |
| result length | UNKNOWN |
| `_qc.status` | UNKNOWN |
| `data_availability` present | UNKNOWN |
| `_qc.data_availability` present | UNKNOWN |
| `section_data_usage` present | UNKNOWN |
| `_qc.section_data_usage` present | UNKNOWN |

Reason:

The logged-in Chrome page rendered successfully, but the same-session raw API body was not captured. The Chrome automation sandbox did not expose fetch/XHR/localStorage raw access, and direct curl is unauthenticated.

### Trust Fields Evidence

Rendered availability modules:

| Module | Rendered status | Rendered detail |
|---|---|---|
| fundamental | Partial | `structured_financial_or_kline` |
| realtime | 暂不可用 | `realtime` |
| macro | 暂不可用 | `macro` |
| news | Partial | `search_sources` |
| capital_flow | 暂不可用 | `capital_flow` |
| valuation | 暂不可用 | `valuation` |
| research | Partial | `search_sources` |
| market_context | Partial | `report_context` |

`section_data_usage`: UNKNOWN from raw body. No per-section usage object was captured in raw evidence.

Cached trust field completeness: UNKNOWN.

### Rendered Evidence

- URL: `https://www.touziagent.com/app/stock.html?three-case-pack=1782725345297`
- Latency: 46.070s
- Report body: PRESENT
- `可信度说明`: PRESENT
- `数据完整性摘要`: PRESENT
- `暂不可用`: PRESENT
- `nan/null/None/N/A` visible leak: NOT OBSERVED
- Console errors: none in captured tail
- Trust panels: 2
- Availability items: 8
- Rendered result length: 3889 chars

HTML evidence:

```html
<div class="trust-panel">
  <div class="trust-panel__title">可信度说明</div>
  <div class="trust-panel__text">
    本报告仅基于已获取的数据生成。暂不可用的数据不会参与任何分析结论。
    部分章节基于不完整数据生成，请结合其他信息综合判断。
  </div>
</div>
<div class="trust-panel">
  <div class="trust-panel__title">数据完整性摘要</div>
  <div class="availability-grid">...
```

Report excerpt:

```text
贵州茅台（600519.SH）深度分析报告
数据截止日期：2026-06-29
一、核心结论
(1) 当前态势判断：高位承压
```

## Case 2: 招商银行 / 600036.SH

Request payload:

```json
{"skill_type":"stock","query":"600036.SH"}
```

### Raw API Evidence

| Field | Evidence |
|---|---|
| HTTP status | UNKNOWN |
| success | UNKNOWN |
| cached | UNKNOWN |
| result length | UNKNOWN |
| `_qc.status` | UNKNOWN |
| `data_availability` present | UNKNOWN |
| `_qc.data_availability` present | UNKNOWN |
| `section_data_usage` present | UNKNOWN |
| `_qc.section_data_usage` present | UNKNOWN |

Reason:

The live browser page rendered successfully, but same-session raw API body was not captured. A previous CA/C claim said `600036 cached=true` includes Trust Data; that claim is not re-proven by this evidence pack.

### Trust Fields Evidence

Rendered availability modules:

| Module | Rendered status | Rendered detail |
|---|---|---|
| fundamental | Partial | `structured_financial_or_kline` |
| realtime | 暂不可用 | `realtime` |
| macro | 暂不可用 | `macro` |
| news | Partial | `search_sources` |
| capital_flow | 暂不可用 | `capital_flow` |
| valuation | 暂不可用 | `valuation` |
| research | Partial | `search_sources` |
| market_context | Partial | `report_context` |

`section_data_usage`: UNKNOWN from raw body. No per-section usage object was captured in raw evidence.

Cached trust field completeness: UNKNOWN in this pack. Render latency was 2.300s, which is cache-consistent behavior, but raw `cached=true` was not captured and is not claimed.

### Rendered Evidence

- URL: `https://www.touziagent.com/app/stock.html?three-case-pack=1782725402742`
- Latency: 2.300s
- Report body: PRESENT
- `可信度说明`: PRESENT
- `数据完整性摘要`: PRESENT
- `暂不可用`: PRESENT
- `nan/null/None/N/A` visible leak: NOT OBSERVED
- Console errors: none in captured tail
- Trust panels: 2
- Availability items: 8
- Rendered result length: 1892 chars

HTML evidence:

```html
<div class="trust-panel">
  <div class="trust-panel__title">可信度说明</div>
  ...
</div>
<div class="trust-panel">
  <div class="trust-panel__title">数据完整性摘要</div>
  <div class="availability-grid">...
```

Report excerpt:

```text
600036.SH 深度分析报告
数据截止日期：2026-06-29
一、核心结论
(1) 当前态势判断：数据暂不可用，无法判断
```

## Case 3: 苏美达 / 600710.SH

Request payload:

```json
{"skill_type":"stock","query":"600710.SH"}
```

### Raw API Evidence

| Field | Evidence |
|---|---|
| HTTP status | UNKNOWN |
| success | UNKNOWN |
| cached | UNKNOWN |
| result length | UNKNOWN |
| `_qc.status` | UNKNOWN |
| `data_availability` present | UNKNOWN |
| `_qc.data_availability` present | UNKNOWN |
| `section_data_usage` present | UNKNOWN |
| `_qc.section_data_usage` present | UNKNOWN |

Reason:

The live browser page rendered successfully, but same-session raw API body was not captured.

### Trust Fields Evidence

Rendered availability modules:

| Module | Rendered status | Rendered detail |
|---|---|---|
| fundamental | Partial | `structured_financial_or_kline` |
| realtime | 暂不可用 | `realtime` |
| macro | 暂不可用 | `macro` |
| news | Partial | `search_sources` |
| capital_flow | 暂不可用 | `capital_flow` |
| valuation | 暂不可用 | `valuation` |
| research | Partial | `search_sources` |
| market_context | Partial | `report_context` |

`section_data_usage`: UNKNOWN from raw body. No per-section usage object was captured in raw evidence.

Cached trust field completeness: UNKNOWN.

### Rendered Evidence

- URL: `https://www.touziagent.com/app/stock.html?three-case-pack=1782725300352`
- Latency: 34.107s
- Report body: PRESENT
- `可信度说明`: PRESENT
- `数据完整性摘要`: PRESENT
- `暂不可用`: PRESENT
- `nan/null/None/N/A` visible leak: NOT OBSERVED
- Console errors: none in captured tail
- Trust panels: 2
- Availability items: 8
- Rendered result length: 2699 chars

HTML evidence:

```html
<div class="trust-panel">
  <div class="trust-panel__title">可信度说明</div>
  ...
</div>
<div class="trust-panel">
  <div class="trust-panel__title">数据完整性摘要</div>
  <div class="availability-grid">...
```

Report excerpt:

```text
常林股份（600710.SH）深度分析报告
数据截止日期：2026-06-29
一、核心结论
(1) 当前态势判断：数据严重缺失，无法判断
```

Note:

The rendered title says `常林股份（600710.SH）`, while the requested business label was `苏美达 / 600710.SH`. This is a data identity/name-mapping concern and should not be silently treated as a Trust Presentation PASS.

## Summary Matrix

| Case | Raw API | Rendered | Trust panel | Availability items | Visible missing display | Leak check | Mapping |
|---|---|---|---|---:|---|---|---|
| 600519.SH | UNKNOWN | PASS | PRESENT | 8 | `暂不可用` normal | PASS | PRESENT via live render |
| 600036.SH | UNKNOWN | PASS | PRESENT | 8 | `暂不可用` normal | PASS | PRESENT via live render |
| 600710.SH | UNKNOWN | PASS | PRESENT | 8 | `暂不可用` normal | PASS | PRESENT via live render, with name-mapping concern |

## Verdict

Raw API Evidence: UNKNOWN

Rendered Evidence: PASS for all three cases

Trust Data Contract: PRESENT in rendered consumption, UNKNOWN in raw top-level/_qc placement

Mapping Evidence: PASS for rendered availability mapping; HOLD for raw field-source mapping

Window 1: PARTIAL / HOLD remains appropriate

Production Ready: NOT CLAIMED
