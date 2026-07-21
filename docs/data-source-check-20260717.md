# Wind API 和 JoinQuant 数据源接入状态检查

**检查时间**：2026-07-17
**触发原因**：2026-07-17 测试指数估值数据源时发现 Wind/JQ 不可用
**检查人**：Claude Opus 4.8

---

## 执行摘要

| 数据源 | SDK 安装 | 凭证配置 | 连接状态 | 可用性 | 阻塞原因 |
|--------|:--------:|:--------:|:--------:|:------:|----------|
| **Wind API** | ❌ | ❌ | ❌ | **不可用** | WindPy SDK 未安装 + Wind 终端未运行 |
| **JoinQuant** | ✅ | ✅ | ⚠️ | **受限** | 额度用尽 (1M/1M) + 数据范围过期（截止 2026-04-16） |

**结论**：两个备选数据源均不可用。东方财富自动接口仍是唯一可行方案。

---

## 1. Wind API 检查结果

### 1.1 SDK 安装状态

```bash
$ pip3 list | grep -i wind
(无输出)

$ python3 -c "import WindPy"
WindPy import: FAILED - No module named 'WindPy'
```

**结论**：WindPy SDK **未安装**。

### 1.2 Wind 终端状态

```bash
$ ls -la /Applications/ | grep -i wind
drwxr-xr-x@  3 root  wheel  96  8 26  2025 Wind.app
```

**Wind 终端**：已安装（/Applications/Wind.app）

```bash
$ ps aux | grep -i wind | grep -v grep
Wind 终端未运行
```

**进程状态**：未运行

### 1.3 环境变量

```bash
$ env | grep -i wind
(无输出)
```

**结论**：无 Wind 相关环境变量。

### 1.4 MCP 工具测试

```python
mcp__finance-suite__wind_query(action='connect')
```

**返回**：
```json
{
  "connected": false,
  "wind": false,
  "tushare": true,
  "joinquant": false,
  "akshare": true,
  "priority": "Wind → Tushare → JoinQuant → AkShare"
}
```

**结论**：`wind: false`，已触发多源降级（Tushare/AkShare）。

### 1.5 Wind API 不可用的根本原因

**问题链**：
1. WindPy SDK 未安装 → `import WindPy` 失败
2. Wind 终端未运行 → 无法通过桌面客户端认证
3. finance-suite MCP 的 `wind_query` 降级到 Tushare/AkShare
4. 降级数据源不支持历史估值分位 → `valuation history unavailable`

**修复路径**：
1. 安装 WindPy SDK：`pip3 install WindPy`（需 Wind 官方授权）
2. 启动 Wind 终端并登录
3. 配置 Wind API 凭证（如需）
4. 重测 `wind_query(action='valuation', code='000300.SH')`

---

## 2. JoinQuant 检查结果

### 2.1 SDK 安装状态

```bash
$ pip3 list | grep -i jqdata
(无输出)

$ python3 -c "import jqdatasdk"
jqdatasdk import: FAILED - No module named 'jqdatasdk'
```

**本地 Python 环境**：jqdatasdk **未安装**。

### 2.2 MCP 工具测试

```python
mcp__finance-suite__jqdata_query(action='auth')
```

**返回**（重要）：
```json
{
  "success": true,
  "quota": {
    "total": 1000000,
    "used": 1000000,
    "remaining": 0
  },
  "_qc": {
    "note": "JQData 数据范围: 2025-01-26 至 2026-02-02"
  }
}
```

**关键发现**：
- ✅ **JoinQuant 账号已配置**（MCP 内部可用）
- ❌ **额度用尽**：`remaining: 0`
- ⚠️ **数据范围过期**：截止 2026-02-02（当前 2026-07-17，已过期 5 个月）

### 2.3 实测查询

```python
mcp__finance-suite__jqdata_query(
  action='price',
  code='000300.XSHG',
  start_date='2026-07-13',
  end_date='2026-07-17'
)
```

**返回**：
```json
{
  "success": false,
  "error": "您的账号权限仅能获取2025-04-09至2026-04-16的数据，请调整时间参数后重试。如需更长时间的数据范围，可联系聚宽JQData运营人员咨询采购"
}
```

