# Finance Suite 后端 API 架构（协议层定型）

**日期**：2026-05-12
**状态**：本地侧事实已固化，ECS 生产入口已做首轮只读确认（2026-05-12）
**定位**：所有接手 Agent 的**后端入口地图**。读完这份不再脑补 `/api/analyze` 这种不存在的调用链
**读者**：任何下一轮要动后端的 Agent / 工程兵 CC / 林妹妹

---

## 〇、一句话

Finance Suite 的后端是**两个仓库、两套 web 框架、两种工具调用方式、两种路由语义**拼出来的混合架构。这份文档告诉你每条边界在哪，以及为什么。

---

## 一、两个仓库（最容易搞错的第一件事）

| 仓库 | 路径 | 职责 | git? |
|---|---|---|---|
| `finance-suite` | 本地 `/Users/Zhuanz/finance-suite/` + ECS `/home/ubuntu/finance-suite/` | MCP server + 工具脚本 + 测试 + 本地 demo server | ✅ git |
| `finance-suite-web` | 仅 ECS `ubuntu@touziagent.com:/home/ubuntu/finance-suite-web/` | FastAPI 主入口、`/api/analyze`、Skill dispatcher、静态前端（线上版） | ❌ 生产目录非 git 仓 |

**关键事实**：

- `/api/analyze` **不在本地仓库**，在 `finance-suite-web/app/routers/api.py`
- 生产前端不是本地 `app/*.html`，是 `finance-suite-web/static/app/*.html`，两者可能漂移
- 生产目录不能用 `git log` 比对版本，要直接 `cat`
- 改后端必须 `sudo systemctl restart finance-suite`

---

## 二、两套 Web 框架（混合架构）

Flask 和 FastAPI 共存。分工：

| 框架 | 文件 | 装挂方式 |
|---|---|---|
| **Flask** Blueprint | `server_scripts/auth.py`（`auth_bp`）、`server_scripts/watchlist_api.py`（`watchlist_bp`） | `register_blueprint()` |
| **FastAPI** APIRouter | `server_scripts/intel_api.py`（`router = APIRouter(prefix="/api/intel")`）、`finance-suite-web/app/routers/api.py` | `include_router()` |

**共存机制（2026-05-12 SSH 已确认）**：
- 主入口是 FastAPI：`/home/ubuntu/finance-suite-web/app/main.py`
- systemd 启动：`uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4`
- `main.py` 当前 include：
  - `pages.router`
  - `api.router`
  - `admin.router`
  - `intel.router`
  - `watchlist.router`
- nginx `/api/` 反代到 `127.0.0.1:8000`

---

## 三、两种路由语义（极易混）

`/api/` 下面有两种路由设计，**不要混用**：

### 3.1 `/api/analyze` — 有 dispatcher

- 单一入口，`POST /api/analyze`，body `{skill_type, query, extra_content}`
- `skill_type` 先过 `SKILL_ALIASES`（把 `deep-research` / `deep_research` / `deepResearch` / `research` → 归一为 `industry`），再查 `SKILLS` 字典找到对应工具函数
- 这是"skill 路由"——**路由级 dispatch**，同一个 URL 根据 body 分发
- 现有 canonical skills：`industry` / `stock` / `macro` / `auction` / `video` / `meeting` …
- **`SKILL_ALIASES` 不要清理**：线上 `deep-research.html` 还在发旧 skill_type，靠 alias 兼容

### 3.2 `/api/intel/*` / `/api/watchlist/*` — 一对一映射

- 每条路由对应一个 MCP 工具或一个本地函数
- 没有 dispatcher，没有 alias，URL 即动作
- 例：生产 `GET /api/intel/research` 当前 → `finance-suite-web/app/routers/intel.py` 占位兼容路由；本地 demo `GET /api/intel/research` → `research_digest.latest()`；`POST /api/watchlist/add` → `watchlist` router

**归纳**：
- 面向"智能分析任务"（灵活、需要 skill 归一化）用 3.1
- 面向"数据面板/资源 CRUD"（稳定、URL 直读）用 3.2
- 新接口按用途选，**不要反过来**

---

## 四、两种工具调用方式

路由拿到请求后，调用下层工具有两种模式：

### 4.1 subprocess + `python -c`（现有 intel_api.py 所有路由）

