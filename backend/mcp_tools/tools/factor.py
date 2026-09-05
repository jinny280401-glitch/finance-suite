"""MCP tools: factor_scan"""
from backend.mcp_tools.server import (
    mcp, _wrap_response, _make_error_response,
    _qc_stock, _qc_macro, _qc_auction,
    _format_jq_signals, _joinquant_stale_entries,
    _check_incremental, _enforce_trust_gate_or_block,
    logger,
)

# Tool 7: 因子选股信号
# ============================================================
@mcp.tool()
def factor_scan(date: str = "") -> str:
    """执行量化因子选股扫描，返回命中股票及评分。
    优先级：trading-system → JoinQuant → Wind → Tushare → AkShare。
    扫描可能需要 1-3 分钟。date 格式 YYYY-MM-DD，留空默认今天。
    返回结构化 _qc 质检 JSON。"""
    try:
        from backend.engine.skills import factor_skill as fs
        import joinquant_data
        from backend.engine.providers import wind_provider as wind_data
        from backend.engine.providers import tushare_provider as tushare_data

        scan_date = date or None
        data = fs.get_factor_signals(scan_date)
        has_error = "error" in data
        source_used = data.get("source_used", "trading_system")
        logger.info("factor_scan start date=%s source=trading_system status=%s", scan_date or 'today', 'error' if has_error else 'ok')

        # 第二层：JoinQuant
        if has_error:
            try:
                jq_data = joinquant_data.get_factor_signals(scan_date)
                if jq_data and "signals" in jq_data and "error" not in jq_data:
                    data = jq_data
                    has_error = False
                    source_used = "joinquant"
                    logger.info("factor_scan fallback success source=joinquant")
                else:
                    logger.warning("factor_scan fallback source=joinquant returned empty/error")
            except Exception as e:
                logger.warning("factor_scan fallback source=joinquant failed: %s", e)

        # 第三层：Wind（以估值/快照近似筛选信号）
        if has_error:
            try:
                universe = ["600519.SH", "000858.SZ", "600036.SH", "601318.SH", "000333.SZ"]
                signals = []
                for code in universe:
                    snap = wind_data.get_stock_snapshot(code) or {}
                    pe = snap.get("pe") or snap.get("pe_ttm")
                    roe = snap.get("roe")
                    mv = snap.get("market_cap") or snap.get("total_mv")
                    if pe is None or roe is None or mv is None:
                        continue
                    try:
                        pe_f = float(pe)
                        roe_f = float(roe)
                        mv_f = float(mv)
                    except Exception:
                        continue
                    if 10 <= pe_f <= 30 and roe_f > 15 and 50 <= mv_f <= 500:
                        signals.append({"code": code, "name": code, "pe": pe_f, "roe": roe_f, "market_cap": mv_f})
                data = {"signals": signals, "scan_date": datetime.now().strftime("%Y-%m-%d")}
                has_error = False
                source_used = "wind"
                logger.info("factor_scan fallback success source=wind")
            except Exception as e:
                logger.warning("factor_scan fallback source=wind failed: %s", e)

        # 第四层：Tushare（以快照近似筛选信号）
        if has_error:
            try:
                universe = ["600519.SH", "000858.SZ", "600036.SH", "601318.SH", "000333.SZ"]
                signals = []
                for code in universe:
                    snap = tushare_data.get_stock_snapshot(code) or {}
                    pe = snap.get("pe") or snap.get("pe_ttm")
                    roe = snap.get("roe")
                    mv = snap.get("market_cap") or snap.get("total_mv")
                    if pe is None or roe is None or mv is None:
                        continue
                    try:
                        pe_f = float(pe)
                        roe_f = float(roe)
                        mv_f = float(mv)
                    except Exception:
                        continue
                    if 10 <= pe_f <= 30 and roe_f > 15 and 50 <= mv_f <= 500:
                        signals.append({"code": code, "name": code, "pe": pe_f, "roe": roe_f, "market_cap": mv_f})
                data = {"signals": signals, "scan_date": datetime.now().strftime("%Y-%m-%d")}
                has_error = False
                source_used = "tushare"
                logger.info("factor_scan fallback success source=tushare")
            except Exception as e:
                logger.warning("factor_scan fallback source=tushare failed: %s", e)

        # 第五层：AkShare（兜底为空结果，不抛错）
        if has_error:
            data = {"signals": [], "scan_date": datetime.now().strftime("%Y-%m-%d"), "note": "AkShare fallback: no factor model"}
            has_error = False
            source_used = "akshare"
            logger.warning("factor_scan fallback source=akshare used")

        has_signals = bool(data.get("signals"))
        market_env = data.get("market_env") or {}
        if isinstance(data, dict) and isinstance(data.get("_qc"), dict):
            qc = data["_qc"]
        else:
            fallback_triggered = source_used != "trading_system"
            attempted_sources = ["trading_system"] if not fallback_triggered else ["trading_system", source_used]
            qc = {
                "status": "success" if has_signals else "partial",
                "completeness": 1.0 if has_signals else (0.5 if market_env else 0.3),
                "sources": attempted_sources,
                "fallback_source": source_used if fallback_triggered else None,
                "missing_dimensions": [] if has_signals else (["候选信号"] if market_env else ["候选信号", "市场环境"]),
                "stale_data": _joinquant_stale_entries(data) if source_used == "joinquant" else [],
            }
            data["_qc"] = qc
        data.setdefault("source_used", source_used)
        data.setdefault("fallback_chain", ["trading_system", "joinquant", "wind", "tushare", "akshare"])
        data.setdefault("fallback_triggered", source_used != "trading_system")
        logger.info(
            "factor_scan success scan_date=%s source=%s fallback_triggered=%s data_date=%s",
            data.get('scan_date', scan_date or 'today'),
            data.get('source_used'),
            data.get('fallback_triggered'),
            (data.get('_metadata') or {}).get('data_date') or data.get('scan_date'),
        )

        if source_used == "trading_system":
            formatted = fs.format_factor_signals(data)
        elif source_used == "joinquant":
            formatted = (
                f"{_format_jq_signals(data)}\n\n"
                f"{json.dumps(data, ensure_ascii=False, indent=2)}"
            )
        else:
            formatted = json.dumps({"source": source_used, "data": data}, ensure_ascii=False, indent=2)

        return _wrap_response(qc, formatted)

    except Exception as e:
        logger.exception("factor_scan fatal error: %s", e)
        return _make_error_response(f"factor_scan 异常: {e}")


# ============================================================


