"""
股票数据获取模块（Wind 优先 + AkShare 降级）
优先使用 Wind（数据质量最高），Wind 不可用时自动降级到 AkShare（免费）
Wind 需要本机运行 Wind API 终端且已登录，否则静默降级

独立CLI脚本，无内部依赖
用法: python3 stock_data.py --query "比亚迪"
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

import akshare as ak

logger = logging.getLogger(__name__)

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

# 实时行情缓存保真期（秒）：超过视为 stale
_CACHE_STALE_SECONDS = 900  # 15分钟


def _is_realtime_stale() -> bool:
    """返回 True 表示实时行情缓存已过期，不适合当"实时"数据用"""
    if _stock_cache_time is None:
        return True
    return (datetime.now() - _stock_cache_time).total_seconds() >= _CACHE_STALE_SECONDS


def _load_stock_cache() -> dict:
    """加载股票名称→代码映射（多源降级：akshare spot → sina → 空缓存）"""
    global _stock_cache, _stock_cache_time
    now = datetime.now()
    if _stock_cache and _stock_cache_time and (now - _stock_cache_time).seconds < 7200:
        return _stock_cache

    _stock_cache = {}

    # 方案1: 腾讯全市场快照（直连，稳定，有 PE/市值/价格，缺 PB）
    try:
        df = _with_timeout(ak.stock_zh_a_spot_tx, timeout_seconds=20.0)
        if df is not None and len(df) > 0:
            for _, row in df.iterrows():
                code = str(row.get("code", ""))
                name = str(row.get("name", ""))
                if code and name:
                    _stock_cache[name] = {"code": code, "price": row.get("zxj"),
                                          "pe": row.get("pe_ttm"), "pb": None,
                                          "mv": row.get("zsz"), "change": row.get("zdf")}
                    _stock_cache[code] = _stock_cache[name]
            _stock_cache_time = now
            return _stock_cache
    except Exception:
        pass

    # 方案2: EastMoney 全市场快照（字段最全含 PB，但走代理可能被阻断）
    try:
        df = _with_timeout(ak.stock_zh_a_spot_em, timeout_seconds=30.0)
        if df is not None and len(df) > 0:
            for _, row in df.iterrows():
                code = str(row.get("代码", ""))
                name = str(row.get("名称", ""))
                if code and name:
                    entry = {"code": code, "price": row.get("最新价"),
                             "pe": row.get("市盈率-动态"), "pb": row.get("市净率"),
                             "mv": row.get("总市值"), "change": row.get("涨跌幅")}
                    _stock_cache[name] = entry
                    _stock_cache[code] = entry
            _stock_cache_time = now
            return _stock_cache
    except Exception:
        pass

    # 方案3: Sina 实时行情（直连，轻量，但只有基本价格字段，无 PE/PB/市值）
    try:
        df = _with_timeout(ak.stock_zh_a_spot, timeout_seconds=20.0)
        if df is not None and len(df) > 0:
            for _, row in df.iterrows():
                raw_code = str(row.get("代码", ""))
                name = str(row.get("名称", ""))
                if raw_code and name:
                    bare_code = raw_code.replace("sh", "").replace("sz", "")
                    entry = {"code": bare_code, "price": row.get("最新价"),
                             "pe": None, "pb": None, "mv": None,
                             "change": row.get("涨跌幅")}
                    _stock_cache[name] = entry
                    _stock_cache[bare_code] = entry
            _stock_cache_time = now
            return _stock_cache
    except Exception:
        pass

    # 方案4: 空缓存（后续 _fetch_realtime_from_cache 逐股降级）
    return _stock_cache or {}


def resolve_stock(query: str) -> tuple[str, str] | None:
    """
    用户输入→(代码, 名称)。
    核心原则：绝不阻塞。如果缓存没就绪，用快速备用方案。
    """
    query = query.strip()

    # 1. 优先用缓存（毫秒级）
    if _stock_cache:
        # 精确匹配
        if query in _stock_cache:
            info = _stock_cache[query]
            code = info["code"]
            name = query if not query.isdigit() else next(
                (k for k, v in _stock_cache.items() if isinstance(v, dict) and v.get("code") == code and not k.isdigit()), query
            )
            return (code, name)
        # 模糊匹配
        for key, info in _stock_cache.items():
            if isinstance(info, dict) and not key.isdigit() and query in key:
                return (info["code"], key)

    # 2. 缓存没就绪 → 快速备用方案（不等待，不阻塞）
    # 常见股票硬编码映射（覆盖最热门的50只）
    QUICK_MAP = {
        "贵州茅台": "600519", "茅台": "600519",
        "比亚迪": "002594", "宁德时代": "300750",
        "中国平安": "601318", "招商银行": "600036",
        "腾讯": "00700", "阿里巴巴": "09988",
        "工商银行": "601398", "建设银行": "601939",
        "中国银行": "601988", "农业银行": "601288",
        "中国中免": "601888", "美的集团": "000333",
        "格力电器": "000651", "海尔智家": "600690",
        "隆基绿能": "601012", "恒瑞医药": "600276",
        "药明康德": "603259", "迈瑞医疗": "300760",
        "五粮液": "000858", "泸州老窖": "000568",
        "长江电力": "600900", "中国神华": "601088",
        "紫金矿业": "601899", "中国石油": "601857",
        "中国移动": "600941", "中国电信": "601728",
        "立讯精密": "002475", "歌尔股份": "002241",
        "东方财富": "300059", "同花顺": "300033",
        "中信证券": "600030", "海天味业": "603288",
        "万科": "000002", "保利发展": "600048",
        "三一重工": "600031", "中联重科": "000157",
        "科大讯飞": "002230", "海康威视": "002415",
        "中芯国际": "688981", "韦尔股份": "603501",
    }
    for name, code in QUICK_MAP.items():
        if query in name or query == code:
            return (code, name)

    # 3. 如果输入看起来像股票代码（纯数字6位），直接用
    if query.isdigit() and len(query) == 6:
        return (query, query)

    # 4. 都匹配不上，返回None（让后续逻辑用用户原始输入搜索）
    return None


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
    """财报主要指标（Wind 优先 → AkShare 财报摘要 → 利润表+资产负债表 → 财务指标降级）"""
    import time as _time
    from scripts.provider_observability import get_request_id, log_provider_call, classify_exception

    # — Tier 0: Wind —
    if _check_wind_available():
        t0_start = _time.monotonic()
        t0_outcome = None; t0_exc_cls = None; t0_exc_msg = None
        try:
            import wind_data
            result = wind_data.get_financials(code)
            if result:
                t0_outcome = "SUCCESS_WITH_DATA"
                log_provider_call(
                    domain="financials", provider="wind",
                    endpoint="get_financials", started_at=t0_start,
                    outcome=t0_outcome, fallback_used=False,
                )
                return result
            else:
                t0_outcome = "VALID_EMPTY"
        except Exception as e:
            t0_exc_cls = type(e).__name__
            t0_exc_msg = str(e)[:200]
            t0_outcome = classify_exception(e)
        finally:
            if t0_outcome != "SUCCESS_WITH_DATA":
                log_provider_call(
                    domain="financials", provider="wind",
                    endpoint="get_financials", started_at=t0_start,
                    outcome=t0_outcome, exception_class=t0_exc_cls,
                    exception_message=t0_exc_msg, fallback_used=False,
                )

    # — Tier 1: AkShare 财报摘要 —
    t1_start = _time.monotonic()
    t1_outcome = None; t1_exc_cls = None; t1_exc_msg = None; t1_rows = None; t1_cols = None
    t1_timeout = 12.0
    try:
        df_abstract = _with_timeout(
            ak.stock_financial_abstract,
            kwargs={"symbol": code},
            timeout_seconds=t1_timeout
        )
        t1_elapsed = _time.monotonic() - t1_start
        if df_abstract is not None and len(df_abstract) > 0:
            t1_outcome = "SUCCESS_WITH_DATA"
            t1_rows = len(df_abstract)
            t1_cols = len(df_abstract.columns)
            period_cols = [c for c in df_abstract.columns if c not in ("选项", "指标")][:4]
            rows = []
            for period in period_cols:
                row = {"报告期": str(period)}
                for _, r in df_abstract.iterrows():
                    indicator = str(r.get("指标", ""))
                    value = r.get(period)
                    if indicator and value is not None:
                        row[indicator] = value
                if len(row) > 1:
                    rows.append(row)
            if rows:
                log_provider_call(
                    domain="financials", provider="akshare",
                    endpoint="stock_financial_abstract", started_at=t1_start,
                    outcome=t1_outcome, row_count=t1_rows, field_count=t1_cols,
                    fallback_used=True,
                )
                return rows
            else:
                t1_outcome = "VALID_EMPTY"
        elif df_abstract is not None and len(df_abstract) == 0:
            t1_outcome = "VALID_EMPTY"
        elif t1_elapsed >= t1_timeout * 0.95:
            t1_outcome = "TIMEOUT"
        else:
            t1_outcome = "VALID_EMPTY"
    except Exception as e:
        t1_exc_cls = type(e).__name__
        t1_exc_msg = str(e)[:200]
        t1_outcome = classify_exception(e)
    finally:
        if t1_outcome != "SUCCESS_WITH_DATA":
            log_provider_call(
                domain="financials", provider="akshare",
                endpoint="stock_financial_abstract", started_at=t1_start,
                outcome=t1_outcome, exception_class=t1_exc_cls,
                exception_message=t1_exc_msg, row_count=t1_rows,
                field_count=t1_cols, fallback_used=True,
            )

    # — Tier 2: 利润表 + 资产负债表 —
    profit_rows = None
    balance_rows = None

    t2a_start = _time.monotonic()
    t2a_outcome = None; t2a_exc_cls = None; t2a_exc_msg = None; t2a_rows = None; t2a_cols = None
    t2a_timeout = 12.0
    try:
        df_profit = _with_timeout(
            ak.stock_profit_sheet_by_report_em,
            kwargs={"symbol": code},
            timeout_seconds=t2a_timeout
        )
        t2a_elapsed = _time.monotonic() - t2a_start
        if df_profit is not None and len(df_profit) > 0:
            t2a_outcome = "SUCCESS_WITH_DATA"
            t2a_rows = len(df_profit)
            t2a_cols = len(df_profit.columns)
            profit_rows = df_profit.tail(4).to_dict(orient="records")
        elif df_profit is not None and len(df_profit) == 0:
            t2a_outcome = "VALID_EMPTY"
        elif t2a_elapsed >= t2a_timeout * 0.95:
            t2a_outcome = "TIMEOUT"
        else:
            t2a_outcome = "VALID_EMPTY"
    except Exception as e:
        t2a_exc_cls = type(e).__name__
        t2a_exc_msg = str(e)[:200]
        t2a_outcome = classify_exception(e)
    finally:
        log_provider_call(
            domain="financials", provider="akshare",
            endpoint="stock_profit_sheet_by_report_em", started_at=t2a_start,
            outcome=t2a_outcome, exception_class=t2a_exc_cls,
            exception_message=t2a_exc_msg, row_count=t2a_rows,
            field_count=t2a_cols, fallback_used=True,
        )

    t2b_start = _time.monotonic()
    t2b_outcome = None; t2b_exc_cls = None; t2b_exc_msg = None; t2b_rows = None; t2b_cols = None
    t2b_timeout = 12.0
    try:
        df_balance = _with_timeout(
            ak.stock_balance_sheet_by_report_em,
            kwargs={"symbol": code},
            timeout_seconds=t2b_timeout
        )
        t2b_elapsed = _time.monotonic() - t2b_start
        if df_balance is not None and len(df_balance) > 0:
            t2b_outcome = "SUCCESS_WITH_DATA"
            t2b_rows = len(df_balance)
            t2b_cols = len(df_balance.columns)
            balance_rows = df_balance.tail(4).to_dict(orient="records")
        elif df_balance is not None and len(df_balance) == 0:
            t2b_outcome = "VALID_EMPTY"
        elif t2b_elapsed >= t2b_timeout * 0.95:
            t2b_outcome = "TIMEOUT"
        else:
            t2b_outcome = "VALID_EMPTY"
    except Exception as e:
        t2b_exc_cls = type(e).__name__
        t2b_exc_msg = str(e)[:200]
        t2b_outcome = classify_exception(e)
    finally:
        log_provider_call(
            domain="financials", provider="akshare",
            endpoint="stock_balance_sheet_by_report_em", started_at=t2b_start,
            outcome=t2b_outcome, exception_class=t2b_exc_cls,
            exception_message=t2b_exc_msg, row_count=t2b_rows,
            field_count=t2b_cols, fallback_used=True,
        )

    if profit_rows or balance_rows:
        merged = []
        for i in range(max(len(profit_rows or []), len(balance_rows or []))):
            row = {}
            if profit_rows and i < len(profit_rows):
                for k, v in profit_rows[i].items():
                    row[k] = v
            if balance_rows and i < len(balance_rows):
                for k, v in balance_rows[i].items():
                    if k not in row:
                        row[k] = v
            merged.append(row)
        if merged:
            return merged

    # — Tier 3: 财务指标兜底 —
    t3_start = _time.monotonic()
    t3_outcome = None; t3_exc_cls = None; t3_exc_msg = None; t3_rows = None; t3_cols = None
    t3_timeout = 10.0
    try:
        df_indicator = _with_timeout(
            ak.stock_financial_analysis_indicator,
            kwargs={"symbol": code, "start_year": "2022"},
            timeout_seconds=t3_timeout
        )
        t3_elapsed = _time.monotonic() - t3_start
        if df_indicator is not None and len(df_indicator) > 0:
            t3_outcome = "SUCCESS_WITH_DATA"
            indicator_rows = df_indicator.tail(4).to_dict(orient="records")
            t3_rows = len(df_indicator)
            t3_cols = len(df_indicator.columns)
        elif df_indicator is not None and len(df_indicator) == 0:
            t3_outcome = "VALID_EMPTY"
            indicator_rows = None
        elif t3_elapsed >= t3_timeout * 0.95:
            t3_outcome = "TIMEOUT"
            indicator_rows = None
        else:
            t3_outcome = "VALID_EMPTY"
            indicator_rows = None
    except Exception as e:
        t3_exc_cls = type(e).__name__
        t3_exc_msg = str(e)[:200]
        t3_outcome = classify_exception(e)
        indicator_rows = None
    finally:
        log_provider_call(
            domain="financials", provider="akshare",
            endpoint="stock_financial_analysis_indicator", started_at=t3_start,
            outcome=t3_outcome, exception_class=t3_exc_cls,
            exception_message=t3_exc_msg, row_count=t3_rows,
            field_count=t3_cols, fallback_used=True,
        )

    return indicator_rows


def _derive_pb(code: str, price: float) -> float | None:
    """从每股净资产推算 PB。腾讯源不提供 PB 时的轻量补全。"""
    import time as _time
    from scripts.provider_observability import get_request_id, log_provider_call, classify_exception

    started = _time.monotonic()
    outcome = None; exc_class = None; exc_msg = None; row_count = None
    timeout_s = 5.0
    try:
        df = _with_timeout(
            ak.stock_financial_analysis_indicator,
            kwargs={"symbol": code, "start_year": "2025"},
            timeout_seconds=timeout_s,
        )
        elapsed = _time.monotonic() - started
        if df is not None and len(df) > 0:
            outcome = "SUCCESS_WITH_DATA"
            row_count = len(df)
            bvps = df.iloc[-1].get("每股净资产_调整前(元)")
            if bvps and float(bvps) > 0:
                return round(price / float(bvps), 2)
        elif df is not None and len(df) == 0:
            outcome = "VALID_EMPTY"
        elif elapsed >= timeout_s * 0.95:
            outcome = "TIMEOUT"
        else:
            outcome = "VALID_EMPTY"
        return None
    except Exception as e:
        exc_class = type(e).__name__
        exc_msg = str(e)[:200]
        outcome = classify_exception(e)
        return None
    finally:
        log_provider_call(
            domain="realtime", provider="akshare",
            endpoint="stock_financial_analysis_indicator",
            started_at=started, outcome=outcome,
            exception_class=exc_class, exception_message=exc_msg,
            row_count=row_count, fallback_used=True,
        )


def _fetch_realtime_from_cache(code: str) -> dict | None:
    """获取实时行情（缓存优先 → K线 降级）

    缓存由 _load_stock_cache 预加载（腾讯→东方财富→Sina 三级降级）。
    单股 API 均走东方财富域（被代理阻断），所以无 Tier 1 逐股查询——
    缓存 miss 直接走 K 线兜底。
    """
    import time as _time
    from scripts.provider_observability import get_request_id, log_provider_call, classify_exception

    cache = _stock_cache or {}
    info = cache.get(code)
    # 缓存 key 可能是 sh/sz 前缀格式（Sina 源），尝试其他写法
    if info is None:
        for prefix in ("sh", "sz"):
            info = cache.get(prefix + code)
            if info is not None:
                break

    # Tier 0: 缓存命中（腾讯/东方财富/Sina 预加载）
    if isinstance(info, dict) and info.get("price") is not None:
        cache_provider = info.get("source_chain", {}).get("primary", "cache_preload")
        log_provider_call(
            domain="realtime", provider=cache_provider,
            endpoint="_load_stock_cache", started_at=_time.monotonic(),
            outcome="SUCCESS_WITH_DATA", fallback_used=False,
        )
        result = {
            **info,
            "source_chain": {"primary": "akshare_spot", "fallback": []},
            "source_type": "primary",
        }
        # 如果缓存缺 PB（腾讯源不提供），从财务指标推算
        if info.get("pb") is None and info.get("price") is not None:
            pb = _derive_pb(code, float(info["price"]))
            if pb is not None:
                result["pb"] = pb
                result["source_chain"]["fallback"].append("pb_derived")
        return result

    # Tier 1: K线收盘价兜底（只有价格/涨跌幅，无 PE/PB/市值）
    k_start = _time.monotonic()
    k_outcome = None; k_exc_cls = None; k_exc_msg = None; k_rows = None
    k_timeout = 6.0
    try:
        df = _with_timeout(ak.stock_zh_a_hist, kwargs={
            "symbol": code, "period": "daily",
            "start_date": (datetime.now() - timedelta(days=5)).strftime("%Y%m%d"),
            "end_date": datetime.now().strftime("%Y%m%d"),
            "adjust": ""
        }, timeout_seconds=k_timeout)
        k_elapsed = _time.monotonic() - k_start
        if df is not None and len(df) > 0:
            k_outcome = "SUCCESS_WITH_DATA"
            k_rows = len(df)
            latest = df.iloc[-1]
            log_provider_call(
                domain="realtime", provider="akshare",
                endpoint="stock_zh_a_hist", started_at=k_start,
                outcome=k_outcome, row_count=k_rows, fallback_used=True,
            )
            return {
                "code": code,
                "price": latest.get("收盘"),
                "change": latest.get("涨跌幅"),
                "date": str(latest.get("日期", "")),
                "source_chain": {"primary": "akshare_spot", "fallback": ["kline_history"]},
                "source_type": "fallback",
            }
        elif df is not None and len(df) == 0:
            k_outcome = "VALID_EMPTY"
        elif k_elapsed >= k_timeout * 0.95:
            k_outcome = "TIMEOUT"
        else:
            k_outcome = "VALID_EMPTY"
    except Exception as e:
        k_exc_cls = type(e).__name__
        k_exc_msg = str(e)[:200]
        k_outcome = classify_exception(e)
    finally:
        if k_outcome != "SUCCESS_WITH_DATA":
            log_provider_call(
                domain="realtime", provider="akshare",
                endpoint="stock_zh_a_hist", started_at=k_start,
                outcome=k_outcome, exception_class=k_exc_cls,
                exception_message=k_exc_msg, row_count=k_rows,
                fallback_used=True,
            )

    # Tier 2: 缓存基本信息兜底（无 price，不可做交易决策）
    if isinstance(info, dict):
        log_provider_call(
            domain="realtime", provider="stale_cache",
            endpoint="_fetch_realtime_from_cache", started_at=_time.monotonic(),
            outcome="VALID_EMPTY", fallback_used=True,
        )
        return {
            **info,
            "source_chain": {"primary": "akshare_spot", "fallback": ["stale_cache"]},
            "source_type": "stale_cache",
        }
    return None


def _fetch_price_history(code: str) -> list[dict] | None:
    """近60日K线（0.2秒）"""
    import time as _time
    from scripts.provider_observability import get_request_id, log_provider_call, classify_exception

    started = _time.monotonic()
    outcome = None; exc_class = None; exc_msg = None; row_count = None

    try:
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
        df = ak.stock_zh_a_hist(symbol=code, period="daily",
                                 start_date=start, end_date=end, adjust="qfq")
        if df is not None and len(df) > 0:
            outcome = "SUCCESS_WITH_DATA"
            row_count = len(df)
            return df.tail(30).to_dict(orient="records")
        elif df is not None and len(df) == 0:
            outcome = "VALID_EMPTY"
            row_count = 0
        else:
            outcome = "VALID_EMPTY"
        return None
    except Exception as e:
        exc_class = type(e).__name__
        exc_msg = str(e)[:200]
        outcome = classify_exception(e)
        return None
    finally:
        log_provider_call(
            domain="price_history",
            provider="akshare",
            endpoint="stock_zh_a_hist",
            started_at=started,
            outcome=outcome,
            exception_class=exc_class,
            exception_message=exc_msg,
            row_count=row_count,
        )


def _fetch_fund_flow(code: str) -> list[dict] | None:
    """个股资金流向"""
    import time as _time
    from scripts.provider_observability import get_request_id, log_provider_call, classify_exception

    market = _get_market(code)
    started = _time.monotonic()
    outcome = None; exc_class = None; exc_msg = None; row_count = None
    timeout_s = 8.0

    try:
        df = _with_timeout(
            ak.stock_individual_fund_flow,
            kwargs={"stock": code, "market": market},
            timeout_seconds=timeout_s,
        )
        elapsed = _time.monotonic() - started
        if df is None:
            outcome = "TIMEOUT" if elapsed >= timeout_s * 0.95 else "VALID_EMPTY"
        elif len(df) == 0:
            outcome = "VALID_EMPTY"
            row_count = 0
        else:
            outcome = "SUCCESS_WITH_DATA"
            row_count = len(df)

        if df is not None and len(df) > 0:
            return df.tail(10).to_dict(orient="records")
        return None
    except Exception as e:
        exc_class = type(e).__name__
        exc_msg = str(e)[:200]
        outcome = classify_exception(e)
        logger.warning(
            "fund_flow unavailable for %s (market=%s): %s: %s",
            code, market, type(e).__name__, e,
        )
        return None
    finally:
        log_provider_call(
            domain="capital_flow",
            provider="akshare",
            endpoint="stock_individual_fund_flow",
            started_at=started,
            outcome=outcome,
            exception_class=exc_class,
            exception_message=exc_msg,
            row_count=row_count,
        )


def _fetch_valuation(code: str) -> dict | None:
    """估值指标 + PE/PB 历史分位（Wind 优先 → AkShare 财报反推）

    返回值包含 valuation_source 结构化类型字段，区分：
      - REAL_PROVIDER: Wind 直接提供的估值数据
      - DERIVED: 从 EPS/BVPS + 行情推算的估值
      - UNKNOWN: 来源不明
    """
    import time as _time
    from scripts.provider_observability import get_request_id, log_provider_call, classify_exception

    # — REAL_PROVIDER path: Wind —
    if _check_wind_available():
        w_start = _time.monotonic()
        w_outcome = None; w_exc_cls = None; w_exc_msg = None
        try:
            import wind_data
            result = wind_data.get_valuation_history(code)
            if result:
                result["valuation_source"] = {
                    "type": "real_provider",
                    "provider": "wind",
                    "provider_status": "available",
                }
                w_outcome = "SUCCESS_WITH_DATA"
                log_provider_call(
                    domain="valuation", provider="wind",
                    endpoint="get_valuation_history", started_at=w_start,
                    outcome=w_outcome, fallback_used=False,
                )
                return result
            else:
                w_outcome = "VALID_EMPTY"
        except Exception as e:
            w_exc_cls = type(e).__name__
            w_exc_msg = str(e)[:200]
            w_outcome = classify_exception(e)
        finally:
            if w_outcome != "SUCCESS_WITH_DATA":
                log_provider_call(
                    domain="valuation", provider="wind",
                    endpoint="get_valuation_history", started_at=w_start,
                    outcome=w_outcome, exception_class=w_exc_cls,
                    exception_message=w_exc_msg, fallback_used=False,
                )

    # — DERIVED path: 从 AkShare 财报 + 行情推算 —
    rt = _fetch_realtime_from_cache(code) or {}
    pe = rt.get("pe")
    pb = rt.get("pb")
    mv = rt.get("mv")

    # Track the AkShare indicator call used for PE/PB derivation
    ak_start = _time.monotonic()
    ak_outcome = None; ak_exc_cls = None; ak_exc_msg = None; ak_rows = None; ak_cols = None
    ak_timeout = 8.0
    if pe is None or pb is None:
        try:
            df = _with_timeout(
                ak.stock_financial_analysis_indicator,
                kwargs={"symbol": code, "start_year": "2022"},
                timeout_seconds=ak_timeout
            )
            ak_elapsed = _time.monotonic() - ak_start
            if df is not None and len(df) > 0:
                ak_outcome = "SUCCESS_WITH_DATA"
                ak_rows = len(df)
                ak_cols = len(df.columns)
                latest = df.iloc[-1]
                eps = latest.get("摊薄每股收益(元)")
                bvps = latest.get("每股净资产_调整前(元)")
                price = rt.get("price")
                if price and eps and float(eps) > 0:
                    pe = round(float(price) / float(eps), 2)
                if price and bvps and float(bvps) > 0:
                    pb = round(float(price) / float(bvps), 2)
            elif df is not None and len(df) == 0:
                ak_outcome = "VALID_EMPTY"
            elif ak_elapsed >= ak_timeout * 0.95:
                ak_outcome = "TIMEOUT"
            else:
                ak_outcome = "VALID_EMPTY"
        except Exception as e:
            ak_exc_cls = type(e).__name__
            ak_exc_msg = str(e)[:200]
            ak_outcome = classify_exception(e)
        finally:
            log_provider_call(
                domain="valuation", provider="akshare",
                endpoint="stock_financial_analysis_indicator",
                started_at=ak_start, outcome=ak_outcome,
                exception_class=ak_exc_cls, exception_message=ak_exc_msg,
                row_count=ak_rows, field_count=ak_cols, fallback_used=True,
            )

    if pe is None and pb is None and mv is None:
        return None

    result = {
        "code": code,
        "note": "当前估值指标（非历史分位，Wind 不可用时从 AkShare 财报+行情推算）",
        "valuation_source": {
            "type": "derived",
            "provider": "akshare_calculation",
        },
        "provider": "akshare_calculation",
        "primary_provider_attempted": "wind",
        "primary_provider_status": "unavailable",
    }
    if pe is not None:
        result["pe"] = pe
    if pb is not None:
        result["pb"] = pb
    if mv is not None:
        result["market_cap"] = mv
    if pe is None and pb is None:
        result["note"] += "；PE/PB 无法计算（EPS 为负或净资产为负）"
    return result


def _fetch_news(code: str) -> list[dict] | None:
    """个股新闻（东方财富，0.7秒）"""
    import time as _time
    from scripts.provider_observability import get_request_id, log_provider_call, classify_exception

    started = _time.monotonic()
    outcome = None; exc_class = None; exc_msg = None; row_count = None

    try:
        df = ak.stock_news_em(symbol=code)
        if df is not None and len(df) > 0:
            outcome = "SUCCESS_WITH_DATA"
            row_count = len(df)
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
        elif df is not None and len(df) == 0:
            outcome = "VALID_EMPTY"
            row_count = 0
        else:
            outcome = "VALID_EMPTY"
        return None
    except Exception as e:
        exc_class = type(e).__name__
        exc_msg = str(e)[:200]
        outcome = classify_exception(e)
        return None
    finally:
        log_provider_call(
            domain="news",
            provider="akshare",
            endpoint="stock_news_em",
            started_at=started,
            outcome=outcome,
            exception_class=exc_class,
            exception_message=exc_msg,
            row_count=row_count,
        )


def _fetch_dividends(code: str) -> list[dict] | None:
    """历史分红"""
    import time as _time
    from scripts.provider_observability import get_request_id, log_provider_call, classify_exception

    started = _time.monotonic()
    outcome = None; exc_class = None; exc_msg = None; row_count = None

    try:
        df = ak.stock_history_dividend_detail(symbol=code, indicator="分红")
        if df is not None and len(df) > 0:
            outcome = "SUCCESS_WITH_DATA"
            row_count = len(df)
            return df.head(5).to_dict(orient="records")
        elif df is not None and len(df) == 0:
            outcome = "VALID_EMPTY"
            row_count = 0
        else:
            outcome = "VALID_EMPTY"
        return None
    except Exception as e:
        exc_class = type(e).__name__
        exc_msg = str(e)[:200]
        outcome = classify_exception(e)
        return None
    finally:
        log_provider_call(
            domain="dividends",
            provider="akshare",
            endpoint="stock_history_dividend_detail",
            started_at=started,
            outcome=outcome,
            exception_class=exc_class,
            exception_message=exc_msg,
            row_count=row_count,
        )


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
    val_task = loop.run_in_executor(_executor, _fetch_valuation, code)

    results = {}
    for key, task in [
        ("financials", fin_task),
        ("price_history", price_task),
        ("fund_flow", flow_task),
        ("news", news_task),
        ("dividends", div_task),
        ("valuation", val_task),
    ]:
        try:
            results[key] = await task
        except Exception:
            results[key] = None

    # 实时行情从缓存取（不额外请求）
    results["realtime"] = _fetch_realtime_from_cache(code)

    # 构建 realtime_availability 元数据（_qc_stock 读取此字段判定 realtime 状态）
    # 区分 direct（腾讯直接返回）与 derived（从其他数据推算），对 Trust Gate 和 QC 证据层分类至关重要
    rt = results.get("realtime") or {}
    rt_available = [k for k in ("price", "pe", "pb", "mv") if rt.get(k) is not None]
    rt_missing = [k for k in ("price", "pe", "pb", "mv") if rt.get(k) is None]
    # PE/市值来自腾讯 source=tencent method=direct，PB 来自 financial_indicator+price method=derived
    # pb_derived 标记来自 source_chain.fallback
    pb_derived = "pb_derived" in rt.get("source_chain", {}).get("fallback", [])
    rt_provenance = {}
    for field in ("price", "pe", "pb", "mv"):
        if rt.get(field) is not None:
            if field == "pb" and pb_derived:
                rt_provenance[field] = {
                    "source": "akshare_financial_indicator+realtime_price",
                    "method": "derived",
                }
            else:
                rt_provenance[field] = {
                    "source": rt.get("source_chain", {}).get("primary", "unknown"),
                    "method": "direct",
                }
    results["realtime_availability"] = {
        "status": "available" if rt_available else "unavailable",
        "source": rt.get("source_chain", {}).get("primary"),
        "source_type": rt.get("source_type", "not_connected"),
        "as_of": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "available": rt_available,
        "missing": rt_missing,
        "allowed_use": rt_available,
        "blocked_fields": rt_missing,
        "provenance": rt_provenance,
    }

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

    # 估值
    val = data.get("valuation")
    if val and isinstance(val, dict):
        parts.append("【估值指标】")
        if val.get("pe") is not None:
            parts.append(f"市盈率(PE)：{val['pe']} 倍")
        if val.get("pb") is not None:
            parts.append(f"市净率(PB)：{val['pb']} 倍")
        if val.get("market_cap") is not None:
            parts.append(f"总市值：{val['market_cap']}")
        if val.get("note"):
            parts.append(f"说明：{val['note']}")
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
