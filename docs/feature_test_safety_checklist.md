# Feature Test Safety Checklist

日期：2026-06-07  
目的：允许测试新功能，禁止生产掉线

---

## 1. 测试期间禁止修改范围

### 必须冻结（除非发现 P0 Bug）

```
research_runtime/
  ├── __init__.py
  ├── evidence_bundle.py
  ├── session.py
  ├── workflow.py
  └── events.py

docs/
  ├── trust_gate_contract.md
  ├── trust_gate_runtime_v0.md
  ├── evidence_manifest_contract_v0.md
  └── report_assembly_contract_v0.md

smoke_trust_gate_*.py（所有 Trust Gate smoke）
```

**理由：** Trust Gate Runtime Sprint 2 已 CLOSED，任何修改需重新审计。

---

## 2. 生产风险审计

### 触发生产 API 的路径

| 路径 | 触发点 | 风险等级 |
|---|---|---|
| `/api/analyze` | `.codex_remote/routers/api.py:808` `generate_analysis()` | HIGH — 调用 LLM |
| `/api/search` | `app/search.py` `unified_search()` | MEDIUM — 调用 Tavily/Exa |
| MCP 工具 | `mcp_server.py` 各工具函数 | MEDIUM — 调用 Wind/Tushare/AkShare |

### 触发生产数据库的路径

| 路径 | 操作类型 | 风险等级 |
|---|---|---|
| `/api/register` | INSERT User | MEDIUM — 写入 |
| `/api/login` | SELECT User | LOW — 只读 |
| `/api/analyze` | INSERT/UPDATE Usage | MEDIUM — 写入 |

### 触发生产 LLM 的路径

| 路径 | 模型 | 计费 | 风险等级 |
|---|---|---|---|
| `/api/analyze` | OpenRouter（详见 `app/llm.py`） | 按 token 计费 | HIGH |

### 触发生产 Auth 的路径

| 路径 | 操作 | 风险等级 |
|---|---|---|
| `/api/login` | JWT 签发 | LOW |
| `/api/register` | 新用户创建 | MEDIUM |

---

## 3. 测试分级

### Level 0：纯文档（允许）
- 阅读 `/docs/**/*.md`
- 编写新文档
- 更新 benchmark
- **无任何风险**

### Level 1：本地 mock（允许）
- 运行 `smoke_*.py` 本地测试
- `research_runtime` 本地调用
- Mock provider（不调用真实 API）
- **无生产影响**

### Level 2：Sandbox（需审批）
- 调用开发环境 API
- 使用测试账号
- 写入测试数据库
- **需确认 Sandbox 与生产隔离**

### Level 3：生产只读（需审批 + 监控）
- `/api/search`（只读，但消耗 Tavily quota）
- MCP 工具只读查询（消耗 Wind/Tushare quota）
- **需监控 API quota 消耗**

### Level 4：生产写入（默认禁止）
- `/api/register` 新用户注册
- `/api/analyze` 调用 LLM + 写入 Usage
- 数据库 schema 变更
- **需明确授权 + Rollback 准备**

---

## 4. Kill Switch

### 快速关闭服务

```bash
# SSH 登录生产服务器
ssh ubuntu@touziagent.com

# 停止后端服务
sudo systemctl stop finance-suite

# 验证
sudo systemctl status finance-suite
# 预期：inactive (dead)

# 恢复时间：<30秒
```

### 路由级别隔离

```bash
# 禁用特定路由（nginx 层）
sudo nano /etc/nginx/sites-available/finance-suite

# 注释掉高风险路由
# location /api/analyze { ... }

# 重载 nginx
sudo nginx -t && sudo nginx -s reload

# 恢复时间：<10秒
```

### 页面级别保护

```bash
# 临时下线单个页面
sudo mv /home/ubuntu/finance-suite-web/static/app/deep-research.html \
       /home/ubuntu/finance-suite-web/static/app/deep-research.html.disabled

# 用户访问时返回 404

# 恢复：
sudo mv /home/ubuntu/finance-suite-web/static/app/deep-research.html.disabled \
       /home/ubuntu/finance-suite-web/static/app/deep-research.html
```

---

## 5. Rollback Checklist

### 前置条件

- [ ] 确认当前 Git commit SHA
- [ ] 确认数据库备份存在（路径：`/home/ubuntu/backups/finance_suite.db.backup_YYYYMMDD`）
- [ ] 确认 nginx 配置备份存在（路径：`/etc/nginx/sites-available/finance-suite.backup.*`）

### 回滚步骤（代码）

```bash
# 1. SSH 登录
ssh ubuntu@touziagent.com

# 2. 停止服务
sudo systemctl stop finance-suite

# 3. 回滚代码
cd /home/ubuntu/finance-suite-web
git log --oneline -5  # 确认目标 commit
git reset --hard <SAFE_COMMIT_SHA>

# 4. 重启服务
sudo systemctl start finance-suite
sudo systemctl status finance-suite

# 5. Smoke 验证
curl -I https://touziagent.com/
# 预期：HTTP/2 200

# 恢复时间：<2分钟
```

### 回滚步骤（数据库）

```bash
# 1. 停止服务
sudo systemctl stop finance-suite

# 2. 备份当前数据库
cp /home/ubuntu/finance-suite-web/finance_suite.db \
   /home/ubuntu/backups/finance_suite.db.before_rollback_$(date +%Y%m%d%H%M%S)

# 3. 恢复备份
cp /home/ubuntu/backups/finance_suite.db.backup_YYYYMMDD \
   /home/ubuntu/finance-suite-web/finance_suite.db

# 4. 重启服务
sudo systemctl start finance-suite

# 恢复时间：<3分钟
```

### 回滚步骤（nginx）

```bash
# 1. 恢复配置
sudo cp /etc/nginx/sites-available/finance-suite.backup.YYYYMMDDHHMMSS \
        /etc/nginx/sites-available/finance-suite

# 2. 测试配置
sudo nginx -t

# 3. 重载
sudo nginx -s reload

# 恢复时间：<30秒
```

---

## 6. 验收标准

测试通过必须满足：

- [ ] **Level 0-1 测试全绿**（本地 smoke）
- [ ] **未触发 Level 4 操作**（无生产写入）
- [ ] **生产服务健康**（`systemctl status finance-suite` = active）
- [ ] **生产页面可访问**（`curl -I https://touziagent.com/` = 200）
- [ ] **无新增 untracked Runtime 资产**（`git status` 仅显示测试文件）
- [ ] **Trust Gate 未被修改**（`git diff research_runtime/` = 空）

**PASS 条件：** 以上全部勾选 ✅

**BLOCK 条件：** 任意一条 ❌

---

## 7. 当前状态

| 检查项 | 状态 |
|---|---|
| research_runtime/ 是否冻结 | ✅ tracked，未修改 |
| trust_gate smoke 是否完整 | ✅ 7个 smoke 文件存在 |
| 生产服务是否在线 | 待验证 |
| Rollback 脚本是否可用 | 待验证 |

**下一步：**

1. 验证生产服务状态（`ssh ubuntu@touziagent.com "sudo systemctl status finance-suite"`）
2. 确认最新数据库备份（`ls -lh /home/ubuntu/backups/finance_suite.db.*`）
3. 开始 Level 0-1 测试

---

**禁止事项（重申）：**

- ❌ 不修改 `research_runtime/`
- ❌ 不修改 Trust Gate 相关文件
- ❌ 不启动 Sprint 5
- ❌ 不开发新 Runtime
- ❌ 不改生产代码（除非 Rollback）

