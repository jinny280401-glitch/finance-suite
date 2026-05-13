# Finance Suite 当前系统状态

**日期**：2026-05-13  
**目标**：单一事实源，所有 Agent 的开机读物  
**原则**：只写当前真实状态，不写未来规划、TODO、猜测、愿景

---

## 一、生产当前状态

### 1.1 生产环境基础设施

| 项目 | 状态 |
|---|---|
| 域名 | `https://www.touziagent.com` |
| 服务器 | ECS `ubuntu@touziagent.com` |
| Web 框架 | FastAPI + Flask 混合 |
| 主入口 | `/home/ubuntu/finance-suite-web/app/main.py` |
| 进程管理 | systemd `finance-suite.service` |
| 启动命令 | `uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4` |
| 反向代理 | nginx `/api/` → `127.0.0.1:8000` |
| 静态文件 | nginx `/app/` → `/home/ubuntu/finance-suite-web/static` |

### 1.2 生产功能状态

**正常运行**：
- ✅ 静态页面：`/app/index.html` `/app/stock.html` `/app/deep-research.html` `/app/auction.html`
- ✅ 登录鉴权：`/api/login` `/api/logout` `/api/check-auth`（未登录返回 401）
- ✅ 核心分析：`/api/analyze`（需登录，支持 skill_type 分发）
- ✅ 自选股：`/api/watchlist/add` `/api/watchlist/remove` `/api/watchlist/list`

**占位 stub（未接 live）**：
- ⚠️ `/api/intel/research`：返回 HTTP 200，但 body 是 `_qc.status=failure`，error 信息：`"research route is not connected to a live upstream yet"`
- ⚠️ `/api/intel/discussions`：路由存在但前端未调用
- ⚠️ `/api/intel/hot-stocks`：路由存在但前端未调用

**未上线**：
- ❌ 4-tab Sidebar UI（热门讨论/热股榜/我的自选/脱水研报）
- ❌ 脱水研报功能（research_digest）
- ❌ 市场情报聚合（market_intel）

### 1.3 生产数据源

| 数据源 | 状态 | 用途 |
|---|---|---|
| Wind API | ✅ 已配置（ECS） | 高级金融数据 |
| Tushare Pro | ✅ 已配置 | A 股数据备源 |
| JoinQuant | ✅ 已配置 | 量化数据备源 |
| AkShare | ✅ 可用 | 免费数据兜底 |

---

## 二、本地当前状态

### 2.1 本地开发环境

| 项目 | 路径 |
|---|---|
| 主仓库 | `/Users/Zhuanz/finance-suite/` |
| Python 版本 | 3.12 |
| 虚拟环境 | `.venv/bin/python3.12` |
| 测试状态 | 核心 research 测试 14 passed；全量 pytest 发现 16 passed |

### 2.2 本地 demo server（8765）

**状态**：✅ 已验证可复现；当前未要求常驻运行

| 项目 | 值 |
|---|---|
| 服务 | `scripts/research_demo_api.py` |
| 端口 | `127.0.0.1:8765` |
| 前端 | `app/index.html`（4-tab Sidebar） |
| 后端 | `/api/intel/research` 直接 import `research_digest.latest()` |
| 数据源 | 东方财富研报 API → SQLite 缓存 |
| 验证命令 | `curl -s "http://127.0.0.1:8765/api/intel/research?limit=3"` |

**关键区分**：
- 本地 8765 是 **sandbox demo**，不代表生产状态
- 本地 8765 绕过了 `finance-suite-web` 的复杂装配
- 本地 8765 **不部署到生产**
- 如果 `127.0.0.1:8765` 当前没有监听进程，不代表功能回归；需要验证时按 `scripts/research_demo_api.py` 文件头命令重新启动

### 2.3 本地功能状态

**已完成**：
- ✅ 东方财富研报数据抓取
- ✅ SQLite 缓存（`~/.finance-suite/research_digest.db`）
- ✅ `research_digest.py`（5 个 action：latest/by_stock/by_industry/by_keyword/digest_one）
- ✅ `digest_llm.py`（LLM wrapper：OpenRouter → Anthropic → 规则 fallback）
- ✅ `market_intel.py`（4 板块聚合：discussions/hot_stocks/watch_alerts/research）
- ✅ `market_intel_schema.py`（统一契约：{items, _qc, meta}）
- ✅ 4-tab Sidebar UI（本地 `app/index.html`）
- ✅ 核心 research 单元测试 14 passed
- ✅ 全量 pytest 发现 16 passed（含 `scripts/test_mcp_quant_scan.py`）

