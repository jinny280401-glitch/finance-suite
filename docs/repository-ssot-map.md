# Repository SSOT Map — Finance Suite

> **目的**：明确 finance-suite 与 finance-suite-web 两个仓库的 source-of-truth 边界。
> **范围**：只读核验结论，不包含 deploy 操作。
> **生成时间**：2026-07-03
> **窗口**：Repository SSOT Alignment Window（只读 + 文档）

---

## 1. 两个仓库的角色

| 仓库 | 角色 | 性质 | 生产目录 |
|---|---|---|---|
| `~/finance-suite/`（**finance-suite**）| **前端静态源 + 同步起点** | git 仓库，main + feature 分支 | `jinny280401-glitch/finance-suite` on GitHub |
| `~/finance-suite-web/`（**finance-suite-web**）| **后端 FastAPI runtime + 静态落地点** | **非 git 仓库**（生产落地目录）| `119.28.156.125:/home/ubuntu/finance-suite-web/` |

**关键事实**：finance-suite-web 生产目录 `fatal: not a git repository` —— 它是 deploy.sh 通过 `curl raw.githubusercontent.com` 把 finance-suite 拉过来落地的目标，**不是 git clone**。

---

## 2. Source of Truth 矩阵（6 类资产）

### ✅ deploy.sh 覆盖范围（finance-suite → finance-suite-web）

| 生产目标文件 | source repo 路径 | main 是否含 | deploy.sh 第几行 |
|---|---|---|---|
| `templates/index.html` | `finance-suite/index.html` | ✅ | L32-33 |
| `static/app/index.html` | `finance-suite/app/index.html` | ✅ | L14-15 |
| `static/app/deep-research.html` | `finance-suite/app/deep-research.html` | ✅ | L19-20 |
| `static/app/stock.html` | `finance-suite/app/stock.html` | ✅ | L19-20 |
| `static/app/macro.html` | `finance-suite/app/macro.html` | ✅ | L19-20 |
| `static/app/auction.html` | `finance-suite/app/auction.html` | ✅ | L19-20 |
| `static/app/meeting.html` | `finance-suite/app/meeting.html` | ✅ | L19-20 |
| `static/app/video.html` | `finance-suite/app/video.html` | ✅ | L19-20 |
| `static/app/xueqiu-hot.html` | `finance-suite/app/xueqiu-hot.html` | ✅ | L19-20 |
| `static/app/workbench-config.html` | `finance-suite/app/workbench-config.html` | ✅ | L19-20 |
| `static/app/market-temperature-mini.html` | `finance-suite/app/market-temperature-mini.html` | ✅ | L19-20 |
| `static/app/sidebar-registry.js` | `finance-suite/app/sidebar-registry.js` | ✅ | L26-27 |
| `static/app/market-temperature-fixture.js` | `finance-suite/app/market-temperature-fixture.js` | ✅ | L26-27 |
| `static/app/market-temperature-mini.js` | `finance-suite/app/market-temperature-mini.js` | ✅ | L26-27 |
| `static/app/market-temperature-mini.css` | `finance-suite/app/market-temperature-mini.css` | ✅ | L26-27 |

**deploy.sh 全部走 `raw.githubusercontent.com/jinny280401-glitch/finance-suite/main/...`**（branch = `main`，**写死**）。

### ❌ deploy.sh 不覆盖（finance-suite-web 自有）

