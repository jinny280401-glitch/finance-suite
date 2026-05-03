"""
市场情报 API
GET /api/intel/xueqiu-hot        - 雪球热门讨论
GET /api/intel/xueqiu-hot-stock  - 雪球热股榜
GET /api/intel/golden-pit        - 黄金坑四重门扫描（?realtime=true 追加实时行情）
"""
from fastapi import APIRouter, HTTPException, Query
import json
import subprocess
import sys
import os

router = APIRouter(prefix="/api/intel")

FINANCE_SUITE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRADING_SYSTEM_PATH = os.path.join(os.path.dirname(FINANCE_SUITE_PATH), "trading-system")


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
            return json.loads(result.stdout.strip())
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
            return json.loads(result.stdout.strip())
        raise HTTPException(status_code=500, detail=result.stderr[-300:] or "扫描失败")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="扫描超时（>5分钟）")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"返回数据解析失败: {e}")


@router.get("/xueqiu-hot")
async def xueqiu_hot():
    """雪球热门讨论"""
    return _call_mcp_tool("xueqiu_fetch", query="热门讨论")


@router.get("/xueqiu-hot-stock")
async def xueqiu_hot_stock():
    """雪球热股榜"""
    return _call_mcp_tool("xueqiu_fetch", query="热股榜")


@router.get("/golden-pit")
async def golden_pit(realtime: bool = Query(False, description="是否追加实时行情（约3-4分钟）")):
    """
    黄金坑四重门扫描
    触发方式：在集合竞价输入框输入"黄金坑"、"四重门"或"ghk"
    """
    try:
        # 直接调用 trading-system 的 factor_scan 脚本（更稳定）
        factor_scan_script = os.path.join(TRADING_SYSTEM_PATH, "scripts", "factor_scan.py")
        cmd = [sys.executable, factor_scan_script, "--json"]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300,
            cwd=TRADING_SYSTEM_PATH
        )
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr[-300:] or "扫描失败")

        stdout = result.stdout.strip()
        json_start = stdout.find("{")
        if json_start < 0:
            raise HTTPException(status_code=500, detail="扫描结果格式异常")

        scan_data = json.loads(stdout[json_start:])

        # 转换为前端期望的格式
        signals = scan_data.get("signals", [])
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

        return {
            "hits": hits,
            "watchlist": [],
            "market_env": scan_data.get("market_env", {}),
            "scan_date": scan_data.get("scan_date", ""),
            "_qc": {
                "status": "success" if hits or scan_data else "partial",
                "completeness": 1.0 if hits else 0.5,
                "sources": ["baostock", "akshare"],
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