**当前限制**：
- ⚠️ LLM 脱水未生效：`digest_status = fallback`（缺 LLM key）
- ⚠️ 规则 fallback：用券商名称+评级+标题拼装摘要

---

## 三、已验证事实

### 3.1 架构事实

1. **两个仓库**：
   - `finance-suite`（本地+ECS）：MCP server + 工具脚本 + demo
   - `finance-suite-web`（仅 ECS）：FastAPI 主入口 + `/api/analyze` + SKILLS dispatcher

2. **两套 web 框架共存**：
   - Flask Blueprint：`auth_bp`、`watchlist_bp`
   - FastAPI Router：`intel_router`、`api.router`

3. **两种路由语义**：
   - `/api/analyze`：单入口 + `skill_type` 字段 + `SKILL_ALIASES` 归一化
   - `/api/intel/*`：URL 即动作，无 dispatcher

4. **两种工具调用方式**：
   - subprocess + `python -c`：老 mcp_server 工具（0.3-1s 冷启）
   - 直接 import：新工具（快 10 倍）

5. **`_qc` envelope 协议**：
   - 字段：`status / completeness / sources / fallback_source / missing_dimensions / stale_data`
   - API 层只透传不自造

### 3.2 ECS 确认事实（2026-05-12）

| 项目 | 确认结果 |
|---|---|
| FastAPI 主入口 | `/home/ubuntu/finance-suite-web/app/main.py` |
| systemd 服务 | `finance-suite.service` |
| routers | `pages/api/admin/intel/watchlist` 均 include |
| nginx 反代 | `/api/` → `127.0.0.1:8000` |
| 静态文件 root | `/home/ubuntu/finance-suite-web/static` |
| 线上 index.html | 未包含 4-tab Sidebar UI |
| `/api/intel/research` | HTTP 200，但只是 stub（`_qc.status=failure`） |

### 3.3 smoke check 结果

**最近一次**：2026-05-12

```
✅ /app/index.html → 200
✅ /app/stock.html → 200
✅ /app/deep-research.html → 200
✅ /app/auction.html → 200
✅ /api/analyze 未登录 → 401（正常）
⚠️ /api/intel/research → 200（stub，_qc.status=failure）
```

---

## 四、当前 freeze line

**生效日期**：2026-05-12  
**原因**：生产事实澄清完成，系统稳定，功能冻结，等待 LLM key 或正式部署窗口

### 4.1 硬纪律（5 条）

1. ❌ **不部署本地 demo**：`scripts/research_demo_api.py` 只服务本地 8765 反馈闭环
2. ❌ **不改生产 router**：不扩展生产 `intel_api`，不加新生产路由
3. ❌ **不扩 Sidebar**：不部署 4-tab UI 到生产
4. ❌ **不加新 intel route**：直到 LLM key 或部署窗口明确
5. ❌ **不做产品化动效**：不做"市场情绪时钟"等需要 LLM 的功能

### 4.2 解锁条件（二选一）

**A 路：LLM key 到位**
- 配置 `.env` 的 `OPENROUTER_API_KEY` 或 `ANTHROPIC_API_KEY`
- 重启本地 demo：`pkill -f research_demo_api && .venv/bin/python3.12 scripts/research_demo_api.py &`
- 验证：`curl "http://127.0.0.1:8765/api/intel/research?limit=3&max_llm=3"`
- 预期：`digest_status` 从 `fallback` → `haiku` / `sonnet`

**B 路：明确部署窗口**
- 把 `research_digest` 正式接入 `finance-suite-web/app/routers/intel.py`
- 同步 4-tab Sidebar UI 到 `finance-suite-web/static/app/index.html`
- 部署前后跑 smoke check
- 确认 no regression

---

## 五、当前唯一未完成项

**LLM 脱水验证**

