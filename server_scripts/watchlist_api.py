"""
自选股 HTTP API Blueprint
POST /api/watchlist/add   { query: "比亚迪" | "002594" }
POST /api/watchlist/remove { code: "SZ002594" }
GET  /api/watchlist/list
"""
from flask import Blueprint, request, jsonify
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import watchlist as wl

watchlist_bp = Blueprint("watchlist", __name__)


def _resolve_code_name(query: str):
    """把用户输入（名称或代码）解析为 (code, name)。
    优先用 AkShare 精确匹配，失败则原样返回。"""
    q = query.strip()
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        # 先按代码匹配
        row = df[df["代码"] == q]
        if not row.empty:
            r = row.iloc[0]
            return q, str(r.get("名称", q))
        # 再按名称匹配
        row = df[df["名称"] == q]
        if not row.empty:
            r = row.iloc[0]
            return str(r.get("代码", q)), q
        # 模糊匹配（包含）
        row = df[df["名称"].str.contains(q, na=False)]
        if not row.empty:
            r = row.iloc[0]
            return str(r.get("代码", q)), str(r.get("名称", q))
    except Exception:
        pass
    return q, q


@watchlist_bp.route("/api/watchlist/add", methods=["POST"])
def add():
    body = request.get_json(silent=True) or {}
    query = (body.get("query") or body.get("name") or "").strip()
    if not query:
        return jsonify({"success": False, "message": "query 不能为空"}), 400

    code, name = _resolve_code_name(query)

    data = wl._load()
    existing = wl._find_stock(data, code)
    if existing:
        return jsonify({
            "success": False,
            "already": True,
            "message": f"{existing['name']}({code}) 已在自选中"
        })

    from datetime import datetime
    stock = {
        "code": code,
        "name": name,
        "market": "A",
        "add_date": datetime.now().strftime("%Y-%m-%d"),
        "add_price": None,
        "tags": [],
        "last_research_date": None,
        "research_history": [],
        "alerts": {}
    }
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"] == code]
        if not row.empty:
            stock["add_price"] = float(row.iloc[0].get("最新价", 0) or 0)
    except Exception:
        pass

    data["stocks"].append(stock)
    wl._save(data)
    return jsonify({
        "success": True,
        "message": f"已加入自选：{name}（{code}）",
        "stock": {"code": code, "name": name, "add_price": stock["add_price"]}
    })


@watchlist_bp.route("/api/watchlist/remove", methods=["POST"])
def remove():
    body = request.get_json(silent=True) or {}
    code = (body.get("code") or "").strip()
    if not code:
        return jsonify({"success": False, "message": "code 不能为空"}), 400

    data = wl._load()
    before = len(data["stocks"])
    data["stocks"] = [s for s in data["stocks"] if s["code"] != code]
    removed = before - len(data["stocks"])
    wl._save(data)
    return jsonify({
        "success": removed > 0,
        "message": f"已移除 {code}" if removed else f"{code} 不在自选中"
    })


@watchlist_bp.route("/api/watchlist/list", methods=["GET"])
def list_stocks():
    data = wl._load()
    stocks = []
    for s in data.get("stocks", []):
        stocks.append({
            "code": s["code"],
            "name": s["name"],
            "add_date": s.get("add_date"),
            "add_price": s.get("add_price"),
            "tags": s.get("tags", []),
            "last_research": s.get("last_research_date"),
        })
    return jsonify({
        "_qc": {"status": "success", "sources": ["watchlist_json"]},
        "count": len(stocks),
        "data": [{"name": s["name"], "code": s["code"], "change": "--"} for s in stocks],
        "stocks": stocks
    })
