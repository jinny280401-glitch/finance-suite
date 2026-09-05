"""
场景注册中心 + Provider 注册中心

ScenarioRegistry: 自动扫描 scenarios/ 目录，加载所有场景配置
ProviderRegistry: 管理所有数据提供者的注册和获取
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


# ── 数据模型 ─────────────────────────────────────────────────────

@dataclass
class ProviderConfig:
    """单个数据源配置（来自 config.yaml 的 providers 列表项）"""
    type: str                           # provider 类型名，如 "akshare_stock"
    config: dict = field(default_factory=dict)  # provider 特定配置


@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    ttl: int = 600                      # 秒


@dataclass
class QCConfig:
    """质量检查配置"""
    min_completeness: float = 0.8
    min_sources: int = 2
    require_structured: bool = False
    hallucination_check: bool = True
    dimensions: dict[str, dict] = field(default_factory=dict)  # {dim: {required, stale_days}}


@dataclass
class ScenarioConfig:
    """
    场景完整配置

    每个 scenarios/<name>/ 目录包含:
    - config.yaml  → name, description, icon, color, skill, dimensions, providers, cache, qc
    - prompt.md    → LLM 系统指令（写作模板）
    - qc_rules.yaml → 自定义质检规则（可选）
    - page.html    → 前端页面（可选）
    """
    name: str
    display_name: str = ""
    description: str = ""
    icon: str = ""
    color: str = ""
    search_type: str = ""

    skill: str = ""                          # Skill 模块名（如 stock_skill）
    dimensions: list[str] = field(default_factory=list)  # 数据维度列表

    providers: list[ProviderConfig] = field(default_factory=list)
    cache: CacheConfig = field(default_factory=CacheConfig)
    qc: QCConfig = field(default_factory=QCConfig)

    prompt: str = ""                    # prompt.md 内容
    qc_rules: dict = field(default_factory=dict)  # qc_rules.yaml 内容
    skip_llm: bool = False              # 是否跳过 LLM（如竞价 QC 不通过时）

    # 运行时元数据
    source_dir: Path | None = None      # 场景目录路径


@dataclass
class ProviderResult:
    """数据提供者的标准返回"""
    text: str = ""                      # 格式化后的文本（喂给 LLM 的参考资料）
    sources: list[dict] = field(default_factory=list)  # [{title, url, content}]
    has_structured: bool = False        # 是否有结构化数据（AkShare）
    raw_data: dict = field(default_factory=dict)  # 原始数据（供 QC 使用）
    error: str | None = None            # 错误信息


@dataclass
class QCResult:
    """质量检查结果"""
    passed: bool = True
    blocked: bool = False               # 是否阻断流程
    score: float = 1.0
    status: str = "success"             # success / partial / failure / insufficient_data
    reject_reasons: list[str] = field(default_factory=list)
    hallucination_risk: str = "low"     # low / medium / high
    matched_count: int = 0
    data_availability: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "blocked": self.blocked,
            "score": self.score,
            "status": self.status,
            "reject_reasons": self.reject_reasons,
            "hallucination_risk": self.hallucination_risk,
            "matched_count": self.matched_count,
            "data_availability": self.data_availability,
        }


# ── Provider 基类 ────────────────────────────────────────────────

class BaseProvider(ABC):
    """
    所有数据源的基类。

    新增数据源只需:
    1. 继承 BaseProvider
    2. 实现 fetch() 方法
    3. 用 ProviderRegistry.register() 注册
    """

    @abstractmethod
    async def fetch(self, query: str, config: dict) -> ProviderResult:
        """
        获取数据。

        Args:
            query: 用户查询（如股票代码/名称/URL）
            config: provider 特定配置（来自 config.yaml）

        Returns:
            ProviderResult: 标准化的数据结果
        """
        ...

    def validate(self, result: ProviderResult) -> QCResult:
        """数据质量自检（可选覆盖）。"""
        if result.error:
            return QCResult(passed=False, status="failure", reject_reasons=[result.error])
        return QCResult(passed=True)


# ── 注册中心 ─────────────────────────────────────────────────────

class ProviderRegistry:
    """Provider 注册中心（类级别单例）"""

    _providers: dict[str, type[BaseProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_class: type[BaseProvider]) -> None:
        """注册一个 Provider"""
        cls._providers[name] = provider_class
        logger.debug("Provider registered: %s", name)

    @classmethod
    def get(cls, name: str) -> BaseProvider | None:
        """获取 Provider 实例"""
        provider_class = cls._providers.get(name)
        if provider_class is None:
            logger.warning("Provider not found: %s", name)
            return None
        return provider_class()

    @classmethod
    def list(cls) -> list[str]:
        """列出所有已注册的 Provider"""
        return list(cls._providers.keys())


class ScenarioRegistry:
    """
    场景注册中心

    自动扫描 scenarios/ 目录，加载所有场景配置。
    新增场景只需在 scenarios/ 下创建目录，无需修改代码。
    """

    def __init__(self, scenarios_dir: Path | str | None = None):
        self.scenarios: dict[str, ScenarioConfig] = {}
        if scenarios_dir is None:
            scenarios_dir = Path(__file__).parent.parent / "scenarios"
        self._scenarios_dir = Path(scenarios_dir)
        self._scan()

    def _scan(self) -> None:
        """扫描 scenarios/ 目录，加载所有场景"""
        if not self._scenarios_dir.exists():
            logger.warning("Scenarios directory not found: %s", self._scenarios_dir)
            return

        for scenario_dir in sorted(self._scenarios_dir.iterdir()):
            if not scenario_dir.is_dir():
                continue
            config_file = scenario_dir / "config.yaml"
            if not config_file.exists():
                continue

            try:
                scenario = self._load_scenario(scenario_dir)
                self.scenarios[scenario.name] = scenario
                logger.info("Scenario loaded: %s (%s)", scenario.name, scenario.display_name)
            except Exception as e:
                logger.error("Failed to load scenario %s: %s", scenario_dir.name, e)

    def _load_scenario(self, scenario_dir: Path) -> ScenarioConfig:
        """加载单个场景配置"""
        # 读取 config.yaml
        config_data = yaml.safe_load((scenario_dir / "config.yaml").read_text(encoding="utf-8"))
        if config_data is None:
            config_data = {}

        # 读取 prompt.md
        prompt_file = scenario_dir / "prompt.md"
        prompt = prompt_file.read_text(encoding="utf-8") if prompt_file.exists() else ""

        # 读取 qc_rules.yaml（可选）
        qc_file = scenario_dir / "qc_rules.yaml"
        qc_rules = {}
        if qc_file.exists():
            qc_rules = yaml.safe_load(qc_file.read_text(encoding="utf-8")) or {}

        # 解析 providers
        providers = []
        for p in config_data.get("providers", []):
            providers.append(ProviderConfig(
                type=p["type"],
                config=p.get("config", {}),
            ))

        # 解析 cache
        cache_data = config_data.get("cache", {})
        cache = CacheConfig(
            enabled=cache_data.get("enabled", True),
            ttl=cache_data.get("ttl", 600),
        )

        # 解析 qc
        qc_data = config_data.get("qc", {})
        qc = QCConfig(
            min_completeness=qc_data.get("min_completeness", 0.8),
            min_sources=qc_data.get("min_sources", 2),
            require_structured=qc_data.get("require_structured", False),
            hallucination_check=qc_data.get("hallucination_check", True),
            dimensions=qc_data.get("dimensions", {}),
        )

        return ScenarioConfig(
            name=scenario_dir.name,
            display_name=config_data.get("name", scenario_dir.name),
            description=config_data.get("description", ""),
            icon=config_data.get("icon", ""),
            color=config_data.get("color", ""),
            search_type=config_data.get("search_type", ""),
            skill=config_data.get("skill", ""),
            dimensions=config_data.get("dimensions", []),
            providers=providers,
            cache=cache,
            qc=qc,
            prompt=prompt,
            qc_rules=qc_rules,
            skip_llm=config_data.get("skip_llm", False),
            source_dir=scenario_dir,
        )

    def get(self, name: str) -> ScenarioConfig | None:
        """获取场景配置"""
        return self.scenarios.get(name)

    def list(self) -> list[dict]:
        """列出所有场景（用于 API 返回）"""
        return [
            {
                "name": s.name,
                "display_name": s.display_name,
                "description": s.description,
                "icon": s.icon,
                "color": s.color,
            }
            for s in self.scenarios.values()
        ]

    def __contains__(self, name: str) -> bool:
        return name in self.scenarios

    def __len__(self) -> int:
        return len(self.scenarios)

    def get_metadata(self, name: str) -> dict | None:
        """获取场景元数据（name/description/icon/color/search_type/prompt）。"""
        s = self.scenarios.get(name)
        if s is None:
            return None
        return {
            "name": s.display_name,
            "description": s.description,
            "icon": s.icon,
            "color": s.color,
            "search_type": s.search_type or None,
            "prompt_template": s.prompt,
        }

    def list_metadata(self) -> list[dict]:
        """列出所有场景元数据（含 type 键，供前端展示）。"""
        return [
            {
                "type": key,
                "name": s.display_name,
                "description": s.description,
                "icon": s.icon,
                "color": s.color,
            }
            for key, s in self.scenarios.items()
        ]


# ── 别名 + 规范化 ──────────────────────────────────────────────────

SCENARIO_ALIASES = {
    "deep-research": "industry",
    "deep_research": "industry",
    "deepResearch": "industry",
    "research": "industry",
}


def normalize_scenario_type(skill_type: str) -> str:
    """Return the canonical scenario type for legacy/frontend aliases."""
    return SCENARIO_ALIASES.get(skill_type, skill_type)
