import httpx
from typing import Optional

from app.config import settings


async def tavily_search(
    query: str,
    topic: str = "general",
    max_results: int = 5,
    time_range: str = "week",
    include_domains: list[str] | None = None,
) -> list[dict]:
    """
    Search via Tavily API.
    Returns list of {title, url, content}.
    """
    key = settings.get_tavily_key()
    if not key:
        return []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.tavily.com/search",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "query": query,
                    "topic": topic,
                    "max_results": max_results,
                    "time_range": time_range,
                    "include_answer": False,
                    **({"include_domains": include_domains} if include_domains is not None else {}),
                },
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                }
                for r in results
            ]
    except Exception:
        return []


async def brave_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Web search via Brave Search API.
    Returns list of {title, url, content}.
    """
    key = settings.get_brave_key()
    if not key:
        return []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "X-Subscription-Token": key,
                },
                params={"q": query, "count": max_results, "search_lang": "zh", "country": "cn"},
            )
            resp.raise_for_status()
            data = resp.json()
            web_results = data.get("web", {}).get("results", [])
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("description", ""),
                }
                for r in web_results
            ]
    except Exception:
        return []


async def brave_news(query: str, max_results: int = 5) -> list[dict]:
    """
    News search via Brave Search API.
    Returns list of {title, url, content}.
    """
    key = settings.get_brave_key()
    if not key:
        return []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                "https://api.search.brave.com/res/v1/news/search",
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "X-Subscription-Token": key,
                },
                params={"q": query, "count": max_results, "search_lang": "zh", "country": "cn"},
            )
            resp.raise_for_status()
            data = resp.json()
            news_results = data.get("results", [])
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("description", ""),
                }
                for r in news_results
            ]
    except Exception:
        return []


async def tavily_extract(url: str) -> Optional[str]:
    """
    Extract content from a URL via Tavily Extract API.
    Returns extracted text or None.
    """
    key = settings.get_tavily_key()
    if not key:
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.tavily.com/extract",
                headers={"Authorization": f"Bearer {key}"},
                json={"urls": [url]},
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            if results:
                return results[0].get("raw_content", "")
            return None
    except Exception:
        return None


async def unified_search(query: str, search_type: str) -> list[dict]:
    """
    Unified search that combines multiple sources based on type.
    Types: stock, macro, industry, news, extract.
    Auto-fallback on failure.
    """
    all_results = []

    if search_type == "stock":
        # Finance-focused search + news
        results_a = await tavily_search(query, topic="finance", max_results=5, time_range="week")
        results_b = await brave_news(query, max_results=3)
        all_results = results_a + results_b

    elif search_type == "macro":
        # Authoritative sources: CN official + intl financial press
        results_a = await tavily_search(query, topic="news", max_results=6, time_range="week",
                                        include_domains=MACRO_DOMAINS)
        results_b = await brave_search(query, max_results=3)
        all_results = results_a + results_b

    elif search_type == "industry":
        # Advanced search + web
        results_a = await tavily_search(query, topic="general", max_results=5, time_range="month")
        results_b = await brave_search(query, max_results=3)
        all_results = results_a + results_b

    elif search_type == "news":
        # News first, tavily fallback
        results_a = await brave_news(query, max_results=5)
        if not results_a:
            results_a = await tavily_search(query, topic="news", max_results=5)
        all_results = results_a

    elif search_type == "extract":
        # URL extraction — query is a URL
        content = await tavily_extract(query)
        if content:
            all_results = [{"title": "提取内容", "url": query, "content": content}]

    # Fallback: if primary search returned nothing, try alternative
    if not all_results and search_type not in ("extract",):
        all_results = await brave_search(query, max_results=5)
    if not all_results:
        all_results = await tavily_search(query, topic="general", max_results=5)

    # Deduplicate by URL
    seen_urls = set()
    unique = []
    for r in all_results:
        url = r.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(r)
        elif not url:
            unique.append(r)

    return unique


CN_FINANCE_DOMAINS = [
    "eastmoney.com",
    "10jqka.com.cn",
    "xueqiu.com",
    "finance.sina.com.cn",
    "cninfo.com.cn",
    "cls.cn",
    "caixin.com",
    "stock.qq.com",
]

MACRO_DOMAINS = [
    # 中国官方
    "xinhuanet.com",
    "news.cn",
    "mfa.gov.cn",
    "gov.cn",
    "ndrc.gov.cn",
    "pbc.gov.cn",
    # 国际财经
    "reuters.com",
    "bloomberg.com",
    "wsj.com",
    "cnbc.com",
    "ft.com",
]


def format_search_results(results: list[dict]) -> str:
    """Format search results into a readable text block for LLM consumption."""
    if not results:
        return "未找到相关搜索结果。"

    parts = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "无标题")
        url = r.get("url", "")
        content = r.get("content", "无内容")
        # Truncate very long content
        if len(content) > 1500:
            content = content[:1500] + "..."
        part = f"【来源{i}】{title}\n链接：{url}\n内容：{content}"
        parts.append(part)

    return "\n\n".join(parts)


async def multi_search_stock(stock_name: str) -> list[dict]:
    """多维度并发搜索股票数据"""
    import asyncio

    tasks = [
        # 维度1：财报数据（月级时间窗口，中文源优先）
        tavily_search(
            f"{stock_name} 最新财报 营收 净利润 毛利率 经营性现金流",
            topic="finance", max_results=5, time_range="month",
            include_domains=CN_FINANCE_DOMAINS
        ),
        # 维度2：资金面
        tavily_search(
            f"{stock_name} 主力资金 北向资金 资金流向 大单",
            topic="finance", max_results=4, time_range="week",
            include_domains=CN_FINANCE_DOMAINS
        ),
        # 维度3：估值与行业对比
        tavily_search(
            f"{stock_name} PE PB 估值 行业均值 ROE 可比公司",
            topic="finance", max_results=4, time_range="month"
        ),
        # 维度4：新闻
        brave_news(f"{stock_name} 股票 最新消息 公告", max_results=5),
        # 维度5：管理层与股东回报
        tavily_search(
            f"{stock_name} 实控人 增减持 分红 回购 股息率",
            topic="finance", max_results=3, time_range="month"
        ),
    ]

    results_groups = await asyncio.gather(*tasks, return_exceptions=True)

    categories = ["财报数据", "资金面数据", "估值与行业对比", "近期新闻", "管理层与股东回报"]

    all_results = []
    for cat, group in zip(categories, results_groups):
        if isinstance(group, Exception) or not group:
            continue
        for r in group:
            r["category"] = cat
            all_results.append(r)

    # 去重
    seen_urls = set()
    unique = []
    for r in all_results:
        url = r.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(r)
        elif not url:
            unique.append(r)

    return unique


def format_search_results_grouped(results: list[dict]) -> str:
    """按维度分组格式化搜索结果"""
    if not results:
        return "未找到相关搜索结果。"

    grouped = {}
    for r in results:
        cat = r.get("category", "其他")
        grouped.setdefault(cat, []).append(r)

    parts = []
    source_idx = 1
    for cat, items in grouped.items():
        parts.append(f"\n=== {cat} ===\n")
        for r in items:
            title = r.get("title", "无标题")
            url = r.get("url", "")
            content = r.get("content", "无内容")
            if len(content) > 1200:
                content = content[:1200] + "..."
            parts.append(f"【来源{source_idx}】{title}\n链接：{url}\n内容：{content}")
            source_idx += 1

    return "\n\n".join(parts)
