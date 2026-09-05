"""
Finance Suite 场景引擎

核心设计：框架是发动机，场景是燃料盒。换场景不换框架。

引擎层（engine/）是稳定的，新增场景不需要修改引擎代码。
每个场景 = config.yaml（数据源声明）+ prompt.md（写作模板）+ qc_rules.yaml（质检规则）
"""

from backend.engine.registry import ScenarioRegistry, ProviderRegistry

__all__ = ["ScenarioRegistry", "ProviderRegistry"]
