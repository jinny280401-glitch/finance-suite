"""FastAPI watchlist endpoints for the static app.

Backs /api/watchlist/* with the existing finance-suite watchlist store.
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from backend.app.auth import get_current_user
from pydantic import BaseModel

try:
    from backend.engine.skills import watchlist as wl
except ImportError:
    wl = None

router = APIRouter(prefix="/api/watchlist")


class WatchlistAddRequest(BaseModel):
    query: str | None = None
    name: str | None = None
    code: str | None = None


class WatchlistRemoveRequest(BaseModel):
    code: str


def _resolve_code_name(query: str) -> tuple[str, str]:
    q = query.strip()
    if not q:
        raise HTTPException(status_code=400, detail="query 不能为空")

    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"] == q]
        if not row.empty:
            r = row.iloc[0]
            return q, str(r.get("名称", q))

        row = df[df["名称"] == q]
        if not row.empty:
            r = row.iloc[0]
            return str(r.get("代码", q)), q

        row = df[df["名称"].str.contains(q, na=False)]
        if not row.empty:
            r = row.iloc[0]
            return str(r.get("代码", q)), str(r.get("名称", q))
    except Exception:
        pass

    return q, q


@router.get("/list", dependencies=[Depends(get_current_user)])
async def list_stocks():
    data = wl._load()
    stocks = []
    for s in data.get("stocks", []):
        stocks.append({
            "code": s.get("code", ""),
            "name": s.get("name", ""),
            "add_date": s.get("add_date"),
            "add_price": s.get("add_price"),
            "tags": s.get("tags", []),
            "last_research": s.get("last_research_date"),
        })

    return {
        "_qc": {"status": "success", "sources": ["watchlist_json"]},
        "count": len(stocks),
        "data": [{"name": s["name"], "code": s["code"], "change": "--"} for s in stocks],
        "stocks": stocks,
    }


@router.post("/add", dependencies=[Depends(get_current_user)])
async def add_stock(req: WatchlistAddRequest):
    query = (req.query or req.name or req.code or "").strip()
    code, name = _resolve_code_name(query)

    data = wl._load()
    existing = wl._find_stock(data, code)
    if existing:
        return {
            "success": False,
            "already": True,
            "message": f"{existing.get('name', code)}({code}) 已在自选中",
        }

    stock = {
        "code": code,
        "name": name,
        "market": "A",
        "add_date": datetime.now().strftime("%Y-%m-%d"),
        "add_price": None,
        "tags": [],
        "last_research_date": None,
        "research_history": [],
        "alerts": {},
    }

    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"] == code]
        if not row.empty:
            stock["add_price"] = float(row.iloc[0].get("最新价", 0) or 0)
    except Exception:
        pass

    data.setdefault("stocks", []).append(stock)
    wl._save(data)
    return {
        "success": True,
        "message": f"已加入自选：{name}（{code}）",
        "stock": {"code": code, "name": name, "add_price": stock["add_price"]},
    }


@router.post("/remove", dependencies=[Depends(get_current_user)])
async def remove_stock(req: WatchlistRemoveRequest):
    code = req.code.strip()
    if not code:
        raise HTTPException(status_code=400, detail="code 不能为空")

    data = wl._load()
    before = len(data.get("stocks", []))
    data["stocks"] = [s for s in data.get("stocks", []) if s.get("code") != code]
    removed = before - len(data["stocks"])
    wl._save(data)
    return {
        "success": removed > 0,
        "message": f"已移除 {code}" if removed else f"{code} 不在自选中",
    }
