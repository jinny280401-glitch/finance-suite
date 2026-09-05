"""
Quality Gate 测试用例
"""

import sys
from pathlib import Path

# 添加 quality-gate 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from core import QualityGate, QualityResult
from rules import QualityRules


def test_pass():
    """测试通过场景"""
    gate = QualityGate()

    # 模拟 MCP 返回的完整数据
    data = {
        "stock_name": "比亚迪",
        "stock_code": "002594",
        "price": 245.67,
        "pe": 28.5,
        "roe": 0.18,
        "_qc": {
            "status": "success",
            "completeness": 0.95,
            "missing_dimensions": [],
            "stale_data": [],
            "sources": ["东方财富", "Wind"],
            "fallback_source": None
        }
    }

    result = gate.check(data, QualityRules.stockData, round=1)

    print("✅ 测试通过场景")
    print(f"  passed: {result.passed}")
    print(f"  score: {result.score:.2f}")
    print(f"  flow_log: {result.flow_log}")

    if result.passed:
        report = gate.finalize(result, lambda d: f"{d['stock_name']} 当前价格 {d['price']} 元")
        print(f"  report: {report[:100]}...")


def test_reject():
    """测试封驳场景"""
    gate = QualityGate()

    # 模拟数据不完整
    data = {
        "stock_name": "比亚迪",
        "_qc": {
            "status": "partial",
            "completeness": 0.45,
            "missing_dimensions": ["财务数据", "资金流向"],
            "stale_data": [],
            "sources": ["东方财富"],  # 只有 1 个信源
            "fallback_source": None
        }
    }

    result = gate.check(data, QualityRules.stockData, round=1)

    print("\n🚫 测试封驳场景")
    print(f"  passed: {result.passed}")
    print(f"  score: {result.score:.2f}")
    print(f"  reject_reasons: {result.reject_reasons}")
    print(f"  required_actions: {result.required_actions}")


def test_max_rounds():
    """测试最大轮次限制"""
    gate = QualityGate()

    data = {
        "_qc": {
            "status": "failure",
            "completeness": 0.3,
            "missing_dimensions": ["所有维度"],
            "sources": []
        }
    }

    result = gate.check(data, QualityRules.stockData, round=3)

    print("\n⚠️ 测试最大轮次")
    print(f"  passed: {result.passed}")
    print(f"  reject_reasons: {result.reject_reasons}")


if __name__ == "__main__":
    test_pass()
    test_reject()
    test_max_rounds()
