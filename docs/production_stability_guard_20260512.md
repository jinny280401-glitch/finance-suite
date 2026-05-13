# Finance Suite 生产守夜清单

**日期**：2026-05-12  
**目标**：保证明天网站基本功能不掉线，不把本地 demo / 半成品路由误推到生产。

---

## 当前判断

生产站点当前核心静态页可达：

- `https://www.touziagent.com/app/index.html` → `200`
- `https://www.touziagent.com/app/stock.html` → `200`
- `https://www.touziagent.com/app/deep-research.html` → `200`

生产 `/api/analyze` 未登录返回 `401`，这是健康行为；不是 500/502。

生产 `/api/intel/research?limit=1` 当前返回 `200`，但 body 是占位失败契约：

```json
{"_qc":{"status":"failure","sources":[],"completeness":0,"error":"research route is not connected to a live upstream yet"},"data":[],"count":0}
```

这是预期状态：本地 research Sidebar demo 已通，但生产 web router 目前只是兼容 stub，尚未接 live `research_digest`。**不要把这个 200 当作脱水研报已上线。**

---

## 今晚硬纪律

1. 不部署 `app/index.html` 的 4 tab 本地 demo 到生产。
2. 不部署 `scripts/research_demo_api.py`，它只服务本地 8765 反馈闭环。
3. 不扩展生产 `intel_api`，不加新生产路由，直到 LLM key 或明确部署窗口到位。ECS §九已完成；后续只在生产事实漂移时复查。
4. 不做“市场情绪时钟”等需要 LLM 的产品化动作，直到 `OPENROUTER_API_KEY` / `ANTHROPIC_API_KEY` 到位并验证 `fallback → haiku/sonnet`。
5. 如必须修生产，只修现有登录、`/api/analyze`、静态页面可达性；不混入 market_intel 新功能。

---

## 明早巡检命令

```bash
cd /Users/Zhuanz/finance-suite
.venv/bin/python3.12 scripts/site_smoke_check.py
```

预期结果：

- 关键路径全部 `OK`
- `optional intel research route` 可以是 `200` 或 `404`，但若是 `200` 也必须看 `_qc.status`；当前生产是 `failure` stub，不影响明天基本功能

手动 curl 时，带 `?` 的 URL 必须加引号，避免 zsh 把 `?` 当 glob：

```bash
curl -i 'https://www.touziagent.com/api/intel/research?limit=1'
```

---

## 如果明天有故障

优先判断是不是生产基本功能：

- 静态页面 5xx / 超时：基本功能故障
- `/api/analyze` 未登录不是 401，而是 500/502/超时：基本功能故障
- `/api/intel/research` 404 或 `_qc.status=failure` stub：不是基本功能故障，本来还没接 live research_digest
- 本地 `127.0.0.1:8765` demo 不通：不是生产故障

处理顺序：

1. 先跑 `scripts/site_smoke_check.py`，确认是页面还是 API。
2. 如果页面 5xx，查 nginx 和 `finance-suite.service`。
3. 如果 `/api/analyze` 5xx，查 `finance-suite-web/app/routers/api.py` 和 skill alias。
4. 不要为了修新 Sidebar 影响旧的 `stock.html` / `deep-research.html`。

---

## 下一步解锁条件

二选一即可推进，但不要绕过：

- **LLM key 路线**：配置 key，重启本地 demo，看 `digest_status` 从 `fallback` 变成 `haiku` / `sonnet`。
- **部署窗口路线**：在明确部署窗口内，把 live `research_digest` 接入 `finance-suite-web` 生产 router，并同步生产 static；上线前后都必须跑 Release Gate。

---

## 长期守门规则

1. 不只看 HTTP code；任何“已上线 / 已接通 / 已部署”的判断必须同时检查 response body。
2. 必须看 `_qc.status`；`200 + _qc.status=failure` 是失败契约或兼容 stub，不是 live 功能。
3. 必须确认生产路径；区分 `finance-suite`、`finance-suite-web`、`8765` research demo sandbox。
4. 必须确认 router 来源；说明请求由哪个 `app/routers/*.py` 或 demo server 处理。
5. 必须检查 static drift；确认生产 `static/app/*.html` 是否真的包含对应 UI。
6. 必须更新事实源；任何状态变化都要同步更新 `current_system_state_20260513.md`、`backend_api_architecture_20260512.md`、本文档或明确说明为什么无需更新。