```python
cmd = [sys.executable, "-c", f"""
import json, sys
sys.path.insert(0, {repr(FINANCE_SUITE_PATH)})
from mcp_server import {tool_name}
result = {tool_name}({args_str})
print(json.dumps(result, ensure_ascii=False))
"""]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
```

- 每次 HTTP 请求 fork 一个 python 子进程
- 优点：web 进程和工具进程隔离，工具崩溃不影响 web；环境变量可独立注入
- 代价：冷启动 0.3-1s，**不适合高频调用**
- 标准输出里可能混日志，用 `_loads_last_json()` 取最后一行 JSON

### 4.2 直接 import（本地 demo 采用，推荐新接口用）

```python
from research_digest import latest
result = latest(limit=30, digest_mode="batch", max_llm_per_call=0)
```

- 同进程内调用，比 subprocess 快 10 倍
- 前提：被调用模块**返回 dict**（不是 mcp_server 的 wrapped string）
- `market_intel` / `research_digest` 这种新工具**应该走这条**

**决策规则**：
- 老的 mcp_server 工具（`stock_analysis`、`market_pulse` 等）返回 `'{"_qc":...}\n\n<content>'` 字符串 → 走 subprocess
- 新工具（`market_intel`、`research_digest`）返回 dict envelope → 直接 import
- 两种都要保留，因为 mcp_server 的工具也被 Claude Code / Linmeimei 通过 MCP stdio 调用，签名不能改

---

## 五、`_qc` envelope 协议（硬规范）

所有工具返回都带质检字段 `_qc`。

### 5.1 标准 `_qc` 字段

```python
{
  "status": "success" | "partial" | "failure",
  "completeness": 0.0-1.0,        # 维度覆盖率
  "sources": ["wind", "akshare"],  # 本次实际用的数据源
  "fallback_source": "akshare",    # 降级备源，未降级为 None
  "missing_dimensions": [],
  "stale_data": [],
}
```

扩展字段（按工具）：
- `source_used` / `attempted_sources` / `fallback_triggered` / `dimension_sources`（market_pulse）
- `warnings` / `fetch_warning`（research_digest）
- `error`（failure 时）
- `note`（降级说明）

### 5.2 透传链路

```
mcp_server 工具函数
  → _wrap_response(qc, content) 返回 '{"_qc":{...}}\n\n<content>' 字符串
  → subprocess stdout
  → intel_api._parse_mcp_response(raw) 拆分 envelope 和 content
  → 返回 {"_qc": {...}, "data": {...}, "raw": "..."} 给前端
```

新工具（直接 import 路径）：
```
research_digest.latest() 返回 dict envelope {items, _qc, meta}
  → intel_api 路由直接 return
  → FastAPI 序列化 JSON
  → 前端 data._qc / data.items / data.meta
```

### 5.3 `_qc` 已知坑

**Golden-pit 双层 `_qc` 事故**（2026-05-09）：
- API 层硬编码了 `sources=["trading_system"]`
- 但 `factor_scan` 实际触发了 joinquant 降级
- 结果：前端看到"trading_system"，实际数据来自 joinquant
- 修复规则：**API 层只透传 `_qc`，不自造**。工具调用失败完全没拿到 envelope 时才兜底一个 failure `_qc`
- 位置：`server_scripts/intel_api.py` `golden_pit()` 的 `real_qc` 提取逻辑

**双层嵌套**：`factor_scan` 把真实 `_qc` 放进了 content 里（而不是只在 envelope），API 层要剥两层。这是历史包袱，**新工具不要这样写**。

---

## 六、Sidebar 前端现状（2026-05-12）

`app/index.html` 右侧情报面板：

| Tab | 当前状态 | 后端 |
|---|---|---|
| 热门讨论 | **mock** (`mockHot()`) | `/api/intel/discussions` 已存在但前端没调 |
| 热股榜 | **mock** (`mockHotStock()`) | `/api/intel/hot-stocks` 已存在但前端没调 |
| 我的自选 | 已接真接口 | `/api/watchlist/list`，失败回退 mock |
| 脱水研报 🆕 | **已通**（本地 demo 8765） | `/api/intel/research` 真实东方财富数据 |

