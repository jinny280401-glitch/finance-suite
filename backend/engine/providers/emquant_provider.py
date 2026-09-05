"""
东方财富 Choice 数据获取模块（EmQuantAPI SDK）
SDK 需从官网下载安装：quantapi.eastmoney.com → 下载中心 → EmQuantAPI Python

环境变量：
  EM_USERNAME   — 东方财富 Choice 账号
  EM_PASSWORD   — 东方财富 Choice 密码

当前账户 (hfzq80016) 数据权限：
  ✅ CSS 基础行情: OPEN, CLOSE, HIGH, LOW, VOLUME, AMOUNT, TURN, DIVIDENDYIELD
  ✅ CSD 序列行情: 同上（日频 OHLCV）
  ✅ EDB 宏观: CPI_YOY, CPI_MOM, SHIBOR_1M
  ❌ 财务数据 (REVENUE, NETPROFIT, ROE, PE, PB 等) — ERR 10000013
  ❌ 一致预期 (WEST_*, RATING_*) — ERR 10000013
  ❌ 板块/行业分类 (sector, SWLEVEL*) — ERR 10000009/10000013
  ❌ 大部分宏观指标 — ERR 10000009

独立 CLI 脚本，无内部依赖
用法:
  python3 emquant_data.py --action connect
  python3 emquant_data.py --action stock --code 300750.SZ
  python3 emquant_data.py --action history --code 600519.SH
  python3 emquant_data.py --action macro
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

_EM_USERNAME = os.getenv("EM_USERNAME", "")
_EM_PASSWORD = os.getenv("EM_PASSWORD", "")

_em_connected = None

# 当前账户实际可用的指标（2026-08-07 实测验证）
_STOCK_INDICATORS = "OPEN,CLOSE,HIGH,LOW,VOLUME,AMOUNT,TURN,DIVIDENDYIELD"
_MACRO_CODES = {
    "CPI_YOY": "EMM00166702",
    "CPI_MOM": "EMM00166704",
    "SHIBOR_1M": "EMM00166489",
}
# 以下指标均不可用（ERR 10000013 service error）：PE_TTM, PB_LF, ROE_TTM, CHANGEPCT,
#   TOTALCAP, NEGOTIABLECAP, REVENUE, NETPROFIT, WEST_*, RATING_*, SWLEVEL2NAME
# 以下 EDB 均不可用（ERR 10000009 no data）：GDP, M2, PMI, LPR, 等


def _ensure_connection() -> bool:
    global _em_connected

    if _em_connected is True:
        return True
    if _em_connected is False:
        return False

    if not _EM_USERNAME or not _EM_PASSWORD:
        logger.warning("⚠️ EmQuantAPI 未配置：需要 EM_USERNAME 和 EM_PASSWORD")
        _em_connected = False
        return False

    try:
        import EmQuantAPI
        options = f"ForceLogin=1,UserName={_EM_USERNAME},Password={_EM_PASSWORD}"
        ret = EmQuantAPI.c.start(options)
        if ret.ErrorCode == 0:
            _em_connected = True
            logger.info("✅ EmQuantAPI 已连接")
            return True
        else:
            logger.warning(f"⚠️ EmQuantAPI 登录失败: {ret.ErrorMsg}")
            _em_connected = False
            return False
    except ImportError:
        logger.warning("⚠️ EmQuantAPI SDK 未安装，请从 quantapi.eastmoney.com 下载")
        _em_connected = False
        return False
    except Exception as e:
        logger.warning(f"⚠️ EmQuantAPI 异常: {e}")
        _em_connected = False
        return False


def _em_code(code: str) -> str:
    """补齐东方财富代码格式"""
    if "." in code:
        return code
    code = code.strip()
    if not code.isdigit() or len(code) != 6:
        return code
    if code.startswith(("600", "601", "603", "605", "688", "689")):
        return f"{code}.SH"
    if code.startswith(("000", "001", "002", "003", "300", "301")):
        return f"{code}.SZ"
    if code.startswith(("8", "9", "4")):
        return f"{code}.BJ"
    return code


# ---- 核心接口 ----

def check_connection() -> dict:
    ok = _ensure_connection()
    return {"connected": ok, "source": "emquant"}


def get_stock_snapshot(code: str) -> dict:
    """实时行情快照：开盘/收盘/最高/最低/成交量/成交额/换手率/股息率"""
    if not _ensure_connection():
        return {}

    try:
        from EmQuantAPI import c
        wcode = _em_code(code)
        result = c.css(wcode, _STOCK_INDICATORS)
        if result.ErrorCode == 0:
            return {"code": wcode, "data": result.Data}
        logger.warning(f"EmQuantAPI get_stock_snapshot 失败({result.ErrorCode}): {result.ErrorMsg}")
    except Exception as e:
        logger.warning(f"EmQuantAPI get_stock_snapshot 异常: {e}")
    return {}


def get_price_history(code: str, days: int = 250) -> dict:
    """历史行情序列：开盘/收盘/最高/最低/成交量/成交额（日频）

    PE/PB/ROE 等估值指标需要更高数据权限（当前账户 ERR 10000013）。
    """
    if not _ensure_connection():
        return {}

    try:
        from EmQuantAPI import c
        wcode = _em_code(code)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days + 30)).strftime("%Y-%m-%d")
        indicators = "open,close,high,low,volume,amount"
        # RowIndex=1 返回矩阵格式：Data[code][indicator_idx][date_idx]，否则无 Dates
        options = "RowIndex=1,period=1,adjustflag=1,curtype=1,pricetype=1,Ispandas=0"
        result = c.csd(wcode, indicators, start_date, end_date, options)
        if result.ErrorCode != 0:
            logger.warning(f"EmQuantAPI get_price_history 失败({result.ErrorCode}): {result.ErrorMsg}")
            return {}

        if not hasattr(result, 'Data') or wcode not in result.Data:
            return {}

        indicator_list = list(result.Indicators) if hasattr(result, 'Indicators') else []
        date_list = list(result.Dates) if hasattr(result, 'Dates') else []
        matrix = result.Data[wcode]  # [n_indicators][n_dates]

        out = {"code": wcode, "dates": date_list}
        for idx, ind in enumerate(indicator_list):
            out[ind.lower()] = matrix[idx] if idx < len(matrix) else []
        return out
    except Exception as e:
        logger.warning(f"EmQuantAPI get_price_history 异常: {e}")
    return {}


def get_macro_data() -> dict:
    """宏观经济数据：CPI 同比/环比、SHIBOR 1M（当前账户可用范围）

    GDP/M2/PMI/LPR 等其他宏观指标需要更高数据权限（ERR 10000009）。
    """
    if not _ensure_connection():
        return {}

    try:
        from EmQuantAPI import c
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365 * 3)).strftime("%Y-%m-%d")

        result = {}
        for name, macro_code in _MACRO_CODES.items():
            r = c.edb(macro_code, f"StartDate={start_date},EndDate={end_date}")
            if r.ErrorCode == 0:
                data = r.Data
                result[name] = {
                    "dates": data.get("DATES", []),
                    "values": data.get(macro_code, []),
                }
        return result
    except Exception as e:
        logger.warning(f"EmQuantAPI get_macro_data 异常: {e}")
    return {}


# ---- 不可用接口（需更高数据权限，已实测确认） ----

_UNAVAILABLE_MSG = (
    "当前 Choice 账户（hfzq80016）为基础行情级别，"
    "仅支持 OHLCV + 换手率 + 股息率 + 少量宏观指标，不支持财务/估值/一致预期/行业分类数据。"
    "如需此功能请联系东方财富升级数据权限。"
)


def get_financials(code: str) -> list:
    """⚠️ 不可用：财务数据需要更高数据权限（CSD REVENUE/NETPROFIT → ERR 10000013）"""
    if not _ensure_connection():
        return []
    logger.warning(_UNAVAILABLE_MSG)
    return []


def get_consensus_estimates(code: str) -> dict:
    """⚠️ 不可用：一致预期需要更高数据权限（WEST_*/RATING_* → ERR 10000013）"""
    if not _ensure_connection():
        return {}
    logger.warning(_UNAVAILABLE_MSG)
    return {}


def get_industry_peers(code: str, max_peers: int = 10) -> list:
    """⚠️ 不可用：行业分类数据需要更高数据权限（sector/SWLEVEL* → ERR 10000009/10000013）"""
    if not _ensure_connection():
        return []
    logger.warning(_UNAVAILABLE_MSG)
    return []


def get_valuation_history(code: str) -> dict:
    """⚠️ 不可用：PE/PB 需要更高数据权限（CSD PE_TTM/PB_LF → ERR 10000013）

    替代方案：使用 get_price_history() 获取日频 OHLCV 序列。
    """
    if not _ensure_connection():
        return {}
    logger.warning(_UNAVAILABLE_MSG)
    return {}


# ---- CLI ----

def main():
    parser = argparse.ArgumentParser(description="东方财富 Choice EmQuantAPI 数据获取")
    parser.add_argument("--action", required=True, choices=[
        "connect", "stock", "history", "macro",
        "financials", "consensus", "peers", "valuation",
    ])
    parser.add_argument("--code", help="股票代码")
    parser.add_argument("--days", type=int, default=250, help="历史数据天数（用于 history）")
    parser.add_argument("--max-peers", type=int, default=10, help="可比公司数量")
    args = parser.parse_args()

    if args.action == "connect":
        print(json.dumps(check_connection(), ensure_ascii=False, indent=2))
        return

    if args.action == "macro":
        result = get_macro_data()
    elif args.action == "history":
        if not args.code:
            print(json.dumps({"error": "--code 是必填参数"}, ensure_ascii=False))
            sys.exit(1)
        result = get_price_history(args.code, args.days)
    elif args.action == "stock":
        if not args.code:
            print(json.dumps({"error": "--code 是必填参数"}, ensure_ascii=False))
            sys.exit(1)
        result = get_stock_snapshot(args.code)
    elif args.action == "financials":
        if not args.code:
            print(json.dumps({"error": "--code 是必填参数"}, ensure_ascii=False))
            sys.exit(1)
        result = get_financials(args.code)
    elif args.action == "consensus":
        if not args.code:
            print(json.dumps({"error": "--code 是必填参数"}, ensure_ascii=False))
            sys.exit(1)
        result = get_consensus_estimates(args.code)
    elif args.action == "peers":
        if not args.code:
            print(json.dumps({"error": "--code 是必填参数"}, ensure_ascii=False))
            sys.exit(1)
        result = get_industry_peers(args.code, args.max_peers)
    elif args.action == "valuation":
        if not args.code:
            print(json.dumps({"error": "--code 是必填参数"}, ensure_ascii=False))
            sys.exit(1)
        result = get_valuation_history(args.code)
    else:
        result = None

    if not result:
        print(json.dumps({
            "success": False,
            "message": "EmQuantAPI 查询无结果。可能原因：账户权限不足、SDK 未安装、或指标不可用。",
        }, ensure_ascii=False))
    else:
        print(json.dumps({
            "success": True,
            "source": "emquant",
            "code": getattr(args, "code", None),
            "data": result,
        }, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