- **状态**：本地 research_digest 链路已跑通，但 LLM 脱水未生效
- **当前**：`digest_status = fallback`（规则拼装）
- **目标**：`digest_status = haiku` 或 `sonnet`（真 AI 脱水）
- **阻塞**：缺 LLM key
- **验证方式**：配置 key 后，浏览器刷新 `127.0.0.1:8765/app/index.html`，看研报卡片的 summary 从模板拼装变成有信息量的中文

---

## 六、关键误判已消除

**误判**：生产 `/api/intel/research` 返回 200 = 脱水研报已上线  
**事实**：那个 200 是安全 stub，不是 live research_digest  
**消除时间**：2026-05-12  
**记录位置**：`docs/production_stability_guard_20260512.md` line 18-24

---

## 七、下一步行动（仅供参考，不是 TODO）

当前不执行任何行动，等待：
- A. LLM key 到位 → 执行 A 路验证
- B. 部署窗口明确 → 执行 B 路部署

在此之前，守门员职责：
- 维护文档一致性
- 审核任何变更提案
- 防止团队陷入"完成度幻觉"

### 7.1 长期守门规则

1. **不只看 HTTP code**：任何”已上线 / 已接通 / 已部署”的判断，必须同时检查 response body。
2. **必须看 `_qc.status`**：`200 + _qc.status=failure` 是失败契约或兼容 stub，不是 live 功能。
3. **必须确认生产路径**：区分 `finance-suite` 工具仓、`finance-suite-web` 生产 web 仓、`8765` research demo sandbox。
4. **必须确认 router 来源**：说明请求由哪个 `app/routers/*.py` 或 demo server 处理，不能只凭 URL 存在下结论。
5. **必须检查 static drift**：确认生产 `static/app/*.html` 是否真的包含对应 UI，不接受”本地页面有”作为上线证据。
6. **必须更新事实源**：任何状态变化都要同步更新本文档、`backend_api_architecture_20260512.md`、`production_stability_guard_20260512.md` 或明确说明为什么无需更新。

### 7.2 完整证据链要求（2026-05-13 新增）

**触发条件**：任何 Agent 声称以下状态时
- “已上线”
- “已接通”
- “生产可用”
- “已部署”
- “已完成集成”

**必须同时给出 6 项证据**（缺一项都不能宣称”已上线”）：

1. **实际 upstream 来源**
   - 例：`research_digest.latest()` / `market_pulse()` / `stock_analysis()`
   - 不能只说”接通了”，必须说明具体调用哪个函数

2. **实际生产文件路径**
   - 例：`/home/ubuntu/finance-suite-web/app/routers/intel.py` line 45-60
   - 不能只说”在 intel.py”，必须给出完整路径

3. **实际 router 挂载位置**
   - 例：`main.py` line 23 `app.include_router(intel.router)`
   - 不能只说”已挂载”，必须说明在哪个文件的哪一行

4. **curl 返回 body**（不仅是 HTTP code）
   - 例：`curl -s 'https://www.touziagent.com/api/intel/research?limit=1' | python3 -m json.tool`
   - 必须包含完整 JSON body，尤其是 `_qc.status` 字段
   - 不能只说”返回 200”

5. **smoke check 结果**
   - 例：`scripts/site_smoke_check.py` 全部 OK
   - 必须包含完整输出，不能只说”通过了”

6. **实际用户可见证据**（UI / static drift / 浏览器行为）
   - 例：`curl -s 'https://www.touziagent.com/app/index.html' | grep -E '(脱水研报|fetchResearch|pane-research)'`
   - 必须证明用户真正访问到的是新版本 static
   - 必须证明 UI 元素真实存在
   - 必须证明前端真实调用了对应接口
   - 必须证明浏览器行为符合预期
   - **不能只证明后端接通，还必须证明前端接通**

**历史教训**：2026-05-12 误判
- 后端：`/api/intel/research` 返回 200 ✅
- 但：`static/app/index.html` 没有 research tab ❌
- 但：没有 `fetchResearch()` ❌
- 但：没有 `pane-research` ❌
- 结果：用户实际上看不到功能，但被误判为”已上线”

**根因**：只证明了后端接通（证据 1-5），没有证明用户可见（证据 6）

