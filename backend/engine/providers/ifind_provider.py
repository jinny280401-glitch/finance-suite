"""
同花顺 iFinD 数据获取模块
支持两种接入方式（自动选择）：
  1. HTTP REST API（需要 access_token，从 quantapi.51ifind.com 后台获取）
  2. iFinDPy SDK（需从官网下载安装：quantapi.10jqka.com.cn）

环境变量：
  THS_USERNAME   — 同花顺账号（SDK 模式使用）
  THS_PASSWORD   — 同花顺密码（SDK 模式使用）
  THS_TOKEN      — HTTP API 静态 access_token（HTTP 模式使用）

独立 CLI 脚本，无内部依赖
用法:
  python3 ifind_data.py --action connect
  python3 ifind_data.py --action stock --code 300750.SZ
  python3 ifind_data.py --action financials --code 600519.SH
  python3 ifind_data.py --action consensus --code 300750.SZ
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

_THS_USERNAME = os.getenv("THS_USERNAME", "")
_THS_PASSWORD = os.getenv("THS_PASSWORD", "")
_THS_TOKEN = os.getenv("THS_TOKEN", "")

_IFIND_BASE_URL = "https://quantapi.51ifind.com/api/v1"

# SDK 连接状态
_sdk_connected = None
_http_mode = False  # True = 使用 HTTP REST API


def _ensure_connection() -> bool:
    """
    优先尝试 iFinDPy SDK，失败则降级到 HTTP REST API（需要 THS_TOKEN）。
    """
    global _sdk_connected, _http_mode

    if _sdk_connected is True:
        return True
    if _http_mode:
        return bool(_THS_TOKEN)

    # 尝试 SDK
    if _THS_USERNAME and _THS_PASSWORD:
        try:
            import iFinDPy as THS
            ret = THS.THS_iFinDLogin(_THS_USERNAME, _THS_PASSWORD)
            if ret == 0:
                _sdk_connected = True
                logger.info("✅ iFinDPy SDK 已连接")
                return True
            else:
                logger.warning(f"⚠️ iFinDPy SDK 登录失败，错误码: {ret}")
        except ImportError:
            logger.info("iFinDPy SDK 未安装，尝试 HTTP REST API 模式")
        except Exception as e:
            logger.warning(f"⚠️ iFinDPy SDK 异常: {e}")

    # 降级到 HTTP REST API
    if _THS_TOKEN:
        _http_mode = True
        logger.info("✅ iFinD HTTP REST API 模式（静态 token）")
        return True

    logger.warning("⚠️ iFinD 未配置：需要 THS_USERNAME+THS_PASSWORD 或 THS_TOKEN")
    return False


def _http_get(endpoint: str, params: dict) -> dict:
    """HTTP REST API 通用请求"""
    try:
        import requests
        headers = {
            "access_token": _THS_TOKEN,
            "Content-Type": "application/json",
        }
        url = f"{_IFIND_BASE_URL}/{endpoint}"
        resp = requests.post(url, headers=headers, json=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"errorcode": -1, "errmsg": str(e)}


def _ths_code(code: str) -> str:
    """补齐同花顺代码格式（与 Wind 格式相同）"""
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
    mode = "sdk" if _sdk_connected else ("http" if _http_mode else "unavailable")
    return {"connected": ok, "source": "ifind", "mode": mode}


def get_stock_snapshot(code: str) -> dict:
    """实时行情快照：价格、涨跌幅、成交量、市值、PE/PB"""
    if not _ensure_connection():
        return {}

    wcode = _ths_code(code)

    if _sdk_connected:
        try:
            import iFinDPy as THS
            indicators = "ths_close_price_stock,ths_change_rate_stock,ths_vol_stock,ths_total_mv_stock,ths_pe_ttm_stock,ths_pb_lf_stock"
            result = THS.THS_BasicData(wcode, indicators, "")
            if result.errorcode == 0:
                return {"code": wcode, "data": result.data}
        except Exception as e:
            logger.warning(f"iFinD SDK get_stock_snapshot 失败: {e}")
        return {}

    # HTTP 模式
    today = datetime.now().strftime("%Y-%m-%d")
    resp = _http_get("real_time_quotation", {
        "codes": wcode,
        "indicators": "open,high,low,close,change,changepct,volume,amount,mktcap,pe_ttm,pb_lf",
        "tradedate": today,
    })
    if resp.get("errorcode") == 0:
        return {"code": wcode, "data": resp.get("tables", {})}
    logger.warning(f"iFinD HTTP get_stock_snapshot 失败: {resp.get('errmsg')}")
    return {}


def get_financials(code: str) -> list:
    """财务数据：营收/净利润/毛利率/ROE（最近4期）"""
    if not _ensure_connection():
        return []

    wcode = _ths_code(code)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=450)).strftime("%Y-%m-%d")

    if _sdk_connected:
        try:
            import iFinDPy as THS
            indicators = "ths_revenue_stock,ths_net_profit_stock,ths_gross_profit_margin_stock,ths_net_profit_margin_stock,ths_roe_stock"
            result = THS.THS_HistoryQuotes(wcode, indicators, "", start_date, end_date)
            if result.errorcode == 0:
                return result.data if isinstance(result.data, list) else [result.data]
        except Exception as e:
            logger.warning(f"iFinD SDK get_financials 失败: {e}")
        return []

    # HTTP 模式
    resp = _http_get("financial_data", {
        "codes": wcode,
        "indicators": "ths_revenue_stock,ths_net_profit_stock,ths_gross_profit_margin_stock,ths_roe_stock",
        "startdate": start_date,
        "enddate": end_date,
        "reporttype": "Q",
    })
    if resp.get("errorcode") == 0:
        tables = resp.get("tables", {})
        return tables if isinstance(tables, list) else [tables]
    logger.warning(f"iFinD HTTP get_financials 失败: {resp.get('errmsg')}")
    return []


def get_consensus_estimates(code: str) -> dict:
    """卖方一致预期：净利润预测/EPS/目标价/评级"""
    if not _ensure_connection():
        return {}

    wcode = _ths_code(code)

    if _sdk_connected:
        try:
            import iFinDPy as THS
            indicators = "ths_np_forecast_fy1_stock,ths_np_forecast_fy2_stock,ths_eps_forecast_fy1_stock,ths_target_price_stock,ths_rating_stock"
            result = THS.THS_BasicData(wcode, indicators, "")
            if result.errorcode == 0:
                return {"code": wcode, "data": result.data}
        except Exception as e:
            logger.warning(f"iFinD SDK get_consensus_estimates 失败: {e}")
        return {}

    resp = _http_get("consensus_data", {
        "codes": wcode,
        "indicators": "ths_np_forecast_fy1_stock,ths_np_forecast_fy2_stock,ths_eps_forecast_fy1_stock,ths_target_price_stock,ths_rating_stock",
    })
    if resp.get("errorcode") == 0:
        return {"code": wcode, "data": resp.get("tables", {})}
    logger.warning(f"iFinD HTTP get_consensus_estimates 失败: {resp.get('errmsg')}")
    return {}


def get_index_constituents(index_code: str) -> list:
    """获取指数成分股"""
    if not _ensure_connection():
        return []

    if _sdk_connected:
        try:
            import iFinDPy as THS
            result = THS.THS_DataPool("block", f"{index_code};date:{datetime.now().strftime('%Y-%m-%d')}", "thscode;security_name")
            if result.errorcode == 0:
                return result.data if isinstance(result.data, list) else [result.data]
        except Exception as e:
            logger.warning(f"iFinD SDK get_index_constituents 失败: {e}")
        return []

    resp = _http_get("index_constituent", {
        "codes": index_code,
        "tradedate": datetime.now().strftime("%Y-%m-%d"),
    })
    if resp.get("errorcode") == 0:
        tables = resp.get("tables", {})
        return tables if isinstance(tables, list) else [tables]
    logger.warning(f"iFinD HTTP get_index_constituents 失败: {resp.get('errmsg')}")
    return []


# ---- CLI ----

def main():
    parser = argparse.ArgumentParser(description="同花顺 iFinD 数据获取")
    parser.add_argument("--action", required=True, choices=[
        "connect", "stock", "financials", "consensus", "index"
    ])
    parser.add_argument("--code", help="股票/指数代码")
    args = parser.parse_args()

    if args.action == "connect":
        print(json.dumps(check_connection(), ensure_ascii=False, indent=2))
        return

    if not args.code:
        print(json.dumps({"error": "--code 是必填参数"}, ensure_ascii=False))
        sys.exit(1)

    actions = {
        "stock": lambda: get_stock_snapshot(args.code),
        "financials": lambda: get_financials(args.code),
        "consensus": lambda: get_consensus_estimates(args.code),
        "index": lambda: get_index_constituents(args.code),
    }

    result = actions[args.action]()
    if not result:
        print(json.dumps({
            "success": False,
            "message": "iFinD 连接失败或查询无结果。请确认 THS_TOKEN 或 iFinDPy SDK 已配置。"
        }, ensure_ascii=False))
    else:
        print(json.dumps({
            "success": True,
            "source": "ifind",
            "code": args.code,
            "data": result
        }, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
