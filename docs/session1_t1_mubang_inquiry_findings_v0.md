# Session 1 T1 Findings — Mubang Inquiry Evidence v0

> Status: Discovery raw material only. Not P0b/P0c/P0d contract.
> Created: 2026-06-08
> Scope: T1 沐邦高科问询函抓取 + negative-test evidence 提炼

## 1. Source Links

| ID | Date | Document | Source URL | Use |
|---|---:|---|---|---|
| MB-2023-AR-REPLY | 2024-07-27 | 2023 年年度报告信息披露监管工作函回复 | https://static.cninfo.com.cn/finalpage/2024-07-27/1220740256.PDF | 历史口径：2023 年继续扩产、未计提商誉减值、客户/供应商重叠解释 |
| MB-2025-PERF-INQUIRY | 2025-01-23 | 业绩预告相关事项问询函 | https://www.sse.com.cn/disclosure/credibility/supervision/inquiries/enquiry/c/10770601/files/d8da1d1938714202a5a67c5690a048e7.pdf | 监管原始问题：收入、销售退回、收入扣除、商誉减值 |
| MB-2025-AR-PARTIAL-REPLY | 2025-07-11 | 2024 年年度报告信息披露监管问询函部分回复公告 | https://static.cninfo.com.cn/finalpage/2025-07-11/1224131515.PDF | 最强 negative-test 材料：募集资金违规、关联方占用、收入差错、在建工程减值 |
| MB-2025-NBD-1 | 2025-02-28 | 每经：业绩预告问询回复报道 | https://cd.nbd.com.cn/articles/2025-02-28/3771679.html | 二手交叉验证：光伏收入锐减、商誉减值 |
| MB-2025-NBD-2 | 2025-07-15 | 每经：2024 年报问询回复报道 | https://www.nbd.com.cn/articles/2025-07-15/3946178.html | 二手交叉验证：关联交易、资金链、项目减值 |

Local fetched copies for this run:

```text
/tmp/mubang_t1/2023_annual_work_letter_reply.pdf
/tmp/mubang_t1/2023_annual_work_letter_reply.txt
/tmp/mubang_t1/2025_performance_forecast_inquiry.pdf
/tmp/mubang_t1/2025_performance_forecast_inquiry.txt
/tmp/mubang_t1/2025_annual_inquiry_partial_reply.pdf
/tmp/mubang_t1/2025_annual_inquiry_partial_reply.txt
```

## 2. Regulator Questions By Theme

### 2.1 Fund Misuse / Related-Party Occupation

2025 年报问询函聚焦：公司以货款或工程款形式支付募集资金，再经关联企业借款形式回流上市公司，用于归还银行借款和供应商欠款。

Key numeric anchors:

| Item | Amount |
|---|---:|
| 内控审计报告所称募集资金违规使用 | 21,920.00 万元 |
| 内控评价报告列为非财务报告缺陷的金额 | 28,858.00 万元 |
| 持续督导报告书相关募集资金违规使用 | 22,967.63 万元 |
| 沐邦控股非经营性资金占用期间发生额 | 2,454.79 万元 |
| 江西豪安非经营性资金占用期间发生额 | 7,957.72 万元 |
| 年报披露关联方资金占用金额 | 4,501.31 万元 |

Regulator asked for:

- 逐项列示募集资金违规使用事实、时间、供应商、金额、是否回流、回流后用途。
- 解释募集资金占用、内控缺陷和披露数据多处不一致。
- 列示募集资金账户资金流、冻结、司法划扣、受限余额。
- 核查募投供应商是否存在付款退回或流向关联方。
- 说明募投项目是否真实，是否存在虚构支出套取募集资金。

Company response status:

- 对问题一未实质回复；公告称相关事项仍需进一步沟通落实，将另行回复。

Worksheet relevance:

- Strong candidate for `tried_not_found` or `conflicting_evidence`, depending on whether Session 1 treats "company deferred reply to explicit regulator concern" as insufficient proof or as conflict against an optimistic capex/expansion claim.
- Best matching rule: Type 3 Cash vs Logistics.
- Best conflict subtype if used as contradiction: `amount_contradiction` or `chain_contradiction`.

### 2.2 Revenue Recognition / Accounting Error / Related Customer

2025 年报问询函指出：2024 年前三季度多处会计处理差错更正，会计师认为客户管理、收入确认等方面存在重大内控缺陷。

Key numeric anchors:

| Item | Amount |
|---|---:|
| 经审计 2024 年年报营业收入 | 27,714.12 万元 |
| 业绩预告问询函披露营业收入 | 34,802.14 万元 |
| Difference | 7,088.02 万元 |
| 玩具原料销售由总额法改净额法冲减收入 | 4,698.98 万元 |
| 豪安能源对共青城奇峰不公允交易冲减收入 | 1,184.14 万元 |
| 豪安能源对共青城奇峰销售金额 | 3,178.54 万元 |
| 共青城奇峰对下游终端客户销售金额 | 1,994.40 万元 |

