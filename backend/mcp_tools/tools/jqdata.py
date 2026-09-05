"""MCP tools: jqdata_query"""
from backend.mcp_tools.server import (
    mcp, _wrap_response, _make_error_response,
    _qc_stock, _qc_macro, _qc_auction,
    _format_jq_signals, _joinquant_stale_entries,
    _check_incremental, _enforce_trust_gate_or_block,
    logger,
)



@mcp.tool()
def jqdata_query(
    action: str,
    code: str = "",
    start_date: str = "",
    end_date: str = "",
    frequency: str = "daily",
    fields: str = "",
    date: str = "",
    index_code: str = "",
    fund_type: str = "etf",
    limit: int = 20
) -> str:
    """
    通过 JQData（聚宽数据）获取金融数据。

    action 可选值:
    - auth: 测试认证和查询额度
    - price: 获取股票/ETF行情数据（需 code, 可选 start_date/end_date/frequency/fields）
    - info: 获取证券基本信息（股票/ETF/基金均可，需 code）
    - fund_nav: 获取场外基金净值（需 code=6位基金代码如000001, 可选 start_date/end_date/limit）
    - fund_list: 获取基金列表（可选 fund_type=etf/lof/open_fund/money_market_fund）
    - fund_info: 获取场内基金(ETF/LOF)信息+近期行情（需 code）
    - fundamentals: 获取财务数据（需 code, 可选 date）
    - index_stocks: 获取指数成分股（需 index_code, 可选 date）

    示例:
    - jqdata_query('auth')
    - jqdata_query('price', code='000001.XSHE', start_date='2026-01-26', end_date='2026-02-02')
    - jqdata_query('fund_nav', code='000001', limit=10)
    - jqdata_query('fund_nav', code='110022', start_date='2026-01-01')
    - jqdata_query('fund_list', fund_type='etf')
    - jqdata_query('fund_info', code='510300.XSHG')
    - jqdata_query('info', code='510300.XSHG')
    - jqdata_query('index_stocks', index_code='000300.XSHG')

    数据时间范围限制: 2025-01-26 至 2026-02-02（试用账号）
    返回结构化 _qc 质检 JSON。
    """
    try:
        from scripts.jqdata_fetch import main as jqdata_main

        # 按 action 精确分发参数，避免把 price 专用参数传给基金/指数接口。
        kwargs = {}
        if action in {"price", "info", "fund_nav", "fund_info", "fundamentals"} and code:
            kwargs["code"] = code
        if action == "price":
            if start_date:
                kwargs["start_date"] = start_date
            if end_date:
                kwargs["end_date"] = end_date
            if frequency:
                kwargs["frequency"] = frequency
            if fields:
                kwargs["fields"] = fields.split(",")
        elif action == "fund_nav":
            if start_date:
                kwargs["start_date"] = start_date
            if end_date:
                kwargs["end_date"] = end_date
            kwargs["limit"] = limit
        elif action == "fund_list":
            kwargs["fund_type"] = fund_type
        elif action == "fundamentals":
            if date:
                kwargs["date"] = date
        elif action == "index_stocks":
            if index_code:
                kwargs["index_code"] = index_code
            if date:
                kwargs["date"] = date

        # 调用 JQData
        result = jqdata_main(action, **kwargs)

        # 质检
        if result.get('success'):
            qc = {
                "status": "success",
                "completeness": 1.0,
                "sources": ["jqdata"],
                "fallback_source": None,
                "missing_dimensions": [],
                "stale_data": [],
                "note": "JQData 数据范围: 2025-01-26 至 2026-02-02"
            }
        else:
            qc = {
                "status": "failure",
                "completeness": 0.0,
                "sources": [],
                "fallback_source": None,
                "missing_dimensions": ["JQData 数据"],
                "stale_data": [],
                "error": result.get('error', '未知错误')
            }

        return _wrap_response(qc, json.dumps(result, ensure_ascii=False, indent=2, default=str))

    except Exception as e:
        return _make_error_response(f"jqdata_query 异常: {e}")


# ============================================================


