# Day 10 Trust Presentation E2E Checklist v0

Status: PREPARED ONLY

Owner: CB

Purpose: prepare Reality -> Presentation acceptance after CC Contract Smoke Review PASS.

## Gate

Do not execute or conclude Reality -> Presentation PASS until:

- CC Contract Smoke Review = PASS
- Real API responses are available
- No synthetic payload is used as acceptance evidence

## Scope

This checklist validates Trust Presentation behavior only.

Allowed:

- Inspect real API payloads
- Inspect rendered UI / report HTML
- Record evidence
- Classify PASS / FAIL / HOLD per case

Forbidden:

- Modify Runtime
- Modify Contract
- Modify Provider
- Add or infer `data_availability`
- Use synthetic payload as acceptance evidence
- Claim Production Ready

## Cases

| Case | Type | Query | Expected Use |
|---|---|---|---|
| Case A | 热门股 | 贵州茅台 / 600519.SH | High-data-availability baseline |
| Case B | 普通股 | 招商银行 / 600036.SH | Normal listed-company baseline |
| Case C | 冷门股 | 苏美达 / 600710.SH | Sparse-data / missing-data stress case |

If any ticker is unavailable in the target environment, replace it with another real A-share in the same bucket and record the replacement reason.

## Required Evidence Per Case

Collect the following after CC Contract Smoke Review PASS:

1. Raw API response body
2. `_qc` object
3. `data_availability` source path
4. `section_data_usage` source path
5. Rendered report HTML
6. Screenshot or saved HTML evidence
7. Console error summary

## Acceptance Checks

### A. 数据完整性摘要是否出现

PASS:

- Report contains `可信度说明`
- Report contains `数据完整性摘要`

FAIL:

- Either block is absent from rendered report

HOLD:

- Page fails before rendering report

### B. 暂不可用是否统一展示

PASS:

- User-visible report does not contain raw `nan`, `null`, `None`, `N/A`, or empty value placeholders
- Missing values are shown as `暂不可用`

FAIL:

- Any raw missing-value token appears in user-visible report

HOLD:

- Cannot inspect rendered report

### C. Partial 是否说明缺什么

PASS:

- Any `Partial` item includes at least one explicit available or missing detail from Runtime/QC payload
- Example: `已获取：收盘价、涨跌幅`; `暂不可用：实时盘口、分时、Level2`

FAIL:

- UI shows `Partial` without explaining what is available or unavailable when payload contains those details

HOLD:

- Real payload contains no `Partial` item; record as not applicable for this case

### D. 章节级数据说明是否按 section_data_usage 显示

PASS:

- When real payload includes `section_data_usage`, matching report sections display `本章节使用的数据`
- Used and missing lists match the payload

FAIL:

- Payload contains `section_data_usage`, but rendered section notes are absent or mismatched

HOLD:

- Real payload does not include `section_data_usage`; cannot validate this check for the case

### E. 页面是否没有 nan/null/None/N/A 泄漏

PASS:

- Search rendered HTML and visible text; no raw missing-value tokens leak

FAIL:

- Any raw token leaks in visible report body, data summary, section note, source block, or error block

HOLD:

- Rendered HTML cannot be captured

### F. UI 是否只消费 Runtime/QC 返回字段

PASS:

- Every displayed availability status traces to one of:
  - `trust_presentation`
  - `presentation`
  - `data_availability`
  - `_qc.data_availability`
  - `section_data_usage`
  - `_qc.section_data_usage`

FAIL:

- UI displays Complete / Partial / Unavailable from a field not present in Runtime/QC payload
- UI reads Provider-specific fields directly

HOLD:

- Payload or rendered evidence is incomplete

### G. realtime / valuation unavailable 是否没有被写进确定结论

PASS:

- If `realtime` or `valuation` is `unavailable`, report does not make deterministic conclusions that rely on unavailable data
- Acceptable phrasing: `基于已获取数据`, `实时盘口暂不可用`, `估值数据暂不可用`

FAIL:

- Report asserts a conclusion that requires unavailable realtime or valuation data
- Example fail: `当前盘口显示...` when realtime盘口 is unavailable

HOLD:

- No realtime / valuation unavailable condition appears in the case payload

## Result Matrix

| Case | A Summary | B Missing Tokens | C Partial Detail | D Section Usage | E Raw Leak | F Traceability | G No Unsupported Conclusion | Result |
|---|---|---|---|---|---|---|---|---|
| Case A 热门股 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | HOLD |
| Case B 普通股 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | HOLD |
| Case C 冷门股 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | HOLD |

## Overall Verdict Rule

Reality -> Presentation PASS requires:

- All three cases have A, B, E, F = PASS
- C, D, G are PASS or justified HOLD based on real payload absence
- No FAIL in any case

Reality -> Presentation HOLD if:

- CC Contract Smoke Review is not PASS
- Real API evidence is unavailable
- Any required rendered evidence is missing

Reality -> Presentation FAIL if:

- Any FAIL appears in A, B, E, or F
- Any unsupported deterministic conclusion appears under check G

## Current Status

Checklist prepared.

Reality -> Presentation Window:

NOT CLOSED

Acceptance PASS:

NOT CLAIMED

Production Ready:

NOT CLAIMED
