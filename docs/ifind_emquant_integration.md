# 同花顺 iFinD 和东方财富 Choice 数据接入文档

## 概述

Finance Suite 已集成同花顺 iFinD 和东方财富 Choice 两大数据源，作为 Wind → Tushare → JoinQuant → AkShare 降级链的补充。

**数据源定位：**
- **同花顺 iFinD**：A 股行情、财报、一致预期、指数成分股
- **东方财富 Choice**：A 股行情、财报、一致预期、同行对比、宏观经济、历史估值分位

**接入状态：**
- ✅ 代码框架已完成（`scripts/ifind_data.py` + `scripts/emquant_data.py`）
- ✅ MCP 工具已注册（`ths_query` + `emquant_query`）
- ✅ 环境变量已配置（`.env` 中账号密码已填入）
- ⚠️ SDK 未安装（需手动下载安装，见下文）

---

## 一、同花顺 iFinD 接入

### 1.1 两种接入模式

iFinD 支持两种接入方式（代码会自动选择）：

#### 模式 A：iFinDPy SDK（推荐）
- **优点**：功能完整，SDK 内部处理认证
- **缺点**：SDK 不在 PyPI，需手动下载安装
- **环境变量**：`THS_USERNAME` + `THS_PASSWORD`

#### 模式 B：HTTP REST API
- **优点**：无需安装 SDK
- **缺点**：需要从后台复制静态 `access_token`，token 有效期未知
- **环境变量**：`THS_TOKEN`

### 1.2 SDK 安装步骤（模式 A）

1. 访问同花顺量化平台：https://quantapi.10jqka.com.cn
2. 登录账号：`hfzqd132` / `Fwu56Ga2`
3. 进入"下载中心" → 下载 `iFinDPy` Python SDK 安装包（.whl 或 .tar.gz）
4. 安装到 finance-suite 虚拟环境：
   ```bash
   cd /Users/Zhuanz/finance-suite
   source .venv/bin/activate
   pip install /path/to/iFinDPy-x.x.x.whl
   ```

### 1.3 HTTP API Token 获取（模式 B）

如果不想安装 SDK，可以使用 HTTP REST API 模式：

1. 登录 https://quantapi.51ifind.com
2. 进入"个人中心" → "Token 管理"
3. 复制 `access_token`（静态 token，长期有效）
4. 写入 `.env`：
   ```bash
   THS_TOKEN=<复制的token>
   ```

### 1.4 测试连接

```bash
cd /Users/Zhuanz/finance-suite
source .venv/bin/activate

# 测试连接
python3 scripts/ifind_data.py --action connect

# 测试个股查询
python3 scripts/ifind_data.py --action stock --code 600519

# 测试财报
python3 scripts/ifind_data.py --action financials --code 600519
```

### 1.5 MCP 工具调用

```python
# 通过 MCP Server 调用
ths_query("connect")
ths_query("stock", code="600519.SH")
ths_query("financials", code="600519.SH")
ths_query("consensus", code="600519.SH")
ths_query("index", code="000300.SH")  # 沪深300成分股
```

---

## 二、东方财富 Choice 接入

### 2.1 SDK 安装（必须）

东方财富 Choice 只支持 SDK 模式，不提供 HTTP REST API。

1. 访问东方财富量化平台：https://quantapi.eastmoney.com
2. 登录账号：`hfzq80016` / `ig733405`
3. 进入"下载中心" → 下载 `EmQuantAPI` Python SDK 安装包
4. 安装到 finance-suite 虚拟环境：
   ```bash
   cd /Users/Zhuanz/finance-suite
   source .venv/bin/activate
   pip install /path/to/EmQuantAPI-x.x.x.whl
   ```

### 2.2 测试连接

```bash
cd /Users/Zhuanz/finance-suite
source .venv/bin/activate

# 测试连接
python3 scripts/emquant_data.py --action connect

# 测试个股查询
python3 scripts/emquant_data.py --action stock --code 600519

# 测试财报
python3 scripts/emquant_data.py --action financials --code 600519

# 测试宏观数据
python3 scripts/emquant_data.py --action macro
```

### 2.3 MCP 工具调用

```python
# 通过 MCP Server 调用
emquant_query("connect")
emquant_query("stock", code="600519.SH")
emquant_query("financials", code="600519.SH")
emquant_query("consensus", code="600519.SH")
emquant_query("peers", code="600519.SH", max_peers=10)
emquant_query("macro")  # GDP/CPI/PMI/M2
emquant_query("valuation", code="600519.SH")  # PE/PB 10年分位
```

---

## 三、环境变量配置

`.env` 文件已配置（不提交到 Git）：

```bash
# 同花顺 iFinD（SDK 模式：THS_USERNAME+THS_PASSWORD；HTTP 模式：THS_TOKEN 从后台复制）
THS_USERNAME=hfzqd132
THS_PASSWORD=Fwu56Ga2
THS_TOKEN=

# 东方财富 Choice EmQuantAPI（SDK 需从 quantapi.eastmoney.com 下载安装）
EM_USERNAME=hfzq80016
EM_PASSWORD=ig733405
```

`.env.example` 已更新（可提交到 Git）：

```bash
# 同花顺 iFinD（SDK 模式：THS_USERNAME+THS_PASSWORD；HTTP 模式：THS_TOKEN 从后台复制）
THS_USERNAME=
THS_PASSWORD=
THS_TOKEN=

# 东方财富 Choice EmQuantAPI（SDK 需从 quantapi.eastmoney.com 下载安装）
EM_USERNAME=
EM_PASSWORD=
```

---

## 四、代码架构

### 4.1 模块结构