| 资产 | 路径 | 性质 |
|---|---|---|
| `app/main.py` | `finance-suite-web/app/` | FastAPI 入口 |
| `app/routers/api.py` | `finance-suite-web/app/routers/` | 业务路由 |
| `app/routers/intel.py` | `finance-suite-web/app/routers/` | intel 路由 |
| `app/routers/pages.py` | `finance-suite-web/app/routers/` | 页面路由 |
| `app/routers/watchlist.py` | `finance-suite-web/app/routers/` | 自选股路由 |
| `app/routers/admin.py` | `finance-suite-web/app/routers/` | 管理路由 |
| `app/auction_data.py` | `finance-suite-web/app/` | 数据层 |
| `app/auth.py` | `finance-suite-web/app/` | 鉴权 |
| `app/database.py` | `finance-suite-web/app/` | DB 层 |
| `app/llm.py` | `finance-suite-web/app/` | LLM 接入 |
| `app/macro_data.py` | `finance-suite-web/app/` | 宏观数据 |
| `app/search.py` | `finance-suite-web/app/` | 搜索层 |
| `app/skills.py` | `finance-suite-web/app/` | skill alias |
| `app/stock_data.py` | `finance-suite-web/app/` | 个股数据 |
| `app/video_data.py` | `finance-suite-web/app/` | 视频数据 |
| `mcp_server.py` | `finance-suite-web/` | MCP server |
| `finance_suite.db` | `finance-suite-web/` | SQLite DB |
| `requirements.txt` | `finance-suite-web/` | Python 依赖 |
| `skill.html` | `finance-suite-web/` | skill 页面 |
| `templates/admin.html` / `base.html` / `dashboard.html` / `login.html` / `pricing.html` / `register.html` | `finance-suite-web/templates/` | Jinja 模板（**除 index.html 外**）|
| `static/auth-fix.js` / `css/` / `js/` / `reset.html` / `reset2.html` / `sidebar-demo.html` | `finance-suite-web/static/` | 静态资源（**除 app/* 外**）|

### ❓ finance-suite 仓库有但 finance-suite-web 不用（dev-only / 文档）

| 资产 | 用途 |
|---|---|
| `finance-suite/scripts/` | 本地开发用脚本（`stock_data.py`, `search.py`, `news_providers.py`, `ifind_data.py`, `market_context.py`, `auction_data.py`, `watchlist.py` 等）|
| `finance-suite/prompts/` | 本地 prompt 模板 |
| `finance-suite/research_runtime/` | 调研 runtime |
| `finance-suite/mcp_server.py` | finance-suite 仓库本地的 MCP server，**生产用的是 finance-suite-web 的 mcp_server.py** |
| `finance-suite/data/` / `finance-suite/handoff/` / `finance-suite/reports/` / `finance-suite/logs/` | 本地数据/日志 |
| `finance-suite/roadshow-2026-06/` | 路演素材（dev-only）|
| `finance-suite/finance-suite-skill-v1.0.0.tar.gz` | skill 包 |
| `finance-suite/MEMORY.md` / `README.md` / `SKILL.md` / `INSTALL.md` 等 | 文档 |

---

## 3. 关键 SSOT 结论（4 个核心问题）

### Q1. Hero 首页 source of truth 是哪个 repo / 文件？

**A**：`finance-suite/index.html`（根目录）。
- 通过 `deploy.sh` L32-33 同步到 `finance-suite-web/templates/index.html`。
- **branch 写死 main**。

### Q2. Workbench source of truth 是哪个 repo / 文件？

**A**：`finance-suite/app/index.html`。
- 通过 `deploy.sh` L14-15 同步到 `finance-suite-web/static/app/index.html`。
- 配套 assets（`sidebar-registry.js`, `market-temperature-*.{js,css}`）从 `finance-suite/app/` 同步。
- **注意**：finance-suite-web 还有 `app/routers/pages.py`，它会从 `static/app/index.html` 渲染工作台页面。

### Q3. scripts/provider source of truth 是哪个 repo / 文件？

**A**：**分两层**：
- **finance-suite-web 后端实际使用**：`finance-suite-web/app/{auction_data,auth,macro_data,search,skills,stock_data,video_data,llm}.py`（**SSOT**）。
- **finance-suite/scripts/**：是 finance-suite 仓库本地的脚本库，**生产不用**。改名/搬家不影响生产。
- ⚠️ 注意命名混淆：两边都有 `auction_data.py` / `search.py` / `macro_data.py` / `stock_data.py`，**路径不同，作用也不同**。

### Q4. 当前 deploy.sh 覆盖哪些目标，不覆盖哪些目标？

**覆盖**（8 类 HTML + 4 类 assets）：
- `templates/index.html`（1 个）
- `static/app/*.html`（10 个工作台页面）
- `static/app/sidebar-registry.js` + `market-temperature-fixture.js` + `market-temperature-mini.{js,css}`（4 个 assets）

**不覆盖**：
- `app/*.py`（FastAPI 后端）
- `app/routers/*.py`（路由）
- `mcp_server.py`、`skill.html`、`skills.py`、DB
- `templates/{admin,base,dashboard,login,pricing,register}.html`（除 index.html 外的 Jinja 模板）
- `static/{auth-fix.js,css/,js/,reset*.html,sidebar-demo.html}`（除 app/ 外的静态资源）
- `data/*`（deploy.sh 0 行 data 同步）

---

## 4. 当前 Hero Live Patch Window 状态（branch/deploy-source mismatch）

### 4.1 当前状态

| 项 | 值 |
|---|---|
| Hero copy patch commit | `1a4e1e2` |
| 所在 branch | `feature/session-1-validation-outcomes` |
| main HEAD | `d352b85`（`fix(deploy): add Sidebar P0 6 new assets to deploy curl list`）|
| main:index.html md5 | `d889da26a38f843b5f6e0b0f3d6729b7` |
| 1a4e1e2:index.html md5 | `aa95cc1b349bbf323397e45f23a5c615` |
| GitHub raw main:index.html md5 | `d889da26a38f843b5f6e0b0f3d6729b7`（**等于** 本地 main md5，远程 main 同步 OK）|
| 生产 templates/index.html md5 | `2d5570e3c953ce97a4431caaf430d994`（**≠** main md5）|

### 4.2 三个 md5 三角关系

```
本地 main:index.html       d889da26a38f843b5f6e0b0f3d6729b7   ←—
   ↓                                                        ↖ 相同
远程 GitHub main:index.html d889da26a38f843b5f6e0b0f3d6729b7   ←     (本地 main = 远程 main)
                                                                   
生产 templates/index.html   2d5570e3c953ce97a4431caaf430d994   ← 不同 (落后于 main)
```

**关键发现**：生产 `templates/index.html` 与本地/远程 `main:index.html` **也不一致**（md5 差）。这说明：
1. 生产上次 deploy 早于本地 main HEAD `d352b85`
2. 或者生产用了一个 fork / 副本
3. **生产落后于 main 分支**

### 4.3 Hero Live Patch Window blocker

**新结论**（取代 source/target mismatch）：
- 1a4e1e2 在 `feature/session-1-validation-outcomes` 分支
- deploy.sh 写死从 `main` 分支拉取
- **Hero copy patch 不会通过 deploy.sh 自动进入生产**
- 即使合并到 main，deploy.sh 不会自动跑（生产需手动 ssh 触发 deploy.sh）
- **blocker = branch/deploy-source mismatch**（不是 target path unknown）

---

## 5. Hero Copy 上线 4 条候选路径（**未授权，仅文档**）

| 路径 | 步骤 | 风险 | 状态 |
|---|---|---|---|
| A. PR 1a4e1e2 → main，再跑 deploy.sh | feature → main merge；触发 deploy.sh 拉 main | main 受影响；触发 nginx reload；deploy.sh 改 nginx conf | 🔴 未授权 |
| B. 直接 rsync /tmp/hero-live-1a4e1e2/index.html 到生产 templates/ | 跳过 deploy.sh | 跳过备份+验证+nginx reload | 🔴 2026-07-02 已尝试，backup 留存但未 deploy |
| C. 在 finance-suite-web 仓库独立打 patch | 单独 commit finance-suite-web/index.html，绕过 deploy.sh | 偏离 SSOT，引入第二个 source of truth | 🔴 未授权 |
| D. 改 deploy.sh 加 multi-branch 支持 | 改 deploy.sh，加 `BRANCH=${BRANCH:-main}` 变量 | 改 deploy.sh（G 禁止）| 🔴 禁止 |

**当前 G 决策**：都不动，1a4e1e2 留本地，等 finance-suite-web production patch window 新窗口。

---

## 6. SSOT 维护纪律

1. **不要把 finance-suite 仓库的本地改动**（working tree / unpushed commit）当作"已上线" —— 走 deploy.sh 才会同步
2. **不要从 finance-suite-web 生产目录回推**到 finance-suite —— 生产是非 git 仓库，回推路径不成立
3. **不要混用两个仓库的 scripts/** —— 同名不同源
4. **生产 deploy 走 deploy.sh** —— 任何绕过 deploy.sh 的"快速同步"都视为偏离 SSOT
5. **branch 写死 main** —— feature 分支的 patch 不会自动同步到生产
6. **deploy.sh 同时改 nginx 配置** —— 跑 deploy.sh 会触发 `nginx -t` + `systemctl reload nginx`，需要独立审视

---

## 7. 关联

- [[project_finance_suite_hero_live_patch_cancelled]] — Hero Live Patch Window CLOSED 详情
- [[project_finance_suite_hero_copy_tianji]] — 1a4e1e2 文案 commit 详情
- [[reference_finance_suite_production_layout]] — finance-suite-web 后端布局（路由器 / app/）
- [[reference_production_webroot]] — 8.138.2.55 vs 119.28.156.125 边界
- [[feedback_deployment_evidence_chain]] — 部署声明必须提供 6 项证据链
- [[feedback_failed_to_fetch_is_auth_not_backend]] — Failed to fetch 默认查 client 侧

---

**生成方式**：纯只读 + ssh 探活 + git ls-tree + curl raw.githubusercontent.com 比对
**未触动**：finance-suite、finance-suite-web、deploy.sh、production templates/、production static/
**未跑**：deploy.sh
**未 push**：1a4e1e2
