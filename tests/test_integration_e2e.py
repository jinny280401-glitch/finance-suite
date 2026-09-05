"""
端到端集成测试：真实登录 → 真实分析 → 验证每个数据维度。

运行方式（需要本地服务在 8001 端口运行）：
    .venv/bin/python tests/test_integration_e2e.py

或在 pytest 中：
    pytest tests/test_integration_e2e.py -v --timeout=180
"""

import sys
import json
import time
import requests
import pytest

BASE_URL = "http://localhost:8001"
TEST_STOCK = "002594"  # 比亚迪
TEST_STOCK_NAME = "比亚迪"


# ── 辅助函数 ──────────────────────────────────────────────────

def _login() -> str:
    """登录获取 token"""
    r = requests.post(f"{BASE_URL}/api/login", json={
        "username": "admin",
        "password": "admin123",
    }, timeout=10)
    assert r.status_code == 200, f"登录失败: {r.status_code} {r.text}"
    data = r.json()
    token = data.get("token") or data.get("access_token", "")
    assert token, f"登录响应无 token: {data.keys()}"
    return token


def _analyze(token: str, stock_code: str, skill_type: str = "stock") -> dict:
    """触发分析并返回 JSON 响应"""
    r = requests.post(f"{BASE_URL}/api/analyze", json={
        "skill_type": skill_type,
        "query": stock_code,
    }, headers={
        "Authorization": f"Bearer {token}",
    }, timeout=120)
    assert r.status_code == 200, f"分析请求失败: {r.status_code} {r.text}"
    return r.json()


# ── 测试用例 ──────────────────────────────────────────────────

