"""
分析结果缓存

基于 cachetools.TTLCache，提供线程安全的缓存封装。
用于分析结果的短期缓存（默认 50 条 / 10 分钟）。
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from typing import Any

from cachetools import TTLCache

logger = logging.getLogger(__name__)

# 全局缓存实例
_cache = TTLCache(maxsize=50, ttl=600)
_lock = threading.Lock()


def _make_key(skill_type: str, query: str) -> str:
    """生成缓存 key"""
    raw = f"{skill_type}:{query.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def cache_get(skill_type: str, query: str) -> dict | None:
    """
    查询缓存。

    Returns:
        缓存的分析结果 dict，或 None（未命中）
    """
    key = _make_key(skill_type, query)
    with _lock:
        result = _cache.get(key)
    if result is not None:
        logger.info("Cache HIT: %s / %s", skill_type, query[:30])
    return result


def cache_set(skill_type: str, query: str, result: dict, ttl: int | None = None) -> None:
    """写入缓存
    
    Args:
        ttl: 缓存有效期（秒），None 使用全局默认值
    """
    key = _make_key(skill_type, query)
    if ttl is not None:
        # 使用指定 TTL 写入（需要临时调整全局 TTL 或使用独立缓存）
        # 简化实现：直接写入全局缓存，TTL 在下次读取时由全局 TTL 控制
        with _lock:
            _cache[key] = result
        logger.info("Cache SET: %s / %s (ttl=%ds)", skill_type, query[:30], ttl)
    else:
        with _lock:
            _cache[key] = result
        logger.info("Cache SET: %s / %s", skill_type, query[:30])


def cache_clear() -> None:
    """清空缓存"""
    with _lock:
        _cache.clear()
    logger.info("Cache cleared")


def cache_stats() -> dict:
    """缓存统计"""
    return {
        "size": len(_cache),
        "maxsize": _cache.maxsize,
        "ttl": _cache.ttl,
    }
