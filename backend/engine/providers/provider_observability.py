"""
Provider 可观测性模块

记录每次数据源调用的结构化日志，便于排查问题。
"""

import logging
import time

logger = logging.getLogger("finance_suite.provider")


def get_request_id() -> str | None:
    """返回当前请求的 trace ID（未集成时返回 None）"""
    return None


def log_provider_call(
    domain: str,
    provider: str,
    endpoint: str,
    started_at: float = 0,
    **kwargs,
) -> None:
    """
    记录一次 provider 调用的可观测性数据。

    输出示例：
        [PROVIDER] domain=capital_flow provider=akshare endpoint=stock_individual_fund_flow
                   outcome=SUCCESS_WITH_DATA rows=10 elapsed=0.32s
        [PROVIDER] domain=capital_flow provider=akshare endpoint=stock_individual_fund_flow
                   outcome=CONNECTION_ERROR exc=ConnectionError elapsed=5.01s
    """
    outcome = kwargs.get("outcome", "UNKNOWN")
    elapsed = time.monotonic() - started_at if started_at else 0
    row_count = kwargs.get("row_count")
    exc_class = kwargs.get("exception_class")
    fallback = kwargs.get("fallback_used")

    parts = [
        f"domain={domain}",
        f"provider={provider}",
        f"endpoint={endpoint}",
        f"outcome={outcome}",
    ]
    if row_count is not None:
        parts.append(f"rows={row_count}")
    if exc_class:
        parts.append(f"exc={exc_class}")
    if fallback is not None:
        parts.append(f"fallback={fallback}")
    parts.append(f"elapsed={elapsed:.2f}s")

    msg = " ".join(parts)

    # 根据 outcome 选择日志级别
    if outcome in ("SUCCESS_WITH_DATA",):
        logger.debug("[PROVIDER] %s", msg)
    elif outcome in ("VALID_EMPTY", "TIMEOUT"):
        logger.info("[PROVIDER] %s", msg)
    else:
        # CONNECTION_ERROR, UNKNOWN_ERROR 等
        logger.warning("[PROVIDER] %s", msg)


def classify_exception(e: Exception) -> str:
    """将异常分类为标准标签"""
    name = type(e).__name__
    if "timeout" in name.lower() or "Timeout" in name:
        return "TIMEOUT"
    if "connection" in name.lower():
        return "CONNECTION_ERROR"
    if "proxy" in name.lower():
        return "PROXY_ERROR"
    if "key" in name.lower() or "auth" in name.lower():
        return "AUTH_ERROR"
    return "UNKNOWN_ERROR"
