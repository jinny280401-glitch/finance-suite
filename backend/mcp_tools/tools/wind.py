"""MCP tools: wind_query"""
from backend.mcp_tools.server import (
    mcp, _wrap_response, _make_error_response,
    _qc_stock, _qc_macro, _qc_auction,
    _format_jq_signals, _joinquant_stale_entries,
    _check_incremental, _enforce_trust_gate_or_block,
    logger,
)

# Tool 8: 金融数据查询（三层降级：Wind → Tushare → AkShare）
# ============================================================
@mcp.tool()
def wind_query(action: str, code: str = "", max_peers: int = 10) -> str:
    """Wind 查询工具（支持多源降级）

    数据源优先级：
        - Wind → Tushare Pro → JoinQuant（聚宽）→ AkShare（免费）

    valuation 动作：
        - Wind → JoinQuant → Tushare → AkShare（JoinQuant 历史分位更完整）

    connect action 返回值示例：
        {
            "wind": True,
            "tushare": True,
            "joinquant": jq_status.get("connected", False),
            "akshare": True,
            "priority": "Wind → Tushare → JoinQuant → AkShare"
        }

    action 可选值：
        - connect: 检查数据源连接状态
        - stock: 个股快照（价格/市值/PE/PB/ROE）
        - financials: 完整三大报表（近4期）
        - consensus: 卖方一致预期（净利润/EPS/ROE/目标价/评级）
        - peers: 同行业可比公司对比
        - valuation: 历史估值分位（PE/PB 10年百分位）
        - shareholders: 前十大股东及持股变动
        - calendar: 财报披露日期

    参数：
        action: str, 查询动作类型
        code: str, 股票代码（connect 动作不需要）
        max_peers: int, peers 动作返回的最大同行数量

    返回：
        dict, 包含数据及 _qc 质检信息（status, completeness, sources, fallback_source）
    """
    try:
        from backend.engine.providers import wind_provider as wind_data
        from backend.engine.providers import tushare_provider as tushare_data
        try:
            import joinquant_data
        except ImportError as exc:
            if exc.name != "joinquant_data":
                raise
            joinquant_data = None
            logger.warning("wind_query optional JoinQuant provider unavailable: %s", exc)

        if action == "connect":
            # 检查所有数据源连接状态
            wind_status = wind_data.check_connection()
            tushare_status = tushare_data.check_connection()
            jq_status = (
                joinquant_data.check_connection()
                if joinquant_data is not None
                else {"connected": False, "available": False, "reason": "provider module unavailable"}
            )

            sources = []
            if wind_status.get("connected"):
                sources.append("wind")
            if tushare_status.get("connected"):
                sources.append("tushare")
            if jq_status.get("connected"):
                sources.append("joinquant")
            sources.append("akshare")  # AkShare 总是可用

            qc = {
                "status": "success",
                "completeness": 1.0,
                "sources": sources,
                "source_chain": {
                    "primary": "multi",
                    "attempted": ["wind", "tushare", "joinquant", "akshare"],
                    "failed": [],
                    "winner": "multi",
                },
                "source_type": "primary",
                "fallback_source": None,
                "missing_dimensions": [],
                "stale_data": [],
            }
            result = {
                "connected": wind_status.get("connected", False),
                "wind": wind_status.get("connected", False),
                "tushare": tushare_status.get("connected", False),
                "joinquant": jq_status.get("connected", False),
                "akshare": True,
                "priority": "Wind → Tushare → JoinQuant → AkShare",
                "joinquant_detail": jq_status,
            }
            raw_response = _wrap_response(qc, json.dumps(result, ensure_ascii=False, indent=2))
            return _enforce_trust_gate_or_block(
                action="connect", code="", result=result, source_used="multi",
                raw_response=raw_response,
            )

        if not code:
            error_qc = {
                "status": "failure",
                "completeness": 0,
                "sources": [],
                "source_chain": {"primary": None, "attempted": [], "failed": [], "winner": None},
                "source_type": "none",
                "fallback_source": "tushare/akshare",
                "missing_dimensions": [f"{action}"],
                "stale_data": [],
                "error": f"action={action} 需要提供 code 参数",
            }
            raw = _wrap_response(error_qc, "")
            return _enforce_trust_gate_or_block(
                action=action, code="", result=None, source_used="",
                raw_response=raw,
            )

        result = None
        source_used = None

        # 按动作定义优先级链
        chains = {
            "stock": ["wind", "tushare", "joinquant"],
            "financials": ["tushare", "joinquant", "akshare"],
            "consensus": ["wind", "tushare"],
            "peers": ["wind", "tushare"],
            "valuation": ["wind", "joinquant", "tushare", "akshare"],
            "shareholders": ["wind"],
            "calendar": ["wind"],
        }
        chain = chains.get(action, ["wind", "tushare", "joinquant"])
        logger.info("wind_query start action=%s code=%s chain=%s", action, code, ' -> '.join(chain))

        def _try_wind() -> dict | None:
            actions_map = {
                "stock": lambda: wind_data.get_stock_snapshot(code),
                "financials": lambda: wind_data.get_financials(code),
                "consensus": lambda: wind_data.get_consensus_estimates(code),
                "peers": lambda: wind_data.get_industry_peers(code, max_peers),
                "valuation": lambda: wind_data.get_valuation_history(code),
                "shareholders": lambda: wind_data.get_major_shareholders(code),
                "calendar": lambda: wind_data.get_earnings_calendar(code),
            }
            fn = actions_map.get(action)
            return fn() if fn else None

        def _try_tushare() -> dict | None:
            actions_map = {
                "stock": lambda: tushare_data.get_stock_snapshot(code),
                "financials": lambda: tushare_data.get_financials(code, "income"),
                "consensus": lambda: tushare_data.get_consensus_estimates(code),
                "peers": lambda: tushare_data.get_industry_peers(code, max_peers),
                "valuation": lambda: tushare_data.get_valuation_history(code) if hasattr(tushare_data, "get_valuation_history") else None,
            }
            fn = actions_map.get(action)
            return fn() if fn else None

        def _try_joinquant() -> dict | None:
            if joinquant_data is None:
                return None
            actions_map = {
                "stock": lambda: joinquant_data.get_stock_snapshot(code),
                "valuation": lambda: joinquant_data.get_valuation_history(code),
                "financials": lambda: joinquant_data.get_financials(code) if hasattr(joinquant_data, "get_financials") else None,
            }
            fn = actions_map.get(action)
            return fn() if fn else None

        def _try_akshare() -> dict | None:
            # 仅对 financials / valuation 提供轻量兜底
            if action == "financials":
                try:
                    import akshare as ak
                    bare = code.split(".")[0]
                    df = ak.stock_financial_analysis_indicator(symbol=bare, start_year="2023")
                    if df is not None and len(df) > 0:
                        return {"financials": df.head(4).to_dict(orient="records")}
                except Exception:
                    return None
            if action == "valuation":
                return {"note": "akshare fallback: valuation history unavailable"}
            return None

        runners = {
            "wind": _try_wind,
            "tushare": _try_tushare,
            "joinquant": _try_joinquant,
            "akshare": _try_akshare,
        }

        chain_attempted: list[str] = []
        chain_failed: list[str] = []
        for source in chain:
            chain_attempted.append(source)
            try:
                candidate = runners[source]()
                if candidate:
                    result = candidate
                    source_used = source
                    logger.info("wind_query success action=%s code=%s source=%s", action, code, source)
                    break
                chain_failed.append(source)
                logger.warning("wind_query empty action=%s code=%s source=%s", action, code, source)
            except Exception as e:
                chain_failed.append(source)
                logger.warning("wind_query failed action=%s code=%s source=%s err=%s", action, code, source, e)

        if not result:
            qc = {
                "status": "failure",
                "completeness": 0,
                "sources": [],
                "source_chain": {
                    "primary": chain[0],
                    "attempted": chain_attempted,
                    "failed": chain_attempted,  # all failed
                    "winner": None,
                },
                "source_type": "none",
                "fallback_source": "akshare",
                "missing_dimensions": [f"{action}"],
                "stale_data": [],
                "error": f"{action} 多源查询失败（Wind/Tushare/JoinQuant/AkShare）",
            }
            raw_response = _wrap_response(qc, "")
            return _enforce_trust_gate_or_block(
                action=action, code=code, result=None, source_used="",
                raw_response=raw_response,
            )

        primary_source = chain[0]
        source_type = "primary" if source_used == primary_source else "fallback"
        source_chain_evidence = {
            "primary": primary_source,
            "attempted": chain_attempted,
            "failed": chain_failed,
            "winner": source_used,
        }
        fallback_map = {"wind": "tushare", "tushare": "joinquant", "joinquant": "akshare", "akshare": None}
        qc = {
            "status": "success" if source_type == "primary" else "partial",
            "completeness": 1.0 if source_type == "primary" else 0.7,
            "sources": [source_used],
            "source_chain": source_chain_evidence,
            "source_type": source_type,
            "fallback_source": fallback_map.get(source_used),
            "missing_dimensions": [],
            "stale_data": _joinquant_stale_entries(result) if source_used == "joinquant" else [],
        }
        formatted = json.dumps({
            "source": source_used, "code": code, "action": action, "data": result,
        }, ensure_ascii=False, indent=2, default=str)
        raw_response = _wrap_response(qc, formatted)
        return _enforce_trust_gate_or_block(
            action=action, code=code, result=result, source_used=source_used,
            raw_response=raw_response,
        )

    except Exception as e:
        logger.exception("wind_query fatal error action=%s code=%s: %s", action, code, e)
        error_qc = {
            "status": "failure",
            "completeness": 0,
            "sources": [],
            "source_chain": {"primary": None, "attempted": [], "failed": [], "winner": None},
            "source_type": "none",
            "fallback_source": "tushare/akshare",
            "missing_dimensions": [f"{action}"],
            "stale_data": [],
            "error": f"wind_query 异常: {e}",
        }
        raw = _wrap_response(error_qc, "")
        return _enforce_trust_gate_or_block(
            action=action, code=code or "", result=None, source_used="",
            raw_response=raw,
        )


# ============================================================


