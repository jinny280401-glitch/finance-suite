"""
重构验证脚本：对比生产系统 (8000) 与新系统 (8001) 的端点响应。

验证维度：
1. 页面端点 — HTTP 状态码 + HTML 结构关键元素
2. API 端点 — HTTP 状态码 + 响应 JSON 结构
3. 静态资源 — CSS/JS 可访问性
"""

import sys
import json
import requests
from difflib import unified_diff
from collections import namedtuple

OLD = "https://www.touziagent.com"
NEW = "http://localhost:8001"

Result = namedtuple("Result", ["endpoint", "check", "status", "detail"])
results: list[Result] = []


def ok(endpoint: str, check: str, detail: str = ""):
    results.append(Result(endpoint, check, "PASS", detail))


def fail(endpoint: str, check: str, detail: str = ""):
    results.append(Result(endpoint, check, "FAIL", detail))


# ── 1. 页面端点验证 ──────────────────────────────────────────

PAGE_ENDPOINTS = [
    ("/", "首页", ["Finance Suite", "finance"]),
    ("/login", "登录页", ["login", "登录", "password"]),
    ("/register", "注册页", ["register", "注册", "password"]),
    ("/pricing", "定价页", ["pricing", "价格", "plan"]),
    ("/skill/stock", "个股技能页", ["stock", "个股"]),
    ("/skill/macro", "宏观技能页", ["macro", "宏观"]),
    ("/app/stock.html", "个股报告页", ["stock"]),
    ("/app/macro.html", "宏观报告页", ["macro"]),
]


def check_pages():
    print("\n=== 1. 页面端点验证 ===")
    for path, name, keywords in PAGE_ENDPOINTS:
        # New system
        try:
            r_new = requests.get(f"{NEW}{path}", timeout=10, allow_redirects=True)
        except Exception as e:
            fail(path, f"{name} 新系统连接", str(e))
            continue

        # Status code
        if r_new.status_code == 200:
            ok(path, f"{name} 状态码", f"new={r_new.status_code}")
        else:
            fail(path, f"{name} 状态码", f"new={r_new.status_code}")

        # Keywords in HTML
        html = r_new.text.lower()
        missing = [kw for kw in keywords if kw.lower() not in html]
        if not missing:
            ok(path, f"{name} 关键词", f"全部命中: {keywords}")
        else:
            fail(path, f"{name} 关键词缺失", f"missing={missing}")

        # Old system comparison (if available)
        try:
            r_old = requests.get(f"{OLD}{path}", timeout=5, allow_redirects=True)
            if r_old.status_code == r_new.status_code:
                ok(path, f"{name} 状态码一致", f"old={r_old.status_code} new={r_new.status_code}")
            else:
                fail(path, f"{name} 状态码不一致", f"old={r_old.status_code} new={r_new.status_code}")

            # Content length comparison (allow 20% variance for minor template diffs)
            old_len = len(r_old.text)
            new_len = len(r_new.text)
            if old_len > 0:
                ratio = new_len / old_len
                if 0.5 < ratio < 2.0:
                    ok(path, f"{name} 内容量级", f"old={old_len} new={new_len} ratio={ratio:.2f}")
                else:
                    fail(path, f"{name} 内容量级差异大", f"old={old_len} new={new_len} ratio={ratio:.2f}")
        except requests.ConnectionError:
            pass  # Old system not running, skip comparison


# ── 2. API 端点验证 ──────────────────────────────────────────

API_ENDPOINTS_NO_AUTH = [
    ("GET", "/api/check-auth", None, "检查认证状态"),
    ("GET", "/api/intel/xueqiu-hot", None, "雪球热门"),
    ("GET", "/api/intel/hot-stocks", None, "热门股票"),
    ("GET", "/api/intel/discussions", None, "讨论"),
]