```
finance-suite/
├── scripts/
│   ├── ifind_data.py       # 同花顺 iFinD 数据模块（独立 CLI）
│   ├── emquant_data.py     # 东方财富 Choice 数据模块（独立 CLI）
│   ├── wind_data.py        # Wind 数据模块（参考模板）
│   └── tushare_data.py     # Tushare 数据模块（参考模板）
├── mcp_server.py           # MCP Server 主入口
│   ├── Tool 17: ths_query
│   └── Tool 18: emquant_query
└── .env                    # 环境变量（gitignored）
```

### 4.2 降级策略

两个新数据源作为 **独立工具**，不参与现有的 Wind → Tushare → JoinQuant → AkShare 降级链。

调用方式：
- 显式调用：`ths_query("stock", code="600519")` 或 `emquant_query("stock", code="600519")`
- 不会自动降级到其他数据源

未来可以考虑：
- 在 `wind_query` 的降级链中加入 iFinD 和 Choice
- 在 `stock_analysis` 中增加多源对比逻辑

---

## 五、故障排查

### 5.1 iFinD SDK 连接失败

**现象：**
```
⚠️ iFinDPy SDK 登录失败，错误码: -1
```

**排查步骤：**
1. 确认 SDK 已安装：`pip list | grep iFinD`
2. 确认账号密码正确：`.env` 中 `THS_USERNAME` / `THS_PASSWORD`
3. 确认账号在同花顺后台有效（未过期/未欠费）
4. 尝试 HTTP API 模式（设置 `THS_TOKEN`）

### 5.2 EmQuantAPI SDK 连接失败

**现象：**
```
⚠️ EmQuantAPI 登录失败: {"ErrorCode": -1, "ErrorMsg": "..."}
```

**排查步骤：**
1. 确认 SDK 已安装：`pip list | grep EmQuant`
2. 确认账号密码正确：`.env` 中 `EM_USERNAME` / `EM_PASSWORD`
3. 确认账号在东方财富后台有效（未过期/未欠费）
4. 查看 SDK 日志（通常在 `~/.emquant/` 或当前目录）

### 5.3 SDK 未安装时的行为

代码设计了 **优雅降级**：
- SDK 未安装时，工具返回空结果 + `_qc.status = "failure"`
- 不会抛异常，不会影响其他工具运行
- MCP Server 正常启动，只是这两个工具不可用

---

## 六、排查结果与结论（2026-05-31）

### 6.1 SDK 安装状态

**同花顺 iFinD**
- ✅ SDK 已安装到服务器 `/opt/ifind/bin64/`
- ✅ 依赖库 `libidn11` 已安装
- ✅ Python import 测试通过
- ❌ 登录失败，错误码 -9

**东方财富 Choice**
- ✅ SDK 已安装到服务器 `/opt/emquant/`
- ✅ Python import 测试通过
- ❌ 登录失败，错误码 10001014（需要 Windows LoginActivator.exe 工具激活）

### 6.2 失败原因分析

**同花顺 iFinD 错误码 -9：账号未开通数据接口权限**
- 账号 `hfzqd132` 已注册，但未开通数据接口服务
- 需要联系同花顺客服（952555）申请开通
- 付费服务，价格需咨询销售

**东方财富 Choice 错误码 10001014：账号未激活**
- 账号 `hfzq80016` 已注册，但未激活数据接口
- 需要使用 Windows 的 `LoginActivator.exe` 工具激活
- Linux 服务器无法完成激活流程
- 付费服务，个人版约 3,000–8,000 元/年

### 6.3 付费信息

| 数据源 | 开通状态 | 付费标准 | 联系方式 |
|--------|---------|---------|---------|
| **同花顺 iFinD** | 未开通 | 价格面议 | 952555 |
| **东方财富 Choice** | 未激活 | 个人版 3,000–8,000 元/年 | 400-620-1818 |

### 6.4 决策与建议

**当前决策：暂时搁置，使用现有数据源**

**理由：**
1. **成本高**：两个数据源都需要付费，且价格不低
2. **数据重叠度高**：Wind + Tushare + JoinQuant + AkShare 已覆盖 A 股 90% 以上数据需求
3. **技术障碍**：东方财富需要 Windows 激活工具，服务器端无法完成
4. **ROI 不明确**：在项目验证商业价值之前，不建议增加固定成本

**代码状态：**
- ✅ 集成代码已完成（`scripts/ifind_data.py` + `scripts/emquant_data.py`）
- ✅ MCP 工具已注册（`ths_query` + `emquant_query`）
- ✅ 代码已推送到 GitHub（branch: `feature/ifind-emquant-integration`）
- ⏸️ 等待账号开通后即可激活

**未来行动：**
- 如果项目有收入后，确定需要这两个数据源的独家数据，再联系供应商开通
- 优先使用现有数据源把 Finance Suite 的核心功能跑起来

### 6.5 未来优化（如果开通）
- [ ] 将 iFinD 和 Choice 加入 `wind_query` 降级链
- [ ] 在 `stock_analysis` 中增加多源数据对比
- [ ] 增加数据缓存层（减少 API 调用次数）
- [ ] 增加 token 有效期监控（HTTP API 模式）

---

## 七、参考资料

- 同花顺量化平台：https://quantapi.10jqka.com.cn
- 同花顺 HTTP API 文档：https://quantapi.51ifind.com/doc
- 东方财富量化平台：https://quantapi.eastmoney.com
- EmQuantAPI 文档：https://quantapi.eastmoney.com/doc

---

**更新日期：** 2026-05-29  
**维护人：** 林嘉勤 (Zhuanz)
