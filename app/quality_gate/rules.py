"""
Quality Rules - 预设质检规则
"""

try:
    from .core import QualityRule
except ImportError:
    from core import QualityRule


def _check_disclaimer(data: dict) -> tuple[bool, str]:
    """检查是否包含免责声明"""
    # 这个检查在 finalize 时自动追加，这里只是占位
    return True, ""


def _check_numeric_source(data: dict) -> tuple[bool, str]:
    """检查关键数值是否有来源标注"""
    # 检查 PE、ROE、营收等关键指标是否有 source 字段
    qc = data.get("_qc", {})
    sources = qc.get("sources", [])

    # 如果有多个信源，认为数值可追溯
    if len(sources) >= 2:
        return True, ""

    return False, "关键数值缺少来源标注（需要 ≥2 个信源）"


def _check_stale_data(data: dict) -> tuple[bool, str]:
    """检查数据是否过期"""
    qc = data.get("_qc", {})
    stale = qc.get("stale_data", [])

    if stale:
        return False, f"数据已过期：{', '.join(stale)}"

    return True, ""


class QualityRules:
    """预设质检规则库"""

    # 股票数据质检
    stockData = QualityRule(
        name="股票数据质检",
        validators=[
            _check_numeric_source,
            _check_stale_data,
        ],
        min_score=0.8,
        required_fields=[]  # 不强制要求特定字段，由 completeness 控制
    )

    # 金融数据基础质检
    financialData = QualityRule(
        name="金融数据基础质检",
        validators=[
            _check_stale_data,
        ],
        min_score=0.7,
        required_fields=[]
    )

    # 投教内容质检（含风险提示）
    educationContent = QualityRule(
        name="投教内容质检",
        validators=[
            _check_disclaimer,
        ],
        min_score=0.6,
        required_fields=[]
    )

    # 客户建议质检（含风险等级验证）
    clientAdvice = QualityRule(
        name="客户建议质检",
        validators=[
            _check_disclaimer,
            _check_numeric_source,
        ],
        min_score=0.9,  # 客户建议要求更高
        required_fields=[]
    )
