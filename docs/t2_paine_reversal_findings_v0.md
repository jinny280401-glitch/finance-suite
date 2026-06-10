# T2 Paine Reversal Findings v0

> Case: 派能能源/派能科技 2022 户储暴增期 vs 2023 暴跌期  
> Question: 卖方研报叙事是否发生反向解释？  
> Boundary: 不接 Trading System；不改 Serenity Skill / L0 ontology / contract / runtime；不扩半导体或苹果链。  
> Evidence pull date: 2026-06-11

## Evidence-backed Verdict

Verdict: YES, evidence supports a narrow narrative reversal.

2022/early-2023 sell-side narrative: 派能的高增被解释为欧洲能源危机、高电价、能源自主可控、政策支持和户储经济性驱动的需求爆发。

2023 downturn narrative: 派能的下滑被解释为欧洲户储渠道库存高企、经销商去库、需求增速阶段性放缓、出货不及预期和低产能利用率。

This is not a verdict that European end-user residential storage demand fully collapsed. The more precise verdict is that sell-side explanation reversed at the shipment/channel layer: 2022 shipments were treated as structural demand pull, while 2023 weakness was later attributed to channel inventory and destocking created by the prior boom.

## 8-column Worksheet

| Serenity Question | Extraction Field | Evidence Source | Extracted Value | Matching Rule | Tolerance | Verdict | Failure Attribution / Conflict Source |
|---|---|---|---|---|---|---|---|
| 2022 暴增期，卖方是否用欧洲能源危机/高电价/经济性解释需求？ | 2022 sell-side demand driver | 东吴证券《户用储能市场需求火爆，龙头迎来快速增长》(2022-04-27), 东方财富 PDF: https://pdf.dfcfw.com/pdf/H3_AP202204271562028053_1.pdf | 报告将 2022 海外户储需求加速爆发归因于海外居民电价上涨、政策驱动、欧洲市场和公司渠道先发优势；预计 2022 出货超 3GWh、2023 持续高增。 | If sell-side names energy price / policy / economics as growth driver and links it to company growth, classify as positive demand-pull narrative. | Exact wording not required; driver must be explicit. | PASS | None. Evidence directly matches 2022 positive narrative. |
| 2022/早 2023 卖方是否把高景气视为可持续，而非一次性冲击？ | Sustained boom narrative | 华福证券《扎根户储扬帆起航，定增扩产量利双升》(2023-04-10), 东方财富 PDF: https://pdf.dfcfw.com/pdf/H3_AP202304101585257820_1.pdf | 报告认为户储高景气仍将持续，俄乌冲突只是催化剂，核心原因是能源自主可控诉求和能源价格高企下户储经济性；预计 2023 储能销量 7.5GWh、收入 131.1 亿元。 | If report explicitly rejects "demand cannot stay high" and forecasts strong 2023 growth, classify as sustained-positive narrative. | Forecast horizon must include 2023. | PASS | Later actuals conflict with forecast, not with extraction. |
| 公司 2022 实际是否支持暴增事实？ | 2022 actual revenue / profit / sales | 派能科技 2022 年年度报告, 新浪财经公告页: https://money.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=8975675&stockid=688063 | 2022 营收 60.13 亿元，同比 +191.55%；归母净利 12.73 亿元，同比 +302.53%；产品销售量 3535.40MWh，其中储能系统 3505.83MWh。 | If official filing confirms revenue / profit / sales surge, classify as actual boom. | RMB figures rounded to 2 decimals in billions; MWh rounded to 2 decimals. | PASS | None. Official filing supports boom baseline. |
| 2023 暴跌期，卖方是否改用库存/去库存解释下滑？ | 2023 sell-side negative driver | 华福证券《户储仍处去库存周期，海外出货不及预期》(2023-10-31), 东方财富 PDF: https://pdf.dfcfw.com/pdf/H3_AP202310311606658231_1.pdf | 报告称 Q3 储能系统出货约 300MWh，前三季度累计 1.7GWh，同比下降 23%；主要受欧洲户储整体去库存影响，需求阶段性放缓，二三季度销量持续不及预期。 | If sell-side assigns weakness to channel inventory / destocking and cuts shipment / profit expectations, classify as negative inventory-cycle narrative. | Must include at least one of inventory, destocking, shipment miss, demand slowdown. | PASS | None. Evidence directly matches 2023 negative narrative. |
| 2023 年报后，卖方是否继续使用去库存解释全年下滑？ | Post-annual-report sell-side confirmation | 东吴证券《2023 年年报点评：产能利用率维持低位》(2024-04-12), 东方财富 PDF: https://pdf.dfcfw.com/pdf/H3_AP202404121630195684_1.pdf | 报告称 2023 出货 1.9GWh，同比下降 47%；库存量 0.6GWh，同比增加 14%；Q4 出货约 0.2GWh，同环比 -85%/-35%，原因是欧洲户储经销商持续去库。 | If a later sell-side report repeats destocking and quantifies shipment decline, classify as confirmed reversal. | Shipment figures can be estimate-based if source labels them as analyst estimate. | PASS | Sell-side shipment data is analyst estimate; official company report confirms sales decline and demand pressure but not every estimate. |
| 公司 2023 实际是否支持暴跌事实？ | 2023 actual revenue / profit / sales | 派能科技 2023 年年度报告, 新浪财经公告页: https://money.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=9961538&stockid=688063 | 2023 营收 32.99 亿元，同比 -45.13%；归母净利 5.16 亿元，同比 -59.49%；软包电池销量 1874.53MWh，同比 -46.92%；公司称家储产品销售量下降。 | If official filing confirms revenue / profit / sales decline, classify as actual downturn. | RMB figures rounded to 2 decimals in billions; MWh rounded to 2 decimals. | PASS | None. Official filing supports downturn baseline. |
| 公司对 2023 下滑的归因是否与卖方去库存叙事一致？ | Company attribution | 派能科技 2023 年年度报告, 新浪财经公告页: https://money.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=9961538&stockid=688063 | 公司称宏观环境变化、部分国家和地区补贴政策退坡、海外下游企业去库存，使家用储能市场需求较上年增速阶段性放缓；还称海外下游渠道商库存高企，2023 年海外家储市场持续处于去库阶段。 | If company filing names overseas downstream/channel inventory and demand slowdown, classify as company-side corroboration. | Need at least one official company source. | PASS | Company adds subsidy phase-out and macro factors, so attribution is multi-factor, not inventory-only. |
| 是否存在“终端需求仍稳健”与“公司出货下滑”的冲突？ | Conflict source | 派能科技投资者关系活动记录表(2024-04-30), 东方财富 PDF: https://pdf.dfcfw.com/pdf/H22_AN202404301632045186_1.pdf | 公司把 2022-2024 称为连续周期：2022 因地缘政治等因素倍增；2023 Q1 供应链恐慌造成库存高企，行业发货量下降；同时观察到欧洲户储装机量相对稳健，没有特别大增长也没有下滑。 | If terminal installations are described as steady while shipments fall due to inventory, classify as channel-stock conflict. | Qualitative steady/weak wording allowed if source distinguishes installation from shipment. | PASS | Conflict source is shipment vs end-installation timing. 2022 channel stocking pulled forward reported shipments. |