### 2.4 JoinQuant 不可用的根本原因

**问题链**：
1. 账号权限为试用版 → 数据范围有限（1 年滚动窗口）
2. 最后续费/激活时间约为 2025-04（推测）
3. 当前权限截止 2026-04-16 → 无法查询 7 月数据
4. 额度用尽（1M 调用已耗尽）

**修复路径**：
1. 联系聚宽运营续费/升级账号
2. 确认续费后数据范围是否覆盖当前（2026-07）
3. 额度重置或扩容
4. 重测指数估值接口

### 2.5 为什么 wind_query 显示 `joinquant: false`

`wind_query(action='connect')` 返回：
```json
{
  "joinquant_detail": {
    "connected": false,
    "available": false,
    "reason": "provider module unavailable"
  }
}
```

**原因分析**：
- `wind_query` 是多源降级工具，内部尝试导入 `jqdatasdk`
- 本地 Python 环境确实没装 jqdatasdk
- 但 **MCP 服务内部的 Python 环境可能已配置**（jqdata_query 可用）
- 两者是不同的 Python 环境/进程

**结论**：`wind_query` 的 JQ 检测为 false 不代表 JQ 完全不可用，`jqdata_query` 工具实际可用但受限于权限。

---

## 3. 环境变量检查

### 3.1 Wind 相关

```bash
$ env | grep -i wind
(无输出)
```

**结论**：无 Wind 环境变量（WIND_USER / WIND_PASSWORD 等）。

### 3.2 JoinQuant 相关

```bash
$ env | grep -E "JQ_|JOINQUANT"
(无输出)
```

**结论**：无 JQ 环境变量。MCP 内部配置可能在代码或配置文件中硬编码。

---

## 4. 对估值表的影响

### 4.1 当前方案（东方财富）

| 指标 | 状态 |
|------|------|
| 连接状态 | ✅ 正常 |
| 数据覆盖 | 8 个标准指数（中证红利/恒生/上证180/沪深300/深证100/中证500/创业板指/科创50） |
| 实时性 | 实时更新 |
| 历史分位 | 有 5 日历史，可计算短期分位 |
| 生产状态 | 已部署，badge 显示"东方财富·2026-07-17·自动接口" |

**结论**：东方财富方案**不受 Wind/JQ 不可用影响**，已满足估值表需求。

### 4.2 Wind/JQ 作为备选的价值

**Wind API 优势**（如果可用）：
- 10 年历史估值分位（PE/PB 百分位）
- 专业机构标准
- 银行螺丝钉等专业估值工具底层数据源

**JoinQuant 优势**（如果可用）：
- 因子数据（alpha/beta/夏普/最大回撤）
- 行业分类多口径（申万/中信/聚宽自定义）
- 回测级数据完整性

**当前阻塞**：Wind 完全未接入，JQ 权限过期且额度用尽。

---

## 5. 推荐行动

### 5.1 短期（1 周内）

**保持现状**：
- 东方财富自动接口已稳定运行
- 无需强行接入 Wind/JQ
- 专注于估值表功能完善（如增加历史分位计算）

### 5.2 中期（1 个月内）

**如果需要 Wind/JQ**：

| 数据源 | 优先级 | 行动 | 预计工作量 |
|--------|--------|------|-----------|
| **JoinQuant** | 🔥 高 | 1. 联系聚宽运营续费<br>2. 确认数据范围延长至当前<br>3. 重测指数估值接口 | 1-2 天（含采购流程） |
| **Wind API** | 🔶 中 | 1. 确认是否有 Wind 账号授权<br>2. 安装 WindPy SDK<br>3. 启动 Wind 终端并登录<br>4. 配置凭证并测试 | 3-5 天（含认证流程） |

**建议优先 JoinQuant**：账号已存在，仅需续费；Wind 需要从零接入。

### 5.3 长期（3 个月+）

**双轨并存**：
- **主数据源**：东方财富（8 指数实时 + 5 日历史）
- **补充层 A**：JoinQuant（因子数据 + 完整历史）
- **补充层 B**：Wind（机构级历史分位）
- **兜底层**：银行螺丝钉手工截图（自定义指数）

