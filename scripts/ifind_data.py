"""
同花顺 iFinD 数据获取模块
支持两种接入方式（自动选择）：
  1. HTTP REST API（需要 access_token，从 quantapi.51ifind.com 后台获取）
  2. iFinDPy SDK（需从官网下载安装：quantapi.10jqka.com.cn）

环境变量：
  THS_USERNAME   — 同花顺账号（SDK 模式使用）
  THS_PASSWORD   — 同花顺密码（SDK 模式使用）
  THS_TOKEN      — HTTP API 静态 access_token（HTTP 模式使用）
  THS_REFRESH_TOKEN — HTTP API refresh_token（用于获取当前有效 access_token）

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
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass

_THS_USERNAME = os.getenv("THS_USERNAME", "")
_THS_PASSWORD = os.getenv("THS_PASSWORD", "")
_THS_TOKEN = os.getenv("THS_TOKEN", "")
_THS_REFRESH_TOKEN = os.getenv("THS_REFRESH_TOKEN", "")

_IFIND_BASE_URL = "https://quantapi.51ifind.com/api/v1"
_IFIND_ACCESS_TOKEN_URL = f"{_IFIND_BASE_URL}/get_access_token"

# SDK 连接状态
_sdk_connected = None
_http_mode = False  # True = 使用 HTTP REST API
_http_token_source = ""


def _ensure_connection() -> bool:
    """
    优先尝试 iFinDPy SDK，失败则降级到 HTTP REST API。

    HTTP 模式优先用 THS_REFRESH_TOKEN 向官方 get_access_token
    接口获取当前有效 access_token；未配置 refresh_token 时复用 THS_TOKEN。
    """
    global _sdk_connected, _http_mode, _http_token_source

    if _sdk_connected is True:
        return True
    if _http_mode:
        return bool(_get_http_access_token())

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

    # 降级到 HTTP REST API。refresh_token 只用于换取 access_token，不写回磁盘。
    if _THS_REFRESH_TOKEN and _get_http_access_token():
        _http_mode = True
        logger.info("✅ iFinD HTTP REST API 模式（refresh_token 换取 access_token）")
        return True

    if _THS_TOKEN:
        _http_mode = True
        _http_token_source = "static"
        logger.info("✅ iFinD HTTP REST API 模式（静态 access_token）")
        return True

    logger.warning("⚠️ iFinD 未配置：需要 THS_USERNAME+THS_PASSWORD、THS_TOKEN 或 THS_REFRESH_TOKEN")
    return False


def _extract_access_token(payload: dict) -> str:
    """兼容官方示例与可能的轻微响应结构差异。"""
    data = payload.get("data") if isinstance(payload, dict) else None
    if isinstance(data, dict):
        return data.get("access_token") or data.get("accessToken") or ""
    return payload.get("access_token") or payload.get("accessToken") or ""


def _get_http_access_token(force_refresh: bool = False) -> str:
    """返回 HTTP access_token；必要时用 refresh_token 换取当前有效 token。"""
    global _THS_TOKEN, _http_token_source

    if _THS_TOKEN and not force_refresh and not _THS_REFRESH_TOKEN:
        if not _http_token_source:
            _http_token_source = "static"
        return _THS_TOKEN

    if not _THS_REFRESH_TOKEN:
        return _THS_TOKEN

    try:
        import requests
        headers = {
            "Content-Type": "application/json",
            "refresh_token": _THS_REFRESH_TOKEN,
        }
        resp = requests.post(_IFIND_ACCESS_TOKEN_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        token = _extract_access_token(payload)
        if token:
            _THS_TOKEN = token
            _http_token_source = "refresh"
            return _THS_TOKEN
        logger.warning("iFinD HTTP get_access_token 未返回 access_token")
    except Exception as e:
        logger.warning(f"iFinD HTTP get_access_token 失败: {e}")

    return _THS_TOKEN if not force_refresh else ""


def _looks_like_auth_failure(resp: dict) -> bool:
    """判断 HTTP 响应是否可能是 access_token 失效，避免把无权限误判成可重试。"""
    if not isinstance(resp, dict):
        return False

    message = " ".join(str(resp.get(key, "")) for key in ("errmsg", "message", "error", "msg"))
    lower_msg = message.lower()
    auth_markers = (
        "access_token",
        "token",
        "expired",
        "expire",
        "unauthorized",
        "authorization",
        "鉴权",
        "认证",
        "失效",
        "过期",
    )
    return any(marker in lower_msg or marker in message for marker in auth_markers)


def _qc_failure(reason: str, detail: str = "") -> dict:
    """构造非敏感失败分类，供上游区分授权、端点、网络等问题。"""
    qc = {
        "status": "failure",
        "provider": "ifind",
        "reason": reason,
        "allowed_use": False,
    }
    if detail:
        qc["detail"] = detail
    return qc


def _with_qc_failure(payload: dict, reason: str, detail: str = "") -> dict:
    result = payload if isinstance(payload, dict) else {"errorcode": -1, "errmsg": str(payload)}
    result["_qc"] = _qc_failure(reason, detail)
    return result


def _classify_http_status(status_code: int) -> str:
    if status_code in (401, 403):
        return "authorization_failed"
    if status_code == 404:
        return "endpoint_mismatch"
    if status_code >= 500:
        return "provider_unavailable"
    return "http_error"


def _classify_exception(exc: Exception) -> str:
    message = str(exc).lower()
    if "401" in message or "403" in message or "unauthorized" in message:
        return "authorization_failed"
    if "404" in message:
        return "endpoint_mismatch"
    if "timeout" in message or "timed out" in message:
        return "upstream_timeout"
    return "request_failed"


def _http_get(endpoint: str, params: dict) -> dict:
    """HTTP REST API 通用请求"""
    token = _get_http_access_token()
    if not token:
        return _with_qc_failure(
            {"errorcode": -1, "errmsg": "THS_TOKEN/THS_REFRESH_TOKEN 未配置"},
            "missing_credentials",
        )

    try:
        import requests
        headers = {
            "access_token": token,
            "Content-Type": "application/json",
        }
        url = f"{_IFIND_BASE_URL}/{endpoint}"
        resp = requests.post(url, headers=headers, json=params, timeout=15)
        if resp.status_code in (401, 403) and _THS_REFRESH_TOKEN:
            token = _get_http_access_token(force_refresh=True)
            if token:
                headers["access_token"] = token
                resp = requests.post(url, headers=headers, json=params, timeout=15)
        if resp.status_code >= 400:
            return _with_qc_failure(
                {"errorcode": resp.status_code, "errmsg": resp.text},
                _classify_http_status(resp.status_code),
            )
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("errorcode") != 0 and _THS_REFRESH_TOKEN and _looks_like_auth_failure(payload):
            token = _get_http_access_token(force_refresh=True)
            if token:
                headers["access_token"] = token
                retry = requests.post(url, headers=headers, json=params, timeout=15)
                if retry.status_code >= 400:
                    return _with_qc_failure(
                        {"errorcode": retry.status_code, "errmsg": retry.text},
                        _classify_http_status(retry.status_code),
                    )
                retry.raise_for_status()
                retry_payload = retry.json()
                if retry_payload.get("errorcode") != 0:
                    return _with_qc_failure(
                        retry_payload,
                        "authorization_failed" if _looks_like_auth_failure(retry_payload) else "provider_error",
                    )
                return retry_payload
        if payload.get("errorcode") != 0:
            return _with_qc_failure(
                payload,
                "authorization_failed" if _looks_like_auth_failure(payload) else "provider_error",
            )
        return payload
    except Exception as e:
        return _with_qc_failure({"errorcode": -1, "errmsg": str(e)}, _classify_exception(e))


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
    token_mode = _http_token_source if mode == "http" else ""
    return {"connected": ok, "source": "ifind", "mode": mode, "token_mode": token_mode}


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
