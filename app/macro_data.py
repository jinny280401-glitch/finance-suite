"""
AkShare 宏观经济数据获取模块
通过国家统计局/央行等数据源获取宏观经济结构化数据
所有函数经过验证，参数与AkShare 1.18.48一致

独立CLI脚本，无内部依赖
用法: python3 macro_data.py --query "宏观经济"
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
import re

import akshare as ak

_executor = ThreadPoolExecutor(max_workers=4)


def _parse_period(value):
    """Parse AkShare mixed macro period values into comparable dates."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime()

    text = str(value).strip()
    if not text:
        return None

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            if fmt == "%Y%m%d":
                if re.match(r"^\d{8}$", text):
                    return datetime.strptime(text, fmt)
            elif re.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$", text[:10]):
                return datetime.strptime(text[:10], fmt)
        except ValueError:
            pass

    year_match = re.search(r"(19|20)\d{2}", text)
    if not year_match:
        return None
    year = int(year_match.group(0))

    month_match = re.search(r"(\d{1,2})\s*月", text)
    if month_match:
        month = max(1, min(12, int(month_match.group(1))))
        return datetime(year, month, 1)

    quarter_match = re.search(r"第\s*(\d)(?:-(\d))?\s*季度", text)
    if quarter_match:
        quarter = int(quarter_match.group(2) or quarter_match.group(1))
        quarter = max(1, min(4, quarter))
        return datetime(year, quarter * 3, 1)

    return datetime(year, 1, 1)


def _record_period(record):
    for field, value in record.items():
        field_text = str(field)
        if any(token in field_text for token in ("日期", "月份", "季度", "TRADE_DATE", "date", "Date")):
            parsed = _parse_period(value)
            if parsed:
                return parsed
    for value in record.values():
        parsed = _parse_period(value)
        if parsed:
            return parsed
    return datetime.min


def _latest_records(df, limit):
    records = df.to_dict(orient="records")
    return sorted(records, key=_record_period)[-limit:]


def _fetch_gdp():
    """GDP数据"""
    try:
        df = ak.macro_china_gdp()
        return _latest_records(df, 8)
    except Exception:
        return None


def _fetch_cpi():
    """CPI数据"""
    try:
        df = ak.macro_china_cpi()
        return _latest_records(df, 12)
    except Exception:
        return None


def _fetch_pmi():
    """PMI数据"""
    try:
        df = ak.macro_china_pmi()
        return _latest_records(df, 12)
    except Exception:
        return None


def _fetch_money_supply():
    """M2货币供应"""
    try:
        df = ak.macro_china_money_supply()
        return _latest_records(df, 12)
    except Exception:
        return None


def _fetch_lpr():
    """LPR利率"""
    try:
        df = ak.macro_china_lpr()
        return _latest_records(df, 12)
    except Exception:
        return None


def _fetch_shibor():
    """SHIBOR利率"""
    try:
        df = ak.rate_interbank(
            market="上海银行间同业拆放利率(Shibor)",
            symbol="隔夜",
            need_page="1",
        )
        return df.tail(30).to_dict(orient="records")
    except Exception:
        return None


async def get_macro_data() -> dict:
    """并发获取所有宏观经济数据"""
    loop = asyncio.get_event_loop()
    tasks = {
        "gdp": loop.run_in_executor(_executor, _fetch_gdp),
        "cpi": loop.run_in_executor(_executor, _fetch_cpi),
        "pmi": loop.run_in_executor(_executor, _fetch_pmi),
        "money_supply": loop.run_in_executor(_executor, _fetch_money_supply),
        "lpr": loop.run_in_executor(_executor, _fetch_lpr),
    }
    results = {}
    for key, task in tasks.items():
        try:
            results[key] = await task
        except Exception:
            results[key] = None
    return results


def format_macro_data(data: dict) -> str:
    """格式化宏观数据为文本"""
    parts = ["=== 宏观经济结构化数据（来源：国家统计局/央行）===\n"]
    for key, records in data.items():
        if records:
            parts.append(f"【{key.upper()}】")
            for r in records[-6:]:
                parts.append(f"  {r}")
            parts.append("")
    return "\n".join(parts)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="获取宏观经济数据（GDP/CPI/PMI/M2/LPR）")
    parser.add_argument("--query", type=str, default="宏观经济", help="查询内容（当前忽略，获取全部宏观数据）")
    args = parser.parse_args()

    print("正在获取宏观经济数据...", flush=True)

    data = asyncio.run(get_macro_data())
    output = format_macro_data(data)
    print(output)
