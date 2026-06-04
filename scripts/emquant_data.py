"""
东方财富 Choice 数据获取模块（EmQuantAPI SDK）
SDK 需从官网下载安装：quantapi.eastmoney.com → 下载中心 → EmQuantAPI Python

环境变量：
  EM_USERNAME   — 东方财富 Choice 账号
  EM_PASSWORD   — 东方财富 Choice 密码

独立 CLI 脚本，无内部依赖
用法:
  python3 emquant_data.py --action connect
  python3 emquant_data.py --action stock --code 300750.SZ
  python3 emquant_data.py --action financials --code 600519.SH
  python3 emquant_data.py --action consensus --code 300750.SZ
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
        import EmQuantAPI as em
        ret = em.start(_EM_USERNAME, _EM_PASSWORD, "-I 0")
        if ret.get("ErrorCode") == 0:
            _em_connected = True
            logger.info("✅ EmQuantAPI 已连接")
            return True
        else:
            logger.warning(f"⚠️ EmQuantAPI 登录失败: {ret.get('ErrorMsg')}")
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
    """实时行情快照：价格、涨跌幅、成交量、市值、PE/PB/ROE"""
    if not _ensure_connection():
        return {}

    try:
        import EmQuantAPI as em
        wcode = _em_code(code)
        indicators = "CLOSE,CHANGEPCT,VOLUME,AMOUNT,TOTALCAP,NEGOTIABLECAP,PE_TTM,PB_LF,ROE_TTM,DIVIDENDYIELD"
        result = em.css(wcode, indicators)
        if result.get("ErrorCode") == 0:
            return {"code": wcode, "data": result.get("Data", {})}
        logger.warning(f"EmQuantAPI get_stock_snapshot 失败: {result.get('ErrorMsg')}")
    except Exception as e:
        logger.warning(f"EmQuantAPI get_stock_snapshot 异常: {e}")
    return {}


def get_financials(code: str) -> list:
    """财务数据：营收/净利润/毛利率/净利率/ROE/ROA（最近4期）"""
    if not _ensure_connection():
        return []

    try:
        import EmQuantAPI as em
        wcode = _em_code(code)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=450)).strftime("%Y-%m-%d")
        indicators = "REVENUE,NETPROFIT,GROSSPROFITMARGIN,NETPROFITMARGIN,ROE,ROA,DEBTTOASSETS,OPERATECASHFLOW"
        result = em.csd(wcode, indicators, start_date, end_date, "period=Q")
        if result.get("ErrorCode") == 0:
            data = result.get("Data", {})
            if isinstance(data, dict):
                rows = []
                dates = data.get("DATES", [])
                for i, dt in enumerate(dates):
                    row = {"date": str(dt)}
                    for field in indicators.split(","):
                        vals = data.get(field, [])
                        row[field.lower()] = vals[i] if i < len(vals) else None
                    rows.append(row)
                return rows
        logger.warning(f"EmQuantAPI get_financials 失败: {result.get('ErrorMsg')}")
    except Exception as e:
        logger.warning(f"EmQuantAPI get_financials 异常: {e}")
    return []


def get_consensus_estimates(code: str) -> dict:
    """卖方一致预期：净利润预测/EPS/目标价/评级"""
    if not _ensure_connection():
        return {}

    try:
        import EmQuantAPI as em
        wcode = _em_code(code)
        indicators = "WEST_NETPROFIT_FY1,WEST_NETPROFIT_FY2,WEST_EPS_FY1,WEST_EPS_FY2,WEST_AVGROE_FY1,WEST_INSTNUM,RATING_AVG,RATING_TARGETPRICE,RATING_NUMOFBUY,RATING_NUMOFHOLD"
        result = em.css(wcode, indicators)
        if result.get("ErrorCode") == 0:
            return {"code": wcode, "data": result.get("Data", {})}
        logger.warning(f"EmQuantAPI get_consensus_estimates 失败: {result.get('ErrorMsg')}")
    except Exception as e:
        logger.warning(f"EmQuantAPI get_consensus_estimates 异常: {e}")
    return {}


def get_industry_peers(code: str, max_peers: int = 10) -> list:
    """同行业可比公司对比"""
    if not _ensure_connection():
        return []

    try:
        import EmQuantAPI as em
        wcode = _em_code(code)
        # 获取申万行业分类
        ind_result = em.css(wcode, "SWLEVEL2NAME")
        if ind_result.get("ErrorCode") != 0:
            return []
        industry = ind_result.get("Data", {}).get("SWLEVEL2NAME", [None])[0]
        if not industry:
            return []

        # 获取同行业成分股
        sector_result = em.sector(f"申万行业分类.{industry}", datetime.now().strftime("%Y-%m-%d"))
        if sector_result.get("ErrorCode") != 0:
            return []
        peer_codes = sector_result.get("Codes", [])[:max_peers]
        if not peer_codes:
            return []

        # 批量获取指标
        indicators = "SECNAME,TOTALCAP,PE_TTM,PB_LF,ROE_TTM,REVENUE_TTM,REVENUEYOY"
        metrics = em.css(",".join(peer_codes), indicators)
        if metrics.get("ErrorCode") != 0:
            return []

        data = metrics.get("Data", {})
        result = []
        for i, pcode in enumerate(peer_codes):
            row = {"code": pcode}
            for field in indicators.split(","):
                vals = data.get(field, [])
                row[field.lower()] = vals[i] if i < len(vals) else None
            result.append(row)
        return result
    except Exception as e:
        logger.warning(f"EmQuantAPI get_industry_peers 异常: {e}")
    return []


def get_macro_data() -> dict:
    """宏观经济数据：GDP/CPI/PMI/M2/LPR"""
    if not _ensure_connection():
        return {}

    try:
        import EmQuantAPI as em
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365 * 3)).strftime("%Y-%m-%d")

        macro_codes = {
            "GDP": "EMM00000548",
            "CPI_YOY": "EMM00166702",
            "PMI_MFG": "EMM00095065",
            "M2_YOY": "EMM00097886",
        }

        result = {}
        for name, macro_code in macro_codes.items():
            r = em.edb(macro_code, start_date, end_date)
            if r.get("ErrorCode") == 0:
                data = r.get("Data", {})
                result[name] = {
                    "dates": data.get("DATES", []),
                    "values": data.get(macro_code, []),
                }
        return result
    except Exception as e:
        logger.warning(f"EmQuantAPI get_macro_data 异常: {e}")
    return {}


def get_valuation_history(code: str) -> dict:
    """历史估值分位（PE/PB 10年百分位）"""
    if not _ensure_connection():
        return {}

    try:
        import EmQuantAPI as em
        wcode = _em_code(code)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=3650)).strftime("%Y-%m-%d")

        result = em.csd(wcode, "PE_TTM,PB_LF", start_date, end_date, "period=D")
        if result.get("ErrorCode") != 0:
            return {}

        data = result.get("Data", {})
        pe_series = [x for x in data.get("PE_TTM", []) if x is not None and x > 0]
        pb_series = [x for x in data.get("PB_LF", []) if x is not None and x > 0]

        if not pe_series or not pb_series:
            return {}

        def percentile(series, value):
            count = sum(1 for x in series if x <= value)
            return round(count / len(series) * 100, 2)

        current_pe = pe_series[-1]
        current_pb = pb_series[-1]
        pe_sorted = sorted(pe_series)
        pb_sorted = sorted(pb_series)

        return {
            "pe_current": current_pe,
            "pe_10y_percentile": percentile(pe_sorted, current_pe),
            "pe_10y_min": pe_sorted[0],
            "pe_10y_max": pe_sorted[-1],
            "pe_10y_median": pe_sorted[len(pe_sorted) // 2],
            "pb_current": current_pb,
            "pb_10y_percentile": percentile(pb_sorted, current_pb),
            "pb_10y_median": pb_sorted[len(pb_sorted) // 2],
        }
    except Exception as e:
        logger.warning(f"EmQuantAPI get_valuation_history 异常: {e}")
    return {}


# ---- CLI ----

def main():
    parser = argparse.ArgumentParser(description="东方财富 Choice EmQuantAPI 数据获取")
    parser.add_argument("--action", required=True, choices=[
        "connect", "stock", "financials", "consensus", "peers", "macro", "valuation"
    ])
    parser.add_argument("--code", help="股票代码")
    parser.add_argument("--max-peers", type=int, default=10, help="可比公司数量")
    args = parser.parse_args()

    if args.action == "connect":
        print(json.dumps(check_connection(), ensure_ascii=False, indent=2))
        return

    if args.action == "macro":
        result = get_macro_data()
    else:
        if not args.code:
            print(json.dumps({"error": "--code 是必填参数"}, ensure_ascii=False))
            sys.exit(1)
        actions = {
            "stock": lambda: get_stock_snapshot(args.code),
            "financials": lambda: get_financials(args.code),
            "consensus": lambda: get_consensus_estimates(args.code),
            "peers": lambda: get_industry_peers(args.code, args.max_peers),
            "valuation": lambda: get_valuation_history(args.code),
        }
        result = actions[args.action]()

    if not result:
        print(json.dumps({
            "success": False,
            "message": "EmQuantAPI 连接失败或查询无结果。请确认 EM_USERNAME/EM_PASSWORD 已配置且 SDK 已安装。"
        }, ensure_ascii=False))
    else:
        print(json.dumps({
            "success": True,
            "source": "emquant",
            "code": getattr(args, "code", None),
            "data": result
        }, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
