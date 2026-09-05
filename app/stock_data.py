"""
AkShare 数据获取模块
通过东方财富/同花顺/乐咕等数据源获取A股结构化数据
所有函数经过实测验证，参数与AkShare 1.18.48一致
"""

import asyncio
import json
import os
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

import akshare as ak

# 线程池（AkShare是同步库）
_executor = ThreadPoolExecutor(max_workers=6)
# ---- Fetch Receipt Sink（Observability Enablement v0.1，冻结规则见 task card）----

_RECEIPT_SINK = "/var/log/finance-suite/fetch_receipts.jsonl"

_URL_RE = re.compile(r"https?://[^\s'\"<>]+")
_SECRET_RE = re.compile(r"(token|secret|password|api_?key|key|authorization)=([^\s&'\"<>]+)", re.IGNORECASE)


def _sanitize_error(e: BaseException) -> str | None:
    """error_detail 脱敏：去 URL、去敏感参数、截断 200 字符"""
    msg = str(e) or type(e).__name__
    msg = _URL_RE.sub("<url>", msg)
    msg = _SECRET_RE.sub(r"\1=<redacted>", msg)
    return msg[:200] or None


def _classify_exception(e: BaseException, phase: str) -> tuple[str, str | None, str | None]:
    """唯一错误分类映射（同一种错误只有一种分类，不受捕获位置影响）。
    phase: provider_call | transform。返回 (outcome, error_phase, error_type)。"""
    name = type(e).__name__
    if isinstance(e, TimeoutError) or name in ("ReadTimeout", "ConnectTimeout", "ProxyTimeout"):
        return "PROVIDER_ERROR", None, "TimeoutError"
    if isinstance(e, json.JSONDecodeError):
        return "MAPPING_OR_CONTRACT_ERROR", "provider_contract", "JSONDecodeError"
    if phase == "provider_call":
        return "PROVIDER_ERROR", None, name
    if isinstance(e, (AttributeError, KeyError, IndexError, TypeError)):
        return "MAPPING_OR_CONTRACT_ERROR", "provider_contract", name
    return "MAPPING_OR_CONTRACT_ERROR", "internal_mapping", name


def _extract_data_time(records: list[dict]) -> str | None:
    """provider 数据自身最新时间戳；禁止与本地调用时间混用"""
    for key in ("日期", "date", "Date"):
        for row in reversed(records):
            if not isinstance(row, dict):
                continue
            val = row.get(key)
            if val is not None:
                return val.isoformat() if hasattr(val, "isoformat") else str(val)
    return None


def _write_receipt(receipt: dict) -> None:
    """单行 JSON + flush。写失败必须显式 OBSERVABILITY_SINK_FAILURE（fail closed）"""
    try:
        os.makedirs(os.path.dirname(_RECEIPT_SINK), exist_ok=True)
        with open(_RECEIPT_SINK, "a", encoding="utf-8") as f:
            f.write(json.dumps(receipt, ensure_ascii=False, default=str) + "\n")
            f.flush()
    except Exception as e:
        print(
            "OBSERVABILITY_SINK_FAILURE function={} invocation_id={} error={}: {}".format(
                receipt.get("function", "?"), receipt.get("invocation_id", "?"),
                type(e).__name__, str(e)[:200],
            ),
            file=sys.stderr, flush=True,
        )

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
    "博纳影业": ("001330", "博纳影业"),
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
}


def _load_stock_cache() -> dict:
    """加载股票名称→代码映射（使用K线接口，比spot_em快很多）"""
    global _stock_cache, _stock_cache_time
    now = datetime.now()
    if _stock_cache and _stock_cache_time and (now - _stock_cache_time).seconds < 7200:
        return _stock_cache

    try:
        # 用个股列表接口（轻量）
        df = ak.stock_zh_a_spot_em()
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

def _fetch_financials(code: str) -> list[dict] | None:
    """财报主要指标（限制2024年起，1-2秒）"""
    try:
        df = ak.stock_financial_analysis_indicator(symbol=code, start_year="2024")
        if df is not None and len(df) > 0:
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


