"""
数据提供层（Provider）— 纯技术适配层

每个 Provider 是外部数据源的薄适配器，只负责"怎么调 API"，
不包含业务逻辑（"拉什么数据、怎么组合"属于 engine/skills/）。

当前包含：
  - akshare_client: AkShare 原始 API 封装（纯 Provider）
  - wind_provider: Wind API 适配
  - tushare_provider: Tushare API 适配
  - ifind_provider: iFinD API 适配
  - emquant_provider: EmQuant API 适配
  - search_provider: 搜索引擎 Provider
  - provider_observability: Provider 调用可观测性桩
"""

from backend.engine.registry import BaseProvider, ProviderResult, ProviderRegistry

__all__ = ["BaseProvider", "ProviderResult", "ProviderRegistry"]
