"""
Unified news provider adapters.

Layer ownership: Layer 3 Research Runtime.

This module only calls provider APIs and reports observed runtime facts from
scripts.search v2 results. It must not perform Trust Gate decisions, Evidence
Contract upgrades, ProviderClass inference, or workflow-level conclusions.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable, Sequence

try:
    from scripts.search import (
        NewsProviderResult,
        RuntimeState,
        brave_news_v2,
        brave_search_v2,
        tavily_search_v2,
    )
except ModuleNotFoundError:  # Allows direct execution from scripts/.
    from search import (  # type: ignore
        NewsProviderResult,
        RuntimeState,
        brave_news_v2,
        brave_search_v2,
        tavily_search_v2,
    )


ProviderCall = Callable[[str, int], Awaitable[NewsProviderResult]]

DEFAULT_NEWS_PROVIDERS: tuple[str, ...] = ("brave_news", "tavily_news")


async def _call_tavily_news(query: str, max_results: int) -> NewsProviderResult:
    return await tavily_search_v2(
        query,
        topic="news",
        max_results=max_results,
        time_range="week",
    )


async def _call_brave_news(query: str, max_results: int) -> NewsProviderResult:
    return await brave_news_v2(query, max_results=max_results)


async def _call_brave_web(query: str, max_results: int) -> NewsProviderResult:
    return await brave_search_v2(query, max_results=max_results)


NEWS_PROVIDER_REGISTRY: dict[str, ProviderCall] = {
    "brave_news": _call_brave_news,
    "tavily_news": _call_tavily_news,
    "brave_web": _call_brave_web,
}


def dedupe_news_items(items: Iterable[dict]) -> list[dict]:
    """Deduplicate provider items by URL while preserving item structure."""
    seen_urls: set[str] = set()
    unique: list[dict] = []
    for item in items:
        url = item.get("url", "")
        if url:
            if url in seen_urls:
                continue
            seen_urls.add(url)
        unique.append(item)
    return unique


async def fetch_news_provider(
    provider: str,
    query: str,
    max_results: int = 5,
) -> NewsProviderResult:
    """Call one registered news provider and return its runtime observation."""
    call = NEWS_PROVIDER_REGISTRY.get(provider)
    if call is None:
        return NewsProviderResult(
            provider=provider,
            runtime_state=RuntimeState.UNAVAILABLE,
            items=[],
            reason="provider_not_registered",
        )
    return await call(query, max_results)


async def fetch_news_providers(
    query: str,
    max_results: int = 5,
    providers: Sequence[str] = DEFAULT_NEWS_PROVIDERS,
) -> list[NewsProviderResult]:
    """
    Call providers in order and return their observed runtime results.

    RuntimeState values are provider observations from scripts.search v2. This
    function does not reinterpret REAL as FALLBACK or upgrade evidence levels.
    """
    results: list[NewsProviderResult] = []
    for provider in providers:
        results.append(await fetch_news_provider(provider, query, max_results))
    return results


async def unified_news_search_v2(
    query: str,
    max_results: int = 5,
    providers: Sequence[str] = DEFAULT_NEWS_PROVIDERS,
) -> tuple[list[dict], list[NewsProviderResult]]:
    """
    Return deduped news items plus provider runtime observations.

    Items preserve the existing {title, url, content} structure. Provider
    observations are returned separately for future Layer 0/0.5 consumers.
    """
    provider_results = await fetch_news_providers(
        query=query,
        max_results=max_results,
        providers=providers,
    )
    items = dedupe_news_items(
        item for result in provider_results for item in result.items
    )
    return items, provider_results