Regulator asked for:

- 重新核实前期业绩预告问询回复中收入确认、前十大客户等信息准确性。
- 明确客户是否有关联关系或潜在利益安排。
- 解释合同结算周期和实际账期差异。
- 判断是否存在虚构业务循环、不当确认收入。
- 列示共青城奇峰关联交易背景、信用政策、货物交付、回款、定价公允性、商业实质。

Company reply highlights:

- 公司承认共青城奇峰实际控制人与豪安能源原实际控制人存在近亲属关系，前期未列为关联方。
- 公司确认对共青城奇峰销售价格明显高于同期非关联方价格，并冲减不公允部分收入。
- 公司称除共青城奇峰之外，未发现前十大客户存在关联关系或潜在利益安排。
- 公司称光伏业务实际账期拉长，是因为行业产能过剩、价格下跌、客户资金承压，信用期可到 1/3/6/12 个月。

Worksheet relevance:

- Strong negative-test candidate against "光伏业务收入/客户质量支撑产能扩张" narrative.
- Best matching rule: Type 1 Mirror Relations or Type 3 Cash vs Logistics.
- Best conflict subtype: `direct_contradiction` for undisclosed related counterparty; `amount_contradiction` for sales amount vs end-customer resale amount.

### 2.3 Fixed Assets / Construction in Progress / Project Impairment

2025 年报问询函关注：在建工程余额高、项目延期、计提减值、框架协议落地不及预期。

Key numeric anchors:

| Item | Amount / Status |
|---|---:|
| 2024 年末在建工程账面余额 | 16.44 亿元 |
| 10GW TOPCON 光伏电池生产基地期末余额 | 10.78 亿元 |
| 10GW TOPCON 工程进度 | 42.27% |
| 10GW TOPCON 原投产时间延期 | 2023-03-30 → 2024-09 |
| 年产 5000 吨硅提纯循环利用项目期末余额 | 2.40 亿元 |
| 年产 5000 吨项目工程进度 | 57.9% |
| 年产 5000 吨项目本期减值 | 9,565.74 万元 |
| 二期年产 3GW 单晶硅棒项目期末余额 | 2.84 亿元 |
| 二期年产 3GW 项目工程进度 | 57.9% |
| 二期年产 3GW 项目本期减值 | 3,993.89 万元 |
| 在建工程本期其他减少 | 1.05 亿元 |

Regulator asked for:

- 补充披露闲置固定资产、减值计提是否及时充分。
- 说明在建工程其他减少金额及会计处理。
- 列示各在建项目累计采购供应商、交易内容、结算、是否存在工程支出利益输送。
- 解释多个项目计提减值的原因、是否存在应计提未计提。
- 结合 5000 吨项目进度和减值，说明同时投建 10000 吨项目的商业合理性和必要性。
- 说明前期框架协议后续安排并提示风险。

Company reply highlights:

- 对二期 3GW 和 5000 吨项目分别计提在建工程减值。
- 披露内蒙古沐邦用于 10000 吨募投项目的募集资金 4,800 万元通过供应商中基建设转出，剔除该挪用资金后再列累计结算金额。
- 称除江西中基建设集团有限公司外，不存在通过工程项目支出进行利益输送。

Worksheet relevance:

- Strong negative-test candidate against "产能扩张真实推进/项目支撑未来增长" narrative.
- Best matching rule: Type 2 Capacity Chain + Type 3 Cash vs Logistics.
- Best conflict subtype: `amount_contradiction` for project investment vs formed asset; `chain_contradiction` for project progress vs claimed capacity expansion.

### 2.4 2023 Historical Reply As Baseline

2023 年报工作函回复是 historical baseline:

- 公司 2023 年光伏板块营收 9.43 亿元，同比 +37.76%，毛利率 8.24%，同比 -11.05pct。
- 监管已要求解释毛利率下行背景下继续推进产能扩张的合理性。
- 公司当时称适度产能扩张具备合理性。
- 公司解释 2023 年制造费用上升，主要因产量上升、水电固定成本、坩埚等耗材成本上升。
- 对 2023 年末商誉减值，公司当时未计提；2025 业绩预告问询函随后要求比较前期商誉减值测试是否客观审慎。

Worksheet relevance:

- Useful for `timing_contradiction` across 2023 → 2024 → 2025.
- The contradiction is not a single direct denial; it is a timeline reversal: 2023 "扩产合理/未减值" vs 2024 large impairment and regulator concern over project reality/fund flow.

## 3. Company Reply Quality Assessment

