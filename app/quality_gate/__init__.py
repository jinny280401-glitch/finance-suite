"""
Quality Gate - 门下省质检模块

轻量级数据质检层，用于验证 MCP 返回数据的完整性、合规性和可追溯性。
支持多轮封驳机制（最多 2 轮）。

Usage:
    from quality_gate import QualityGate, QualityRules

    gate = QualityGate()
    result = gate.check(data=mcp_result, rules=QualityRules.stockData, round=1)

    if result.passed:
        reply = gate.finalize(result, generate_fn)
    else:
        # 封驳，补充数据后重试
        print(result.reject_reasons)
        print(result.required_actions)
"""

from .core import QualityGate, QualityResult
from .rules import QualityRules

__version__ = "0.1.0"
__all__ = ["QualityGate", "QualityResult", "QualityRules"]
