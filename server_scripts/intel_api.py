"""
市场情报 API
GET /api/intel/xueqiu-hot        - 雪球热门讨论
GET /api/intel/xueqiu-hot-stock  - 雪球热股榜
GET /api/intel/golden-pit        - 黄金坑四重门扫描（?realtime=true 追加实时行情）
GET /api/intel/discussions       - Sidebar 热门讨论统一契约
GET /api/intel/hot-stocks        - Sidebar 热股榜统一契约
GET /api/intel/watch-alerts      - Sidebar 自选股异动统一契约
GET /api/intel/research          - Sidebar 脱水研报统一契约
GET /api/intel/all               - Sidebar 四板块聚合
GET /api/intel/market-context    - 今日市场画像 / Market Context Layer
"""
from fastapi import APIRouter, HTTPException, Query
import json
import subprocess
import sys
import os

router = APIRouter(prefix="/api/intel")

FINANCE_SUITE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_PATH = os.path.join(FINANCE_SUITE_PATH, "scripts")
# trading-system 通过环境变量配置，支持独立部署
TRADING_SYSTEM_PATH = os.getenv("TRADING_SYSTEM_PATH") or os.path.join(os.path.dirname(FINANCE_SUITE_PATH), "trading-system")

if SCRIPTS_PATH not in sys.path:
    sys.path.insert(0, SCRIPTS_PATH)


def _parse_mcp_response(raw: str) -> dict:
    if not raw:
        return {}
    parts = raw.split("\n\n", 1)
    try:
        envelope = json.loads(parts[0])
    except Exception:
        envelope = {}
    content = parts[1] if len(parts) > 1 else ""
    parsed = {"_qc": envelope.get("_qc", {}), "raw": content}
    json_start = content.find("{")
    if json_start >= 0:
        try:
            parsed["data"] = json.loads(content[json_start:])
        except Exception:
            pass
    return parsed


def _loads_last_json(stdout: str):
    """子进程可能输出日志/SDK 提示，取最后一行 JSON 作为工具返回。"""
    for line in reversed((stdout or "").splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    raise json.JSONDecodeError("No JSON object found in subprocess stdout", stdout or "", 0)


def _call_mcp_tool(tool_name: str, **kwargs) -> dict:
    """调用 Finance Suite MCP 工具"""
    try:
        args_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
        cmd = [
            sys.executable, "-c",
            f"""
import json, sys
sys.path.insert(0, {repr(FINANCE_SUITE_PATH)})
from mcp_server import {tool_name}
result = {tool_name}({args_str})
print(json.dumps(result, ensure_ascii=False))
"""
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            return _loads_last_json(result.stdout)
        raise HTTPException(status_code=500, detail=result.stderr[-300:] or "工具调用失败")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="工具调用超时")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"返回数据解析失败: {e}")


def _call_trading_tool(tool_name: str, **kwargs) -> dict:
    """调用 Trading System MCP 工具"""
    try:
        args_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
        cmd = [
            sys.executable, "-c",
            f"""
import json, sys
sys.path.insert(0, {repr(TRADING_SYSTEM_PATH)})
from mcp_server import {tool_name}
result = {tool_name}({args_str})
# result 是字符串（_wrap 格式），解析出 JSON 部分
if isinstance(result, str):
    lines = result.split('\\n\\n', 1)
    qc = json.loads(lines[0]) if lines else {{}}
    content = lines[1] if len(lines) > 1 else ''
    print(json.dumps({{"_qc": qc.get("_qc", {{}}), "raw": content}}, ensure_ascii=False))
else:
    print(json.dumps(result, ensure_ascii=False))
"""
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300,
            cwd=TRADING_SYSTEM_PATH
        )
        if result.returncode == 0 and result.stdout.strip():
            return _loads_last_json(result.stdout)
        raise HTTPException(status_code=500, detail=result.stderr[-300:] or "扫描失败")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="扫描超时（>5分钟）")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"返回数据解析失败: {e}")


def _contract_failure(module: str, error: str) -> dict:
    """本地契约工具失败时的统一 HTTP 返回，避免 API 层伪造 success。"""
    return {
        "items": [],
        "_qc": {
            "status": "failure",
            "completeness": 0,
            "sources": [],
            "fallback_source": None,
            "missing_dimensions": [module],
            "stale_data": [],
            "error": error,
        },
        "meta": {"module": module, "count": 0},
    }


@router.get("/xueqiu-hot")
async def xueqiu_hot():
    """雪球热门讨论"""
    return _call_mcp_tool("xueqiu_fetch", query="热门讨论")


@router.get("/xueqiu-hot-stock")
async def xueqiu_hot_stock():
    """雪球热股榜"""
    return _call_mcp_tool("xueqiu_fetch", query="热股榜")


@router.get("/discussions")
async def intel_discussions(limit: int = Query(10, ge=1, le=50)):
    """市场情报 Sidebar：热门讨论。返回 {items, _qc, meta} 契约。"""
    try:
        import market_intel
        return market_intel.discussions(limit=limit)
    except Exception as e:
        return _contract_failure("discussions", str(e))


@router.get("/hot-stocks")
async def intel_hot_stocks(limit: int = Query(10, ge=1, le=50)):
    """市场情报 Sidebar：热股榜。返回 {items, _qc, meta} 契约。"""
    try:
        import market_intel
        return market_intel.hot_stocks(limit=limit)
    except Exception as e:
        return _contract_failure("hot_stocks", str(e))


