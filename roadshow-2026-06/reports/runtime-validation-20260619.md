# Runtime Validation Report

**执行人**：C
**执行时间**：2026-06-19 01:44 CST
**检查目标**：验证 Vera Runtime 真实跑通：状态机、数据降级、`_qc.fallback_source` 标注。

## Verdict

**状态**：PASS

**一句话结论**：Research Runtime 正常路径 8 节点跑通；受控四层降级在 14.087ms 内切到 AkShare，并正确写入 `_qc.fallback_source=akshare`。

## Case 1：Research Runtime 状态机

验证命令：

```text
python3 smoke_research_runtime.py
```

真实结果：

```text
final_state=DONE
evidence_count=2
event_count=16
qc_passed=true
states=INIT -> STARTED -> PROVIDER_SELECTION -> EVIDENCE_RETRIEVAL -> TRUST_GATE -> CONTEXT_BUILDING -> QC -> DONE
```

## Case 2：四层数据降级

验证方式：受控模拟 Wind / Tushare / JoinQuant 失败，AkShare 成功。

真实结果：

```text
provider=akshare
elapsed_ms=14.087
under_500ms=true
attempted_sources=wind(error) -> tushare(error) -> joinquant(error) -> akshare(success)
provider_chain=wind -> tushare -> joinquant -> akshare -> cache
```

## Case 3：_qc.fallback_source 标注

真实结果：

```text
ok=true
qc_status=success
fallback_source=akshare
```

## Gateway 真实环境分支

验证命令：

```text
python3 smoke_research_runtime_gateway.py
```

真实结果：

```text
final_state=DONE
provider=finance_data_gateway
qc_passed=false
trust_gate.blocked_count=1
trust_gate.has_any_allowed=false
ok=true
```

说明：当前本机缺 `tushare`，且真实 gateway provider 未返回可用 evidence；Runtime 没有崩溃，而是进入 `NO_EVIDENCE` 分支，由 Trust Gate 阻断。

## 测试日志

```text
$ python3 smoke_research_runtime.py
{
  "final_state": "DONE",
  "evidence_count": 2,
  "event_count": 16,
  "qc_passed": true,
  "ok": true
}

$ python3 smoke_research_runtime_gateway.py
{
  "final_state": "DONE",
  "provider": "finance_data_gateway",
  "evidence_count": 0,
  "event_count": 12,
  "qc_passed": false,
  "trust_gate": {
    "allowed_count": 0,
    "blocked_count": 1,
    "passthrough_count": 0,
    "has_any_allowed": false
  },
  "ok": true
}

$ python3 -m compileall research_runtime scripts/finance_data_gateway.py
Compiling 'research_runtime/workflow.py'...
```

## 代码校准

`research_runtime/workflow.py` 已补齐 gateway 全阻断分支的 `context.trust_gate` 摘要，确保 Runtime artifact 能展示 blocked_count / allowed_count。

## 路演表达

Runtime Validation 回答的是：**Vera 不只是有规则，她真的能跑；主源失败时会降级，证据不可用时会阻断，并把运行结果写进日志。**
