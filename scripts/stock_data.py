"""
股票数据获取模块（Wind 优先 + AkShare 降级）
优先使用 Wind（数据质量最高），Wind 不可用时自动降级到 AkShare（免费）
Wind 需要本机运行 Wind API 终端且已登录，否则静默降级

独立CLI脚本，无内部依赖
用法: python3 stock_data.py --query "比亚迪"
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

import akshare as ak

# ---- 数据源选择 ----
# 环境变量 FS_DATA_SOURCE 可强制指定：wind/akshare/auto（默认auto）
_DATA_SOURCE = os.environ.get("FS_DATA_SOURCE", "auto").lower()
_wind_available = None  # None=未检测, True/False=检测结果


def _check_wind_available():
    """懒加载检测 Wind 是否可用，支持自动重连"""
    global _wind_available
    # 如果强制使用 akshare，直接返回
    if _DATA_SOURCE == "akshare":
        _wind_available = False
        return False
    # 如果已经检测过且成功，直接返回
    if _wind_available is True:
        return True
    # 如果之前失败过，但距离上次检测超过5分钟，重新尝试（自动恢复）
    if _wind_available is False:
        # 简单实现：每次都重试（由 wind_data._ensure_wind 的重试机制保护）
        pass
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import wind_data
        status = wind_data.check_connection()
        _wind_available = status.get("connected", False)
    except Exception:
        _wind_available = False
    return _wind_available

# 线程池（AkShare是同步库）
_executor = ThreadPoolExecutor(max_workers=6)

# ---- 数据源标识 ----
def get_active_source() -> str:
    """返回当前活跃的数据源：wind 或 akshare"""
    if _check_wind_available():
        return "wind"
    return "akshare"


# ---- 股票名称缓存 ----
_stock_cache: dict | None = None
_stock_cache_time: datetime | None = None

# 确定性 identity map。优先于缓存模糊匹配，用来处理自然语言句子
# 中包含股票名的输入，避免把"招商银行..."、"苏美达..."解析到错误证券。
QUICK_MAP = {
    "贵州茅台": ("600519", "贵州茅台"),
    "茅台": ("600519", "贵州茅台"),
    "招商银行": ("600036", "招商银行"),
    "招行": ("600036", "招商银行"),
    "苏美达": ("600710", "苏美达"),
    "常林股份": ("600710", "苏美达"),
    "比亚迪": ("002594", "比亚迪"),
    "宁德时代": ("300750", "宁德时代"),
    "中国平安": ("601318", "中国平安"),
    "腾讯": ("00700", "腾讯"),
    "阿里巴巴": ("09988", "阿里巴巴"),
    "工商银行": ("601398", "工商银行"),
    "建设银行": ("601939", "建设银行"),
    "中国银行": ("601988", "中国银行"),
    "农业银行": ("601288", "农业银行"),
    "中国中免": ("601888", "中国中免"),
    "美的集团": ("000333", "美的集团"),
    "格力电器": ("000651", "格力电器"),
    "海尔智家": ("600690", "海尔智家"),
    "隆基绿能": ("601012", "隆基绿能"),
    "恒瑞医药": ("600276", "恒瑞医药"),
    "药明康德": ("603259", "药明康德"),
    "迈瑞医疗": ("300760", "迈瑞医疗"),
    "五粮液": ("000858", "五粮液"),
    "泸州老窖": ("000568", "泸州老窖"),
    "长江电力": ("600900", "长江电力"),
    "中国神华": ("601088", "中国神华"),
    "紫金矿业": ("601899", "紫金矿业"),
    "中国石油": ("601857", "中国石油"),
    "中国移动": ("600941", "中国移动"),
    "中国电信": ("601728", "中国电信"),
    "立讯精密": ("002475", "立讯精密"),
    "歌尔股份": ("002241", "歌尔股份"),
    "东方财富": ("300059", "东方财富"),
    "同花顺": ("300033", "同花顺"),
    "中信证券": ("600030", "中信证券"),
    "海天味业": ("603288", "海天味业"),
    "万科": ("000002", "万科"),
    "保利发展": ("600048", "保利发展"),
    "三一重工": ("600031", "三一重工"),
    "中联重科": ("000157", "中联重科"),
    "科大讯飞": ("002230", "科大讯飞"),
    "海康威视": ("002415", "海康威视"),
    "中芯国际": ("688981", "中芯国际"),
    "韦尔股份": ("603501", "韦尔股份"),
    "博纳影业": ("001330", "博纳影业"),
}

# 实时行情缓存保真期（秒）：超过视为 stale
_CACHE_STALE_SECONDS = 900  # 15分钟
REALTIME_TRADING_BLOCKED_FIELDS = [
    "price",
    "volume",
    "amount",
    "current_price_judgment",
    "intraday_strength",
    "support_resistance",
    "short_term_breakout",
    "position_advice",
    "short_term_signal",
    "buy_sell_recommendation",
]


def _is_realtime_stale() -> bool:
    """返回 True 表示实时行情缓存已过期，不适合当"实时"数据用"""
    if _stock_cache_time is None:
        return True
    return (datetime.now() - _stock_cache_time).total_seconds() >= _CACHE_STALE_SECONDS


def _load_stock_cache() -> dict:
    """加载股票名称→代码映射（使用K线接口，比spot_em快很多）"""
    global _stock_cache, _stock_cache_time
    now = datetime.now()
    if _stock_cache and _stock_cache_time and (now - _stock_cache_time).seconds < 7200:
        return _stock_cache

    try:
        # 用个股列表接口（轻量），设置超时保护
        import signal
        def timeout_handler(signum, frame):
            raise TimeoutError("AkShare 请求超时")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)  # 30秒超时
        try:
            df = ak.stock_zh_a_spot_em()
            signal.alarm(0)  # 取消超时
        except TimeoutError:
            signal.alarm(0)
            raise

        _stock_cache = {}
        for _, row in df.iterrows():
            code = str(row.get("代码", ""))
            name = str(row.get("名称", ""))
            if code and name:
                _stock_cache[name] = {"code": code, "price": row.get("最新价"),
                                       "pe": row.get("市盈率-动态"), "pb": row.get("市净率"),
                                       "mv": row.get("总市值"), "change": row.get("涨跌幅")}
                _stock_cache[code] = _stock_cache[name]
        _stock_cache_time = now
    except Exception:
        pass
    return _stock_cache or {}


def _strip_exchange_suffix(query: str) -> str:
    upper = query.strip().upper()
    for suffix in (".SH", ".SZ", ".BJ", "SH", "SZ", "BJ"):
        if upper.endswith(suffix) and len(upper) > len(suffix):
            return upper[: -len(suffix)]
    return query.strip()


def resolve_stock_detail(query: str) -> dict | None:
    """
    用户输入→解析详情。
    核心原则：绝不阻塞。如果缓存没就绪，用快速备用方案。
    """
    query = query.strip()
    normalized_query = _strip_exchange_suffix(query)

    # 0. 确定性锚点优先。支持自然语言句子包含股票名，
    # 如"招商银行当前基本面和风险如何？"。
    if normalized_query.isdigit() and len(normalized_query) == 6:
        for alias, (code, canonical_name) in QUICK_MAP.items():
            if normalized_query == code:
                return {
                    "code": code,
                    "name": canonical_name,
                    "resolver_source": "quick_map_code",
                    "matched_text": normalized_query,
                    "input_text": query,
                }
        return {
            "code": normalized_query,
            "name": normalized_query,
            "resolver_source": "direct_code",
            "matched_text": normalized_query,
            "input_text": query,
        }

    for alias in sorted(QUICK_MAP, key=len, reverse=True):
        code, canonical_name = QUICK_MAP[alias]
        if alias == normalized_query or alias in normalized_query:
            return {
                "code": code,
                "name": canonical_name,
                "resolver_source": "quick_map_alias",
                "matched_text": alias,
                "input_text": query,
            }

    # 1. 优先用缓存（毫秒级）
    if _stock_cache:
        # 精确匹配
        if normalized_query in _stock_cache:
            info = _stock_cache[normalized_query]
            code = info["code"]
            name = normalized_query if not normalized_query.isdigit() else next(
                (k for k, v in _stock_cache.items() if isinstance(v, dict) and v.get("code") == code and not k.isdigit()),
                normalized_query,
            )
            return {
                "code": code,
                "name": name,
                "resolver_source": "cache_exact",
                "matched_text": normalized_query,
                "input_text": query,
            }
        # 模糊匹配
        for key, info in sorted(_stock_cache.items(), key=lambda item: len(str(item[0])), reverse=True):
            key_text = str(key)
            if isinstance(info, dict) and not key_text.isdigit() and key_text in normalized_query:
                return {
                    "code": info["code"],
                    "name": key_text,
                    "resolver_source": "cache_name_contains",
                    "matched_text": key_text,
                    "input_text": query,
                }

    # 2. 都匹配不上，返回None（让后续逻辑用用户原始输入搜索）
    return None


def resolve_stock(query: str) -> tuple[str, str] | None:
    """用户输入→(代码, 名称)。兼容旧调用方。"""
    detail = resolve_stock_detail(query)
    if not detail:
        return None
    return (detail["code"], detail["name"])


def _get_market(code: str) -> str:
    if code.startswith(("6", "9")):
        return "sh"
    elif code.startswith(("0", "3")):
        return "sz"
    return "bj"


# ---- 数据获取函数（同步，在线程池中执行）----

def _with_timeout(fn, args=(), kwargs=None, timeout_seconds: float = 8.0):
    """对任意函数执行加超时保护（跨平台）"""
    import threading
    result = [None]
    exc = [None]
    if kwargs is None:
        kwargs = {}

    def target():
        try:
            result[0] = fn(*args, **kwargs)
        except Exception as e:
            exc[0] = e

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout=timeout_seconds)
    if t.is_alive():
        # 超时后不等，直接返回 None（触发降级）
        return None
    if exc[0]:
        raise exc[0]
    return result[0]


def _fetch_financials(code: str) -> list[dict] | None:
    """财报主要指标（Wind 优先，失败降级 AkShare）"""
    # Wind 优先：完整三大报表
    if _check_wind_available():
        try:
            import wind_data
            result = wind_data.get_financials(code)
            if result:
                return result
        except Exception:
            pass
    # 降级：AkShare 主要指标（8秒超时保护）
    try:
        current_year = datetime.now().year
        start_year = str(current_year - 2)  # 拉最近3年数据，避免硬编码年份滞后
        df = _with_timeout(ak.stock_financial_analysis_indicator, (), {"symbol": code, "start_year": start_year}, timeout_seconds=8.0)
        if df is not None and len(df) > 0:
            # 按报告期降序排列，取最新4期（默认升序，head(4)会取到最旧数据）
            date_col = next((c for c in ["报告期", "日期", "date"] if c in df.columns), None)
            if date_col:
                df = df.sort_values(date_col, ascending=False)
            return df.head(4).to_dict(orient="records")
    except Exception:
        pass
    return None


def _fetch_realtime_from_cache(code: str) -> dict | None:
    """从缓存获取实时行情（如果缓存已加载）"""
    cache = _stock_cache or {}
    info = cache.get(code)
    if isinstance(info, dict):
        return info
    return None


def _fetch_quote_gateway(code: str) -> dict:
    """Use the unified quote gateway instead of relying on the optional stock cache."""
    try:
        import finance_data_gateway

        symbol = code if "." in code else f"{code}.SH" if code.startswith(("6", "9")) else f"{code}.SZ"
        return finance_data_gateway.get_finance_data("quote", symbol=symbol)
    except Exception as exc:
        return {
            "ok": False,
            "symbol": code,
            "data_type": "quote",
            "provider": None,
            "freshness": "unavailable",
            "as_of": None,
            "data": {},
            "_qc": {
                "status": "failure",
                "reason": "quote_gateway_error",
                "sources": [],
                "missing_fields": ["quote"],
                "missing_dimensions": ["quote"],
                "blocked_fields": ["all"],
                "error": str(exc),
            },
        }


def _quote_realtime_status(quote: dict | None) -> str:
    qc = (quote or {}).get("_qc") or {}
    status = str(qc.get("status") or "failure").lower()
    freshness = str((quote or {}).get("freshness") or qc.get("freshness") or "").lower()
    if status == "success" and freshness == "realtime":
        return "available"
    if status in {"success", "partial"} and freshness in {"daily", "delayed", "cached", "stale"}:
        return "partial"
    if status == "partial":
        return "partial"
    return "unavailable"


def _quote_allowed_use(quote: dict | None) -> list[str]:
    status = _quote_realtime_status(quote)
    freshness = str((quote or {}).get("freshness") or ((quote or {}).get("_qc") or {}).get("freshness") or "").lower()
    if status == "available":
        return ["realtime_snapshot", "price_reference"]
    if status == "partial" and freshness in {"daily", "delayed", "cached", "stale"}:
        return ["daily_reference", "historical_context"]
    if status == "partial":
        return ["limited_quote_reference"]
    return []


def _quote_blocked_fields(quote: dict | None) -> list[str]:
    status = _quote_realtime_status(quote)
    qc = (quote or {}).get("_qc") or {}
    blocked = list(qc.get("blocked_fields") or [])
    for field in qc.get("missing_fields") or qc.get("missing_dimensions") or []:
        if field not in blocked:
            blocked.append(str(field))
    if status != "available":
        for field in ("price", "volume", "amount"):
            if field not in blocked:
                blocked.append(field)
        for field in REALTIME_TRADING_BLOCKED_FIELDS:
            if field not in blocked:
                blocked.append(field)
    if status == "unavailable" and not blocked:
        blocked.extend(["all_realtime_fields", *REALTIME_TRADING_BLOCKED_FIELDS])
    return blocked


def _strip_blocked_quote_fields(quote: dict | None) -> dict | None:
    data = dict((quote or {}).get("data") or {})
    if not data:
        return None
    for field in _quote_blocked_fields(quote):
        data.pop(field, None)
    return data or None


def build_realtime_availability(quote: dict | None) -> dict:
    """Build Trust Presentation metadata for single-stock realtime quote data."""
    qc = (quote or {}).get("_qc") or {}
    data = (quote or {}).get("data") or {}
    status = _quote_realtime_status(quote)
    blocked_fields = _quote_blocked_fields(quote)
    if status == "available":
        available = [
            field
            for field in ("price", "volume", "amount", "change", "pe", "pb", "mv")
            if data.get(field) not in (None, "") and field not in blocked_fields
        ]
    else:
        available = [
            label
            for field, label in (("close", "daily_close"), ("change", "daily_change"), ("trade_date", "trade_date"), ("pe", "pe"), ("pb", "pb"), ("mv", "mv"))
            if data.get(field) not in (None, "")
        ]
    missing = [str(field) for field in (qc.get("missing_fields") or qc.get("missing_dimensions") or [])]
    if status == "unavailable" and not missing:
        missing = ["realtime"]
    return {
        "status": status,
        "source": (quote or {}).get("provider"),
        "source_type": "real" if (quote or {}).get("provider") else "not_connected",
        "as_of": (quote or {}).get("as_of"),
        "freshness": (quote or {}).get("freshness"),
        "available": available,
        "missing": missing,
        "allowed_use": _quote_allowed_use(quote),
        "blocked_fields": blocked_fields,
        "reason": qc.get("reason"),
    }


def _fetch_price_history(code: str) -> list[dict] | None:
    """近60日K线（0.2秒）"""
    try:
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
        df = ak.stock_zh_a_hist(symbol=code, period="daily",
                                 start_date=start, end_date=end, adjust="qfq")
        if df is not None and len(df) > 0:
            return df.tail(30).to_dict(orient="records")
    except Exception:
        pass
    return None


def _fetch_fund_flow(code: str) -> list[dict] | None:
    """个股资金流向（0.5秒）"""
    try:
        market = _get_market(code)
        df = ak.stock_individual_fund_flow(stock=code, market=market)
        if df is not None and len(df) > 0:
            return df.tail(10).to_dict(orient="records")
    except Exception:
        pass
    return None


def _fetch_valuation(code: str) -> dict | None:
    """估值指标 + PE/PB 10年历史分位（Wind 独有能力）"""
    if _check_wind_available():
        try:
            import wind_data
            result = wind_data.get_valuation_history(code)
            if result:
                return result
        except Exception:
            pass
    # AkShare 无法提供个股历史估值分位，返回 None 由 LLM 从缓存取当前 PE/PB
    return None


def _fetch_news(code: str) -> list[dict] | None:
    """个股新闻（东方财富，0.7秒）"""
    try:
        df = ak.stock_news_em(symbol=code)
        if df is not None and len(df) > 0:
            return [
                {
                    "title": str(row.get("新闻标题", "")),
                    "content": str(row.get("新闻内容", ""))[:300],
                    "time": str(row.get("发布时间", "")),
                    "source": str(row.get("文章来源", "")),
                    "url": str(row.get("新闻链接", "")),
                }
                for _, row in df.head(8).iterrows()
            ]
    except Exception:
        pass
    return None


def _fetch_dividends(code: str) -> list[dict] | None:
    """历史分红"""
    try:
        df = ak.stock_history_dividend_detail(symbol=code, indicator="分红")
        if df is not None and len(df) > 0:
            return df.head(5).to_dict(orient="records")
    except Exception:
        pass
    return None


# ---- 异步并发获取 ----

async def get_stock_full_data(code: str) -> dict:
    """并发获取全维度数据"""
    loop = asyncio.get_event_loop()

    # 并发执行所有数据获取
    fin_task = loop.run_in_executor(_executor, _fetch_financials, code)
    price_task = loop.run_in_executor(_executor, _fetch_price_history, code)
    flow_task = loop.run_in_executor(_executor, _fetch_fund_flow, code)
    news_task = loop.run_in_executor(_executor, _fetch_news, code)
    div_task = loop.run_in_executor(_executor, _fetch_dividends, code)

    results = {}
    for key, task in [
        ("financials", fin_task),
        ("price_history", price_task),
        ("fund_flow", flow_task),
        ("news", news_task),
        ("dividends", div_task),
    ]:
        try:
            results[key] = await task
        except Exception:
            results[key] = None

    # 实时行情走统一 quote gateway，不再只依赖可为空的内存 cache。
    quote = _fetch_quote_gateway(code)
    results["realtime_quote"] = quote
    results["realtime_availability"] = build_realtime_availability(quote)
    results["realtime"] = _strip_blocked_quote_fields(quote) if _quote_realtime_status(quote) in {"available", "partial"} else None

    return results


# ---- 格式化 ----

def format_stock_data(data: dict, stock_name: str = "", stock_code: str = "") -> str:
    """格式化为LLM可读文本"""
    parts = []
    parts.append(f"=== {stock_name}({stock_code}) 东方财富结构化数据 ===")
    parts.append(f"数据获取时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # 实时/行情参考
    rt = data.get("realtime")
    if rt and isinstance(rt, dict):
        availability = data.get("realtime_availability") or {}
        freshness = availability.get("freshness")
        is_realtime_available = availability.get("status") == "available"
        title = "实时行情" if is_realtime_available else "行情参考（非实时）"
        parts.append(f"【{title}】")
        if freshness:
            parts.append(f"数据新鲜度：{freshness}")
        if is_realtime_available:
            parts.append(f"最新价：{rt.get('price', 'N/A')} 元")
            parts.append(f"涨跌幅：{rt.get('change', 'N/A')}%")
        else:
            if rt.get("close") not in (None, ""):
                parts.append(f"参考收盘价：{rt.get('close')} 元")
            if rt.get("change") not in (None, ""):
                parts.append(f"日涨跌幅：{rt.get('change')}%")
            if rt.get("trade_date"):
                parts.append(f"交易日：{rt.get('trade_date')}")
        parts.append(f"市盈率(动态)：{rt.get('pe', 'N/A')} 倍")
        parts.append(f"市净率：{rt.get('pb', 'N/A')} 倍")
        parts.append(f"总市值：{rt.get('mv', 'N/A')}")
        if not is_realtime_available:
            parts.append("说明：该行情不可用于盘中强弱、支撑压力、短线突破或仓位建议。")
        parts.append("")

    # 财报
    fin = data.get("financials")
    if fin:
        parts.append("【财报主要指标（近4期）】")
        for row in fin:
            period = row.get("日期", "未知期")
            parts.append(f"\n--- 报告期：{period} ---")
            for key, val in row.items():
                if key != "日期" and val is not None and str(val).strip():
                    parts.append(f"  {key}：{val}")
        parts.append("")

    # 资金流向
    ff = data.get("fund_flow")
    if ff:
        parts.append("【个股资金流向（近期）】")
        for row in ff[-5:]:
            date = row.get("日期", "")
            main_in = row.get("主力净流入-净额", "N/A")
            main_pct = row.get("主力净流入-净占比", "N/A")
            big_in = row.get("超大单净流入-净额", "N/A")
            parts.append(f"  {date}：主力净流入{main_in}（占比{main_pct}%），超大单{big_in}")
        parts.append("")

    # K线
    ph = data.get("price_history")
    if ph:
        parts.append("【近期K线（近10日）】")
        for row in ph[-10:]:
            parts.append(f"  {row.get('日期','')}：开{row.get('开盘','')} 收{row.get('收盘','')} "
                         f"涨跌幅{row.get('涨跌幅','')}% 成交量{row.get('成交量','')} 换手率{row.get('换手率','')}%")
        parts.append("")

    # 新闻
    news = data.get("news")
    if news:
        parts.append("【个股新闻（东方财富）】")
        for i, n in enumerate(news[:5], 1):
            parts.append(f"  {i}. {n.get('title', '')} ({n.get('time', '')})")
            parts.append(f"     来源：{n.get('source', '')} | 链接：{n.get('url', '')}")
            content = n.get('content', '')
            if content:
                parts.append(f"     摘要：{content[:150]}")
        parts.append("")

    # 分红
    div = data.get("dividends")
    if div:
        parts.append("【历史分红记录】")
        for row in div:
            parts.append(f"  {row}")
        parts.append("")

    if len(parts) <= 3:
        parts.append("未获取到结构化数据。")

    return "\n".join(parts)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="获取A股个股全维度数据")
    parser.add_argument("--query", type=str, required=True, help="股票名称或代码，如 比亚迪 或 002594")
    args = parser.parse_args()

    # 先尝试加载缓存（可选，会使实时行情可用）
    print(f"正在查询：{args.query} ...", flush=True)
    _load_stock_cache()

    # 解析股票
    resolved = resolve_stock(args.query)
    if resolved:
        code, name = resolved
    else:
        print(f"未找到匹配的股票：{args.query}")
        exit(1)

    print(f"匹配到：{name}({code})，正在获取数据...", flush=True)

    # 获取全维度数据
    data = asyncio.run(get_stock_full_data(code))

    # 格式化输出
    output = format_stock_data(data, stock_name=name, stock_code=code)
    print(output)