@router.get("/watch-alerts")
async def intel_watch_alerts(change_threshold: float = Query(3.0, ge=0, le=20)):
    """市场情报 Sidebar：自选股异动。返回 {items, _qc, meta} 契约。"""
    try:
        import market_intel
        return market_intel.watch_alerts(change_threshold=change_threshold)
    except Exception as e:
        return _contract_failure("watch_alerts", str(e))


@router.get("/research")
async def intel_research(
    limit: int = Query(10, ge=1, le=50),
    mode: str = Query("batch", pattern="^(batch|deep)$"),
    max_llm: int = Query(0, ge=0, le=20),
):
    """市场情报 Sidebar：脱水研报。默认不在 HTTP 请求里触发 LLM，优先读预计算缓存。"""
    try:
        if not isinstance(mode, str):
            mode = "batch"
        import research_digest
        return research_digest.latest(limit=limit, digest_mode=mode, max_llm_per_call=max_llm)
    except Exception as e:
        return _contract_failure("research", str(e))


@router.get("/all")
async def intel_all(
    limit: int = Query(10, ge=1, le=50),
    mode: str = Query("batch", pattern="^(batch|deep)$"),
    modules: str = Query("", description="逗号分隔：discussions,hot_stocks,watch_alerts,research"),
):
    """市场情报 Sidebar：四板块聚合。返回 {panels, _qc, meta}。"""
    try:
        if not isinstance(mode, str):
            mode = "batch"
        if not isinstance(modules, str):
            modules = ""
        import market_intel
        selected = [m.strip() for m in modules.split(",") if m.strip()] or None
        return market_intel.aggregate(modules=selected, limit=limit, digest_mode=mode)
    except Exception as e:
        return {
            "panels": {},
            "_qc": {
                "status": "failure",
                "completeness": 0,
                "sources": [],
                "fallback_source": None,
                "missing_dimensions": ["market_intel"],
                "stale_data": [],
                "error": str(e),
            },
            "meta": {"modules": [], "limit": limit},
        }


@router.get("/market-context")
async def market_context_layer():
    """今日市场画像：只读市场结构摘要，不写库，不返回交易指令。"""
    try:
        import market_context
        return await market_context.snapshot()
    except Exception as e:
        return {
            "title": "今日市场画像",
            "positioning": "市场结构摘要 / Market Context Layer",
            "generated_at": "",
            "date_label": "",
            "conclusion": "数据不足，暂不下结论",
            "metrics": {},
            "context": {
                "market_preference": "数据不足，暂不下结论",
                "theme_concentration": "数据不足，暂不下结论",
                "breadth": "数据不足，暂不下结论",
                "top_sector": None,
            },
            "themes": [],
            "roles": {
                "streak_samples": [],
                "large_turnover_samples": [],
                "high_change_samples": [],
            },
            "monitoring": ["数据不足，暂不下结论"],
            "disclaimer": "本页面呈现市场结构数据，不含操作建议。仅供参考，不构成投资建议。",
            "_qc": {
                "status": "failure",
                "completeness": 0,
                "sources": [],
                "fallback_source": None,
                "missing_dimensions": ["market_context"],
                "stale_data": [],
                "error": str(e),
            },
        }


@router.get("/golden-pit")
async def golden_pit(realtime: bool = Query(False, description="是否追加实时行情（约3-4分钟）")):
    """
    黄金坑四重门扫描
    触发方式：在集合竞价输入框输入"黄金坑"、"四重门"或"ghk"
    """
    try:
        # 通过 Finance Suite MCP factor_scan 取真实 _qc，避免 API 层硬编码 sources。
        cmd = [
            sys.executable, "-c",
            f"""
import json, sys
sys.path.insert(0, {repr(FINANCE_SUITE_PATH)})
sys.path.insert(0, {repr(os.path.join(FINANCE_SUITE_PATH, "scripts"))})
from mcp_server import factor_scan
print(json.dumps(factor_scan(), ensure_ascii=False))
"""
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300,
            cwd=FINANCE_SUITE_PATH
        )
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr[-300:] or "扫描失败")

        wrapped = _loads_last_json(result.stdout)
        parsed = _parse_mcp_response(wrapped)
        scan_data = parsed.get("data") or {}
        real_qc = scan_data.get("_qc") if isinstance(scan_data.get("_qc"), dict) else parsed.get("_qc", {})
        if not scan_data and parsed.get("raw"):
            scan_data = {"raw": parsed["raw"]}

        # 转换为前端期望的格式
        signals = scan_data.get("signals", []) if isinstance(scan_data, dict) else []
        hits = []
        for s in signals:
            hits.append({
                "code": s.get("code"),
                "name": s.get("name", ""),
                "close": s.get("close"),
                "composite": s.get("composite_score"),
                "dist_to_lower_pct": s.get("dist_to_lower_pct", 999),
                "gates_passed": 4,
            })

        if not real_qc:
            real_qc = {
                "status": "success" if hits else "partial",
                "completeness": 1.0 if hits else 0.5,
                "sources": scan_data.get("_sources", []) if isinstance(scan_data, dict) else [],
                "fallback_source": None,
                "missing_dimensions": [] if hits else ["候选信号"],
                "stale_data": [],
            }

        return {
            "hits": hits,
            "watchlist": [],
            "market_env": scan_data.get("market_env", {}),
            "scan_date": scan_data.get("scan_date", ""),
            "source_used": scan_data.get("source_used") or real_qc.get("fallback_source"),
            "fallback_chain": scan_data.get("fallback_chain", []),
            "fallback_triggered": scan_data.get("fallback_triggered", False),
            "_qc": real_qc,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