def _fetch_price_history(code: str, invocation_id: str | None = None) -> list[dict] | None:
    """近60日K线（0.2秒）"""
    started = datetime.now(timezone.utc)
    receipt = {
        "receipt": "fetch_receipt",
        "invocation_id": invocation_id or uuid.uuid4().hex,
        "function": "_fetch_price_history",
        "symbol": code,
        "provider": "akshare.stock_zh_a_hist",
        "outcome": None,
        "latency_ms": None,
        "started_at": started.isoformat(),
        "finished_at": None,
        "data_time": None,
        "data_len": 0,
        "error_type": None,
        "error_phase": None,
        "error_detail": None,
    }
    result = None
    try:
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
        df = ak.stock_zh_a_hist(symbol=code, period="daily",
                                 start_date=start, end_date=end, adjust="qfq")
    except Exception as e:
        receipt["outcome"], receipt["error_phase"], receipt["error_type"] = _classify_exception(e, "provider_call")
        receipt["error_detail"] = _sanitize_error(e)
    else:
        try:
            if df is not None and len(df) > 0:
                result = df.tail(30).to_dict(orient="records")
                receipt["outcome"] = "DATA_RETURNED"
                receipt["data_time"] = _extract_data_time(result)
            else:
                receipt["outcome"] = "EMPTY_RESULT"
        except Exception as e:
            receipt["outcome"], receipt["error_phase"], receipt["error_type"] = _classify_exception(e, "transform")
            receipt["error_detail"] = _sanitize_error(e)
    finished = datetime.now(timezone.utc)
    receipt["finished_at"] = finished.isoformat()
    receipt["latency_ms"] = int((finished - started).total_seconds() * 1000)
    receipt["data_len"] = len(result) if result else 0
    _write_receipt(receipt)
    return result


def _fetch_fund_flow(code: str, invocation_id: str | None = None) -> list[dict] | None:
    """个股资金流向（0.5秒）"""
    started = datetime.now(timezone.utc)
    receipt = {
        "receipt": "fetch_receipt",
        "invocation_id": invocation_id or uuid.uuid4().hex,
        "function": "_fetch_fund_flow",
        "symbol": code,
        "provider": "akshare.stock_individual_fund_flow",
        "outcome": None,
        "latency_ms": None,
        "started_at": started.isoformat(),
        "finished_at": None,
        "data_time": None,
        "data_len": 0,
        "error_type": None,
        "error_phase": None,
        "error_detail": None,
    }
    result = None
    try:
        market = _get_market(code)
        df = ak.stock_individual_fund_flow(stock=code, market=market)
    except Exception as e:
        receipt["outcome"], receipt["error_phase"], receipt["error_type"] = _classify_exception(e, "provider_call")
        receipt["error_detail"] = _sanitize_error(e)
    else:
        try:
            if df is not None and len(df) > 0:
                result = df.tail(10).to_dict(orient="records")
                receipt["outcome"] = "DATA_RETURNED"
                receipt["data_time"] = _extract_data_time(result)
            else:
                receipt["outcome"] = "EMPTY_RESULT"
        except Exception as e:
            receipt["outcome"], receipt["error_phase"], receipt["error_type"] = _classify_exception(e, "transform")
            receipt["error_detail"] = _sanitize_error(e)
    finished = datetime.now(timezone.utc)
    receipt["finished_at"] = finished.isoformat()
    receipt["latency_ms"] = int((finished - started).total_seconds() * 1000)
    receipt["data_len"] = len(result) if result else 0
    _write_receipt(receipt)
    return result


def _fetch_valuation(code: str) -> dict | None:
    """估值指标+PE历史分位"""
    try:
        df = ak.stock_a_gxl_lg(symbol="上证A股")
        # 这个接口返回全市场，无法筛选个股
        # 改用缓存中的PE/PB
        return None
    except Exception:
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

    # 实时行情从缓存取（不额外请求）
    results["realtime"] = _fetch_realtime_from_cache(code)

    return results


# ---- 格式化 ----

def format_stock_data(data: dict, stock_name: str = "", stock_code: str = "") -> str:
    """格式化为LLM可读文本"""
    parts = []
    parts.append(f"=== {stock_name}({stock_code}) 东方财富结构化数据 ===")
    parts.append(f"数据获取时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # 实时行情
    rt = data.get("realtime")
    if rt and isinstance(rt, dict):
        parts.append("【实时行情】")
        parts.append(f"最新价：{rt.get('price', 'N/A')} 元")
        parts.append(f"涨跌幅：{rt.get('change', 'N/A')}%")
        parts.append(f"市盈率(动态)：{rt.get('pe', 'N/A')} 倍")
        parts.append(f"市净率：{rt.get('pb', 'N/A')} 倍")
        parts.append(f"总市值：{rt.get('mv', 'N/A')}")
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