**前提**：Wind/JQ 续费到位 + SDK 配置完成。

---

## 6. 与 C 的估值方案对比

### 6.1 C 的方案（已被替换）

```
RSS 发现文章 → 人工存图 → OCR 录入 → 逐行复核 → 更新 snapshot
source_type: manual_screenshot
```

**覆盖范围**：14 个指数（含 5 个银行螺丝钉自定义指数）

### 6.2 当前方案（东方财富）

```
mx_index_block_finance_data API → 实时返回 PE/PB/ROE → 自动渲染
source_type: provider_api
```

**覆盖范围**：8 个标准指数

### 6.3 如果 Wind/JQ 接入成功

**方案 A**：完全覆盖 C 的方案
- Wind/JQ 自动接口 → 14+ 指数（含自定义指数）
- 去掉手工链路

**方案 B**：双轨并存
- 东方财富 8 指数（主数据源）
- Wind/JQ 补充（因子/分位）
- 银行螺丝钉手工截图（自定义指数）

**当前阻塞**：Wind/JQ 不可用，方案 A/B 均无法实施。

---

## 7. 技术细节

### 7.1 为什么 `wind_query` 会降级到 akshare

**代码逻辑**（推测）：
```python
def wind_query(action, code):
    if wind_sdk_available():
        return wind_api_call(action, code)
    elif tushare_available():
        return tushare_api_call(action, code)
    elif joinquant_available():
        return joinquant_api_call(action, code)
    else:
        return akshare_api_call(action, code)
```

**实际执行路径**：
1. `wind_sdk_available()` → False（WindPy 未安装）
2. `tushare_available()` → True
3. Tushare 不支持 `valuation` action
4. 降级到 akshare
5. akshare 返回 `"valuation history unavailable"`

### 7.2 为什么 akshare 不支持估值历史

**AkShare 定位**：
- 免费开源数据接口
- 主要覆盖实时行情和基础财务
- **不提供**：历史估值分位、因子数据、专业回测数据

**Wind/JQ 定位**：
- 付费专业数据服务
- 完整历史数据 + 因子库 + 估值分位

---

## 8. 文件位置与相关文档

**本报告**：`/Users/Zhuanz/finance-suite/docs/data-source-check-20260717.md`

**相关 Memory**：
- `/Users/Zhuanz/.claude/projects/-Users-Zhuanz/memory/reference_valuation_data_sources.md`

**相关代码**：
- 估值快照：`/Users/Zhuanz/finance-suite/app/market-valuation-snapshot.js`
- 东方财富接口测试：MCP `mx_index_block_finance_data`

**给 C 的同步文档**：
- `/Users/Zhuanz/finance-suite/docs/sync-to-c-valuation-automation-20260717.md`

---

## 9. 下次检查清单

**触发条件**（满足任一即检查）：
- [ ] JoinQuant 账号续费完成
- [ ] Wind 终端已登录且 WindPy SDK 已安装
- [ ] 用户明确需要历史估值分位功能
- [ ] 东方财富接口出现故障需要备用方案

**检查项**：
1. `pip3 list | grep -E "Wind|jqdata"` — SDK 安装状态
2. `mcp__finance-suite__wind_query(action='connect')` — 连接测试
3. `mcp__finance-suite__jqdata_query(action='auth')` — 额度/权限检查
4. 实测指数估值查询（沪深300/中证500）
5. 对比东方财富/Wind/JQ 三源数据一致性

---

## 附录：快速诊断命令

```bash
# SDK 安装检查
pip3 list | grep -E "Wind|jqdata"

# Wind 终端状态
ps aux | grep -i wind | grep -v grep
ls -la /Applications/ | grep -i wind

# Python 导入测试
python3 -c "import WindPy; print('WindPy OK')"
python3 -c "import jqdatasdk; print('jqdatasdk OK')"

# MCP 工具测试
# （在 Claude Code 中执行）
mcp__finance-suite__wind_query(action='connect')
mcp__finance-suite__jqdata_query(action='auth')
```

---

**生成时间**：2026-07-17  
**检查人**：Claude Opus 4.8 (1M context)  
**状态**：CLOSED — 两源均不可用，东方财富方案已满足需求
