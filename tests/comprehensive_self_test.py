#!/usr/bin/env python3
"""全面自测脚本：对比本地重构环境与生产环境的功能和数据一致性"""
import asyncio, json, sys, os, time
sys.path.insert(0, os.getcwd())

LOCAL_BASE = "http://127.0.0.1:8899"
PROD_BASE = "https://www.touziagent.com"

def color(text, c):
    colors = {"green": "\033[92m", "red": "\033[91m", "yellow": "\033[93m", "cyan": "\033[96m", "reset": "\033[0m", "bold": "\033[1m"}
    return f"{colors.get(c, '')}{text}{colors['reset']}"

def get_token(base, username="30440", password="30440"):
    import urllib.request
    data = json.dumps({"username": username, "password": password}).encode()
    req = urllib.request.Request(f"{base}/api/login", data=data, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        return result.get("token", "")
    except Exception as e:
        print(f"  {color('登录失败', 'red')}: {e}")
        return ""

def api_get(url, token="", timeout=30):
    import urllib.request
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        body = resp.read()
        return resp.status, body
    except Exception as e:
        return 0, str(e).encode()

def api_post(url, data, token="", timeout=60):
    import urllib.request
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        body = resp.read()
        return resp.status, body
    except Exception as e:
        return 0, str(e).encode()

def check_page(base, token, path, label):
    status, body = api_get(f"{base}{path}", token, timeout=10)
    body_str = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
    has_form = "analyzeForm" in body_str or "form" in body_str.lower()
    has_input = 'type="text"' in body_str or '<textarea' in body_str or 'type="hidden"' in body_str
    has_js = "backend.app.js" in body_str
    ok = status == 200 and len(body_str) > 500
    return ok, status, len(body_str), has_form, has_input, has_js

def check_api(base, token, method, path, label, post_data=None, timeout=30):
    if method == "GET":
        status, body = api_get(f"{base}{path}", token, timeout=timeout)
    else:
        status, body = api_post(f"{base}{path}", post_data or {}, token, timeout=timeout)
    body_str = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
    try:
        data = json.loads(body_str)
        has_data = bool(data)
        keys = list(data.keys())[:8]
    except:
        data = None
        has_data = len(body_str) > 10
        keys = []
    ok = status == 200 and has_data
    return ok, status, len(body_str), keys

# ============================================================
print(color("=" * 70, "bold"))
print(color("  Finance Suite 全面自测 — 本地重构 vs 生产环境", "bold"))
print(color("=" * 70, "bold"))

# 1. 获取 token
print(f"\n{color('1. 认证', 'cyan')}")
local_token = get_token(LOCAL_BASE)
prod_token = get_token(PROD_BASE)
print(f"  本地 token: {'✅ ' + local_token[:20] + '...' if local_token else color('❌ 失败', 'red')}")
print(f"  生产 token: {'✅ ' + prod_token[:20] + '...' if prod_token else color('❌ 失败', 'red')}")

# 2. 页面测试
print(f"\n{color('2. 页面渲染测试', 'cyan')}")
print(f"  {'页面':<25} {'本地HTTP':<10} {'本地大小':<10} {'表单':<6} {'输入框':<6} {'JS':<6} {'状态'}")
print(f"  {'-'*70}")

pages = [
    ("/", "首页"),
    ("/login", "登录页"),
    ("/register", "注册页"),
    ("/dashboard", "工作台"),
    ("/pricing", "定价页"),
    ("/skill/stock", "看票分析"),
    ("/skill/macro", "宏观内参"),
    ("/skill/industry", "行业报告"),
    ("/skill/auction", "集合竞价"),
    ("/skill/mckinsey", "麦肯锡报告"),
    ("/skill/video", "视频拆解"),
    ("/skill/meeting", "会议纪要"),
    ("/skill/deep-research", "深度研究"),
    ("/admin", "管理后台"),
]

page_results = []
for path, label in pages:
    ok, status, size, has_form, has_input, has_js = check_page(LOCAL_BASE, local_token, path, label)
    status_str = f"{status}"
    size_str = f"{size}"
    form_str = "✅" if has_form else ""
    input_str = "✅" if has_input else "❌"
    js_str = "✅" if has_js else "❌"
    result_str = color("✅", "green") if ok else color("❌", "red")
    print(f"  {label:<22} {status_str:<10} {size_str:<10} {form_str:<6} {input_str:<6} {js_str:<6} {result_str}")
    page_results.append((path, label, ok, status, size, has_form, has_input, has_js))

# 3. API 端点测试
print(f"\n{color('3. API 端点测试', 'cyan')}")
print(f"  {'端点':<35} {'HTTP':<6} {'大小':<10} {'Keys':<40} {'状态'}")
print(f"  {'-'*100}")

api_tests = [
    ("GET", "/api/health", "健康检查", None, 10),
    ("GET", "/api/check-auth", "认证检查", None, 10),
    ("GET", "/api/usage", "用量统计", None, 10),
    ("GET", "/api/intel/all", "情报汇总", None, 60),
    ("GET", "/api/intel/xueqiu-hot", "雪球热帖", None, 30),
    ("GET", "/api/intel/xueqiu-hot-stock", "雪球热股", None, 30),
    ("GET", "/api/intel/discussions", "讨论区", None, 30),
    ("GET", "/api/intel/hot-stocks", "热门股票", None, 30),
    ("GET", "/api/intel/watch-alerts", "关注提醒", None, 30),
    ("GET", "/api/intel/research", "研究报告", None, 30),
    ("GET", "/api/intel/market-context", "市场背景", None, 30),
    ("GET", "/api/intel/golden-pit", "黄金坑", None, 30),
    ("GET", "/api/watchlist/list", "自选股列表", None, 10),
    ("GET", "/api/admin/stats", "管理统计", None, 10),
    ("GET", "/api/admin/users", "用户列表", None, 10),
]

api_results = []
for method, path, label, post_data, timeout in api_tests:
    ok, status, size, keys = check_api(LOCAL_BASE, local_token, method, path, label, post_data, timeout)
    keys_str = ",".join(keys) if keys else "-"
    result_str = color("✅", "green") if ok else color("❌", "red")
    print(f"  {path:<35} {status:<6} {size:<10} {keys_str:<40} {result_str}")
    api_results.append((method, path, label, ok, status, size, keys))

# 4. 核心分析 API 测试
print(f"\n{color('4. 核心分析 API 测试', 'cyan')}")
analyze_tests = [
    ("stock", "比亚迪", "个股分析"),
    ("macro", "最近经济形势", "宏观分析"),
    ("auction", "今日集合竞价分析", "集合竞价"),
]

for skill_type, query, label in analyze_tests:
    print(f"\n  --- {label} ({skill_type}: {query}) ---")
    status, body = api_post(
        f"{LOCAL_BASE}/api/analyze",
        {"skill_type": skill_type, "query": query},
        local_token, timeout=120
    )
    body_str = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
    try:
        data = json.loads(body_str)
        has_qc = "_qc" in data
        has_sources = "sources" in data
        has_result = "result" in data
        result_len = len(data.get("result", ""))
        qc_status = data.get("_qc", {}).get("status", "N/A")
        source_count = len(data.get("sources", []))
        print(f"    HTTP: {status}")
        print(f"    _qc.status: {qc_status}")
        print(f"    sources: {source_count} 条")
        print(f"    result 长度: {result_len} 字符")
        print(f"    有数据来源: {'✅' if has_sources else '❌'}")
        print(f"    状态: {color('✅ 正常', 'green') if status == 200 and has_sources else color('⚠️ 异常', 'yellow')}")
    except json.JSONDecodeError:
        print(f"    {color(' JSON 解析失败', 'red')}: {body_str[:200]}")

# 5. 生产 vs 本地数据对比
print(f"\n{color('5. 生产 vs 本地 数据对比', 'cyan')}")
if prod_token and local_token:
    for skill_type, query, label in analyze_tests:
        print(f"\n  --- {label} ---")
        # 本地
        ls, lb = api_post(f"{LOCAL_BASE}/api/analyze", {"skill_type": skill_type, "query": query}, local_token, timeout=120)
        ld = json.loads(lb.decode()) if lb else {}
        # 生产
        try:
            ps, pb = api_post(f"{PROD_BASE}/api/analyze", {"skill_type": skill_type, "query": query}, prod_token, timeout=120)
            pb_str = pb.decode("utf-8", errors="replace") if isinstance(pb, bytes) else str(pb)
            pd = json.loads(pb_str) if pb_str.strip() else {}
        except (json.JSONDecodeError, Exception) as e:
            pd = {}
            print(f"    生产请求失败: {e}")
        
        # 对比
        l_sources = len(ld.get("sources", []))
        p_sources = len(pd.get("sources", []))
        l_qc = ld.get("_qc", {}).get("status", "N/A")
        p_qc = pd.get("_qc", {}).get("status", "N/A")
        l_result = len(ld.get("result", ""))
        p_result = len(pd.get("result", ""))
        
        src_match = "✅" if l_sources == p_sources else f"⚠️ 本地{l_sources} vs 生产{p_sources}"
        qc_match = "✅" if l_qc == p_qc else f"⚠️ 本地{l_qc} vs 生产{p_qc}"
        
        print(f"    数据来源: {src_match}")
        print(f"    QC 状态:  {qc_match}")
        print(f"    结果长度: 本地 {l_result} vs 生产 {p_result}")
else:
    print(f"  {color('️ 无法对比（token 获取失败）', 'yellow')}")

# 6. 汇总
print(f"\n{color('=' * 70, 'bold')}")
print(f"{color('  汇总报告', 'bold')}")
print(f"{color('=' * 70, 'bold')}")

page_ok = sum(1 for r in page_results if r[2])
page_total = len(page_results)
api_ok = sum(1 for r in api_results if r[3])
api_total = len(api_results)

print(f"\n  页面渲染: {color(f'{page_ok}/{page_total}', 'green' if page_ok == page_total else 'red')} 通过")
print(f"  API 端点: {color(f'{api_ok}/{api_total}', 'green' if api_ok == api_total else 'red')} 通过")

# 列出失败项
failed_pages = [(r[1], r[0]) for r in page_results if not r[2]]
failed_apis = [(r[2], r[1]) for r in api_results if not r[3]]
missing_inputs = [(r[1], r[0]) for r in page_results if r[2] and not r[5]]

if failed_pages:
    print(f"\n  {color('❌ 页面失败:', 'red')}")
    for label, path in failed_pages:
        print(f"    - {label} ({path})")

if failed_apis:
    print(f"\n  {color(' API 失败:', 'red')}")
    for label, path in failed_apis:
        print(f"    - {label} ({path})")

if missing_inputs:
    print(f"\n  {color('⚠️ 缺少输入框的页面:', 'yellow')}")
    for label, path in missing_inputs:
        print(f"    - {label} ({path})")

print()
