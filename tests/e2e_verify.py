"""
End-to-end verification script.
Tests the FULL chain with real external API calls:
  1. App startup + DB init
  2. Register + Login (real JWT)
  3. Stock analysis (real Qwen + real Tavily + real AkShare)
  4. Macro analysis (real Qwen + real Tavily)
"""
import sys
import os
import time

# Ensure .env is loaded
from dotenv import load_dotenv
load_dotenv()

from fastapi.testclient import TestClient

print("=" * 60)
print("Finance Suite 端到端验证")
print("=" * 60)

# ---- Step 1: App startup ----
print("\n[1/5] 启动应用...")
t0 = time.time()
from backend.app.main import app
client = TestClient(app)
print(f"  ✅ 应用启动成功 ({time.time() - t0:.1f}s)")

# ---- Step 2: Health check ----
print("\n[2/5] 健康检查...")
resp = client.get("/api/health")
assert resp.status_code == 200
print(f"  ✅ Health: {resp.json()}")

# ---- Step 3: Auth flow ----
print("\n[3/5] 认证流程...")
import random
ts = int(time.time())
test_username = f"e2e_test_{ts}"
test_email = f"e2e_{ts}@test.local"
test_password = "e2e_test_pass_123"

# Register
resp = client.post("/api/register", json={
    "username": test_username,
    "email": test_email,
    "password": test_password,
})
assert resp.status_code == 200, f"Register failed: {resp.text}"
data = resp.json()
assert data["success"] is True
token = data["token"]
print(f"  ✅ 注册成功: {test_username}")

# Login
resp = client.post("/api/login", json={
    "username": test_username,
    "password": test_password,
})
assert resp.status_code == 200
print(f"  ✅ 登录成功")

headers = {"Authorization": f"Bearer {token}"}

# Check auth
resp = client.get("/api/check-auth", headers=headers)
assert resp.status_code == 200
assert resp.json()["authenticated"] is True
print(f"  ✅ 认证检查通过: {resp.json()['username']}")

# Usage
resp = client.get("/api/usage", headers=headers)
assert resp.status_code == 200
print(f"  ✅ 用量查询: {resp.json()}")

# ---- Step 4: Stock analysis (REAL) ----
print("\n[4/5] 股票分析（真实 API 调用）...")
print("  ⏳ 正在调用 Qwen + Tavily + AkShare，可能需要 30-60 秒...")
t0 = time.time()
resp = client.post("/api/analyze", json={
    "skill_type": "stock",
    "query": "贵州茅台",
}, headers=headers, timeout=180)
elapsed = time.time() - t0

if resp.status_code == 200:
    data = resp.json()
    result = data.get("result", "")
    print(f"  ✅ 股票分析成功 ({elapsed:.1f}s)")
    print(f"     - 结果长度: {len(result)} 字符")
    print(f"     - 信源数量: {len(data.get('sources', []))}")
    print(f"     - QC 状态: {data.get('_qc', {}).get('status', 'N/A')}")
    print(f"     - 幻觉风险: {data.get('_qc', {}).get('hallucination_risk', {}).get('level', 'N/A')}")
    # Show first 200 chars of result
    preview = result[:200].replace("\n", " ")
    print(f"     - 预览: {preview}...")
else:
    print(f"  ❌ 股票分析失败: HTTP {resp.status_code}")
    print(f"     {resp.text[:500]}")

# ---- Step 5: Macro analysis (REAL) ----
print("\n[5/5] 宏观内参（真实 API 调用）...")
print("  ⏳ 正在调用 Qwen + Tavily + 事件事实预检...")
t0 = time.time()
resp = client.post("/api/analyze", json={
    "skill_type": "macro",
    "query": "美联储降息",
}, headers=headers, timeout=180)
elapsed = time.time() - t0

if resp.status_code == 200:
    data = resp.json()
    result = data.get("result", "")
    print(f"  ✅ 宏观内参成功 ({elapsed:.1f}s)")
    print(f"     - 结果长度: {len(result)} 字符")
    print(f"     - 信源数量: {len(data.get('sources', []))}")
    print(f"     - QC 状态: {data.get('_qc', {}).get('status', 'N/A')}")
    preview = result[:200].replace("\n", " ")
    print(f"     - 预览: {preview}...")
else:
    print(f"  ❌ 宏观内参失败: HTTP {resp.status_code}")
    print(f"     {resp.text[:500]}")

# ---- Summary ----
print("\n" + "=" * 60)
print("端到端验证完成")
print("=" * 60)