## Conclusion

The case passes the reversal test.

- 2022/early-2023 sell-side explanation: high electricity prices, energy security, policy support, economics, channel advantage, capacity expansion.
- 2023 negative explanation: overseas downstream/channel inventory, destocking, demand growth slowdown, lower shipments, low utilization, price competition.
- Company filings corroborate both the 2022 boom and 2023 downturn.
- Cleanest failure attribution: channel inventory and shipment timing, not a simple collapse in European terminal installation demand.

## Source Register

- 东吴证券, 《派能科技：户用储能市场需求火爆，龙头迎来快速增长》, 2022-04-27: https://pdf.dfcfw.com/pdf/H3_AP202204271562028053_1.pdf
- 华福证券, 《派能科技：扎根户储扬帆起航，定增扩产量利双升》, 2023-04-10: https://pdf.dfcfw.com/pdf/H3_AP202304101585257820_1.pdf
- 华福证券, 《派能科技：户储仍处去库存周期，海外出货不及预期》, 2023-10-31: https://pdf.dfcfw.com/pdf/H3_AP202310311606658231_1.pdf
- 东吴证券, 《派能科技：2023 年年报点评：产能利用率维持低位》, 2024-04-12: https://pdf.dfcfw.com/pdf/H3_AP202404121630195684_1.pdf
- 派能科技, 2022 年年度报告: https://money.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=8975675&stockid=688063
- 派能科技, 2023 年年度报告: https://money.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=9961538&stockid=688063
- 派能科技, 投资者关系活动记录表, 2024-04-30: https://pdf.dfcfw.com/pdf/H22_AN202404301632045186_1.pdf