---

## 八、Release Gate 定义

**目标**：避免再次出现"HTTP 200 被误判为上线"的情况

### 8.1 什么算"research_digest 已生产上线"

必须同时满足以下 **6 个条件**：

1. ✅ **production /api/intel/research 连接 live upstream**
   - 不是 stub
   - 不是 mock
   - 真正调用 `research_digest.latest()`

2. ✅ **_qc.status != failure**
   - 返回的 `_qc.status` 必须是 `success` 或 `partial`
   - 不能是 `failure`

3. ✅ **production static/app/index.html 存在 research tab**
   - 线上 `finance-suite-web/static/app/index.html` 包含 4-tab Sidebar UI
   - 包含 `fetchResearch()` 函数
   - 包含 `pane-research` DOM 元素

4. ✅ **smoke check 通过**
   - `scripts/site_smoke_check.py` 全部 OK
   - `/api/intel/research` 返回 200 且 `_qc.status != failure`

5. ✅ **no regression**
   - 旧功能（`/app/stock.html` `/app/deep-research.html` `/app/auction.html`）正常
   - `/api/analyze` 正常
   - 登录鉴权正常

6. ✅ **fallback/haiku/sonnet 状态明确**
   - 明确知道当前是 `fallback` 还是 `haiku` 还是 `sonnet`
   - 如果是 `fallback`，必须在文档中说明原因（缺 LLM key）

### 8.2 什么不算上线

以下情况 **不算** research_digest 已上线：

- ❌ `/api/intel/research` 返回 HTTP 200，但 `_qc.status=failure`
- ❌ `/api/intel/research` 返回 HTTP 200，但 body 是 mock 数据
- ❌ 本地 `127.0.0.1:8765` 能访问，但生产访问不了
- ❌ 生产 `/api/intel/research` 能访问，但前端没有 UI
- ❌ 前端有 UI，但调用的是 mock 函数（`mockResearch()`）
- ❌ 数据能返回，但 smoke check 没跑
- ❌ smoke check 跑了，但旧功能挂了（regression）

### 8.3 验证清单

部署后必须执行以下验证：

```bash
# 1. smoke check
cd /Users/Zhuanz/finance-suite
.venv/bin/python3.12 scripts/site_smoke_check.py

# 2. 检查 _qc.status
curl -s 'https://www.touziagent.com/api/intel/research?limit=1' | python3 -m json.tool | grep '"status"'
# 预期：不是 "failure"

# 3. 检查前端 UI
curl -s 'https://www.touziagent.com/app/index.html' | grep -E '(脱水研报|fetchResearch|pane-research)'
# 预期：能找到这些关键词

# 4. 检查旧功能
curl -I 'https://www.touziagent.com/app/stock.html'
curl -I 'https://www.touziagent.com/app/deep-research.html'
curl -I 'https://www.touziagent.com/app/auction.html'
# 预期：全部 200

# 5. 检查 digest_status
curl -s 'https://www.touziagent.com/api/intel/research?limit=1' | python3 -m json.tool | grep 'digest_status'
# 预期：fallback / haiku / sonnet（明确状态）
```

### 8.4 回滚条件

如果部署后发现以下情况，必须立即回滚：

1. smoke check 任何一项失败
2. 旧功能出现 regression（5xx / 超时 / 功能异常）
3. `/api/intel/research` 返回 5xx
4. 前端 UI 白屏或报错
5. 用户无法登录

### 8.5 历史误判记录

**2026-05-12 误判**：
- **误判内容**：生产 `/api/intel/research` 返回 200 = 脱水研报已上线
- **实际情况**：那个 200 是安全 stub，`_qc.status=failure`
- **根因**：只看了 HTTP 状态码，没看 `_qc.status`
- **修复**：建立 release gate 定义，明确 6 个条件

---

**维护责任**：
- 每次生产状态变化，必须更新 §一
- 每次本地功能变化，必须更新 §二
- 每次 freeze line 变化，必须更新 §四
- 每次发现新的误判，必须记录到 §六 和 §八.5
- 每次部署前，必须检查 §八.1 的 6 个条件
- 每次部署后，必须执行 §八.3 的验证清单