class TestE2EStockAnalysis:
    """个股分析端到端测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """检查服务可用性"""
        try:
            r = requests.get(f"{BASE_URL}/api/health", timeout=5)
            if r.status_code != 200:
                pytest.skip(f"本地服务未运行或不可用: {BASE_URL}")
        except requests.ConnectionError:
            pytest.skip(f"本地服务未运行: {BASE_URL}")
        self.token = _login()

    def test_01_response_structure(self):
        """验证响应包含所有必要字段"""
        data = _analyze(self.token, TEST_STOCK)

        # 核心字段必须存在
        assert "success" in data, "缺少 success 字段"
        assert "result" in data, "缺少 result 字段"
        assert "_qc" in data, "缺少 _qc 字段"
        assert "sources" in data, "缺少 sources 字段"

        # 分析必须成功
        assert data["success"] is True, f"分析失败: {data}"

        # 报告必须有实质内容
        assert len(data["result"]) > 500, \
            f"报告内容过短: {len(data['result'])} 字符"

    def test_02_qc_envelope(self):
        """验证 QC 信息信封"""
        data = _analyze(self.token, TEST_STOCK)
        qc = data["_qc"]

        assert "status" in qc, "QC 缺少 status"
        assert qc["status"] in ("success", "partial"), \
            f"QC 状态异常: {qc['status']}"

    def test_03_data_dimensions(self):
        """验证各数据维度返回情况"""
        data = _analyze(self.token, TEST_STOCK)
        qc = data.get("_qc", {})
        dims = qc.get("dimension_status", {})

        # 至少有一半维度可用
        available = [k for k, v in dims.items() if v == "available"]
        assert len(available) >= len(dims) // 2, \
            f"可用维度过少: {available}/{list(dims.keys())}"

        # 打印维度状态（供调试）
        print(f"\n维度状态 ({len(available)}/{len(dims)} available):")
        for k, v in sorted(dims.items()):
            flag = "✅" if v == "available" else "⚠️"
            print(f"  {flag} {k}: {v}")

    def test_04_no_type_errors(self):
        """验证没有参数名不匹配导致的 TypeError。

        检查方式：如果 success=True 且 result 有内容，说明没有未捕获的 TypeError。
        同时检查 fund_flow 的失败原因不是 TypeError（网络问题可以接受）。
        """
        data = _analyze(self.token, TEST_STOCK)

        # 分析必须成功（即使部分维度缺失）
        assert data["success"] is True

        # 检查 QC 日志中是否有 TypeError
        qc = data.get("_qc", {})
        provider_log = qc.get("provider_log", [])
        type_errors = [
            entry for entry in provider_log
            if "TypeError" in str(entry.get("exception_message", ""))
        ]
        assert len(type_errors) == 0, \
            f"发现 TypeError（参数名不匹配）: {type_errors}"

    def test_05_sources_populated(self):
        """验证数据源列表有内容"""
        data = _analyze(self.token, TEST_STOCK)
        sources = data.get("sources", [])
        assert len(sources) >= 3, \
            f"数据源过少: {len(sources)}"
        print(f"\n数据源: {len(sources)} 条")
        for s in sources[:5]:
            if isinstance(s, dict):
                print(f"  - {s.get('source', s.get('name', str(s)[:60]))}")
            else:
                print(f"  - {str(s)[:60]}")


class TestE2EAuth:
    """认证流程端到端测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        try:
            r = requests.get(f"{BASE_URL}/api/health", timeout=5)
            if r.status_code != 200:
                pytest.skip(f"本地服务不可用")
        except requests.ConnectionError:
            pytest.skip(f"本地服务未运行")

    def test_login_success(self):
        """正常登录"""
        r = requests.post(f"{BASE_URL}/api/login", json={
            "username": "admin",
            "password": "admin123",
        }, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data.get("success") is True
        assert "token" in data

    def test_unauthenticated_rejected(self):
        """未认证请求被拒绝"""
        r = requests.post(f"{BASE_URL}/api/analyze", json={
            "skill_type": "stock",
            "query": TEST_STOCK,
        }, timeout=10)
        assert r.status_code in (401, 403)

    def test_check_auth(self):
        """认证状态检查"""
        token = _login()
        r = requests.get(f"{BASE_URL}/api/check-auth", headers={
            "Authorization": f"Bearer {token}",
        }, timeout=10)
        assert r.status_code == 200


class TestE2EIntelAPI:
    """Intel API 端到端测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        try:
            r = requests.get(f"{BASE_URL}/api/health", timeout=5)
            if r.status_code != 200:
                pytest.skip(f"本地服务不可用")
        except requests.ConnectionError:
            pytest.skip(f"本地服务未运行")

    def test_xueqiu_hot(self):
        """雪球热门"""
        r = requests.get(f"{BASE_URL}/api/intel/xueqiu-hot", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "data" in data or "count" in data or "_qc" in data

    def test_hot_stocks(self):
        """热门股票"""
        r = requests.get(f"{BASE_URL}/api/intel/hot-stocks", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "data" in data or "count" in data

    def test_discussions(self):
        """讨论"""
        r = requests.get(f"{BASE_URL}/api/intel/discussions", timeout=15)
        assert r.status_code == 200


# ── 独立运行入口 ──────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("端到端集成测试")
    print(f"目标: {BASE_URL}")
    print(f"测试股票: {TEST_STOCK} ({TEST_STOCK_NAME})")
    print("=" * 60)

    # 检查服务
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"\n服务状态: {r.json()}")
    except Exception as e:
        print(f"\n❌ 服务不可达: {e}")
        print("请先启动: .venv/bin/uvicorn backend.app.main:app --port 8001")
        sys.exit(1)

    # 登录
    print("\n--- 认证测试 ---")
    token = _login()
    print(f"✅ 登录成功, token: {token[:20]}...")

    # 分析
    print(f"\n--- 个股分析 ({TEST_STOCK}) ---")
    t0 = time.time()
    data = _analyze(token, TEST_STOCK)
    elapsed = time.time() - t0

    print(f"✅ 分析完成 ({elapsed:.1f}s)")
    print(f"   success: {data.get('success')}")
    print(f"   result: {len(data.get('result', ''))} 字符")
    print(f"   sources: {len(data.get('sources', []))} 条")

    qc = data.get("_qc", {})
    print(f"   QC status: {qc.get('status')}")

    dims = qc.get("dimension_status", {})
    print(f"\n   维度状态 ({sum(1 for v in dims.values() if v == 'available')}/{len(dims)}):")
    for k, v in sorted(dims.items()):
        flag = "✅" if v == "available" else "⚠️"
        print(f"     {flag} {k}: {v}")

    # 检查 TypeError
    provider_log = qc.get("provider_log", [])
    type_errors = [
        e for e in provider_log
        if "TypeError" in str(e.get("exception_message", ""))
    ]
    if type_errors:
        print(f"\n❌ 发现 {len(type_errors)} 个 TypeError:")
        for e in type_errors:
            print(f"   {e.get('endpoint')}: {e.get('exception_message')}")
        sys.exit(1)
    else:
        print(f"\n✅ 无 TypeError（参数名全部匹配）")

    print(f"\n{'=' * 60}")
    print("全部通过")
    print(f"{'=' * 60}")
