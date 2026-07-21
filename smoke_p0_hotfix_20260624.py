#!/usr/bin/env python3
"""
P0 Hotfix 验收脚本 (2026-06-24)

验收目标:
1. stock_analysis("博纳影业") 能解析到 001330.SZ
2. 如果结构化 K线/资金流缺失,报告不出现支撑位/压力位/资金流金额
3. 报告不得再出现"基于公开价格行为推演"式免责声明
4. 搜索来源不得支撑资金技术数字
5. 回归: 博纳影业、贵州茅台、宁德时代

用法:
  python3 smoke_p0_hotfix_20260624.py

需要 MCP server 已重启,或者直接调用 stock_data.py
"""

import sys
import asyncio
import json
import re

sys.path.insert(0, "scripts")
from stock_data import resolve_stock, get_stock_full_data, format_stock_data


async def test_case(stock_name: str, expect_code: str) -> dict:
    """
    单个股票验收:
    - 名称解析是否成功
    - 数据获取是否有财报/K线/资金流
    - 格式化输出是否符合 P0-2 约束
    """
    print(f"\n{'='*60}")
    print(f"测试: {stock_name} (期望代码: {expect_code})")
    print("="*60)

    result = {"stock": stock_name, "expect_code": expect_code}

    # Step 1: 名称解析
    resolved = resolve_stock(stock_name)
    if not resolved:
        result["resolve"] = "FAIL - 解析失败"
        result["overall"] = "FAIL"
        print(f"❌ 名称解析: 失败")
        return result

    code, name = resolved
    if code != expect_code:
        result["resolve"] = f"FAIL - 解析到 {code},期望 {expect_code}"
        result["overall"] = "FAIL"
        print(f"❌ 名称解析: {name} → {code} (期望 {expect_code})")
        return result

    result["resolve"] = "PASS"
    print(f"✓ 名称解析: {name} → {code}")

    # Step 2: 数据获取
    try:
        data = await get_stock_full_data(code)
    except Exception as e:
        result["data_fetch"] = f"FAIL - 异常: {str(e)}"
        result["overall"] = "FAIL"
        print(f"❌ 数据获取异常: {e}")
        return result

    has_financials = bool(data.get("financials"))
    has_klines = bool(data.get("klines"))
    has_flow = bool(data.get("capital_flow"))

    result["has_financials"] = has_financials
    result["has_klines"] = has_klines
    result["has_flow"] = has_flow

    print(f"  财报: {'✓ 有数据' if has_financials else '✗ 空'}")
    print(f"  K线: {'✓ 有数据' if has_klines else '✗ 空'}")
    print(f"  资金流: {'✓ 有数据' if has_flow else '✗ 空'}")

    # Step 3: 格式化输出 & P0-2 约束检查
    formatted = format_stock_data(data, stock_name=name, stock_code=code)

    violations = []

    # 检查违规模式
    if not has_klines or not has_flow:
        # 技术面数据缺失时,不应出现具体点位
        patterns = [
            (r"压力位[:：]\s*[\d\.]+\s*元", "出现压力位具体点位(K线数据缺失)"),
            (r"支撑位[:：]\s*[\d\.]+\s*元", "出现支撑位具体点位(K线数据缺失)"),
            (r"主力.*流[入出][:：]\s*[\d\.]+\s*[亿万]", "出现资金流金额(资金流数据缺失)"),
            (r"北向资金.*[:：]\s*[\d\.]+\s*[亿万]", "出现北向资金金额(数据缺失)"),
        ]
        for pattern, desc in patterns:
            if re.search(pattern, formatted):
                violations.append(desc)

    # 检查免责声明(禁止"基于公开价格行为推演")
    if "公开价格行为推演" in formatted or "价格行为推演" in formatted:
        violations.append("出现'公开价格行为推演'免责声明")

    if "非技术指标计算" in formatted and (not has_klines or not has_flow):
        violations.append("数据缺失时仍生成'非技术指标计算'兜底话术")

    # 检查是否正确标注"暂不可用"
    if not has_flow:
        if "[资金面数据暂不可用]" not in formatted and "[技术面数据暂不可用]" not in formatted:
            violations.append("资金流数据缺失但未标注'暂不可用'")

    if violations:
        result["p0_2_check"] = f"FAIL - {len(violations)} 项违规"
        result["violations"] = violations
        result["overall"] = "FAIL"
        print(f"\n❌ P0-2 约束检查: {len(violations)} 项违规")
        for v in violations:
            print(f"   - {v}")
    else:
        result["p0_2_check"] = "PASS"
        result["overall"] = "PASS"
        print(f"\n✓ P0-2 约束检查: 无违规")

    # 保存格式化输出样本(前500字符)
    result["formatted_sample"] = formatted[:500] + "..." if len(formatted) > 500 else formatted

    return result


async def main():
    print("="*60)
    print("P0 Hotfix 验收脚本 - 2026-06-24")
    print("="*60)

    test_cases = [
        ("博纳影业", "001330"),  # 本次修复的 case
        ("贵州茅台", "600519"),  # 回归: QUICK_MAP 里的热门股
        ("宁德时代", "300750"),  # 回归: QUICK_MAP 里的热门股
    ]

    results = []
    for stock, code in test_cases:
        result = await test_case(stock, code)
        results.append(result)
        await asyncio.sleep(1)  # 防止 API 限流

    # 汇总
    print("\n" + "="*60)
    print("验收汇总")
    print("="*60)

    pass_count = sum(1 for r in results if r.get("overall") == "PASS")
    fail_count = len(results) - pass_count

    for r in results:
        status = "✓ PASS" if r["overall"] == "PASS" else "✗ FAIL"
        print(f"{status}  {r['stock']} ({r['expect_code']})")
        if r["overall"] == "FAIL":
            if "violations" in r:
                for v in r["violations"]:
                    print(f"       - {v}")

    print(f"\n总计: {pass_count}/{len(results)} 通过")

    # 保存详细结果
    with open("smoke_p0_hotfix_20260624.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n详细结果已保存: smoke_p0_hotfix_20260624.json")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