**部署差异**：
- 本地 `app/index.html` 已经有 4 个 tab 和 `fetchResearch()`
- 线上 `finance-suite-web/static/app/index.html` 已确认还是旧版：grep 不到 `脱水研报` / `fetchResearch` / `pane-research`
- 生产 `/api/intel/research?limit=1` 返回 HTTP 200，但 body 是占位失败契约：
  ```json
  {"_qc":{"status":"failure","sources":[],"completeness":0,"error":"research route is not connected to a live upstream yet"},"data":[],"count":0}
  ```
- 因此：**生产 research route 的 200 不是 live research_digest，不代表脱水研报已上线**

---

## 七、三个子系统角色（当前与未来）

### 7.1 `server_scripts/intel_api.py`（FastAPI）
- 前缀 `/api/intel`
- 旧 3 条路由：`/xueqiu-hot` `/xueqiu-hot-stock` `/golden-pit`（subprocess 模式）
- 新 5 条路由：`/discussions` `/hot-stocks` `/watch-alerts` `/research` `/all`（直接 import 模式）
- 生产实际 router 文件是 `/home/ubuntu/finance-suite-web/app/routers/intel.py`
- `main.py` 已确认 `include_router(intel.router)`
- 当前生产 `/api/intel/research` 是占位兼容路由，返回 `_qc.status=failure`，没有接 `research_digest`

### 7.2 `server_scripts/watchlist_api.py`（Flask Blueprint）
- 前缀 `/api/watchlist`
- CRUD：`/add` `/remove` `/list`
- 维护用户自选股（持久化到 `~/.finance-suite/watchlist.json`）
- 和情报板块**分开部署**不要合并

### 7.3 `server_scripts/auth.py`（Flask Blueprint）
- `/api/login` `/api/logout` `/api/check-auth`
- SQLite 存用户（`finance_suite.db`），sha256 密码哈希
- session 在 Flask 层管理

### 7.4 `scripts/research_demo_api.py`（本地 demo，非生产）
- 只为反馈闭环存在的独立 FastAPI（127.0.0.1:8765）
- 绕过 finance-suite-web 复杂装配，直接挂 `app/*.html` 静态 + `/api/intel/research`
- 本地 localhost 跳过登录重定向，生产域名不受影响
- **不部署**，只做本地验证工具

---

## 八、设计约束和已知坑

### 8.1 为什么 `/api/analyze` 不在本地
因为生产 web 层是独立仓库 `finance-suite-web`，本地只有 MCP server 和工具脚本。接手 Agent 第一次看到"`/api/analyze` 被调用但本地找不到"时，**不要往本地 grep**，直接去 ECS。

### 8.2 为什么 `SKILL_ALIASES` 不能清理
线上 `static/app/deep-research.html` 还在用旧命名 `skill_type: 'deep-research'`。删 alias 会立刻 500。**前端和后端不同步部署**是这个约束的根因，短期解决不了。

### 8.3 为什么 subprocess 模式不能全换成 import
- MCP 工具要通过 stdio 被 Claude Code / Linmeimei 调用，签名（返回 `str`）不能改
- 改签名意味着所有 MCP client 也要同步升级
- 所以保留两条：subprocess 兼容老工具，直接 import 走新工具

### 8.4 生产目录非 git 仓
比对版本**只能 cat**，不能 `git log`。部署流程基本是 `scp` + `systemctl restart`。见 `deploy-backend.sh` 和 `project_production_ops_docs_split` memory。

### 8.5 为什么混合架构（Flask + FastAPI）没有推倒重来
- Flask 部分（auth + watchlist）是早期实现，session/Blueprint 已经稳定
- FastAPI 部分是后加的（`/api/intel`、`/api/analyze`），用 Pydantic 做请求校验
- 迁移成本高且没有即时收益，**短期继续共存**，新代码用 FastAPI
- 真要统一，选 FastAPI（支持 async、Pydantic、OpenAPI）

---

## 九、ECS 事实确认（2026-05-12 首轮）

已执行只读确认，结论如下：

