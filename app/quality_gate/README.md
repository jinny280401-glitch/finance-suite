# Quality Gate - 门下省质检模块

轻量级数据质检层，用于验证 MCP 返回数据的完整性、合规性和可追溯性。

## 快速开始

```python
from quality_gate import QualityGate, QualityRules

gate = QualityGate()

# 第 1 轮质检
result = gate.check(
    data=mcp_result,
    rules=QualityRules.stockData,
    round=1
)

if result.passed:
    # 通过 → 生成报告
    reply = gate.finalize(result, lambda d: "报告内容...")
    print(reply)
else:
    # 封驳 → 补充数据
    print("封驳原因:", result.reject_reasons)
    print("需要补充:", result.required_actions)
    
    # 补充数据后重试第 2 轮
    result2 = gate.check(data=补充后的数据, rules=QualityRules.stockData, round=2)
```

## 预设规则

- `QualityRules.stockData` - 股票数据质检
- `QualityRules.financialData` - 金融数据基础质检
- `QualityRules.educationContent` - 投教内容（含风险提示）
- `QualityRules.clientAdvice` - 客户建议（含风险等级验证）

## 质检维度

1. **数据完整性** - `completeness ≥ 0.8`
2. **信源数量** - `sources ≥ 2`
3. **数值溯源** - 关键指标有来源标注
4. **数据时效** - 无过期数据
5. **合规声明** - 自动追加免责声明

## 封驳机制

- 最多 2 轮
- 第 2 轮仍不通过 → 返回"数据不足，暂不下结论"
- 每轮记录 `flow_log`（from/to/round/remark）

## 集成示例

### 林妹妹 Agent

```python
# 在 finance-suite skill 中
from quality_gate import QualityGate, QualityRules

gate = QualityGate()

# MCP 调用
mcp_result = await mcp_tool.stock_analysis(query)

# 质检
result = gate.check(mcp_result, QualityRules.stockData, round=1)

if not result.passed:
    # 补充数据
    mcp_result = await补充缺失维度(mcp_result, result.required_actions)
    result = gate.check(mcp_result, QualityRules.stockData, round=2)

# 生成报告
reply = gate.finalize(result, format_report)
```

### touziagent.com

```python
# 在 Flask /api/analyze 接口中
from quality_gate import QualityGate, QualityRules

@app.route('/api/analyze', methods=['POST'])
async def analyze():
    query = request.json['query']
    
    # MCP 调用
    mcp_result = await mcp_client.call_tool('stock_analysis', {'query': query})
    
    # 质检
    gate = QualityGate()
    result = gate.check(mcp_result, QualityRules.stockData, round=1)
    
    # 返回结果（前端根据 result.passed 显示进度条状态）
    return jsonify({
        'report': gate.finalize(result, format_report),
        '_qc': mcp_result.get('_qc'),
        'qa_result': {
            'passed': result.passed,
            'reject_reasons': result.reject_reasons
        }
    })
```

## 版本

v0.1.0 - 2026-05-04
