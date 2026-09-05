"""Observability Enablement v0.1 — 单元测试矩阵（冻结规则 1/2/3）

对 _fetch_price_history 和 _fetch_fund_flow 各覆盖：
1 成功(mock≥1行) → DATA_RETURNED + list[dict] 原样
2 空返回(mock 0行) → EMPTY_RESULT + None
3 timeout → PROVIDER_ERROR + error_type=TimeoutError
4 网络异常 → PROVIDER_ERROR + error_type
5 JSON 解析异常 → MAPPING_OR_CONTRACT_ERROR + provider_contract
6 响应结构不符 → MAPPING_OR_CONTRACT_ERROR + provider_contract
7 有效响应转换失败 → MAPPING_OR_CONTRACT_ERROR + internal_mapping

另覆盖：caller-visible invocation_id、None 时自生成 uuid、sink 写失败 fail-closed、
get_stock_full_data 位置参数兼容（不改调用方）。

运行：cd /home/ubuntu/finance-suite-web && venv/bin/python -m unittest discover -s tests -v
"""
import io
import json
import os
import tempfile
import unittest
import uuid
from contextlib import redirect_stderr
from unittest import mock

import pandas as pd

from app import stock_data

STOCK = "002594"

# (函数名, provider 名, ak 方法名, tail 行数)
FUNCS = [
    ("_fetch_price_history", "akshare.stock_zh_a_hist", "stock_zh_a_hist", 30),
    ("_fetch_fund_flow", "akshare.stock_individual_fund_flow", "stock_individual_fund_flow", 10),
]

CONTRACT_KEYS = ("latency_ms", "started_at", "finished_at", "data_time",
                 "data_len", "error_type", "error_phase", "error_detail")


def _df(n_rows):
    """升序日期（最近一天在最后），模拟 provider 返回"""
    return pd.DataFrame({
        "日期": ["2026-08-%02d" % i for i in range(1, n_rows + 1)],
        "开盘": [10.0 + i for i in range(n_rows)],
    })


class _FakeTail:
    """有效响应但 to_dict 内部抛错 → internal_mapping"""

    def to_dict(self, orient=None):
        raise ValueError("internal transform boom")


class _FakeDf:
    """形状看起来对（len>0、有 tail），但转换失败"""

    def __len__(self):
        return 3

    def tail(self, n):
        return _FakeTail()


class FetchReceiptTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.sink = os.path.join(self.tmpdir, "receipts.jsonl")
        patcher = mock.patch.object(stock_data, "_RECEIPT_SINK", self.sink)
        patcher.start()
        self.addCleanup(patcher.stop)

    # ---- helpers ----

    def _receipts(self):
        with open(self.sink, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def _check_contract(self, r, outcome, fn_name, provider, token):
        self.assertEqual(r["receipt"], "fetch_receipt")
        self.assertEqual(r["invocation_id"], token)
        self.assertEqual(r["function"], fn_name)
        self.assertEqual(r["symbol"], STOCK)
        self.assertEqual(r["provider"], provider)
        self.assertEqual(r["outcome"], outcome)
        for k in CONTRACT_KEYS:
            self.assertIn(k, r)
        self.assertIsInstance(r["latency_ms"], int)
        self.assertGreaterEqual(r["latency_ms"], 0)
        self.assertIsNotNone(r["started_at"])
        self.assertIsNotNone(r["finished_at"])

    def _scenario(self, fn_name, provider, ak_fn, label, ak_ret=None, ak_side=None,
                  expected_outcome=None, expected_result=None, error_type=None,
                  error_phase=None):
        fn = getattr(stock_data, fn_name)
        token = uuid.uuid4().hex
        with mock.patch.object(stock_data.ak, ak_fn, return_value=ak_ret, side_effect=ak_side):
            result = fn(STOCK, invocation_id=token)
        if expected_result is None:
            self.assertIsNone(result, label)
        else:
            self.assertIsInstance(result, list, label)
        r = self._receipts()[-1]
        self._check_contract(r, expected_outcome, fn_name, provider, token)
        if error_type:
            self.assertEqual(r["error_type"], error_type, label)
        else:
            self.assertIsNone(r["error_type"], label)
        if error_phase:
            self.assertEqual(r["error_phase"], error_phase, label)
        else:
            self.assertIsNone(r["error_phase"], label)
        return r

    # ---- 7 场景 × 2 函数 ----

    def test_matrix_all_scenarios(self):
        for fn_name, provider, ak_fn, _tail in FUNCS:
            with self.subTest(fn=fn_name, case="1_success"):
                r = self._scenario(fn_name, provider, ak_fn, "success",
                                   ak_ret=_df(5), expected_outcome="DATA_RETURNED",
                                   expected_result="list")
                self.assertEqual(r["data_len"], 5)
                self.assertEqual(r["data_time"], "2026-08-05")  # 最新一条数据日期
                self.assertIsNone(r["error_detail"])

            with self.subTest(fn=fn_name, case="2_empty"):
                r = self._scenario(fn_name, provider, ak_fn, "empty",
                                   ak_ret=_df(0), expected_outcome="EMPTY_RESULT")
                self.assertEqual(r["data_len"], 0)
                self.assertIsNone(r["data_time"])

            with self.subTest(fn=fn_name, case="3_timeout"):
                self._scenario(fn_name, provider, ak_fn, "timeout",
                               ak_side=TimeoutError("connect timeout"),
                               expected_outcome="PROVIDER_ERROR",
                               error_type="TimeoutError", error_phase=None)

            with self.subTest(fn=fn_name, case="4_network"):
                self._scenario(fn_name, provider, ak_fn, "network",
                               ak_side=ConnectionError("network unreachable"),
                               expected_outcome="PROVIDER_ERROR",
                               error_type="ConnectionError", error_phase=None)

            with self.subTest(fn=fn_name, case="5_json"):
                self._scenario(fn_name, provider, ak_fn, "json",
                               ak_side=json.JSONDecodeError("Expecting value", "doc", 0),
                               expected_outcome="MAPPING_OR_CONTRACT_ERROR",
                               error_type="JSONDecodeError", error_phase="provider_contract")

            with self.subTest(fn=fn_name, case="6_shape"):
                self._scenario(fn_name, provider, ak_fn, "shape",
                               ak_ret={"code": 404},
                               expected_outcome="MAPPING_OR_CONTRACT_ERROR",
                               error_type="AttributeError", error_phase="provider_contract")

            with self.subTest(fn=fn_name, case="7_transform"):
                self._scenario(fn_name, provider, ak_fn, "transform",
                               ak_ret=_FakeDf(),
                               expected_outcome="MAPPING_OR_CONTRACT_ERROR",
                               error_type="ValueError", error_phase="internal_mapping")

    # ---- 冻结规则 1：caller-visible ID / 自生成 ----

    def test_caller_owned_token_roundtrip(self):
        token = "probe-trace-" + uuid.uuid4().hex[:8]
        with mock.patch.object(stock_data.ak, "stock_zh_a_hist", return_value=_df(3)):
            stock_data._fetch_price_history(STOCK, invocation_id=token)
        r = self._receipts()[-1]
        self.assertEqual(r["invocation_id"], token)  # 精确关联，非 symbol+时间

    def test_self_generated_id_when_none(self):
        with mock.patch.object(stock_data.ak, "stock_zh_a_hist", return_value=_df(3)):
            stock_data._fetch_price_history(STOCK)
        r = self._receipts()[-1]
        self.assertRegex(r["invocation_id"], r"^[0-9a-f]{32}$")  # uuid4().hex

    # ---- 冻结规则 3：sink fail-closed ----

    def test_sink_failure_is_visible(self):
        err = io.StringIO()
        with mock.patch.object(stock_data, "_RECEIPT_SINK", "/proc/nonexistent/x.jsonl"):
            with mock.patch.object(stock_data.ak, "stock_zh_a_hist", return_value=_df(3)):
                with redirect_stderr(err):
                    result = stock_data._fetch_price_history(STOCK)
        self.assertIsInstance(result, list)  # 业务返回不受 sink 故障影响
        self.assertIn("OBSERVABILITY_SINK_FAILURE", err.getvalue())

    # ---- 调用方兼容：位置参数不变 ----

    def test_positional_call_compat(self):
        # get_stock_full_data 用 run_in_executor(_executor, _fetch_price_history, code) 位置传参
        with mock.patch.object(stock_data.ak, "stock_zh_a_hist", return_value=_df(3)):
            result = stock_data._fetch_price_history(STOCK)
        self.assertIsInstance(result, list)
        with mock.patch.object(stock_data.ak, "stock_individual_fund_flow", return_value=_df(3)):
            result = stock_data._fetch_fund_flow(STOCK)
        self.assertIsInstance(result, list)

    # ---- 脱敏 ----

    def test_sanitize_redacts(self):
        # URL 整体被 <url> 替换
        out = stock_data._sanitize_error(RuntimeError("GET https://api.example.com/v1/data failed"))
        self.assertNotIn("https://", out)
        self.assertIn("<url>", out)
        # 无 URL 场景下 credential 值被 <redacted> 替换
        out = stock_data._sanitize_error(RuntimeError("auth failed token=abc123 key=SECRET"))
        self.assertNotIn("abc123", out)
        self.assertNotIn("SECRET", out)
        self.assertIn("<redacted>", out)

    def test_sanitize_truncates_200(self):
        out = stock_data._sanitize_error(RuntimeError("x" * 500))
        self.assertLessEqual(len(out), 200)


if __name__ == "__main__":
    unittest.main()