| 项 | 结论 |
|---|---|
| FastAPI 主入口 | `/home/ubuntu/finance-suite-web/app/main.py` |
| systemd | `finance-suite.service`，`uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4` |
| routers | `pages/api/admin/intel/watchlist` 均 include |
| nginx | `/api/` 反代 `http://127.0.0.1:8000`，`/app/` root `/home/ubuntu/finance-suite-web/static` |
| 线上 static index | 未包含本地 4-tab research UI |
| `/api/intel/research` | 生产 HTTP 200，但只是 `_qc.status=failure` 占位 stub，不是 live upstream |

复查命令：

```bash
ssh ubuntu@touziagent.com

# 1. FastAPI 主入口
cat /home/ubuntu/finance-suite-web/app/main.py
#   看：include_router 列表、WSGIMiddleware 用法、app.mount 用法

# 2. Skill 注册表
cat /home/ubuntu/finance-suite-web/app/skills.py
#   看：SKILLS 全量 canonical list、SKILL_ALIASES 全量映射、normalize 函数

# 3. /api/analyze 实现
cat /home/ubuntu/finance-suite-web/app/routers/api.py
#   看：AnalyzeRequest 字段、错误处理、流式 vs 非流式

# 4. systemd 和 uvicorn 启动方式
systemctl cat finance-suite
#   看：ExecStart、workers 数、reload 策略、环境变量注入

# 5. nginx 反代规则（已确认：/api/ → 127.0.0.1:8000，/app/ → finance-suite-web/static）
cat /etc/nginx/sites-enabled/touziagent.conf  # 或类似路径
#   看：/api/* 反代目标、静态文件 root、websocket 支持

# 6. 线上静态前端和本地差异（已确认：线上 index 没有 research tab）
diff /home/ubuntu/finance-suite-web/static/app/index.html ~/finance-suite/app/index.html
diff /home/ubuntu/finance-suite-web/static/app/stock.html ~/finance-suite/app/stock.html
#   看：Tab 数量、fetch 调用、联动逻辑、mock 残留

# 7. intel_api 是否已经装进去（已确认：app/routers/intel.py 被 include）
grep -rn "intel_api\|intel_router" /home/ubuntu/finance-suite-web/
#   看：是否 include_router，prefix 有没有重复
```

---

## 十、接手 Agent 行动清单

```
第 1 步  读本文档 + docs/market_intel_first_render_20260512.md
第 2 步  pytest tests/ -q                         # 核心 research 应 14 passed；全量发现当前 16 passed
第 3 步  启动本地 demo: .venv/bin/python3.12 scripts/research_demo_api.py &
第 4 步  浏览器访问 127.0.0.1:8765/app/index.html 看脱水研报 tab
第 5 步  如生产事实出现漂移，再 SSH 到 ECS 按 §9 命令复查
第 6 步  对照 docs/current_system_state_20260513.md 更新事实源
第 7 步  只有在 LLM key 或明确部署窗口到位后，才讨论是否扩 intel_api / 加新接口
```

**当前 freeze line**：在 LLM key 或明确部署窗口到位前，不扩展 `intel_api`、不加新路由、不部署本地 4-tab Sidebar。ECS §9 已完成；后续只在生产事实漂移时复查。

---

## 十一、相关文档和 memory

- `docs/market_intel_sidebar_handoff_20260512.md` — Sidebar 项目级交接
- `docs/market_intel_first_render_20260512.md` — 反馈闭环时刻归档
- `docs/MCP_TOOLS_GUIDE.md` — MCP 工具目录
- `docs/research_reports_integration_proposal.md` — 海外投行研报集成
- `docs/acceptance_joinquant_qc_20260510.md` — golden-pit `_qc` 事故复盘
- `docs/project_progress_20260509.md` — 生产环境变更记录
- `docs/wind_api_diagnosis_20260510.md` — Wind 数据源诊断
- memory `reference_finance_suite_production_layout` — 生产路径索引
- memory `project_finance_suite_market_intel_sidebar` — Sidebar 当前状态
- memory `feedback_see_feedback_loop_first` — 方法论沉淀
- memory `project_production_ops_docs_split` — 运维文档结构

---

**维护责任**：
- 每次改 `server_scripts/*.py` 路由或新增接口，必须 diff 对照本文档 §三
- 每次改 `_qc` 字段或新增扩展字段，必须追加到 §五
- 每次部署产生"线上/本地漂移"，必须在 §六 记录
- ECS 入口发生变化，必须重走 §九 验证并回填
