# Evidence Sample Registration — Verified_LOCAL_SMOKE

> Evidence Verification Mini-Window = CLOSED / PARTIAL LOCAL VERIFIED / E2E GATED
> 本文件仅登记运行样本指纹，不是完整报告，不扩大 Evidence Map。

## 样本指纹

| 字段 | 值 |
|---|---|
| sample_path | `/tmp/research_runtime_events.jsonl` |
| sha256 | `e1d1ea7aed83e28ba5863f88f9e844dcb3f212cf23eeb070b510ac9af2c9ed60` |
| timestamp | `2026-07-04T16:01:18Z` |
| line_count | 16 |
| final_state | `DONE` |
| evidence_count | 2 |
| qc_passed | `true` |
| provider | **local**（`local_research_stub`，NOT production）|
| symbol | 300750.SZ |
| smoke_script | `smoke_research_runtime.py` |

## 清理策略

- 登记完成后，如需清 /tmp，可只保留本表（sha256 + 摘要），不保留原始 16 行样本。
- 登记完成前**不清理**。

## 窗口收口

```
P1 Evidence Map = PARTIAL / LOCAL VERIFIED / E2E GATED

Verified:
- 3 个演示账号        = Verified_DB_ONLY
- 一分钟研报主流程    = Verified_LOCAL_SMOKE
- Evidence Bundle 生成 = Verified_LOCAL_SMOKE
- Trust Gate / QC 拦截 = Verified_LOCAL_GUARD

Unknown (不得升级):
- Login E2E
- 生产 /api/analyze E2E
- 生产报告中 Trust Gate 真实参与
- trust_gate payload 缺失分支行为（finding：error 分支非 fail-closed，待单独评估）

Production Ready: NOT CLAIMED
```

---

## 年报 PDF Evidence Metadata（#1 DONE，追加登记 2026-07-05）

> 仅登记校验信息，不含 PDF 正文。授权范围：source/HTTP/path/sha256/size/pages/validation/parser/verdict。

### 宝钢股份 2024 年年度报告全文

| 字段 | 值 |
|---|---|
| source URL | `https://static.cninfo.com.cn/finalpage/2025-04-26/1223329102.PDF`（巨潮官方公告全文）|
| HTTP / content-type | 200 / application/pdf |
| local path | `/tmp/baosteel_pdf/baosteel_2024.pdf` |
| sha256 | `0f607360d5977d9ede8ade0fc4c9de176545b04c30ec269059dd7754b4ebebaa` |
| file size | 1,999,933 bytes (1.9 MB) |
| page count | 272 |
| title/body validation | 正文首页「宝山钢铁股份有限公司2024年年度报告 公司代码 600019」；含董事会声明/审计意见/利润分配，确认全文非摘要 |
| parser | pypdf（本地）|
| verdict | Verified_LOCAL_DOWNLOAD + Verified_LOCAL_PARSE |

### 宝钢股份 2023 年年度报告全文

| 字段 | 值 |
|---|---|
| source URL | `https://static.cninfo.com.cn/finalpage/2024-04-27/1219853660.PDF`（巨潮官方公告全文）|
| HTTP / content-type | 200 / application/pdf |
| local path | `/tmp/baosteel_pdf/baosteel_2023.pdf` |
| sha256 | `2bd0a79214c24e45b43d5c64cd8bbc5b114c0fd727811b8865b5b3656f22db04` |
| file size | 5,325,620 bytes (5.1 MB) |
| page count | 280 |
| title/body validation | PDF metadata title 不完整（「股份有限公司」），但正文首页明确「宝山钢铁股份有限公司 2023 年年度报告 公司代码 600019」，以正文为准，确认全文非摘要 |
| parser | pypdf（本地）|
| verdict | Verified_LOCAL_DOWNLOAD + Verified_LOCAL_PARSE |

### PDF 实体清理策略

- 实体在 `/tmp/baosteel_pdf/`，先保留。
- 登记完成后可清理，只保留本表（sha256 + 摘要），不保留原始 PDF。

### 状态锁定（#1 收口）

```
Evidence Verification #1: DONE

Annual Report PDF:
  2024: Verified_LOCAL_DOWNLOAD / Verified_LOCAL_PARSE
  2023: Verified_LOCAL_DOWNLOAD / Verified_LOCAL_PARSE

Remaining Unknown (local-verifiable branch): 0

Still Gated:
  #2 Login E2E
  #3 Production /api/analyze E2E
  #4 trust_gate fail-closed decision
```