| Theme | Reply Quality | Evidence Strength | Notes |
|---|---|---|---|
| 募集资金违规 / 关联方占用 | Weak / deferred | Strong regulator concern, incomplete company answer | 最关键问题未在部分回复中实质回答 |
| 收入确认 / 共青城奇峰 | Strong enough for negative test | Strong | 公司承认关联识别、价格公允性和收入冲减问题 |
| 项目减值 / 在建工程 | Medium | Strong for impairment, partial for project authenticity | 有减值和项目进度数字；是否虚构支出仍需后续回复 |
| 2023 扩产合理性 | Medium | Historical baseline only | 可作为时间窗口对照，不宜单独判定 |

## 4. Suggested 8-Column Negative Assertions

### Candidate A — Related Counterparty Revenue

| Column | Draft Value |
|---|---|
| 1. Serenity Question | 沐邦高科跨界光伏业务的客户收入是否能支撑其产能扩张故事？ |
| 2. Assertion | [NEGATIVE TEST] 豪安能源 2024 年对共青城奇峰的硅片销售具备独立商业实质且收入金额可直接支撑光伏业务增长。 |
| 3. Extraction Field | `revenue_cny`; `relation_type`; `is_related_party`; `amount_cny` |
| 4. Evidence Source | MB-2025-AR-PARTIAL-REPLY, pages around revenue correction / related customer |
| 5. Matching Rule | Type 1 Mirror Relations + Type 3 Cash vs Logistics |
| 6. Tolerance | ±5% amount difference; related-party flag must be exact |
| 7. Verdict | `conflicting_evidence` |
| 8. Conflict Source | `direct_contradiction` or `amount_contradiction` |

Rationale: company acknowledged relationship not previously listed as related party, sales price exceeded comparable non-related price, and income was adjusted downward by 1,184.14 万元.

### Candidate B — Fund Flow vs Project Reality

| Column | Draft Value |
|---|---|
| 1. Serenity Question | 沐邦高科的硅提纯募投项目是否形成了可验证的真实产能资产？ |
| 2. Assertion | [NEGATIVE TEST] 10000 吨/年智能化硅提纯循环利用项目募集资金投入与在建工程形成金额一致，资金未通过供应商流向关联方或被挪用。 |
| 3. Extraction Field | `amount_cny`; `CapexProject.total_budget`; `CapexProject.disclosed_capex`; `is_related_party` |
| 4. Evidence Source | MB-2025-AR-PARTIAL-REPLY, problem one and problem four |
| 5. Matching Rule | Type 3 Cash vs Logistics |
| 6. Tolerance | ±10% for capex-to-asset amount; related-party/fund diversion flag exact |
| 7. Verdict | `tolerance_unresolved` or `conflicting_evidence` |
| 8. Conflict Source | If conflicting: `amount_contradiction` |

Rationale: regulator identified multiple inconsistent amounts and asked whether project expenditure was fictitious. Company deferred the main fund-misuse answer, but later disclosed 4,800 万元 through supplier 中基建设.

### Candidate C — Expansion Progress vs Impairment

| Column | Draft Value |
|---|---|
| 1. Serenity Question | 沐邦高科在行业下行中继续推进光伏产能扩张是否有硬证据支撑？ |
| 2. Assertion | [NEGATIVE TEST] 2023 年所称适度产能扩张在 2024 年仍按计划推进，且关键在建项目不存在重大减值或延期风险。 |
| 3. Extraction Field | `capacity_value`; `capacity_status`; `yoy_capex_growth`; `amount_cny` |
| 4. Evidence Source | MB-2023-AR-REPLY; MB-2025-AR-PARTIAL-REPLY |
| 5. Matching Rule | Type 2 Capacity Chain + Type 4 Temporal Alignment |
| 6. Tolerance | project progress ±10%; timing tolerance 2 quarters |
| 7. Verdict | `conflicting_evidence` |
| 8. Conflict Source | `timing_contradiction` or `chain_contradiction` |

Rationale: 2023 baseline frames expansion as reasonable; 2024 year-end materials show project delays, impairment, and questions about continued project necessity.

## 5. Open Items For Session 1

| Item | Status |
|---|---|
| Original 2025 annual inquiry letter itself | Not separately fetched; content embedded in partial reply公告 and secondary sources. Search key: `上证公函 2025 0712 沐邦` |
| Company later full reply to problem one | Need follow-up search; partial reply explicitly deferred fund-misuse details |
| Page-level PDF mapping | Text extraction done, but page references need visual PDF page confirmation if worksheet requires page numbers |
| Whether to set Verdict for Candidate B as `conflicting_evidence` or `tolerance_unresolved` | Session 1 decision; depends on evidence threshold for unresolved fund-flow questions |

