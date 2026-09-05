"""
Quality Gate Core - 质检核心逻辑
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class QualityResult:
    """质检结果"""
    passed: bool
    round: int
    score: float  # 0-1
    reject_reasons: list[str] = field(default_factory=list)
    required_actions: list[str] = field(default_factory=list)
    data: dict = field(default_factory=dict)
    flow_log: dict = field(default_factory=dict)


@dataclass
class QualityRule:
    """质检规则"""
    name: str
    validators: list[Callable[[dict], tuple[bool, str]]]
    min_score: float = 0.8
    required_fields: list[str] = field(default_factory=list)


class QualityGate:
    """门下省质检层"""

    MAX_ROUNDS = 2

    def __init__(self):
        self.flow_logs = []

    def check(
        self,
        data: dict,
        rules: QualityRule,
        round: int = 1
    ) -> QualityResult:
        """
        执行质检

        Args:
            data: MCP 返回的数据（必须包含 _qc 字段）
            rules: 质检规则
            round: 当前轮次（1 或 2）

        Returns:
            QualityResult
        """
        if round > self.MAX_ROUNDS:
            return QualityResult(
                passed=False,
                round=round,
                score=0.0,
                reject_reasons=["超过最大重试次数"],
                required_actions=["数据不足，暂不下结论"],
                data=data
            )

        # 提取 _qc 字段
        qc = data.get("_qc", {})
        if not qc:
            return QualityResult(
                passed=False,
                round=round,
                score=0.0,
                reject_reasons=["缺少 _qc 质检字段"],
                required_actions=["MCP 工具必须返回 _qc 字段"],
                data=data
            )

        # 计算基础分数
        completeness = qc.get("completeness", 0.0)
        status = qc.get("status", "failure")

        # 执行规则验证
        reject_reasons = []
        required_actions = []

        # 1. 检查完整性
        if completeness < rules.min_score:
            reject_reasons.append(f"数据完整性不足 ({completeness:.1%} < {rules.min_score:.0%})")
            missing = qc.get("missing_dimensions", [])
            if missing:
                required_actions.append(f"补充缺失维度：{', '.join(missing)}")

        # 2. 检查状态
        if status == "failure":
            reject_reasons.append("数据源返回失败状态")
            required_actions.append("检查数据源连接或切换备用源")

        # 3. 检查信源数量
        sources = qc.get("sources", [])
        if len(sources) < 2:
            reject_reasons.append(f"信源不足（{len(sources)} < 2）")
            required_actions.append("至少需要 2 个独立数据源交叉验证")

        # 4. 执行自定义验证器
        for validator in rules.validators:
            passed, message = validator(data)
            if not passed:
                reject_reasons.append(message)

        # 5. 检查必需字段
        for field in rules.required_fields:
            if field not in data or not data[field]:
                reject_reasons.append(f"缺少必需字段：{field}")
                required_actions.append(f"补充 {field} 数据")

        # 计算最终分数
        score = completeness if not reject_reasons else completeness * 0.5

        # 记录 flow_log
        flow_log = {
            "from": "中书省",
            "to": "门下省",
            "round": round,
            "timestamp": self._now(),
            "remark": "通过" if not reject_reasons else f"封驳：{'; '.join(reject_reasons[:2])}"
        }
        self.flow_logs.append(flow_log)

        return QualityResult(
            passed=len(reject_reasons) == 0,
            round=round,
            score=score,
            reject_reasons=reject_reasons,
            required_actions=required_actions,
            data=data,
            flow_log=flow_log
        )

    def finalize(
        self,
        result: QualityResult,
        generate_fn: Callable[[dict], str]
    ) -> str:
        """
        生成最终回复（通过质检后调用）

        Args:
            result: 质检结果
            generate_fn: 报告生成函数

        Returns:
            最终回复文本
        """
        if not result.passed:
            return "数据不足，暂不下结论。\n\n" + "\n".join(result.reject_reasons)

        # 生成报告
        report = generate_fn(result.data)

        # 追加免责声明
        disclaimer = "\n\n---\n⚠️ 以上数据仅供参考，不构成投资建议。投资有风险，决策需谨慎。"
        return report + disclaimer

    @staticmethod
    def _now() -> str:
        from datetime import datetime
        return datetime.now().isoformat()