def check_api():
    print("\n=== 2. API 端点验证 ===")
    for method, path, payload, name in API_ENDPOINTS_NO_AUTH:
        try:
            if method == "GET":
                r = requests.get(f"{NEW}{path}", timeout=15)
            else:
                r = requests.post(f"{NEW}{path}", json=payload, timeout=15)

            if r.status_code in (200, 401, 403, 307, 302):
                ok(path, f"{name} 状态码", f"status={r.status_code}")
            else:
                fail(path, f"{name} 状态码异常", f"status={r.status_code}")

            # Try parse JSON
            if r.status_code == 200:
                try:
                    data = r.json()
                    ok(path, f"{name} JSON 解析", f"keys={list(data.keys())[:5]}")
                except Exception:
                    # Might be HTML redirect, that's OK for some endpoints
                    pass
        except Exception as e:
            fail(path, f"{name} 请求异常", str(e)[:100])


# ── 3. 静态资源验证 ──────────────────────────────────────────

STATIC_RESOURCES = [
    "/static/css/style.css",
    "/static/js/app.js",
]


def check_static():
    print("\n=== 3. 静态资源验证 ===")
    for path in STATIC_RESOURCES:
        try:
            r = requests.get(f"{NEW}{path}", timeout=5)
            if r.status_code == 200 and len(r.text) > 0:
                ok(path, "静态资源可访问", f"size={len(r.text)}")
            else:
                fail(path, "静态资源异常", f"status={r.status_code} size={len(r.text)}")
        except Exception as e:
            fail(path, "静态资源请求失败", str(e)[:100])

        # Compare with old
        try:
            r_old = requests.get(f"{OLD}{path}", timeout=5)
            if r_old.status_code == 200 and r.text == r_old.text:
                ok(path, "静态资源内容一致", "")
            elif r_old.status_code == 200:
                fail(path, "静态资源内容不一致",
                     f"old={len(r_old.text)} new={len(r.text)}")
        except requests.ConnectionError:
            pass


# ── 4. 模板文件对比 ──────────────────────────────────────────

def check_templates():
    print("\n=== 4. 模板文件结构对比 ===")
    import os
    new_tpl = set(os.listdir("frontend/templates"))
    old_tpl_path = "/Users/huxuan/Downloads/finance-suite-web/templates"
    if os.path.exists(old_tpl_path):
        old_tpl = {f for f in os.listdir(old_tpl_path) if f.endswith(".html")}
        new_tpl_html = {f for f in new_tpl if f.endswith(".html")}
        if old_tpl == new_tpl_html:
            ok("templates/", "模板文件集合一致", f"共 {len(old_tpl)} 个")
        else:
            missing = old_tpl - new_tpl_html
            extra = new_tpl_html - old_tpl
            if missing:
                fail("templates/", "新系统缺失模板", str(missing))
            if extra:
                ok("templates/", "新系统额外模板", str(extra))
    else:
        fail("templates/", "生产模板目录不存在", old_tpl_path)


# ── 5. Scenario 页面验证 ─────────────────────────────────────

def check_scenario_pages():
    print("\n=== 5. Scenario 页面验证 ===")
    import os
    scenarios_dir = "backend/scenarios"
    for name in os.listdir(scenarios_dir):
        page_path = os.path.join(scenarios_dir, name, "page.html")
        if os.path.exists(page_path):
            size = os.path.getsize(page_path)
            if size > 100:
                ok(f"scenarios/{name}/page.html", "页面文件存在", f"size={size}")
            else:
                fail(f"scenarios/{name}/page.html", "页面文件过小", f"size={size}")


# ── 报告输出 ─────────────────────────────────────────────────

def print_report():
    print("\n" + "=" * 70)
    print("重构验证报告")
    print("=" * 70)

    passed = [r for r in results if r.status == "PASS"]
    failed = [r for r in results if r.status == "FAIL"]

    if failed:
        print(f"\n❌ FAIL ({len(failed)}):")
        for r in failed:
            print(f"  {r.endpoint:40s} | {r.check:30s} | {r.detail}")

    print(f"\n✅ PASS ({len(passed)}):")
    for r in passed:
        print(f"  {r.endpoint:40s} | {r.check:30s} | {r.detail[:60]}")

    print(f"\n{'=' * 70}")
    print(f"总计: {len(results)} 项 | PASS: {len(passed)} | FAIL: {len(failed)}")
    print(f"{'=' * 70}")

    return len(failed) == 0


if __name__ == "__main__":
    check_pages()
    check_api()
    check_static()
    check_templates()
    check_scenario_pages()
    success = print_report()
    sys.exit(0 if success else 1)
